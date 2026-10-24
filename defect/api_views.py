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
import logging

logger = logging.getLogger(__name__)


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
    """POST /api/v1/jobs/ — 上传图片/视频建推理任务"""
    source_type = request.data.get("source_type", "image")
    source_path = request.data.get("source_path", "")
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    job = InferenceJob.objects.create(
        job_id=job_id,
        source_type=source_type,
        source_path=source_path,
        model_version="train-20261024-150656-demo-yolov8n-best.pt",
        data_fingerprint="c324743351c8bfb5d6555bfadbcaa84b9fede6aea00475fc9e430a58824e7b67",
        status="pending",
    )
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
    """POST /api/v1/events/{id}/explain/ — 让LLM研判"""
    event = get_object_or_404(DefectEvent, event_id=pk)
    serializer = ExplainRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    invocation_id = f"llm-{uuid.uuid4().hex[:8]}"
    invocation = LLMInvocation.objects.create(
        invocation_id=invocation_id,
        target_type="event",
        target_id=event.id,
        prompt_version=serializer.validated_data["prompt_version"],
        model_name="qwen2.5-vl-7b",
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        raw_request={},
        raw_response={},
    )
    return Response({
        "invocation_id": invocation_id,
        "event_id": event.event_id,
        "status": "queued",
    })
