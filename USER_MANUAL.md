# IronClad.Ai - Official User Manual

Welcome to the **IronClad.Ai UPI Fraud Engine**. This manual will guide you through testing and utilizing the real-time AI security dashboard.

![Fraud vs Safe Scenarios](fraud_scenarios.jpg)

---

## 1. Real-Time Transaction Inference

The dashboard allows you to inject simulated data into the Machine Learning backend to test its anomaly detection capabilities.

### Scenario A: The Safe Baseline
To simulate a normal, everyday transaction:
1. Click the **"Load Baseline"** button at the top of the form. This automatically fills the inputs with safe historical data (e.g., a ₹450 Grocery purchase in Mumbai from a Trusted Device).
2. Click **"Execute ML Inference"**.
3. **Result:** The system will process the data, the Threat Gauge will remain green, and the Threat Intelligence panel will state the transaction is **Approved**.

### Scenario B: The Cyber Attack
To simulate a fraudster attempting an account takeover:
1. Click the **"Simulate Attack"** button. This automatically fills the form with anomalous data (e.g., a sudden ₹85,000 transfer from Moscow on an Unknown Device).
2. Click **"Execute ML Inference"**.
3. **Result:** The unsupervised ML model will instantly flag the behavioral deviations. The UI will transition to **Red (CRITICAL)**, and the Threat Intelligence panel will detail exactly why the transaction was **Blocked** (e.g., Location mismatch, Velocity spike).

---

## 2. Batch Fraud Scanning (Enterprise Feature)

For enterprise-scale analysis, the system supports bulk CSV processing.

1. Ensure you have a generated dataset (e.g., `upi_transactions.csv`).
2. At the bottom of the web dashboard, click **"Run Batch Fraud Scan"**.
3. Select your `.csv` dataset from your file explorer.
4. The system will enter **"Processing Batch..."** mode as the FastAPI backend loops every transaction through the Isolation Forest engine.
5. Once complete, an official, color-coded **PDF Audit Report** will automatically download to your device, providing a complete breakdown of all identified fraudulent anomalies!
