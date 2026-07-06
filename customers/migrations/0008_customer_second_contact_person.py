from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0007_customer_vat_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='contact_person_2',
            field=models.CharField(
                blank=True,
                default='',
                max_length=200,
                verbose_name='2ος υπεύθυνος επικοινωνίας',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_person_2_email',
            field=models.EmailField(
                blank=True,
                default='',
                max_length=254,
                verbose_name='Email 2ου υπεύθυνου',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_person_2_gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Άνδρας'), ('female', 'Γυναίκα')],
                default='',
                max_length=10,
                verbose_name='Φύλο 2ου υπεύθυνου',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_person_2_phone',
            field=models.CharField(
                blank=True,
                default='',
                max_length=20,
                verbose_name='Τηλέφωνο 2ου υπεύθυνου',
            ),
        ),
    ]
