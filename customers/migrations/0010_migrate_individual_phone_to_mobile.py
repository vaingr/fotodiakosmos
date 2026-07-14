from django.db import migrations


def migrate_individual_phone_to_mobile(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    for customer in Customer.objects.filter(customer_type='individual').exclude(phone=''):
        if not customer.contact_mobile:
            customer.contact_mobile = customer.phone
            customer.phone = ''
            customer.save(update_fields=['contact_mobile', 'phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0009_contact_mobile_landline'),
    ]

    operations = [
        migrations.RunPython(migrate_individual_phone_to_mobile, migrations.RunPython.noop),
    ]
