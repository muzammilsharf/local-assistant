#!/usr/bin/env bash
set -euo pipefail

# Model to use: base.en by default, or run: ./scripts/setup_whisper.sh tiny.en
MODEL="${1:-base.en}"

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
WHISPER_DIR="$ROOT/vendor/whisper.cpp"

# 1. Check the tools
for tool in git cmake g++; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Missing $tool. Install with: sudo dnf install git cmake gcc-c++"
    exit 1
  }
done

# 2. Clone if needed
if [ ! -d "$WHISPER_DIR" ]; then
  echo "Cloning whisper.cpp..."
  git clone https://github.com/ggml-org/whisper.cpp "$WHISPER_DIR"
else
  echo "whisper.cpp already cloned, skipping."
fi

# 3. Build if needed
if [ ! -f "$WHISPER_DIR/build/bin/whisper-cli" ]; then
  echo "Building whisper.cpp (about 10 min)..."
  cd "$WHISPER_DIR"
  cmake -B build
  cmake --build build -j4 --config Release
else
  echo "whisper-cli already built, skipping."
fi

# 4. Download the model if needed
MODEL_FILE="$WHISPER_DIR/models/ggml-$MODEL.bin"
if [ ! -f "$MODEL_FILE" ]; then
  echo "Downloading model $MODEL..."
  cd "$WHISPER_DIR"
  sh ./models/download-ggml-model.sh "$MODEL"
else
  echo "Model $MODEL already downloaded, skipping."
fi

echo
echo "Done. Binary: $WHISPER_DIR/build/bin/whisper-cli"
echo "Model:  $MODEL_FILE"
