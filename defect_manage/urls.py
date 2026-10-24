from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('defect/', include("defect.urls")),
]

# 开发环境下，让Django可以访问media上传图片
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
