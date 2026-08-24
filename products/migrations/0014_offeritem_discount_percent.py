import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_task_stock_reservation'),
    ]

    operations = [
        migrations.AddField(
            model_name='offeritem',
            name='discount_percent',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name='Έκπτωση %',
            ),
        ),
    ]
