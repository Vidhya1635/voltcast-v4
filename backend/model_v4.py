"""
Model inference module for the V4 Hybrid Model.
Loads XGBoost and PyTorch DL ensemble, and performs blended inference.
"""
import os
import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from config import XGB_MODEL_PATH, DL_MODEL_PATHS, BLEND_ALPHA, CONFIG_PATH, TARGET_SCALER_PATH, FEATURE_SCALER_PATH
from features import engineer_xgb_features

# ── DL Model Architecture (Replicated from V4 Notebook) ────────────────

class LightCNN(nn.Module):
    def __init__(self, ch, dropout=0.15):
        super().__init__()
        self.conv3 = nn.Conv1d(ch, ch, 3, padding=1)
        self.conv7 = nn.Conv1d(ch, ch, 7, padding=3)
        self.bn = nn.BatchNorm1d(ch * 2)
        self.proj = nn.Conv1d(ch * 2, ch, 1)
        self.bn2 = nn.BatchNorm1d(ch)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        c3 = F.gelu(self.conv3(x))
        c7 = F.gelu(self.conv7(x))
        out = F.gelu(self.bn(torch.cat([c3, c7], dim=1)))
        return self.drop(F.gelu(self.bn2(self.proj(out))))


class ResidualPredictor(nn.Module):
    def __init__(self, n_features, pred_len,
                 conv_filters=48, lstm_hidden=128, n_heads=4,
                 dropout=0.25, noise_std=0.015):
        super().__init__()
        self.noise_std = noise_std
        d = lstm_hidden * 2

        self.input_proj = nn.Sequential(
            nn.Linear(n_features, conv_filters),
            nn.LayerNorm(conv_filters), nn.GELU(),
            nn.Dropout(dropout * 0.5))

        self.cnn = LightCNN(conv_filters, dropout * 0.5)

        self.lstm = nn.LSTM(conv_filters, lstm_hidden,
                            batch_first=True, bidirectional=True)
        self.ln1 = nn.LayerNorm(d)
        self.drop = nn.Dropout(dropout)

        self.attn = nn.MultiheadAttention(d, n_heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d)
        self.ffn = nn.Sequential(nn.Linear(d, d*2), nn.GELU(),
                                 nn.Dropout(dropout), nn.Linear(d*2, d))
        self.ln3 = nn.LayerNorm(d)

        self.head = nn.Sequential(
            nn.Linear(d, d // 2), nn.GELU(),
            nn.Dropout(dropout), nn.Linear(d // 2, 1))

    def forward(self, x):
        x = self.input_proj(x)
        x = self.cnn(x.permute(0,2,1)).permute(0,2,1)
        h, _ = self.lstm(x)
        h = self.drop(self.ln1(h))
        a, _ = self.attn(h, h, h)
        h = self.ln2(h + a)
        h = self.ln3(h + self.ffn(h))
        return self.head(h).squeeze(-1)


# ── Model Manager ─────────────────────────────────────────────────────

class ModelV4Manager:
    def __init__(self):
        self.device = torch.device('cpu') # Use CPU for production inference
        self.xgb_model = None
        self.dl_ensemble = []
        self.feature_scaler = None
        self.target_scaler = None
        self.config = None
        self.loaded = False

    def load(self):
        """Load all models and scalers into memory."""
        print("🚀 Loading V4 Hybrid Model components...")
        
        # ── HF Hub Integration ──────────────────────────────────────────
        global CONFIG_PATH, FEATURE_SCALER_PATH, TARGET_SCALER_PATH, XGB_MODEL_PATH, DL_MODEL_PATHS
        repo_id = (os.environ.get('HF_REPO_ID') or "vidhyaramu/voltcast-v4").strip()
        
        # Check if we should skip network sync (saves 3-5 seconds on cold start)
        already_synced = os.path.exists(XGB_MODEL_PATH) and os.path.getsize(XGB_MODEL_PATH) > 1000
        
        if repo_id and not already_synced:
            from huggingface_hub import hf_hub_download
            print(f"📦 First-time Cloud Sync for '{repo_id}'...")
            try:
                # Fetch all core artifacts
                CONFIG_PATH = hf_hub_download(repo_id=repo_id, filename="config.joblib")
                FEATURE_SCALER_PATH = hf_hub_download(repo_id=repo_id, filename="feature_scaler.joblib")
                TARGET_SCALER_PATH = hf_hub_download(repo_id=repo_id, filename="target_scaler.joblib")
                XGB_MODEL_PATH = hf_hub_download(repo_id=repo_id, filename="xgb_v4.joblib")
                
                # Fetch ensemble
                new_dl_paths = []
                for i in range(len(DL_MODEL_PATHS)):
                    fname = f"residual_ensemble_seed_{i}.pth"
                    new_dl_paths.append(hf_hub_download(repo_id=repo_id, filename=fname))
                DL_MODEL_PATHS = new_dl_paths
                print("✨ Cloud weights synchronized.")
            except Exception as e:
                print(f"⚠️ Sync skipped: {e}")
        elif already_synced:
            print("🚀 Using cached weights (Turbo Load).")
        else:
            print("ℹ️ No HF_REPO_ID found. Using local paths.")

        # 1. Load config and scalers
        self.config = joblib.load(CONFIG_PATH)
        self.feature_scaler = joblib.load(FEATURE_SCALER_PATH)
        self.target_scaler = joblib.load(TARGET_SCALER_PATH)
        
        # 2. Load XGBoost
        self.xgb_model = joblib.load(XGB_MODEL_PATH)
        
        import gc
        gc.collect()

        # 3. Load DL Ensemble (3 models)
        n_feat_aug = self.config['N_FEATURES'] + 1 # +1 for XGBoost prediction
        for path in DL_MODEL_PATHS:
            model = ResidualPredictor(
                n_features=n_feat_aug,
                pred_len=self.config['OUTPUT_LEN']
            )
            model.load_state_dict(torch.load(path, map_location=self.device, weights_only=True))
            model.eval()
            self.dl_ensemble.append(model)
            gc.collect() # Force clear after each sub-model
            
        self.loaded = True
        print("✅ All models loaded successfully. Memory cleared.")
        gc.collect()

    def predict(self, X_window_raw):
        """
        Perform blended hybrid inference.
        X_window_raw: last 168h of data (DataFrame with correct columns)
        Returns: (168,) array of load predictions in MW
        """
        if not self.loaded:
            self.load()

        # 1. Scale input features
        # Training logic: numerical columns scaled, sin/cos not, load scaled separately.
        # But wait, X_window should already have FEATURE_COLS in correct order.
        X_raw = X_window_raw.copy()
        
        # Scale numerical parts
        num_cols = self.config['NUMERICAL_COLS']
        X_raw = X_raw.ffill().bfill().fillna(0.0) # Ensure no NaNs before scaling
        X_raw[num_cols] = self.feature_scaler.transform(X_raw[num_cols])
        
        # Scale load column
        target_col = self.config['TARGET_COL']
        X_raw[[target_col]] = self.target_scaler.transform(X_raw[[target_col]])
        
        # order features as per training
        X_scaled = X_raw[self.config['FEATURE_COLS']].values.astype(np.float32)
        
        # 2. XGBoost Prediction (Base)
        # Engineer stats from current window
        load_idx = self.config['load_col_idx']
        Xf_xgb = engineer_xgb_features(X_scaled, load_idx) # (1, n_xgb_feats)
        xgb_pred_scaled = self.xgb_model.predict(Xf_xgb.reshape(1, -1))[0] # (168,)
        
        # 3. DL Residual Prediction
        # Augment DL input: (1, 168, N+1)
        X_dl_aug = np.concatenate([X_scaled, xgb_pred_scaled[:, None]], axis=-1)
        X_tensor = torch.tensor(X_dl_aug, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        res_preds = []
        with torch.no_grad():
            for model in self.dl_ensemble:
                res_preds.append(model(X_tensor).cpu().numpy()[0])
        
        avg_res_scaled = np.mean(res_preds, axis=0) # (168,)
        
        # 4. Blending (Optimized Alpha)
        # hybrid = XGB + Residual
        # final = α * hybrid + (1-α) * XGB
        # note: final = XGB + α * Residual
        final_pred_scaled = xgb_pred_scaled + (BLEND_ALPHA * avg_res_scaled)
        
        # 5. Inverse Scale
        final_pred_mw = self.target_scaler.inverse_transform(final_pred_scaled.reshape(-1, 1)).flatten()
        xgb_pred_mw   = self.target_scaler.inverse_transform(xgb_pred_scaled.reshape(-1, 1)).flatten()
        
        return {
            "prediction": np.nan_to_num(final_pred_mw).tolist(),
            "xgb_base": np.nan_to_num(xgb_pred_mw).tolist(),
            "residual_correction": np.nan_to_num(final_pred_mw - xgb_pred_mw).tolist()
        }

# Singleton instance
model_manager = ModelV4Manager()
