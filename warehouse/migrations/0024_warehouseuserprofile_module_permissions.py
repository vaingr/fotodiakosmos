from django.db import migrations, models


def grant_module_permissions_to_admins(apps, schema_editor):
    WarehouseUserProfile = apps.get_model('warehouse', 'WarehouseUserProfile')
    WarehouseUserProfile.objects.filter(role='admin').update(
        perm_finished_products_warehouse=True,
        perm_offers=True,
        perm_customers=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0023_warehouseuserprofile_is_managed_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehouseuserprofile',
            name='perm_finished_products_warehouse',
            field=models.BooleanField(
                default=False,
                verbose_name='Αποθήκη Έτοιμων Προϊόντων',
            ),
        ),
        migrations.AddField(
            model_name='warehouseuserprofile',
            name='perm_offers',
            field=models.BooleanField(default=False, verbose_name='Προσφορές'),
        ),
        migrations.AddField(
            model_name='warehouseuserprofile',
            name='perm_customers',
            field=models.BooleanField(default=False, verbose_name='Πελάτες'),
        ),
        migrations.RunPython(grant_module_permissions_to_admins, migrations.RunPython.noop),
    ]
