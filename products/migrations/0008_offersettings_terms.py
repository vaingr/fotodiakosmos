from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_offer_bank_account_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='offersettings',
            name='delivery_time',
            field=models.CharField(default='Κατόπιν συνεννόησης', max_length=200, verbose_name='Χρόνος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offersettings',
            name='delivery_place',
            field=models.CharField(default='Έδρα πελάτη', max_length=200, verbose_name='Τόπος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offersettings',
            name='delivery_method',
            field=models.CharField(default='Κατόπιν συνεννόησης', max_length=200, verbose_name='Τρόπος παράδοσης'),
        ),
        migrations.AddField(
            model_name='offersettings',
            name='packaging',
            field=models.CharField(default='Δέματα', max_length=200, verbose_name='Συσκευασία'),
        ),
        migrations.AddField(
            model_name='offersettings',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Τρόπος πληρωμής'),
        ),
    ]
