# Finding RPS Models Online

This guide helps you find Rock-Paper-Scissors hand gesture recognition models that can run on OAK-D's TPU.

## Quick Search Resources

### 1. GitHub Repositories
Search GitHub for:
- "rock paper scissors hand gesture"
- "hand gesture recognition onnx"
- "rps gesture classification"

**Recommended Repos:**
- https://github.com/search?q=rock+paper+scissors+hand+gesture
- https://github.com/search?q=hand+gesture+recognition+onnx

### 2. Model Zoos
- **Luxonis Model Zoo**: https://github.com/luxonis/depthai-model-zoo
- **ONNX Model Zoo**: https://github.com/onnx/models
- **TensorFlow Hub**: https://tfhub.dev/ (search for "hand gesture")
- **Hugging Face**: https://huggingface.co/models (search for "hand gesture")

### 3. Pre-trained Models

**Option A: MediaPipe-based**
- MediaPipe Hand Landmarks: https://google.github.io/mediapipe/solutions/hands.html
- Convert to ONNX, then to .blob

**Option B: TensorFlow Lite**
- Search TensorFlow Hub for hand gesture models
- Convert TFLite → ONNX → Blob

**Option C: Custom Training**
- Use TensorFlow/PyTorch to train on RPS dataset
- Export to ONNX
- Compile to .blob

### 4. Datasets for Training

If you need to train your own:
- **Kaggle**: https://www.kaggle.com/datasets?search=rock+paper+scissors
- **Google Dataset Search**: https://datasetsearch.research.google.com/
- **Roboflow**: https://roboflow.com/

## Conversion Process

Once you find a model:

1. **If it's ONNX**: Direct conversion
   ```bash
   python3 -m depthai_blobconverter --onnx model.onnx --shaves 6
   ```

2. **If it's TensorFlow/PyTorch**: Export to ONNX first
   ```python
   # TensorFlow example
   import tf2onnx
   tf2onnx.convert.from_keras(model, output_path="model.onnx")
   ```

3. **If it's TFLite**: Convert to ONNX
   ```python
   # Use onnx-tf or similar tools
   ```

## Quick Start: Use Existing Hand Detection + Classification

If you can't find a ready RPS model, you can:

1. Use OAK-D's hand detection (from model zoo)
2. Crop hand regions
3. Run a simple classifier on hand landmarks
4. Classify as rock/paper/scissors based on finger positions

This approach:
- Uses hand detection on TPU (fast)
- Classification can be simple rule-based or small NN
- No need for complex RPS-specific model

## Recommended Approach

**Best option**: Use MediaPipe hand landmarks + simple classifier

1. Download MediaPipe hand detection model
2. Extract hand landmarks (21 points)
3. Use simple rules or small NN to classify:
   - **Rock**: Fist (all fingers closed)
   - **Paper**: Open hand (all fingers extended)
   - **Scissors**: Two fingers extended (index + middle)

This can be implemented as a small ONNX model or even rule-based logic.

## Example: Simple Rule-Based RPS

```python
def classify_gesture(landmarks):
    # landmarks: 21 points from MediaPipe
    # Check finger positions
    fingers_up = count_fingers_up(landmarks)
    
    if fingers_up == 0:
        return "rock"
    elif fingers_up == 5:
        return "paper"
    elif fingers_up == 2:  # Index + middle
        return "scissors"
    else:
        return "none"
```

This can run on TPU if you create a small neural network that takes landmarks as input.

