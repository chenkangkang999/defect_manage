"""W3: 统计看板、复核工作流、空间热力图视图。"""
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Q
from .models import DefectRecord, DefectType, DefectEvent, InferenceJob
from django.utils import timezone
from datetime import timedelta
import json


def dashboard(request):
    """统计看板：缺陷类型分布、时间趋势、设备对比、置信度分布、良率。"""
    # 缺陷类型分布
    type_stats = (DefectRecord.objects
                  .values("defect_type__type_name")
                  .annotate(count=Count("id"))
                  .order_by("-count"))
    type_labels = [t["defect_type__type_name"] for t in type_stats]
    type_counts = [t["count"] for t in type_stats]

    # 近7天趋势
    days = []
    trend = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        count = DefectRecord.objects.filter(detect_time__date=day).count()
        days.append(day.strftime("%m-%d"))
        trend.append(count)

    # 设备对比
    device_stats = (DefectRecord.objects
                    .values("device_id")
                    .annotate(total=Count("id"),
                              avg_conf=Avg("confidence"))
                    .order_by("-total"))

    # 置信度分布（分桶）
    conf_buckets = {"0-0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-0.9": 0, "0.9-1.0": 0}
    for r in DefectRecord.objects.all():
        c = r.confidence
        if c < 0.3: conf_buckets["0-0.3"] += 1
        elif c < 0.5: conf_buckets["0.3-0.5"] += 1
        elif c < 0.7: conf_buckets["0.5-0.7"] += 1
        elif c < 0.9: conf_buckets["0.7-0.9"] += 1
        else: conf_buckets["0.9-1.0"] += 1

    # 良率
    total = DefectRecord.objects.count()
    reviewed = DefectRecord.objects.filter(review_status__in=["confirmed", "rejected"]).count()
    confirmed = DefectRecord.objects.filter(review_status="confirmed").count()
    yield_rate = round(confirmed / total * 100, 1) if total else 0

    # 待复核数量
    pending_count = DefectRecord.objects.filter(review_status="pending").count()

    context = {
        "type_labels": json.dumps(type_labels, ensure_ascii=False),
        "type_counts": json.dumps(type_counts),
        "trend_days": json.dumps(days),
        "trend_data": json.dumps(trend),
        "device_stats": device_stats,
        "conf_labels": json.dumps(list(conf_buckets.keys())),
        "conf_data": json.dumps(list(conf_buckets.values())),
        "total": total,
        "reviewed": reviewed,
        "confirmed": confirmed,
        "yield_rate": yield_rate,
        "pending_count": pending_count,
    }
    return render(request, "defect/dashboard.html", context)


def review_queue(request):
    """复核工作流：待复核队列。"""
    records = DefectRecord.objects.filter(review_status="pending").order_by("-detect_time")
    return render(request, "defect/review_queue.html", {"records": records})


def review_action(request, defect_id, action):
    """人工确认/驳回。"""
    record = get_object_or_404(DefectRecord, id=defect_id)
    if action == "confirm":
        record.review_status = "confirmed"
    elif action == "reject":
        record.review_status = "rejected"
        record.reject_reason = request.POST.get("reject_reason", "")
    record.reviewed_by = request.user.username if request.user.is_authenticated else "admin"
    record.reviewed_at = timezone.now()
    record.save()
    return redirect("review_queue")


def heatmap(request):
    """缺陷空间热力图：历史所有bbox中心叠加。"""
    points = []
    for r in DefectRecord.objects.all():
        if r.engine_raw and "boxes" in r.engine_raw:
            for box in r.engine_raw["boxes"]:
                cx = box.get("cx", box.get("x1", 320) + box.get("w", 0) / 2)
                cy = box.get("cy", box.get("y1", 240) + box.get("h", 0) / 2)
                points.append([round(cx), round(cy)])

    if not points:
        # 用DefectEvent的bbox_trace
        for ev in DefectEvent.objects.all():
            for pt in ev.bbox_trace:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    points.append([round(pt[0]), round(pt[1])])

    if not points:
        points = [[100, 200], [150, 180], [200, 220], [300, 300], [400, 350]]

    return render(request, "defect/heatmap.html", {
        "points": json.dumps(points),
        "point_count": len(points),
    })


def event_list(request):
    """事件列表（视频聚合结果）。"""
    events = DefectEvent.objects.all().order_by("-created_at")
    return render(request, "defect/event_list.html", {"events": events})
