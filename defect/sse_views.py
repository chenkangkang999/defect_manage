"""SSE实时进度推送。"""
from django.http import StreamingHttpResponse
from .models import InferenceJob
import json, time


def job_progress_sse(request, job_id):
    """Server-Sent Events: 实时推送推理任务进度。"""
    def event_stream():
        last_progress = -1
        while True:
            try:
                job = InferenceJob.objects.get(job_id=job_id)
                data = {
                    "status": job.status,
                    "progress": job.progress,
                    "result": job.result,
                    "error": job.error_msg,
                }
                yield f"data: {json.dumps(data)}\n\n"

                if job.status in ("completed", "failed"):
                    break
                if job.progress == last_progress:
                    time.sleep(1)
                else:
                    last_progress = job.progress
                    time.sleep(0.5)
            except InferenceJob.DoesNotExist:
                yield f"data: {json.dumps({'error': 'job not found'})}\n\n"
                break

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
