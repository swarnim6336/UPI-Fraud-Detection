# 🚨 Real-Time UPI Fraud Detection System

An end-to-end Machine Learning pipeline and real-time API for detecting fraudulent UPI transactions. Built with **Python, FastAPI, Scikit-Learn, and Streamlit**.

## 📊 Overview
This project simulates, processes, and analyzes UPI (Unified Payments Interface) transactions to detect fraud in real-time. It uses a hybrid scoring engine combining:
1. **Statistical Outlier Detection (IQR):** Flags transactions that deviate from a user's historical baseline.
2. **Time-Series Tracking (Z-Scores):** Detects sudden spikes in transaction velocity (e.g., card testing or bot activity).
3. **Machine Learning (Isolation Forest):** An unsupervised anomaly detection model that evaluates complex behavioral patterns across multiple dimensions (amount, time gaps, location spoofing, new devices).

## 🚀 Features
- **Data Simulation Engine:** Generates realistic datasets with injected fraud patterns (late-night unknown transfers, location spoofing, massive spending spikes).
- **Automated Feature Engineering:** Calculates rolling 7-day averages, time since last transaction, and velocity metrics on the fly.
- **Hybrid Scoring Engine:** Aggregates predictions into a single, interpretable **Fraud Risk Score (0-100)** with human-readable explanations.
- **FastAPI Backend:** A blazing-fast REST API for real-time inference.
- **Interactive Streamlit Dashboard:** A sleek UI to test transactions and visualize the scoring engine's decisions.

## 🛠️ Tech Stack
- **Data Science:** `pandas`, `numpy`, `scikit-learn`
- **Backend API:** `fastapi`, `uvicorn`
- **Frontend Dashboard:** `streamlit`

## 🏃‍♂️ How to Run Locally

1. **Clone and Setup**
```bash
git clone https://github.com/yourusername/UPI-Fraud-Detection.git
cd UPI-Fraud-Detection
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

2. **Generate Data and Train Models**
```bash
python generate_data.py
python preprocess.py
python train_models.py
```

3. **Launch the Real-Time Dashboard**
Simply run the included batch file (Windows):
```bash
run_demo.bat
```
*(This will automatically start both the FastAPI server on port 8000 and the Streamlit UI on port 8501).*

## 🧠 Model Performance Summary
In our synthetic test dataset of 10,000 transactions (5% fraud rate), the unsupervised **Isolation Forest** model successfully flagged over 54% of complex behavioral anomalies entirely on its own, without relying on labeled training data. When combined with the statistical IQR and Z-Score engines, the hybrid system accurately identifies high-risk behavior instantly.
