from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    WarehouseUserProfile = apps.get_model('warehouse', 'WarehouseUserProfile')
    for user in User.objects.all():
        WarehouseUserProfile.objects.get_or_create(
            user_id=user.id,
            defaults={
                'role': 'admin',
                'perm_dashboard': True,
                'perm_view_products': True,
                'perm_create_products': True,
                'perm_edit_products': True,
                'perm_delete_products': True,
                'perm_add_quantity': True,
                'perm_remove_quantity': True,
                'perm_measurement_units': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse', '0021_stock_movement'),
    ]

    operations = [
        migrations.CreateModel(
            name='WarehouseUserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Διαχειριστής Αποθήκης'), ('user', 'Απλός Χρήστης')], default='user', max_length=10, verbose_name='Ρόλος')),
                ('perm_dashboard', models.BooleanField(default=True, verbose_name='Αρχική Αποθήκη')),
                ('perm_view_products', models.BooleanField(default=True, verbose_name='Προβολή Υλικών')),
                ('perm_create_products', models.BooleanField(default=False, verbose_name='Δημιουργία Υλικών')),
                ('perm_edit_products', models.BooleanField(default=False, verbose_name='Επεξεργασία Υλικών')),
                ('perm_delete_products', models.BooleanField(default=False, verbose_name='Διαγραφή Υλικών')),
                ('perm_add_quantity', models.BooleanField(default=False, verbose_name='Προσθήκη Ποσότητας')),
                ('perm_remove_quantity', models.BooleanField(default=False, verbose_name='Αφαίρεση Ποσότητας')),
                ('perm_measurement_units', models.BooleanField(default=False, verbose_name='Μονάδες Μέτρησης')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Δημιουργίας')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_profile', to=settings.AUTH_USER_MODEL, verbose_name='Χρήστης')),
            ],
            options={
                'verbose_name': 'Προφίλ Χρήστη Αποθήκης',
                'verbose_name_plural': 'Προφίλ Χρηστών Αποθήκης',
            },
        ),
        migrations.RunPython(create_profiles_for_existing_users, migrations.RunPython.noop),
    ]
