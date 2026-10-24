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

    # 数据血缘溯源字段
    infer_run_id = models.CharField(max_length=50, blank=True, verbose_name="推理运行ID")
    model_version = models.CharField(max_length=200, blank=True, verbose_name="模型版本")
    data_fingerprint = models.CharField(max_length=64, blank=True, verbose_name="数据指纹")
    manifest_ref = models.CharField(max_length=500, blank=True, verbose_name="划分契约路径")
    engine_raw = models.JSONField(default=dict, blank=True, verbose_name="引擎原始检测输出")
    llm_review = models.JSONField(default=dict, blank=True, verbose_name="LLM研判结果")

    # 复核工作流
    review_status = models.CharField(
        max_length=20, default="pending", verbose_name="复核状态",
        choices=[("pending", "待复核"), ("confirmed", "已确认"), ("rejected", "已驳回")]
    )
    reviewed_by = models.CharField(max_length=50, blank=True, verbose_name="复核人")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="复核时间")
    reject_reason = models.TextField(blank=True, verbose_name="驳回原因")

    def __str__(self):
        return f"{self.defect_type.type_name} - {self.detect_person}"

    class Meta:
        verbose_name = "缺陷检测记录"
        verbose_name_plural = "缺陷检测记录"


class DefectEvent(models.Model):
    """视频聚合出的缺陷事件（帧→事件抽象层）"""
    event_id = models.CharField(max_length=50, unique=True, verbose_name="事件ID")
    defect_type = models.ForeignKey(DefectType, on_delete=models.SET_NULL, null=True, verbose_name="缺陷类型")
    start_time = models.FloatField(verbose_name="起始时间(秒)")
    end_time = models.FloatField(verbose_name="结束时间(秒)")
    peak_confidence = models.FloatField(verbose_name="峰值置信度")
    avg_confidence = models.FloatField(verbose_name="平均置信度")
    frame_count = models.IntegerField(verbose_name="持续帧数")
    bbox_trace = models.JSONField(default=list, verbose_name="轨迹bbox")
    region = models.CharField(max_length=50, blank=True, verbose_name="画面区域")
    inference_job = models.ForeignKey("InferenceJob", on_delete=models.CASCADE, verbose_name="推理任务")
    llm_review = models.JSONField(default=dict, blank=True, verbose_name="LLM研判结果")
    review_status = models.CharField(
        max_length=20, default="pending", verbose_name="复核状态",
        choices=[("pending", "待复核"), ("confirmed", "已确认"), ("rejected", "已驳回")]
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.event_id} {self.defect_type} {self.start_time:.1f}s-{self.end_time:.1f}s"

    class Meta:
        verbose_name = "缺陷事件"
        verbose_name_plural = "缺陷事件"


class InferenceJob(models.Model):
    """推理任务队列"""
    STATUS_CHOICES = [
        ("pending", "排队中"),
        ("running", "推理中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]
    job_id = models.CharField(max_length=50, unique=True, verbose_name="任务ID")
    source_type = models.CharField(max_length=20, verbose_name="输入类型",
                                   choices=[("image", "图片"), ("video", "视频"), ("camera", "摄像头")])
    source_path = models.CharField(max_length=500, verbose_name="输入路径")
    model_version = models.CharField(max_length=200, verbose_name="模型版本")
    data_fingerprint = models.CharField(max_length=64, blank=True, verbose_name="数据指纹")
    status = models.CharField(max_length=20, default="pending", verbose_name="状态", choices=STATUS_CHOICES)
    progress = models.IntegerField(default=0, verbose_name="进度百分比")
    result = models.JSONField(default=dict, blank=True, verbose_name="推理结果")
    error_msg = models.TextField(blank=True, verbose_name="错误信息")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")

    def __str__(self):
        return f"{self.job_id} [{self.status}]"

    class Meta:
        verbose_name = "推理任务"
        verbose_name_plural = "推理任务"


class LLMInvocation(models.Model):
    """每次LLM调用记录（prompt版本/tokens/耗时/原始输出）"""
    invocation_id = models.CharField(max_length=50, unique=True, verbose_name="调用ID")
    target_type = models.CharField(max_length=20, verbose_name="目标类型",
                                   choices=[("record", "缺陷记录"), ("event", "缺陷事件")])
    target_id = models.IntegerField(verbose_name="目标ID")
    prompt_version = models.CharField(max_length=50, verbose_name="Prompt版本")
    model_name = models.CharField(max_length=100, verbose_name="模型名")
    input_tokens = models.IntegerField(default=0, verbose_name="输入tokens")
    output_tokens = models.IntegerField(default=0, verbose_name="输出tokens")
    latency_ms = models.IntegerField(default=0, verbose_name="耗时(毫秒)")
    raw_request = models.JSONField(default=dict, verbose_name="原始请求")
    raw_response = models.JSONField(default=dict, verbose_name="原始响应")
    retry_count = models.IntegerField(default=0, verbose_name="重试次数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="调用时间")

    def __str__(self):
        return f"{self.invocation_id} {self.model_name} {self.latency_ms}ms"

    class Meta:
        verbose_name = "LLM调用"
        verbose_name_plural = "LLM调用"
