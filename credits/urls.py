from django.urls import path
from . import views

urlpatterns = [
    path('', views.credit_list, name='credit_list'),
    path('create/', views.credit_create, name='credit_create'),
    path('<int:pk>/', views.credit_detail, name='credit_detail'),
    path('<int:pk>/pay/', views.make_payment, name='make_payment'),
    path('<int:pk>/edit/', views.credit_edit, name='credit_edit'),
    path('reports/', views.reports, name='reports'),
    path('dashboard/', views.dashboard, name='dashboard'),
]