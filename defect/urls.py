from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.defect_list, name="defect_list"),
    path('add/', views.defect_add, name="defect_add"),
    path('detail/<int:defect_id>/', views.defect_detail, name="defect_detail"),
    path('edit/<int:defect_id>/', views.defect_edit, name="defect_edit"),
    path('delete/<int:defect_id>/', views.defect_delete, name="defect_delete"),
]
