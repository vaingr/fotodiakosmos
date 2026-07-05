from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_customer_contact_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='company_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Όνομα εταιρείας / Δήμου'),
        ),
        migrations.AddField(
            model_name='customer',
            name='customer_type',
            field=models.CharField(
                choices=[('individual', 'Ιδιώτης'), ('company', 'Εταιρία / Δήμος')],
                default='individual',
                max_length=20,
                verbose_name='Τύπος πελάτη',
            ),
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Όνομα'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Επώνυμο'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Τηλέφωνο'),
        ),
    ]
