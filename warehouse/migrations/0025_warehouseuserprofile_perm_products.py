from django.db import migrations, models


def grant_products_permission_to_admins(apps, schema_editor):
    WarehouseUserProfile = apps.get_model('warehouse', 'WarehouseUserProfile')
    WarehouseUserProfile.objects.filter(role='admin').update(perm_products=True)


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0024_warehouseuserprofile_module_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehouseuserprofile',
            name='perm_products',
            field=models.BooleanField(default=False, verbose_name='Προϊόντα'),
        ),
        migrations.RunPython(grant_products_permission_to_admins, migrations.RunPython.noop),
    ]
