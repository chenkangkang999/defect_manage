from django.shortcuts import render, redirect, get_object_or_404
from .models import DefectRecord, DefectType
from .forms import DefectForm
from .inference import run_inference
import logging

logger = logging.getLogger(__name__)


def defect_list(request):
    records = DefectRecord.objects.all().order_by("-detect_time")
    return render(request, "defect/list.html", {"records": records})


def defect_add(request):
    if request.method == "POST":
        form = DefectForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("defect_list")
    else:
        form = DefectForm()
    return render(request, "defect/add.html", {"form": form})


def defect_detail(request, defect_id):
    record = get_object_or_404(DefectRecord, id=defect_id)
    return render(request, "defect/detail.html", {"record": record})


def defect_edit(request, defect_id):
    record = get_object_or_404(DefectRecord, id=defect_id)
    if request.method == "POST":
        form = DefectForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            return redirect("defect_list")
    else:
        form = DefectForm(instance=record)
    return render(request, "defect/edit.html", {"form": form})


def defect_delete(request, defect_id):
    record = get_object_or_404(DefectRecord, id=defect_id)
    if request.method == "POST":
        record.delete()
        return redirect("defect_list")
    return render(request, "defect/delete_confirm.html", {"record": record})


def defect_infer(request):
    """上传图片 → 自动调用YOLO推理 → 自动创建缺陷记录。"""
    result = None
    if request.method == "POST" and request.FILES.get("image"):
        uploaded = request.FILES["image"]
        detect_person = request.POST.get("detect_person", "系统")
        device_id = request.POST.get("device_id", "web-upload")

        # 保存上传的原图
        import uuid
        from django.conf import settings
        from pathlib import Path

        save_dir = Path(settings.MEDIA_ROOT) / "original"
        save_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{uuid.uuid4().hex}_{uploaded.name}"
        img_path = save_dir / fname
        with open(img_path, "wb") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        # 调YOLO推理
        inference = run_inference(str(img_path))

        if "error" in inference:
            result = inference
        else:
            # 匹配DefectType
            type_name = inference["class_name"]
            defect_type, created = DefectType.objects.get_or_create(
                type_name=type_name,
                defaults={"description": f"自动检测类别: {type_name}"}
            )

            # 复制画框图到media
            defect_img_field = ""
            if inference.get("defect_img_path"):
                src = inference["defect_img_path"]
                dst = Path(settings.MEDIA_ROOT) / "defect_img" / Path(src).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(src, dst)
                defect_img_field = f"defect_img/{Path(src).name}"

            # 自动创建缺陷记录
            record = DefectRecord.objects.create(
                defect_type=defect_type,
                detect_person=detect_person,
                device_id=device_id,
                confidence=inference["confidence"],
                original_img=f"original/{fname}",
                defect_img=defect_img_field,
                model_version=inference["model_version"],
                inference_run_id=inference["run_id"],
                data_fingerprint=inference["data_fingerprint"],
            )
            result = {
                "class_name": type_name,
                "confidence": inference["confidence"],
                "record_id": record.id,
            }

    return render(request, "defect/infer.html", {"result": result})
