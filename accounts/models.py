from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    expiry_date = models.DateField()

    def is_active(self):
        return self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"Συνδρομή για {self.user.username} έως {self.expiry_date}"


class ScheduledTask(models.Model):
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Χαμηλή'),
        (PRIORITY_MEDIUM, 'Μεσαία'),
        (PRIORITY_HIGH, 'Υψηλή'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Σε εκκρεμότητα'),
        (STATUS_COMPLETED, 'Ολοκληρωμένη'),
        (STATUS_CANCELLED, 'Ακυρωμένη'),
    ]

    TYPE_CONSTRUCTION = 'construction'
    TYPE_REPAIR = 'repair'
    TYPE_CHOICES = [
        (TYPE_CONSTRUCTION, 'Κατασκευή'),
        (TYPE_REPAIR, 'Επισκευή'),
    ]

    task_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Είδος εργασίας',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='scheduled_tasks',
        verbose_name='Πελάτης',
    )
    description = models.TextField(blank=True, verbose_name='Περιγραφή')
    scheduled_date = models.DateField(verbose_name='Επιθυμητή Ημερομηνία Ολοκλήρωσης')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Προτεραιότητα',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Κατάσταση',
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Ανάθεση σε',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks',
        verbose_name='Δημιουργήθηκε από',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία δημιουργίας')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ημερομηνία ενημέρωσης')

    class Meta:
        verbose_name = 'Προγραμματισμένη εργασία'
        verbose_name_plural = 'Προγραμματισμένες εργασίες'
        ordering = ['scheduled_date', '-priority', 'task_type']

    def __str__(self):
        return f'{self.get_task_type_display()} - {self.customer.display_name()}'

    def display_label(self):
        return f'{self.get_task_type_display()} ({self.customer.display_name()})'

    @property
    def is_active(self):
        return self.status == self.STATUS_PENDING

    def is_overdue(self):
        return (
            self.scheduled_date < timezone.localdate()
            and self.is_active
        )

    def assigned_to_display(self):
        if not self.assigned_to:
            return '—'
        full_name = self.assigned_to.get_full_name().strip()
        return full_name or self.assigned_to.username

    def products_summary(self):
        items = list(self.items.select_related('product'))
        if not items:
            return ''
        return ', '.join(
            f'{item.product.code} x{item.quantity}'
            for item in items
        )

    def get_under_work_label(self):
        if self.task_type == self.TYPE_REPAIR:
            return 'Υπό Επισκευή'
        return 'Υπό Κατασκευή'

    def refresh_status_from_items(self):
        items = list(self.items.all())
        if not items:
            return

        all_completed = all(
            item.item_status == ScheduledTaskItem.STATUS_COMPLETED
            for item in items
        )
        new_status = (
            self.STATUS_COMPLETED if all_completed else self.STATUS_PENDING
        )

        if self.status == self.STATUS_CANCELLED:
            return

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])


class ScheduledTaskItem(models.Model):
    STATUS_UNDER_WORK = 'under_work'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_UNDER_WORK, 'Υπό κατασκευή'),
        (STATUS_COMPLETED, 'Ολοκληρώθηκε'),
    ]

    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Εργασία',
    )
    product = models.ForeignKey(
        'products.FinishedProduct',
        on_delete=models.PROTECT,
        related_name='task_items',
        verbose_name='Προϊόν',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Ποσότητα',
    )
    item_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_UNDER_WORK,
        verbose_name='Κατάσταση προϊόντος',
    )

    class Meta:
        verbose_name = 'Προϊόν εργασίας'
        verbose_name_plural = 'Προϊόντα εργασίας'
        ordering = ['id']

    def __str__(self):
        return f'{self.product.code} x {self.quantity}'

    def get_status_label(self):
        if self.item_status == self.STATUS_COMPLETED:
            return 'Ολοκληρώθηκε'
        if self.task.task_type == ScheduledTask.TYPE_REPAIR:
            return 'Υπό Επισκευή'
        return 'Υπό Κατασκευή'
