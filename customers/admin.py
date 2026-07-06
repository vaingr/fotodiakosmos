from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'customer_type', 'phone', 'email', 'created_at')
    list_filter = ('customer_type', 'created_at')
    search_fields = (
        'last_name', 'first_name', 'company_name', 'phone', 'email',
        'contact_person', 'contact_phone', 'contact_email',
        'contact_person_2', 'contact_person_2_phone', 'contact_person_2_email',
    )
    ordering = ('last_name', 'first_name', 'company_name')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Όνομα')
    def display_name(self, obj):
        return obj.display_name()
    
    fieldsets = (
        ('Τύπος πελάτη', {
            'fields': ('customer_type',)
        }),
        ('Στοιχεία ιδιώτη', {
            'fields': ('last_name', 'first_name')
        }),
        ('Στοιχεία εταιρείας / Δήμου', {
            'fields': (
                'company_name',
                ('contact_person', 'contact_person_gender'),
                ('contact_phone', 'contact_email'),
                ('contact_person_2', 'contact_person_2_gender'),
                ('contact_person_2_phone', 'contact_person_2_email'),
            ),
        }),
        ('Επικοινωνία', {
            'fields': ('phone', 'email', 'vat_rate')
        }),
        ('Πληροφορίες Συστήματος', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
