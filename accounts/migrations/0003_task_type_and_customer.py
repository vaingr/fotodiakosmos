from django.db import migrations, models
import django.db.models.deletion


def assign_customer_to_existing_tasks(apps, schema_editor):
    ScheduledTask = apps.get_model('accounts', 'ScheduledTask')
    Customer = apps.get_model('customers', 'Customer')
    customer = Customer.objects.order_by('pk').first()
    if not customer:
        ScheduledTask.objects.all().delete()
        return
    ScheduledTask.objects.filter(customer__isnull=True).update(customer=customer)


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
        ('accounts', '0002_scheduled_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledtask',
            name='task_type',
            field=models.CharField(
                choices=[('construction', 'Κατασκευή'), ('repair', 'Επισκευή')],
                default='construction',
                max_length=20,
                verbose_name='Είδος εργασίας',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scheduledtask',
            name='customer',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='scheduled_tasks',
                to='customers.customer',
                verbose_name='Πελάτης',
            ),
        ),
        migrations.RunPython(assign_customer_to_existing_tasks, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='scheduledtask',
            name='title',
        ),
        migrations.AlterField(
            model_name='scheduledtask',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='scheduled_tasks',
                to='customers.customer',
                verbose_name='Πελάτης',
            ),
        ),
        migrations.AlterModelOptions(
            name='scheduledtask',
            options={
                'ordering': ['scheduled_date', '-priority', 'task_type'],
                'verbose_name': 'Προγραμματισμένη εργασία',
                'verbose_name_plural': 'Προγραμματισμένες εργασίες',
            },
        ),
    ]
