from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('last_name', 'first_name', 'phone', 'email')
    ordering = ('last_name', 'first_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('last_name', 'first_name', 'phone', 'email')
        }),
        ('Πληροφορίες Συστήματος', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
