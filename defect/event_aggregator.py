"""L2: EventAggregator — 帧级检测结果聚合成缺陷事件。

把逐帧boxes按类别+空间IoU做跨帧关联，时间窗合并间隙<N帧的同一事件，
输出 DefectEvent：起止时间、类别、峰值/平均置信度、持续帧数、bbox轨迹。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class FrameBox:
    """单帧检测框"""
    frame_idx: int
    cls_name: str
    confidence: float
    cx: float   # bbox中心x
    cy: float   # bbox中心y
    w: float
    h: float


@dataclass
class TrackedEvent:
    """正在追踪的事件"""
    cls_name: str
    frames: List[int] = field(default_factory=list)
    confidences: List[float] = field(default_factory=list)
    cx_history: List[float] = field(default_factory=list)
    cy_history: List[float] = field(default_factory=list)
    last_frame: int = -1

    @property
    def peak_conf(self):
        return max(self.confidences) if self.confidences else 0

    @property
    def avg_conf(self):
        return sum(self.confidences) / len(self.confidences) if self.confidences else 0

    @property
    def frame_count(self):
        return len(self.frames)

    @property
    def start(self):
        return self.frames[0] if self.frames else 0

    @property
    def end(self):
        return self.frames[-1] if self.frames else 0

    @property
    def region(self):
        """根据bbox中心判断画面区域"""
        cx = sum(self.cx_history) / len(self.cx_history) if self.cx_history else 0
        cy = sum(self.cy_history) / len(self.cy_history) if self.cy_history else 0
        h_pos = "左" if cx < 213 else ("中" if cx < 426 else "右")
        v_pos = "上" if cy < 160 else ("中" if cy < 320 else "下")
        return f"{v_pos}{h_pos}区"


def _iou_distance(cx1, cy1, w1, h1, cx2, cy2, w2, h2) -> float:
    """简化版空间相似度：中心距离归一化"""
    import math
    dist = math.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
    scale = max(w1 + w2, h1 + h2)
    return 1.0 - min(dist / scale, 1.0) if scale > 0 else 0


def aggregate(frames: List[FrameBox], gap_threshold: int = 5,
              match_threshold: float = 0.3) -> List[dict]:
    """
    聚合帧级检测结果为缺陷事件。

    Args:
        frames: 所有帧的检测框列表
        gap_threshold: 间隙<N帧视为同一事件
        match_threshold: 跨帧匹配阈值

    Returns:
        List[dict]: 事件列表，可直接写入DefectEvent表
    """
    active: List[TrackedEvent] = []
    completed: List[TrackedEvent] = []

    # 按帧号排序
    frames.sort(key=lambda f: f.frame_idx)

    for box in frames:
        matched = None
        # 在活跃事件中找同类最佳匹配
        for ev in active:
            if ev.cls_name != box.cls_name:
                continue
            sim = _iou_distance(
                box.cx, box.cy, box.w, box.h,
                ev.cx_history[-1], ev.cy_history[-1], 50, 50
            )
            if sim > match_threshold:
                matched = ev
                break

        if matched:
            # 追加到现有事件
            matched.frames.append(box.frame_idx)
            matched.confidences.append(box.confidence)
            matched.cx_history.append(box.cx)
            matched.cy_history.append(box.cy)
            matched.last_frame = box.frame_idx
        else:
            # 开新事件
            ev = TrackedEvent(
                cls_name=box.cls_name,
                frames=[box.frame_idx],
                confidences=[box.confidence],
                cx_history=[box.cx],
                cy_history=[box.cy],
                last_frame=box.frame_idx,
            )
            active.append(ev)

    # 把超时未更新的事件移到完成列表
    for ev in active:
        completed.append(ev)

    # 转成字典
    results = []
    for ev in completed:
        results.append({
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "cls_name": ev.cls_name,
            "start_time": float(ev.start) / 30.0,  # 假设30fps
            "end_time": float(ev.end) / 30.0,
            "peak_confidence": round(ev.peak_conf, 4),
            "avg_confidence": round(ev.avg_conf, 4),
            "frame_count": ev.frame_count,
            "bbox_trace": list(zip(ev.cx_history, ev.cy_history)),
            "region": ev.region,
        })

    return results
