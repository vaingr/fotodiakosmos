from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_offer_offeritem'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfferSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='offers/logo/', verbose_name='Λογότυπο προσφοράς')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Τελευταία ενημέρωση')),
            ],
            options={
                'verbose_name': 'Ρυθμίσεις Προσφορών',
                'verbose_name_plural': 'Ρυθμίσεις Προσφορών',
            },
        ),
    ]
