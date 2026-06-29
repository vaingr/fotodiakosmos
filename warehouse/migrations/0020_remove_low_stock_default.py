from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0019_product_low_stock_threshold'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='low_stock_threshold',
            field=models.IntegerField(
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Όριο Χαμηλού Αποθέματος',
            ),
        ),
    ]
