# Model Artifacts

Place the source YOLO model and generated TensorRT engine here:

- `best.pt`: user-provided YOLO model
- `best.engine`: TensorRT engine generated from `best.pt`

Generated `.engine` and `.onnx` files are ignored by Git because they are
hardware/runtime-specific artifacts.
