from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_productstock_construction_stage'),
    ]

    operations = [
        migrations.AddField(
            model_name='productstock',
            name='bulb',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ΛΑΜΠΑΚΙ'),
        ),
        migrations.AddField(
            model_name='productstock',
            name='carpet',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ΜΟΚΕΤΑ'),
        ),
        migrations.AddField(
            model_name='productstock',
            name='dimensions',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ΔΙΑΣΤΑΣΕΙΣ'),
        ),
        migrations.AddField(
            model_name='productstock',
            name='photocell',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ΦΩΤΟΣΩΛΗΝΑΣ'),
        ),
    ]
