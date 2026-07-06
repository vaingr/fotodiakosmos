from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_customer_contact_person_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='vat_rate',
            field=models.CharField(
                choices=[('24', '24%'), ('17', '17%'), ('0', 'Μηδενικό')],
                default='24',
                max_length=5,
                verbose_name='ΦΠΑ',
            ),
        ),
    ]
