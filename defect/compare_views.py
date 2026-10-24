"""检测对比视图：原图/标注图并排展示。"""
from django.shortcuts import render, get_object_or_404
from .models import DefectRecord


def compare_view(request, defect_id):
    """原图与标注图并排对比，支持hover高亮bbox。"""
    record = get_object_or_404(DefectRecord, id=defect_id)

    # 从engine_raw提取bbox列表（如果有）
    boxes = []
    if record.engine_raw and "boxes" in record.engine_raw:
        boxes = record.engine_raw["boxes"]

    return render(request, "defect/compare.html", {
        "record": record,
        "boxes": boxes,
    })
