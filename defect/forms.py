from django import forms
from .models import DefectRecord


class DefectForm(forms.ModelForm):
    class Meta:
        model = DefectRecord
        fields = ["defect_type", "detect_person", "device_id", "confidence",
                  "original_img", "defect_img", "remark"]
