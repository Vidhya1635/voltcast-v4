# VoltCast V4 - Hybrid Regional Electricity Load Forecasting

## Overview
VoltCast V4 is an advanced, hybrid deep learning and machine learning application designed to forecast regional electricity loads (ISO-NE) with high precision. It leverages an ensemble blending strategy (85% PyTorch Deep Learning / 15% XGBoost) that mathematically unifies neural networks trained on diverse random seeds with highly optimized decision trees.

## Directory Structure
- **`/backend`**: The Flask REST API that loads the models, processes live weather via external APIs, and generates dynamic 7-day load forecasts.
- **`/frontend`**: The Vite + Vue 3 dashboard UI, which presents interactive forecast charts and metrics.
- **`/models` & `/models/v4`**: The fully trained AI weights (`.pt` PyTorch files and `.pkl` XGBoost/Scaler files).
- **`/data` & `/raw_data`**: The reliable, gold-standard ISO-NE load datasets used to construct and train the models.
- **`/database`**: SQLite cached forecasting data.
- **`/notebook` & `/dataprocessing_notebook`**: Jupyter notebooks detailing the data cleaning, exploratory analysis, and AI model training processes.

## Requirements
This project requires **Node.js** (for the frontend) and **Python 3.9+** (for the backend and AI models).

## Setup & Run Instructions

### 1. Backend API (Python Environment)
1. Open a terminal in the main project directory.
2. (Optional but recommended) Create and activate a Python virtual environment.
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the backend Flask API:
   ```bash
   cd backend
   python app.py
   ```
   *The backend will boot up at `http://127.0.0.1:5000/`*

### 2. Frontend Dashboard (Vue Environment)
1. Open a **new, separate** terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the necessary Node packages (this creates the `node_modules` folder):
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The fully functioning dashboard will instantly launch at `http://localhost:5173/`*

## Validating Model Training (Optional)
If you wish to view how the ISO-NE dataset was utilized and how the AI models were built and trained:
1. Ensure the Python `requirements.txt` dependencies are installed from above.
2. Run `jupyter notebook` in your terminal at the root directory.
3. Navigate into the `notebook/` folder or `dataprocessing_notebook/` to explore the training pipelines.
