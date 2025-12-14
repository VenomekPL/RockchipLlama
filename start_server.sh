#!/bin/bash
# Quick start script for RockchipLlama server

# Set high performance mode (requires sudo)
echo "⚡ Setting high performance mode (requires sudo)..."
if sudo ./scripts/fix_freq_rk3588.sh; then
    echo "✅ Performance mode set."
else
    echo "⚠️  Failed to set performance mode. Server will run slower."
    echo "   Run 'sudo ./scripts/fix_freq_rk3588.sh' manually if needed."
fi

cd "$(dirname "$0")/src"
source ../venv/bin/activate

echo "🚀 Starting RockchipLlama Server..."
echo "   Access at: http://192.168.10.53:8021"
echo "   Docs at: http://192.168.10.53:8021/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

mkdir -p ../logs
timestamp=$(date +%s)
python -u main.py 2>&1 | tee -a ../logs/serverlog_${timestamp}.log
