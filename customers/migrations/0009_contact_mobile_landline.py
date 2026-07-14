from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0008_customer_second_contact_person'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='contact_phone',
            new_name='contact_mobile',
        ),
        migrations.RenameField(
            model_name='customer',
            old_name='contact_person_2_phone',
            new_name='contact_person_2_mobile',
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_landline',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Σταθερό υπεύθυνου'),
        ),
        migrations.AddField(
            model_name='customer',
            name='contact_person_2_landline',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Σταθερό 2ου υπεύθυνου'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='contact_mobile',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Κινητό υπεύθυνου'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='contact_person_2_mobile',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Κινητό 2ου υπεύθυνου'),
        ),
    ]
