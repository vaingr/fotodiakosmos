from django.db import migrations, models


def copy_terms_from_settings(apps, schema_editor):
    Offer = apps.get_model('products', 'Offer')
    OfferSettings = apps.get_model('products', 'OfferSettings')
    settings, _ = OfferSettings.objects.get_or_create(pk=1)
    Offer.objects.update(
        delivery_time=settings.delivery_time,
        delivery_place=settings.delivery_place,
        delivery_method=settings.delivery_method,
        packaging=settings.packaging,
        payment_method=settings.payment_method,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_offersettings_terms'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='delivery_method',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Τρόπος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offer',
            name='delivery_place',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Τόπος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offer',
            name='delivery_time',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Χρόνος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offer',
            name='packaging',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Συσκευασία'),
        ),
        migrations.AddField(
            model_name='offer',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Τρόπος πληρωμής'),
        ),
        migrations.RunPython(copy_terms_from_settings, migrations.RunPython.noop),
    ]
