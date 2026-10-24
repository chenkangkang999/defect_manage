from django.contrib import admin
from .models import DefectType, DefectRecord, DefectEvent, InferenceJob, LLMInvocation


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "type_name", "description"]
    search_fields = ["type_name"]


@admin.register(DefectRecord)
class DefectRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "defect_type", "detect_person", "device_id", "confidence",
                    "review_status", "model_version", "detect_time"]
    list_filter = ["defect_type", "detect_person", "review_status"]
    search_fields = ["device_id", "infer_run_id"]


@admin.register(DefectEvent)
class DefectEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "defect_type", "start_time", "end_time",
                    "peak_confidence", "frame_count", "review_status"]
    list_filter = ["defect_type", "review_status"]
    search_fields = ["event_id"]


@admin.register(InferenceJob)
class InferenceJobAdmin(admin.ModelAdmin):
    list_display = ["job_id", "source_type", "status", "progress", "model_version", "created_at"]
    list_filter = ["status", "source_type"]
    search_fields = ["job_id"]


@admin.register(LLMInvocation)
class LLMInvocationAdmin(admin.ModelAdmin):
    list_display = ["invocation_id", "target_type", "model_name", "input_tokens",
                    "output_tokens", "latency_ms", "created_at"]
    list_filter = ["target_type", "model_name"]
    search_fields = ["invocation_id"]
