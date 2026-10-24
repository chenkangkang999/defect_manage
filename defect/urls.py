from django.urls import path, include
from . import views, api_views, dashboard_views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"records", api_views.DefectRecordViewSet)
router.register(r"events", api_views.DefectEventViewSet)
router.register(r"jobs", api_views.InferenceJobViewSet)
router.register(r"llm", api_views.LLMInvocationViewSet)

urlpatterns = [
    # 传统模板页面
    path('list/', views.defect_list, name="defect_list"),
    path('add/', views.defect_add, name="defect_add"),
    path('detail/<int:defect_id>/', views.defect_detail, name="defect_detail"),
    path('edit/<int:defect_id>/', views.defect_edit, name="defect_edit"),
    path('delete/<int:defect_id>/', views.defect_delete, name="defect_delete"),
    path('infer/', views.defect_infer, name="defect_infer"),

    # W3 看板与工作流
    path('dashboard/', dashboard_views.dashboard, name="dashboard"),
    path('review/', dashboard_views.review_queue, name="review_queue"),
    path('review/<int:defect_id>/confirm/', dashboard_views.review_action, {"action": "confirm"}, name="review_confirm"),
    path('review/<int:defect_id>/reject/', dashboard_views.review_action, {"action": "reject"}, name="review_reject"),
    path('heatmap/', dashboard_views.heatmap, name="heatmap"),
    path('events/', dashboard_views.event_list, name="event_list"),

    # REST API
    path('api/v1/', include(router.urls)),
    path('api/v1/jobs/create/', api_views.create_job),
    path('api/v1/jobs/<str:pk>/', api_views.job_detail),
    path('api/v1/records/<int:pk>/review/', api_views.review_record),
    path('api/v1/events/<str:pk>/explain/', api_views.explain_event),
]
