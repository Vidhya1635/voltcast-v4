import os
from huggingface_hub import HfApi
from config import CONFIG_PATH, FEATURE_SCALER_PATH, TARGET_SCALER_PATH, XGB_MODEL_PATH, DL_MODEL_PATHS

def upload_to_hf(repo_id, token):
    api = HfApi()
    
    print(f"🚀 Starting upload to {repo_id}...")
    
    # Files to upload
    files = {
        CONFIG_PATH: "config.joblib",
        FEATURE_SCALER_PATH: "feature_scaler.joblib",
        TARGET_SCALER_PATH: "target_scaler.joblib",
        XGB_MODEL_PATH: "xgb_v4.joblib",
    }
    
    for i, path in enumerate(DL_MODEL_PATHS):
        files[path] = f"residual_ensemble_seed_{i}.pth"

    for local_path, repo_path in files.items():
        if os.path.exists(local_path):
            print(f"📤 Uploading {repo_path}...")
            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=repo_path,
                repo_id=repo_id,
                token=token
            )
        else:
            print(f"❌ File not found: {local_path}")

    print("✅ Upload complete!")

if __name__ == "__main__":
    # User should set these or input them
    repo = input("Enter HF Repo ID (e.g., username/voltcast-v4): ")
    hf_token = input("Enter HF Write Token: ")
    upload_to_hf(repo, hf_token)
