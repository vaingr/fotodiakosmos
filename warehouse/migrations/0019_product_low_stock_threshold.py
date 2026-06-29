# Generated manually for per-product low stock threshold

import django.core.validators
from django.db import migrations, models


def copy_global_threshold(apps, schema_editor):
    Product = apps.get_model('warehouse', 'Product')
    WarehouseSettings = apps.get_model('warehouse', 'WarehouseSettings')
    settings = WarehouseSettings.objects.first()
    threshold = settings.low_stock_threshold if settings else 10
    Product.objects.all().update(low_stock_threshold=threshold)


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0018_measurement_units'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='low_stock_threshold',
            field=models.IntegerField(
                default=10,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Όριο Χαμηλού Αποθέματος',
            ),
        ),
        migrations.RunPython(copy_global_threshold, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='WarehouseSettings',
        ),
    ]
