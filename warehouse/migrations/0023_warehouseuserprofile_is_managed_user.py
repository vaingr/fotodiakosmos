from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0022_warehouse_user_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehouseuserprofile',
            name='is_managed_user',
            field=models.BooleanField(
                default=False,
                verbose_name='Δημιουργήθηκε από Διαχείριση Αποθήκης',
            ),
        ),
    ]
