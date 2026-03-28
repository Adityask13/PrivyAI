#!/bin/bash
echo "🚀 Starting PrivyAI..."
cd ~/PrivyAI
/Users/aditya/PrivyAI/.venv/bin/python3 -m chainlit run ui/app.py --port 8000
