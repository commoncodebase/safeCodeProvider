from django.urls import path
from .views import teacher_home, start_exam, submits_page, bring_code, open_student_port, close_student_port

urlpatterns = [
    path('', teacher_home, name='teacher_home'),
    path('start_exam/', start_exam, name='start_exam'),
    path('submits/', submits_page, name='submits_page'),
    path('bring_code/', bring_code, name='bring_code'),
    path("open_port/", open_student_port, name="open_port"),
    path("close_port/", close_student_port, name="close_port"),

]