#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run the Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py