from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0005_alter_customer_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='contact_person_gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Άνδρας'), ('female', 'Γυναίκα')],
                default='',
                max_length=10,
                verbose_name='Φύλο υπεύθυνου επικοινωνίας',
            ),
        ),
    ]
