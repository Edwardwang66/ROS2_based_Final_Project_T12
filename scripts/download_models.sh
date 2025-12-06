#!/bin/bash
# Script to download models for OAK-D TPU acceleration

set -e

MODELS_DIR="models"
mkdir -p $MODELS_DIR

echo "Downloading models for OAK-D TPU acceleration..."

# MobileNet-SSD for person detection
# This is the standard model provided by Luxonis
echo "Downloading MobileNet-SSD model for person detection..."
if [ ! -f "$MODELS_DIR/mobilenet-ssd_openvino_2021.4_6shave.blob" ]; then
    wget -O "$MODELS_DIR/mobilenet-ssd_openvino_2021.4_6shave.blob" \
        https://github.com/luxonis/depthai/raw/main/resources/nn/mobilenet-ssd/mobilenet-ssd_openvino_2021.4_6shave.blob
    echo "MobileNet-SSD downloaded successfully"
else
    echo "MobileNet-SSD already exists"
fi

# Hand gesture recognition model
# Note: You may need to train or find a suitable RPS model
# Here are some options:
# 1. Use MediaPipe hand landmarks and convert to ONNX
# 2. Use a pre-trained hand gesture model
# 3. Train your own model

echo ""
echo "For RPS (Rock-Paper-Scissors) model:"
echo "Option 1: Download a pre-trained hand gesture model"
echo "Option 2: Convert MediaPipe to ONNX and compile to .blob"
echo "Option 3: Train your own model"
echo ""
echo "To convert a model to .blob format, use:"
echo "  python3 -m depthai_blobconverter --onnx model.onnx --shaves 6"
echo ""
echo "You can find hand gesture models at:"
echo "  - https://github.com/tensorflow/models"
echo "  - https://github.com/MediaPipe/mediapipe"
echo "  - https://github.com/luxonis/depthai-model-zoo"

# Example: Download a hand detection model (can be adapted for gestures)
if [ ! -f "$MODELS_DIR/hand_gesture_rps_openvino_2021.4_6shave.blob" ]; then
    echo ""
    echo "RPS model not found. Please:"
    echo "1. Train or download an RPS model"
    echo "2. Convert to ONNX format"
    echo "3. Compile to .blob using depthai_blobconverter"
    echo ""
    echo "For now, you can use MediaPipe hand landmarks as a fallback"
fi

echo ""
echo "Models directory: $MODELS_DIR"
ls -lh $MODELS_DIR/

