@echo off
echo Starting UPI Fraud Detection Backend API...
start "FastAPI Backend" cmd /c ".\venv\Scripts\uvicorn app:app --reload --host 127.0.0.1 --port 8000"

echo Waiting 3 seconds for API to initialize...
timeout /t 3 /nobreak >nul

echo Starting Streamlit Live Dashboard...
start "Streamlit Dashboard" cmd /c ".\venv\Scripts\streamlit run dashboard.py"

echo Both services are now running! 
echo Dashboard: http://localhost:8501
echo API Docs: http://localhost:8000/docs
