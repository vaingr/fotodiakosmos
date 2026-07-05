from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='contact_person',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Υπεύθυνος επικοινωνίας'),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_phone',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Τηλέφωνο υπεύθυνου'),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_email',
            field=models.EmailField(blank=True, default='', max_length=254, verbose_name='Email υπεύθυνου'),
        ),
    ]
