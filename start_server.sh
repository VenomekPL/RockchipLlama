#!/bin/bash
# Quick start script for RockchipLlama server

cd "$(dirname "$0")/src"
source ../venv/bin/activate

echo "🚀 Starting RockchipLlama Server..."
echo "   Access at: http://192.168.10.53:8080"
echo "   Docs at: http://192.168.10.53:8080/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
