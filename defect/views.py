from django.shortcuts import render, redirect, get_object_or_404
from .models import DefectRecord
from .forms import DefectForm


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
