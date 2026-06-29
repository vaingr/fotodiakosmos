# Generated manually for measurement units feature

import django.db.models.deletion
from django.db import migrations, models


def create_default_units(apps, schema_editor):
    MeasurementUnit = apps.get_model('warehouse', 'MeasurementUnit')
    MeasurementUnit.objects.get_or_create(name='ΤΕΜΑΧΙΑ')
    MeasurementUnit.objects.get_or_create(name='ΜΕΤΡΑ')


def assign_default_unit_to_products(apps, schema_editor):
    Product = apps.get_model('warehouse', 'Product')
    MeasurementUnit = apps.get_model('warehouse', 'MeasurementUnit')
    default_unit = MeasurementUnit.objects.filter(name='ΤΕΜΑΧΙΑ').first()
    if default_unit:
        Product.objects.filter(measurement_unit__isnull=True).update(measurement_unit=default_unit)


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0017_remove_inventory'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeasurementUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Όνομα')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Δημιουργίας')),
            ],
            options={
                'verbose_name': 'Μονάδα Μέτρησης',
                'verbose_name_plural': 'Μονάδες Μέτρησης',
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(create_default_units, migrations.RunPython.noop),
        migrations.AddField(
            model_name='product',
            name='measurement_unit',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='products',
                to='warehouse.measurementunit',
                verbose_name='Μονάδα Μέτρησης',
            ),
        ),
        migrations.RunPython(assign_default_unit_to_products, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='measurement_unit',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='products',
                to='warehouse.measurementunit',
                verbose_name='Μονάδα Μέτρησης',
            ),
        ),
    ]
