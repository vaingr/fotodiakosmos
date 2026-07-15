from django.contrib import admin
from .models import Subscription, ScheduledTask, ScheduledTaskItem

# Register your models here.
admin.site.register(Subscription)


class ScheduledTaskItemInline(admin.TabularInline):
    model = ScheduledTaskItem
    extra = 0
    fields = ('product', 'quantity', 'item_status')


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('task_type', 'customer', 'scheduled_date', 'priority', 'status', 'assigned_to', 'created_by')
    list_filter = ('status', 'priority', 'task_type', 'scheduled_date')
    search_fields = ('description', 'customer__company_name', 'customer__first_name', 'customer__last_name')
    inlines = [ScheduledTaskItemInline]
