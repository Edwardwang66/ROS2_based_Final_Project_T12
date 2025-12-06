# Model Setup Guide for OAK-D TPU Acceleration

This guide explains how to set up neural network models to run on OAK-D Lite's TPU (Myriad X VPU) for acceleration.

## Overview

All computer vision computations in this project run on OAK-D Lite's TPU, not on the host CPU. This provides:
- **Low latency**: Inference happens directly on the camera
- **Low power**: TPU is optimized for edge AI
- **High throughput**: Dedicated AI accelerator

## Required Models

### 1. Person Detection Model
- **Model**: MobileNet-SSD
- **Purpose**: Detect people in camera frames
- **Format**: `.blob` (compiled for OAK-D TPU)
- **Download**: Included in DepthAI repository

### 2. Hand Gesture Recognition Model (RPS)
- **Model**: Custom or pre-trained hand gesture model
- **Purpose**: Recognize rock, paper, scissors gestures
- **Format**: `.blob` (compiled for OAK-D TPU)
- **Status**: Needs to be obtained/trained

## Model Download

Run the download script:
```bash
./scripts/download_models.sh
```

Or manually download:
```bash
mkdir -p models
wget -O models/mobilenet-ssd_openvino_2021.4_6shave.blob \
  https://github.com/luxonis/depthai/raw/main/resources/nn/mobilenet-ssd/mobilenet-ssd_openvino_2021.4_6shave.blob
```

## RPS Model Options

### Option 1: Use Pre-trained Hand Gesture Model

Search for hand gesture recognition models that can be converted:

1. **MediaPipe Hand Landmarks**
   - Convert MediaPipe to ONNX
   - Add gesture classification layer
   - Compile to `.blob`

2. **TensorFlow Lite Hand Gesture Models**
   - Available on TensorFlow Hub
   - Convert TFLite → ONNX → Blob

3. **Custom Trained Model**
   - Train on your own dataset
   - Export to ONNX
   - Compile to `.blob`

### Option 2: Convert Existing Model to OAK-D Format

If you have an ONNX model:

```bash
# Install blob converter
pip3 install depthai-blobconverter

# Convert ONNX to blob
python3 -m depthai_blobconverter \
  --onnx your_model.onnx \
  --shaves 6 \
  --output-dir models/
```

### Option 3: Use DepthAI Model Zoo

Check Luxonis model zoo for available models:
- https://github.com/luxonis/depthai-model-zoo
- https://github.com/luxonis/model-zoo

## Model Training (If Needed)

If you need to train a custom RPS model:

1. **Collect Dataset**
   - Images of rock, paper, scissors gestures
   - Label with classes: rock, paper, scissors

2. **Train Model**
   - Use TensorFlow/PyTorch
   - Export to ONNX format

3. **Convert to Blob**
   ```bash
   python3 -m depthai_blobconverter --onnx model.onnx --shaves 6
   ```

## Model Configuration

Update model paths in `perception_node.py` or via ROS2 parameters:

```bash
ros2 launch full_system.launch.py \
  person_model_path:=models/mobilenet-ssd_openvino_2021.4_6shave.blob \
  rps_model_path:=models/hand_gesture_rps_openvino_2021.4_6shave.blob
```

Or in config file:
```yaml
perception_node:
  ros__parameters:
    person_model_path: "models/mobilenet-ssd_openvino_2021.4_6shave.blob"
    rps_model_path: "models/hand_gesture_rps_openvino_2021.4_6shave.blob"
```

## Model Format Requirements

- **Input**: RGB image (typically 300x300 for MobileNet-SSD)
- **Output**: 
  - Person detection: Bounding boxes with confidence scores
  - RPS: Class probabilities [rock, paper, scissors]
- **Precision**: FP16 (half precision) for TPU
- **Shaves**: 6 (number of SHAVE cores used)

## Testing Models

Test models individually:

```python
import depthai as dai

# Load and test model
pipeline = dai.Pipeline()
nn = pipeline.create(dai.node.NeuralNetwork)
nn.setBlobPath("models/your_model.blob")

# Test inference
device = dai.Device(pipeline)
# ... run inference
```

## Resources

- **DepthAI Documentation**: https://docs.luxonis.com/
- **Blob Converter**: https://github.com/luxonis/depthai-blobconverter
- **Model Zoo**: https://github.com/luxonis/depthai-model-zoo
- **OpenVINO Model Optimizer**: https://docs.openvino.ai/
- **ONNX**: https://onnx.ai/

## Quick Start with MediaPipe Alternative

If you can't find a suitable RPS model, you can use MediaPipe hand landmarks on CPU as a fallback (slower but works):

1. Install MediaPipe: `pip3 install mediapipe`
2. Modify `perception_node.py` to use MediaPipe when TPU model is not available
3. This will run on CPU, not TPU, but provides functionality

## Troubleshooting

### Model Not Found
- Check file path is correct
- Ensure model is in `.blob` format
- Verify model was compiled for correct OpenVINO version

### Inference Errors
- Check model input/output shapes match expectations
- Verify model was compiled with correct number of shaves (6)
- Check OpenVINO version compatibility

### Low Performance
- Ensure models are running on TPU, not CPU
- Check model complexity (lighter models = faster)
- Verify input image size matches model expectations

