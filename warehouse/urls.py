from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_dashboard, name='dashboard'),
    path('add-quantity/', views.quantity_select_add, name='quantity_select_add'),
    path('remove-quantity/', views.quantity_select_remove, name='quantity_select_remove'),
    path('products/', views.product_list, name='product_list'),
    path('products/print/', views.product_list_print, name='product_list_print'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/add-quantity/', views.product_add_quantity, name='product_add_quantity'),
    path('products/<int:pk>/remove-quantity/', views.product_remove_quantity, name='product_remove_quantity'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/search/', views.product_search_api, name='product_search_api'),
    path('settings/', views.warehouse_settings, name='settings'),
    path('settings/measurement-units/', views.measurement_unit_list, name='measurement_unit_list'),
    path('settings/measurement-units/create/', views.measurement_unit_create, name='measurement_unit_create'),
    path('settings/measurement-units/<int:pk>/edit/', views.measurement_unit_edit, name='measurement_unit_edit'),
    path('settings/measurement-units/<int:pk>/delete/', views.measurement_unit_delete, name='measurement_unit_delete'),
    path('settings/users/', views.warehouse_user_list, name='warehouse_user_list'),
    path('settings/users/create/', views.warehouse_user_create, name='warehouse_user_create'),
    path('settings/users/<int:pk>/edit/', views.warehouse_user_edit, name='warehouse_user_edit'),
    path('settings/users/<int:pk>/delete/', views.warehouse_user_delete, name='warehouse_user_delete'),
]

