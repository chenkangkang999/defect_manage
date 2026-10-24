from django.db import models


class DefectType(models.Model):
    """缺陷类型：划痕、污渍、缺角、变形"""
    type_name = models.CharField(max_length=50, verbose_name="缺陷类型名称")
    description = models.TextField(blank=True, verbose_name="类型说明")

    def __str__(self):
        return self.type_name

    class Meta:
        verbose_name = "缺陷类型"
        verbose_name_plural = "缺陷类型"


class DefectRecord(models.Model):
    """缺陷检测记录"""
    defect_type = models.ForeignKey(DefectType, on_delete=models.CASCADE, verbose_name="缺陷类型")
    detect_person = models.CharField(max_length=50, verbose_name="检测人员")
    device_id = models.CharField(max_length=50, verbose_name="检测设备编号")
    confidence = models.FloatField(verbose_name="检测置信度", help_text="0~1之间")
    original_img = models.ImageField(upload_to="original/", verbose_name="原图")
    defect_img = models.ImageField(upload_to="defect_img/", verbose_name="缺陷标注图", blank=True)
    detect_time = models.DateTimeField(auto_now_add=True, verbose_name="检测时间")
    remark = models.TextField(blank=True, verbose_name="备注")

    def __str__(self):
        return f"{self.defect_type.type_name} - {self.detect_person}"

    class Meta:
        verbose_name = "缺陷检测记录"
        verbose_name_plural = "缺陷检测记录"
