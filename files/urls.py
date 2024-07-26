from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload, name='upload'),
    path('list', views.list, name='list'),
    path('files_api', views.files_api, name='files_api'),
    path('preview',views.preview_file,name="preview"),
    # 其他路径...
]
