from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:customer_id>/delete/', views.delete_customer, name='delete_customer'),
    path('<int:customer_id>/send-sms/', views.send_sms_to_customer, name='send_sms'),
] 