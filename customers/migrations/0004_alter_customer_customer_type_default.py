from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_customer_type_and_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='customer_type',
            field=models.CharField(
                choices=[('company', 'Εταιρία / Δήμος'), ('individual', 'Ιδιώτης')],
                default='company',
                max_length=20,
                verbose_name='Τύπος πελάτη',
            ),
        ),
    ]
