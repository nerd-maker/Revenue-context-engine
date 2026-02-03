#!/bin/bash
# Railway startup script

# Install dependencies if not already installed
pip install -r requirements.txt

# Start the application
python -m uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
