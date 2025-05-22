from django.conf import settings
from django.conf.urls.static import static
from django.urls import path  
from . import views 


urlpatterns = [
    path('', views.student_login, name='student_login'),  
    path('exam/', views.exam_page, name='exam_page'),  
    path('control/', views.student_control, name='student_control'),  # Öğrenci giriş kontrolünü sağlayan API URL'si
    path('save_code/', views.save_code, name='save_code'),
    path('run_code/', views.run_code, name='run_code'),
    path('delete_docker/', views.delete_docker, name='delete_docker'),
    path('list_assignment_files/', views.list_assignment_files, name='list_assignment_files'),
    # path("get_exam_time/", views.get_exam_time, name="get_exam_time"),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)