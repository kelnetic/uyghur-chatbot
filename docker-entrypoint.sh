#!/bin/bash

# Start Nginx
service nginx start

# Start FastAPI server in the background
uvicorn server.app:app --host 0.0.0.0 --port 7860 --workers 3 &

# Start Streamlit app
streamlit run /app/client/streamlit_app.py --server.port 8501 --server.address 0.0.0.0