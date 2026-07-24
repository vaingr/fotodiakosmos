from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import ScheduledTaskItem
from .task_stock import release_reservation_counters


@receiver(pre_delete, sender=ScheduledTaskItem)
def release_stock_on_task_item_delete(sender, instance, **kwargs):
    """Αποδέσμευση αποθέματος όταν διαγράφεται γραμμή με ενεργή δέσμευση."""
    if instance.has_active_reservation():
        release_reservation_counters(instance.reserved_stock_id, instance.quantity)
