from collections import defaultdict

from django.db import migrations, models


def merge_duplicate_complete_stocks(apps, schema_editor):
    ProductStock = apps.get_model('products', 'ProductStock')
    ProductStockMovement = apps.get_model('products', 'ProductStockMovement')

    groups = defaultdict(list)
    for stock in ProductStock.objects.filter(construction_stage='complete'):
        key = (stock.product_id, stock.carpet, stock.bulb, stock.dimensions)
        groups[key].append(stock)

    for stocks in groups.values():
        if len(stocks) <= 1:
            continue
        primary = min(stocks, key=lambda item: item.created_at)
        primary.quantity = sum(item.quantity for item in stocks)
        primary.save(update_fields=['quantity'])
        for duplicate in stocks:
            if duplicate.pk == primary.pk:
                continue
            ProductStockMovement.objects.filter(stock_id=duplicate.pk).update(stock_id=primary.pk)
            duplicate.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_productstock_complete_details'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_complete_stocks, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='productstock',
            name='unique_product_construction_stage',
        ),
        migrations.AddConstraint(
            model_name='productstock',
            constraint=models.UniqueConstraint(
                fields=('product', 'construction_stage', 'carpet', 'bulb', 'dimensions'),
                name='unique_product_stock_variant',
            ),
        ),
    ]
