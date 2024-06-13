from django.urls import path
from . import views

urlpatterns = [
    path('', views.worker_list, name='worker_list'),
    path('add_worker/', views.add_worker, name='add_worker'),
    path('add_site/', views.add_site, name='add_site'),
    path('sites/', views.site_list, name='site_list'),
    path('record_attendance/', views.record_attendance, name='record_attendance'),
    path('record_advance_payment/', views.record_advance_payment, name='record_advance_payment'),
    path('calculate_salary/', views.calculate_salary, name='calculate_salary'),
]
