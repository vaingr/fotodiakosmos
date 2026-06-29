# Generated manually to initialize the code counter

from django.db import migrations

def initialize_code_counter(apps, schema_editor):
    """Initialize the code counter with the maximum existing code"""
    ProductCodeCounter = apps.get_model('warehouse', 'ProductCodeCounter')
    Product = apps.get_model('warehouse', 'Product')
    
    # Find the maximum numeric code from existing products
    max_code = -1
    for product in Product.objects.all():
        if product.code and len(product.code) == 5 and product.code.isdigit():
            try:
                code_num = int(product.code)
                if code_num > max_code:
                    max_code = code_num
            except ValueError:
                continue
    
    # Create or update the counter
    counter, created = ProductCodeCounter.objects.get_or_create(
        pk=1,
        defaults={'last_code': max_code}
    )
    if not created and counter.last_code < max_code:
        counter.last_code = max_code
        counter.save()

def reverse_initialize_code_counter(apps, schema_editor):
    """Reverse migration - nothing to do"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0010_add_product_code_counter'),
    ]

    operations = [
        migrations.RunPython(initialize_code_counter, reverse_initialize_code_counter),
    ]

