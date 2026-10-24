"""调用ODPlatform的YOLO模型进行缺陷推理。"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 模型权重路径
MODEL_PATH = Path(r"D:\ODPlatform\models\trained\train-20261024-150656-demo-yolov8n-best.pt")

# 数据指纹（从demo.yaml读到的最新值）
DATA_FINGERPRINT = "c324743351c8bfb5d6555bfadbcaa84b9fede6aea00475fc9e430a58824e7b67"

# 运行ID
INFERENCE_RUN_ID = "web-infer-001"


def run_inference(image_path: str) -> dict:
    """
    对图片运行YOLO推理，返回检测结果。

    Returns:
        {
            "class_name": "划痕",
            "confidence": 0.85,
            "defect_img_path": "D:/.../annotated.jpg",
            "model_version": "...",
            "run_id": "...",
            "data_fingerprint": "..."
        }
    """
    from ultralytics import YOLO

    if not MODEL_PATH.exists():
        return {"error": f"模型权重不存在: {MODEL_PATH}"}

    model = YOLO(str(MODEL_PATH))
    results = model(image_path, verbose=False)

    if not results or len(results[0].boxes) == 0:
        return {
            "class_name": "未检测到缺陷",
            "confidence": 0.0,
            "defect_img_path": "",
            "model_version": MODEL_PATH.name,
            "run_id": INFERENCE_RUN_ID,
            "data_fingerprint": DATA_FINGERPRINT,
        }

    # 取置信度最高的那个检测框
    boxes = results[0].boxes
    best_idx = boxes.conf.argmax().item()
    class_id = int(boxes.cls[best_idx].item())
    class_name = results[0].names[class_id]
    confidence = float(boxes.conf[best_idx].item())

    # 保存画框后的图片
    annotated = results[0].plot()
    save_path = str(Path(image_path).parent.parent / "defect_img" / f"annotated_{Path(image_path).name}")
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    import cv2
    cv2.imwrite(save_path, annotated)

    logger.info(f"推理完成: {class_name} ({confidence:.2f})")

    return {
        "class_name": class_name,
        "confidence": round(confidence, 4),
        "defect_img_path": save_path,
        "model_version": MODEL_PATH.name,
        "run_id": INFERENCE_RUN_ID,
        "data_fingerprint": DATA_FINGERPRINT,
    }
