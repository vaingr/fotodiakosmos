"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import dashboard, create_user, CustomLoginView, manage_subscriptions, manage_users, database_backup, database_restore, database_management, manage_client_name, manage_app_name, manage_partner_name, manage_email_settings, manage_sms_settings, send_sms_view, send_bulk_sms_view, check_sms_balance, sms_dashboard, get_sms_history_view, manage_customers_module, task_scheduling
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('task-scheduling/', task_scheduling, name='task_scheduling'),
    path('create-user/', create_user, name='create_user'),
    path('manage-subscriptions/', manage_subscriptions, name='manage_subscriptions'),
    path('manage-users/', manage_users, name='manage_users'),
    path('database-management/', database_management, name='database_management'),
    path('database-backup/', database_backup, name='database_backup'),
    path('database-restore/', database_restore, name='database_restore'),
    path('manage-client-name/', manage_client_name, name='manage_client_name'),
    path('manage-app-name/', manage_app_name, name='manage_app_name'),
    path('manage-partner-name/', manage_partner_name, name='manage_partner_name'),
    path('manage-email-settings/', manage_email_settings, name='manage_email_settings'),
    path('manage-sms-settings/', manage_sms_settings, name='manage_sms_settings'),
    path('manage-customers-module/', manage_customers_module, name='manage_customers_module'),
    path('sms/', sms_dashboard, name='sms_dashboard'),
    path('send-sms/', send_sms_view, name='send_sms'),
    path('send-bulk-sms/', send_bulk_sms_view, name='send_bulk_sms'),
    path('check-sms-balance/', check_sms_balance, name='check_sms_balance'),
    path('get-sms-history/', get_sms_history_view, name='get_sms_history'),
    path('customers/', include('customers.urls')),
    path('products/', include('products.urls')),
    path('warehouse/', include('warehouse.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
