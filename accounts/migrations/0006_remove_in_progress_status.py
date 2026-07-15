from django.db import migrations, models


def migrate_in_progress_to_pending(apps, schema_editor):
    ScheduledTask = apps.get_model('accounts', 'ScheduledTask')
    ScheduledTask.objects.filter(status='in_progress').update(status='pending')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_scheduledtaskitem_status'),
    ]

    operations = [
        migrations.RunPython(
            migrate_in_progress_to_pending,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='scheduledtask',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Σε εκκρεμότητα'),
                    ('completed', 'Ολοκληρωμένη'),
                    ('cancelled', 'Ακυρωμένη'),
                ],
                default='pending',
                max_length=20,
                verbose_name='Κατάσταση',
            ),
        ),
    ]
