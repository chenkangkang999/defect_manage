"""生成示例事件数据并写入数据库。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "defect_manage.settings")
import django
django.setup()

from defect.event_aggregator import FrameBox, aggregate
from defect.models import DefectEvent, DefectType, InferenceJob

# 模拟一段视频的检测结果
frames = []
for i in range(10, 53):
    frames.append(FrameBox(frame_idx=i, cls_name="划痕",
                           confidence=0.85 + (i % 5) * 0.02,
                           cx=150, cy=350, w=80, h=30))
for i in range(60, 76):
    frames.append(FrameBox(frame_idx=i, cls_name="污渍",
                           confidence=0.72 + (i % 3) * 0.05,
                           cx=500, cy=100, w=60, h=60))

events = aggregate(frames)
print(f"聚合出 {len(events)} 个事件:")
for e in events:
    print(f"  {e['event_id']}: {e['cls_name']} "
          f"{e['start_time']:.1f}s-{e['end_time']:.1f}s "
          f"峰值{e['peak_confidence']} 持续{e['frame_count']}帧 "
          f"区域:{e['region']}")

job, _ = InferenceJob.objects.get_or_create(
    job_id="job-demo-001",
    defaults={"source_type": "video", "source_path": "demo.mp4",
              "model_version": "yolov8n", "status": "completed"})

for e in events:
    dt, _ = DefectType.objects.get_or_create(
        type_name=e["cls_name"],
        defaults={"description": f"{e['cls_name']}类"})
    DefectEvent.objects.create(
        event_id=e["event_id"], defect_type=dt,
        start_time=e["start_time"], end_time=e["end_time"],
        peak_confidence=e["peak_confidence"], avg_confidence=e["avg_confidence"],
        frame_count=e["frame_count"], bbox_trace=e["bbox_trace"],
        region=e["region"], inference_job=job)

print("已写入DefectEvent表")
