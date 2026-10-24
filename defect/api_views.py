"""REST API视图。"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import DefectRecord, DefectEvent, InferenceJob, LLMInvocation
from .serializers import (
    DefectRecordSerializer, DefectEventSerializer,
    InferenceJobSerializer, LLMInvocationSerializer,
    ReviewRequestSerializer, ExplainRequestSerializer,
)
import uuid
import threading
import logging

logger = logging.getLogger(__name__)

# 全局模型缓存（避免每次请求重新加载YOLO）
_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from ultralytics import YOLO
                from pathlib import Path
                model_path = Path(r"D:\ODPlatform\models\trained\train-20261024-150656-demo-yolov8n-best.pt")
                logger.info(f"加载YOLO模型: {model_path}")
                _model = YOLO(str(model_path))
    return _model


def _run_inference_background(job_id, image_path):
    """后台线程：跑YOLO推理并更新任务状态。"""
    try:
        job = InferenceJob.objects.get(job_id=job_id)
        job.status = "running"
        job.progress = 10
        job.save()

        model = _get_model()
        job.progress = 30
        job.save()

        results = model(image_path, verbose=False)
        job.progress = 80
        job.save()

        # 解析结果
        boxes_data = []
        best_cls = "未检测到"
        best_conf = 0.0
        if results and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                cls_name = results[0].names[cls_id]
                conf = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].tolist()
                boxes_data.append({
                    "cls": cls_name, "conf": round(conf, 4),
                    "x1": round(xyxy[0]), "y1": round(xyxy[1]),
                    "x2": round(xyxy[2]), "y2": round(xyxy[3]),
                })
                if conf > best_conf:
                    best_conf = conf
                    best_cls = cls_name

        job.result = {"boxes": boxes_data, "best_class": best_cls, "best_conf": best_conf}
        job.status = "completed"
        job.progress = 100
        job.finished_at = timezone.now()
        job.save()
        logger.info(f"任务 {job_id} 推理完成: {best_cls} {best_conf}")

    except Exception as e:
        logger.error(f"任务 {job_id} 推理失败: {e}")
        job = InferenceJob.objects.get(job_id=job_id)
        job.status = "failed"
        job.error_msg = str(e)
        job.save()


class DefectRecordViewSet(viewsets.ModelViewSet):
    queryset = DefectRecord.objects.all().order_by("-detect_time")
    serializer_class = DefectRecordSerializer


class DefectEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DefectEvent.objects.all().order_by("-created_at")
    serializer_class = DefectEventSerializer


class InferenceJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InferenceJob.objects.all().order_by("-created_at")
    serializer_class = InferenceJobSerializer


class LLMInvocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LLMInvocation.objects.all().order_by("-created_at")
    serializer_class = LLMInvocationSerializer


@api_view(["POST"])
def create_job(request):
    """POST /api/v1/jobs/ — 上传图片建任务，后台异步跑YOLO推理。"""
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"error": "请上传图片"}, status=status.HTTP_400_BAD_REQUEST)

    # 保存图片
    from django.conf import settings
    from pathlib import Path
    save_dir = Path(settings.MEDIA_ROOT) / "original"
    save_dir.mkdir(parents=True, exist_ok=True)
    fname = f"job-{uuid.uuid4().hex[:8]}_{image_file.name}"
    img_path = save_dir / fname
    with open(img_path, "wb") as f:
        for chunk in image_file.chunks():
            f.write(chunk)

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    job = InferenceJob.objects.create(
        job_id=job_id,
        source_type="image",
        source_path=str(img_path),
        model_version="train-20261024-150656-demo-yolov8n-best.pt",
        data_fingerprint="c324743351c8bfb5d6555bfadbcaa84b9fede6aea00475fc9e430a58824e7b67",
        status="pending",
    )

    # 启动后台线程跑推理
    t = threading.Thread(target=_run_inference_background, args=(job.job_id, str(img_path)))
    t.daemon = True
    t.start()

    return Response(InferenceJobSerializer(job).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def job_detail(request, pk):
    """GET /api/v1/jobs/{id}/ — 查任务进度"""
    job = get_object_or_404(InferenceJob, job_id=pk)
    return Response(InferenceJobSerializer(job).data)


@api_view(["POST"])
def review_record(request, pk):
    """POST /api/v1/records/{id}/review/ — 人工复核"""
    record = get_object_or_404(DefectRecord, id=pk)
    serializer = ReviewRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    action = serializer.validated_data["action"]
    record.review_status = "confirmed" if action == "confirm" else "rejected"
    record.reviewed_by = serializer.validated_data["reviewer"]
    record.reviewed_at = timezone.now()
    record.reject_reason = serializer.validated_data.get("reason", "")
    record.save()
    return Response(DefectRecordSerializer(record).data)


@api_view(["POST"])
def explain_event(request, pk):
    """POST /api/v1/events/{id}/explain/ — 调DeepSeek LLM研判缺陷事件。"""
    import time
    from .llm_client import call_deepseek

    event = get_object_or_404(DefectEvent, event_id=pk)

    # 构造prompt
    prompt = f"""你是工业缺陷检测专家。请分析以下缺陷事件：
- 缺陷类型：{event.defect_type.type_name if event.defect_type else '未知'}
- 起止时间：{event.start_time:.1f}s - {event.end_time:.1f}s
- 峰值置信度：{event.peak_confidence:.3f}
- 持续帧数：{event.frame_count}
- 画面区域：{event.region}

请输出JSON：
{{"severity":"高/中/低","cause_hypothesis":"...","suggested_action":"...","confidence":0.0}}"""

    invocation_id = f"llm-{uuid.uuid4().hex[:8]}"
    t0 = time.time()

    result = call_deepseek(prompt)

    latency = int((time.time() - t0) * 1000)

    invocation = LLMInvocation.objects.create(
        invocation_id=invocation_id,
        target_type="event",
        target_id=event.id,
        prompt_version="v1",
        model_name="deepseek-chat",
        input_tokens=result.get("usage", {}).get("prompt_tokens", 0),
        output_tokens=result.get("usage", {}).get("completion_tokens", 0),
        latency_ms=latency,
        raw_request={"prompt": prompt},
        raw_response=result.get("choices", [{}])[0].get("message", {}),
    )

    # 把LLM结果存到event
    event.llm_review = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    event.save()

    return Response({
        "invocation_id": invocation_id,
        "event_id": event.event_id,
        "llm_result": event.llm_review,
        "latency_ms": latency,
    })
