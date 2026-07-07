from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('warehouse/', views.product_warehouse, name='product_warehouse'),
    path('warehouse/print/', views.product_warehouse_print, name='product_warehouse_print'),
    path('warehouse/email/', views.product_warehouse_email, name='product_warehouse_email'),
    path('offers/', views.offers, name='offers'),
    path('offers/settings/', views.offer_settings, name='offer_settings'),
    path('offers/create/', views.offer_create, name='offer_create'),
    path('offers/<int:pk>/edit/', views.offer_edit, name='offer_edit'),
    path('offers/<int:pk>/print/', views.offer_print, name='offer_print'),
    path('offers/<int:pk>/email/', views.offer_email, name='offer_email'),
    path('offers/<int:pk>/pdf/', views.offer_pdf, name='offer_pdf'),
    path('offers/<int:pk>/delete/', views.offer_delete, name='offer_delete'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
]
