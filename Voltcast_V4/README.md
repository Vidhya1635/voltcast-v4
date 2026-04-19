# VoltCast V4 - Hybrid Regional Electricity Load Forecasting

![Status](https://img.shields.io/badge/Status-Complete-green)
![Tech](https://img.shields.io/badge/Tech-PyTorch%20%7C%20XGBoost%20%7C%20Vue3-blue)

## 📌 The Problem Statement
Regional electricity grids face constant volatility due to changing weather patterns, industrial demand, and domestic consumption. **Inaccurate load forecasting** leads to:
*   **Grid Instability:** Risk of blackouts or surges.
*   **Economic Inefficiency:** High costs from over-purchasing energy or emergency generation.
*   **Sustainability Challenges:** Difficulty in integrating renewable energy sources without stable demand predictions.

## 💡 The Solution: VoltCast V4
**VoltCast V4** solves this by implementing an **Advanced Hybrid Ensemble Strategy** to forecast ISO-NE (New England) electricity loads. Instead of relying on a single model, it mathematically blends two distinct AI architectures:

1.  **PyTorch Deep Learning (85% Weighting):** Captures complex temporal dependencies and non-linear patterns.
2.  **XGBoost Gradient Boosting (15% Weighting):** Handles sharp variance and residual errors with highly optimized decision trees.

### 🚀 Key Innovations
*   **Residual Error Correction:** The XGBoost layer specifically targets the errors made by the Deep Learning model.
*   **Real-time Weather Integration:** Dynamically fetches weather features to adjust forecasts on the fly.
*   **Intuitive Dashboard:** A professional Vue 3 UI that allows operators to visualize 7-day windows and model performance metrics.

---

## 📂 Project Architecture
```text
Voltcast_v4/
├── backend/                # Flask REST API & Forecasting Logic
├── frontend/               # Vue 3 + Vite Dashboard UI
├── models/                 # Pre-trainedWeights (.pt, .pkl)
├── data/                   # Gold-standard processed datasets
├── notebook/               # Model development & Training logs
└── raw_data/               # Source ISO-NE datasets
```

---

## 🛠️ Requirements & Quick Start

### Prerequisites
*   **Python 3.9+** (For AI models & Backend)
*   **Node.js 16+** (For Dashboard UI)
*   **Git** (For version control)

### 1. Launch the Backend (AI Engine)
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
cd backend
python app.py
```
*API running at: `http://127.0.0.1:5000/`*

### 2. Launch the Frontend (Dashboard)
```bash
# Navigate to frontend
cd frontend

# Install & Run
npm install
npm run dev
```
*Dashboard running at: `http://localhost:5173/`*

---

## 📈 Performance & Results
The Hybrid V4 model achieved significant MAE and RMSE reductions compared to baseline LSTM and XGBoost models. Detailed training logs and comparison charts can be found in the `notebook/` directory.

---
*Developed by Vidhya as part of the Python Projects Portfolio.*
