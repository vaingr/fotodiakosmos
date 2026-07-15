from django import forms
from django.forms import inlineformset_factory

from customers.models import Customer
from products.models import FinishedProduct
from .models import ScheduledTask, ScheduledTaskItem


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
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'task-product-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'task-quantity-input',
                'min': 1,
                'step': 1,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = FinishedProduct.objects.order_by('name')
        self.fields['product'].empty_label = 'Επιλέξτε προϊόν...'
        self.fields['product'].required = False
        self.fields['quantity'].required = False

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        if not product:
            if quantity:
                self.add_error('product', 'Επιλέξτε προϊόν.')
            return cleaned_data
        if not quantity or quantity < 1:
            self.add_error('quantity', 'Η ποσότητα πρέπει να είναι τουλάχιστον 1.')
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

    def save(self, commit=True):
        if not self.instance.pk:
            raise ValueError('Η εργασία πρέπει να αποθηκευτεί πριν τα προϊόντα.')

        saved_instances = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                if form.instance.pk and commit:
                    form.instance.delete()
                continue
            if not form.cleaned_data.get('product'):
                continue
            item = form.save(commit=False)
            item.task = self.instance
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
