#!/bin/bash

# RockchipLlama Automated Test Suite
# Usage: ./scripts/tests.sh

BASE_URL="http://localhost:8080"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="test_results/run_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

echo "🚀 Starting Test Suite at $(date)"
echo "📂 Results will be saved to: $RESULTS_DIR"
echo "============================================================"

# Helper function to run a test
run_test() {
    local test_name="$1"
    local description="$2"
    local curl_cmd="$3"
    local output_file="${RESULTS_DIR}/${test_name}.json"
    local headers_file="${RESULTS_DIR}/${test_name}_headers.txt"

    echo "🧪 Running Test: $description"
    echo "   Command: $curl_cmd"
    
    # Run curl, capture body to file and headers to separate file
    eval "$curl_cmd -D \"$headers_file\" -s" > "$output_file"
    
    # Try to format JSON if valid
    if command -v python3 &> /dev/null; then
        cat "$output_file" | python3 -m json.tool > "${output_file}.formatted" 2>/dev/null
        if [ $? -eq 0 ]; then
            mv "${output_file}.formatted" "$output_file"
        else
            rm "${output_file}.formatted"
        fi
    fi

    echo "   ✅ Saved response to $output_file"
    echo "------------------------------------------------------------"
}

# 1. Smoke Test - List Models
run_test "01_list_models" "List Available Models" \
    "curl -X GET ${BASE_URL}/v1/models"

# 2. Load Model (Qwen3-0.6B)
# Note: Adjust model name if needed based on what's in your models/ folder
MODEL_NAME="qwen3-0.6b"
run_test "02_load_model" "Load Model ${MODEL_NAME}" \
    "curl -X POST ${BASE_URL}/v1/models/load -H 'Content-Type: application/json' -d '{\"model\": \"${MODEL_NAME}\"}'"

# Wait a bit for model to load
echo "⏳ Waiting 5 seconds for model load..."
sleep 5

# 3. Basic Chat Completion
run_test "03_basic_chat" "Basic Chat Completion" \
    "curl -X POST ${BASE_URL}/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{
        \"model\": \"${MODEL_NAME}\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Hello, are you working?\"}],
        \"max_tokens\": 50
    }'"

# 4. Chat Template Verification (Pirate Test)
run_test "04_chat_template_pirate" "Chat Template (Pirate Persona)" \
    "curl -X POST ${BASE_URL}/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{
        \"model\": \"${MODEL_NAME}\",
        \"messages\": [
            {\"role\": \"system\", \"content\": \"You are a pirate. Always speak like a pirate.\"},
            {\"role\": \"user\", \"content\": \"Who are you?\"}
        ],
        \"temperature\": 0.7,
        \"max_tokens\": 100
    }'"

# 5. Ollama API - Generate
run_test "05_ollama_generate" "Ollama API Generate Endpoint" \
    "curl -X POST ${BASE_URL}/api/generate \
    -H 'Content-Type: application/json' \
    -d '{
        \"model\": \"${MODEL_NAME}\",
        \"prompt\": \"Why is the sky blue? Answer briefly.\",
        \"stream\": false
    }'"

# 6. Ollama API - Chat
run_test "06_ollama_chat" "Ollama API Chat Endpoint" \
    "curl -X POST ${BASE_URL}/api/chat \
    -H 'Content-Type: application/json' \
    -d '{
        \"model\": \"${MODEL_NAME}\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Tell me a joke.\"}],
        \"stream\": false
    }'"

echo "============================================================"
echo "🏁 Test Suite Completed."
echo "📂 Review results in: $RESULTS_DIR"
