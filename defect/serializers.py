"""DRF序列化器。"""
from rest_framework import serializers
from .models import DefectRecord, DefectEvent, InferenceJob, LLMInvocation, DefectType


class DefectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectType
        fields = "__all__"


class DefectRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectRecord
        fields = "__all__"


class DefectEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectEvent
        fields = "__all__"


class InferenceJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceJob
        fields = "__all__"


class LLMInvocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMInvocation
        fields = "__all__"


class ReviewRequestSerializer(serializers.Serializer):
    """人工复核请求"""
    action = serializers.ChoiceField(choices=["confirm", "reject"])
    reviewer = serializers.CharField(max_length=50)
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ExplainRequestSerializer(serializers.Serializer):
    """LLM研判请求"""
    prompt_version = serializers.CharField(default="v1")
