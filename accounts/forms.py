from django import forms
from django.db import transaction
from django.forms import inlineformset_factory

from customers.models import Customer
from products.models import FinishedProduct, ProductStock
from .models import ScheduledTask, ScheduledTaskItem
from .task_stock import release_reservation_counters, reserve_stock


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = ScheduledTask
        fields = [
            'task_type',
            'customer',
            'description',
            'scheduled_date',
            'priority',
        ]
        widgets = {
            'task_type': forms.RadioSelect(),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Προαιρετικές λεπτομέρειες εργασίας...',
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'task-date-native',
            }),
            'priority': forms.Select(),
            'customer': forms.Select(attrs={
                'class': 'task-customer-select',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by(
            'last_name',
            'first_name',
            'company_name',
        )
        self.fields['customer'].empty_label = '— Επιλέξτε πελάτη —'
        self.fields['customer'].required = True
        self.fields['task_type'].required = True
        self.fields['task_type'].choices = ScheduledTask.TYPE_CHOICES
        if not self.is_bound:
            self.fields['task_type'].initial = ScheduledTask.TYPE_CONSTRUCTION
            self.fields['customer'].initial = None


class TaskItemForm(forms.ModelForm):
    class Meta:
        model = ScheduledTaskItem
        fields = ['product', 'quantity', 'notes', 'reserved_stock']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'task-product-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'task-quantity-input',
                'min': 1,
                'step': 1,
            }),
            'notes': forms.TextInput(attrs={
                'class': 'task-item-notes-input',
                'maxlength': 500,
                'placeholder': 'Προαιρετικές σημειώσεις...',
            }),
            'reserved_stock': forms.HiddenInput(attrs={
                'class': 'task-reserved-stock-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = FinishedProduct.objects.order_by('name')
        self.fields['product'].empty_label = 'Επιλέξτε προϊόν...'
        self.fields['product'].required = False
        self.fields['quantity'].required = False
        self.fields['notes'].required = False
        self.fields['reserved_stock'].queryset = ProductStock.objects.filter(
            construction_stage__in=[
                ProductStock.STAGE_COMPLETE,
                ProductStock.STAGE_SKELETON,
            ],
        )
        self.fields['reserved_stock'].required = False

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        reserved_stock = cleaned_data.get('reserved_stock')

        if not product:
            if quantity:
                self.add_error('product', 'Επιλέξτε προϊόν.')
            cleaned_data['reserved_stock'] = None
            return cleaned_data

        if not quantity or quantity < 1:
            self.add_error('quantity', 'Η ποσότητα πρέπει να είναι τουλάχιστον 1.')
            return cleaned_data

        if reserved_stock:
            if reserved_stock.product_id != product.pk:
                self.add_error('reserved_stock', 'Το απόθεμα δεν ανήκει στο επιλεγμένο προϊόν.')
            elif reserved_stock.construction_stage not in (
                ProductStock.STAGE_COMPLETE,
                ProductStock.STAGE_SKELETON,
            ):
                self.add_error('reserved_stock', 'Μόνο ολοκληρωμένα ή σκελετοί μπορούν να δεσμευτούν.')
            else:
                available = reserved_stock.available_quantity
                if (
                    self.instance.pk
                    and self.instance.reserved_stock_id == reserved_stock.pk
                    and self.instance.has_active_reservation()
                ):
                    available += self.instance.quantity
                if quantity > available:
                    self.add_error(
                        'quantity',
                        f'Διαθέσιμα μόνο {available} τεμάχια για δέσμευση.',
                    )
        return cleaned_data


class BaseTaskItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        active_items = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('product'):
                active_items += 1

        if active_items == 0:
            raise forms.ValidationError('Προσθέστε τουλάχιστον ένα προϊόν.')

    @transaction.atomic
    def save(self, commit=True):
        if not self.instance.pk:
            raise ValueError('Η εργασία πρέπει να αποθηκευτεί πριν τα προϊόντα.')

        saved_instances = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue

            # Το ModelForm έχει ήδη εφαρμόσει τα POST values στο instance·
            # η πραγματική προηγούμενη κατάσταση πρέπει να διαβαστεί από τη ΒΔ.
            previous_stock_id = None
            previous_quantity = 0
            previous_was_reserved = False
            if form.instance.pk:
                original = (
                    ScheduledTaskItem.objects
                    .filter(pk=form.instance.pk)
                    .only('reserved_stock_id', 'quantity', 'item_status')
                    .first()
                )
                if original:
                    previous_stock_id = original.reserved_stock_id
                    previous_quantity = original.quantity
                    previous_was_reserved = original.has_active_reservation()

            if form.cleaned_data.get('DELETE'):
                if form.instance.pk and commit:
                    if previous_was_reserved:
                        release_reservation_counters(
                            previous_stock_id,
                            previous_quantity,
                        )
                        # Αποφυγή διπλής αποδέσμευσης από το pre_delete signal
                        form.instance.reserved_stock_id = None
                        form.instance.item_status = ScheduledTaskItem.STATUS_UNDER_WORK
                    form.instance.delete()
                continue

            if not form.cleaned_data.get('product'):
                continue

            item = form.save(commit=False)
            item.task = self.instance
            reserved_stock = form.cleaned_data.get('reserved_stock')

            if reserved_stock:
                reserve_stock(
                    reserved_stock,
                    item.quantity,
                    previous_stock_id=previous_stock_id if previous_was_reserved else None,
                    previous_quantity=previous_quantity if previous_was_reserved else 0,
                )
                item.reserved_stock = reserved_stock
                item.item_status = ScheduledTaskItem.STATUS_RESERVED
            else:
                if previous_was_reserved:
                    release_reservation_counters(previous_stock_id, previous_quantity)
                item.reserved_stock = None
                if item.item_status == ScheduledTaskItem.STATUS_RESERVED:
                    item.item_status = ScheduledTaskItem.STATUS_UNDER_WORK
                elif not item.pk:
                    item.item_status = ScheduledTaskItem.STATUS_UNDER_WORK

            if commit:
                item.save()
            saved_instances.append(item)
        return saved_instances


TaskItemFormSet = inlineformset_factory(
    ScheduledTask,
    ScheduledTaskItem,
    form=TaskItemForm,
    formset=BaseTaskItemFormSet,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
