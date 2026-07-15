from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_offer_terms_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='productstock',
            name='construction_stage',
            field=models.CharField(
                choices=[('skeleton', 'Σκελετός'), ('complete', 'Ολοκληρωμένο')],
                default='complete',
                max_length=20,
                verbose_name='Στάδιο Κατασκευής',
            ),
        ),
        migrations.AlterField(
            model_name='productstock',
            name='product',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='stocks',
                to='products.finishedproduct',
                verbose_name='Προϊόν',
            ),
        ),
        migrations.AddConstraint(
            model_name='productstock',
            constraint=models.UniqueConstraint(
                fields=('product', 'construction_stage'),
                name='unique_product_construction_stage',
            ),
        ),
    ]
