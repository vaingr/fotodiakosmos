from django.db import migrations
from django.db.models import Count, F, Q


def reopen_tasks_awaiting_shipment(apps, schema_editor):
    ScheduledTask = apps.get_model('accounts', 'ScheduledTask')
    tasks = (
        ScheduledTask.objects.filter(status='completed')
        .annotate(
            total_items=Count('items'),
            shipped_items=Count(
                'items',
                filter=Q(items__item_status='shipped'),
            ),
        )
        .filter(total_items__gt=0)
        .exclude(total_items=F('shipped_items'))
    )
    tasks.update(status='pending')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_scheduledtaskitem_notes'),
    ]

    operations = [
        migrations.RunPython(reopen_tasks_awaiting_shipment, noop),
    ]
