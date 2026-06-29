# Generated manually for stock movements

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse', '0020_remove_low_stock_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('add', 'Προσθήκη'), ('remove', 'Αφαίρεση')], max_length=10, verbose_name='Τύπος')),
                ('amount', models.PositiveIntegerField(verbose_name='Ποσότητα')),
                ('quantity_before', models.IntegerField(verbose_name='Ποσότητα Πριν')),
                ('quantity_after', models.IntegerField(verbose_name='Ποσότητα Μετά')),
                ('note', models.TextField(blank=True, verbose_name='Σημείωση')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to=settings.AUTH_USER_MODEL, verbose_name='Καταχωρήθηκε από')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='warehouse.product', verbose_name='Υλικό')),
            ],
            options={
                'verbose_name': 'Κίνηση Αποθέματος',
                'verbose_name_plural': 'Κινήσεις Αποθέματος',
                'ordering': ['-created_at'],
            },
        ),
    ]
