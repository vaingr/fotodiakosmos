from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from customers.models import Customer
from products.models import FinishedProduct, ProductStock

from .forms import TaskItemFormSet
from .models import ScheduledTask, ScheduledTaskItem
from .task_stock import get_complete_stocks_for_product


class TaskReservationEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tasks', password='x')
        self.customer = Customer.objects.create(company_name='CAN SUPPLIES')
        self.product = FinishedProduct.objects.create(code='ET460', name='ΦΙΟΓΚΟΣ')
        self.stock = ProductStock.objects.create(
            product=self.product,
            construction_stage=ProductStock.STAGE_COMPLETE,
            quantity=Decimal('55'),
            reserved_quantity=Decimal('50'),
        )
        self.task = ScheduledTask.objects.create(
            task_type=ScheduledTask.TYPE_CONSTRUCTION,
            customer=self.customer,
            scheduled_date=date(2026, 11, 21),
            created_by=self.user,
        )
        self.item = ScheduledTaskItem.objects.create(
            task=self.task,
            product=self.product,
            quantity=50,
            item_status=ScheduledTaskItem.STATUS_RESERVED,
            reserved_stock=self.stock,
        )

    def _formset_data(self, **overrides):
        data = {
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '1',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-id': str(self.item.pk),
            'items-0-product': str(self.product.pk),
            'items-0-quantity': '50',
            'items-0-notes': 'ΤΕΣΤ',
            'items-0-reserved_stock': str(self.stock.pk),
        }
        data.update(overrides)
        return data

    def test_fully_reserved_stock_stays_visible_as_number(self):
        full = ProductStock.objects.create(
            product=self.product,
            construction_stage=ProductStock.STAGE_SKELETON,
            quantity=Decimal('1.00'),
            reserved_quantity=Decimal('1.00'),
            carpet='Α',
        )
        rows = get_complete_stocks_for_product(self.product.pk)
        by_id = {row['id']: row for row in rows}
        self.assertIn(full.pk, by_id)
        self.assertEqual(by_id[full.pk]['available'], 0)
        self.assertIsInstance(by_id[full.pk]['available'], int)
        self.assertEqual(by_id[self.stock.pk]['available'], 5)
        self.assertIsInstance(by_id[self.stock.pk]['available'], int)

    def test_saving_note_keeps_reservation_and_completed_status(self):
        self.item.item_status = ScheduledTaskItem.STATUS_COMPLETED
        self.item.save(update_fields=['item_status'])
        formset = TaskItemFormSet(self._formset_data(), instance=self.task)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()

        self.item.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(self.item.notes, 'ΤΕΣΤ')
        self.assertEqual(self.item.quantity, 50)
        self.assertEqual(self.item.reserved_stock_id, self.stock.pk)
        self.assertEqual(self.item.item_status, ScheduledTaskItem.STATUS_COMPLETED)
        self.assertEqual(self.stock.reserved_quantity, Decimal('50'))
        self.assertEqual(self.task.items.count(), 1)

    def test_shipped_line_keeps_stock_link_when_form_omits_it(self):
        self.item.item_status = ScheduledTaskItem.STATUS_SHIPPED
        self.item.save(update_fields=['item_status'])
        formset = TaskItemFormSet(
            self._formset_data(**{'items-0-reserved_stock': ''}),
            instance=self.task,
        )
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()

        self.item.refresh_from_db()
        self.assertEqual(self.item.item_status, ScheduledTaskItem.STATUS_SHIPPED)
        self.assertEqual(self.item.reserved_stock_id, self.stock.pk)
        self.assertEqual(self.item.notes, 'ΤΕΣΤ')
