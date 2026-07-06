import re

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from warehouse.models import Product as WarehouseProduct

from customers.models import Customer

from .models import FinishedProduct, Offer, OfferItem, OfferBankAccount, OfferSettings, ProductMaterial, ProductStock


class FinishedProductForm(forms.ModelForm):
    class Meta:
        model = FinishedProduct
        fields = ['code', 'name', 'description', 'photo']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Κωδικός',
                'autocomplete': 'off',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα προϊόντος',
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Περιγραφή (προαιρετικό)',
                'rows': 3,
                'autocomplete': 'off',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'photo-file-input',
                'accept': 'image/*',
                'id': 'id_photo',
            }),
        }
        labels = {
            'code': 'Κωδικός',
            'name': 'Όνομα',
            'description': 'Περιγραφή',
            'photo': 'Φωτογραφία',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise forms.ValidationError('Ο κωδικός είναι υποχρεωτικός.')
        return code

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip().upper()
        if not name:
            raise forms.ValidationError('Το όνομα είναι υποχρεωτικό.')
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        return description.strip()

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo or not hasattr(photo, 'content_type'):
            return photo

        if photo.size > 1 * 1024 * 1024:
            raise forms.ValidationError('Η εικόνα δεν μπορεί να υπερβαίνει το 1 MB.')

        content_type = getattr(photo, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('Επιτρέπονται μόνο αρχεία εικόνας.')

        return photo


class ProductMaterialForm(forms.ModelForm):
    class Meta:
        model = ProductMaterial
        fields = ['material', 'quantity']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control material-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': 1,
                'step': 1,
                'placeholder': 'Ποσότητα',
            }),
        }
        labels = {
            'material': 'Υλικό',
            'quantity': 'Ποσότητα',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = (
            WarehouseProduct.objects.select_related('measurement_unit').order_by('name')
        )
        self.fields['material'].empty_label = 'Επιλέξτε υλικό...'
        self.fields['material'].label_from_instance = self._material_label

    @staticmethod
    def _material_label(material):
        unit = material.measurement_unit.name if material.measurement_unit_id else ''
        return f'{material.code} - {material.name} ({unit})'.strip()

    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        quantity = cleaned_data.get('quantity')

        if cleaned_data.get('DELETE'):
            return cleaned_data

        if not material and not quantity:
            return cleaned_data

        if material and not quantity:
            self.add_error('quantity', 'Η ποσότητα είναι υποχρεωτική.')
        if quantity and not material:
            self.add_error('material', 'Επιλέξτε υλικό.')

        return cleaned_data


ProductMaterialFormSet = inlineformset_factory(
    FinishedProduct,
    ProductMaterial,
    form=ProductMaterialForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class ProductWarehouseAddForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=FinishedProduct.objects.none(),
        label='Προϊόν',
        empty_label='Επιλέξτε προϊόν...',
        widget=forms.Select(attrs={
            'class': 'warehouse-product-select',
            'id': 'id_warehouse_product',
        }),
    )
    quantity = forms.IntegerField(
        label='Ποσότητα',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'warehouse-quantity-input',
            'id': 'id_warehouse_quantity',
            'min': 1,
            'step': 1,
            'placeholder': 'Ποσότητα',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = FinishedProduct.objects.order_by('name')
        self.fields['product'].label_from_instance = lambda product: f'{product.code} - {product.name}'


class ProductWarehouseRemoveForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=FinishedProduct.objects.none(),
        label='Προϊόν',
        empty_label='Επιλέξτε προϊόν...',
        widget=forms.Select(attrs={
            'class': 'warehouse-product-select',
            'id': 'id_remove_warehouse_product',
        }),
    )
    quantity = forms.IntegerField(
        label='Ποσότητα',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'warehouse-quantity-input',
            'id': 'id_remove_warehouse_quantity',
            'min': 1,
            'step': 1,
            'placeholder': 'Ποσότητα',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = (
            FinishedProduct.objects.filter(stock__quantity__gt=0).order_by('name')
        )
        self.fields['product'].label_from_instance = lambda product: (
            f'{product.code} - {product.name} (απόθεμα: {product.stock.quantity})'
        )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity is not None:
            stock = ProductStock.objects.filter(product=product).first()
            if not stock:
                raise forms.ValidationError('Το προϊόν δεν βρίσκεται στην αποθήκη.')
            if quantity > stock.quantity:
                self.add_error(
                    'quantity',
                    f'Η ποσότητα δεν μπορεί να υπερβαίνει το διαθέσιμο απόθεμα ({stock.quantity}).',
                )

        return cleaned_data


def get_customer_delivery_email(customer):
    return customer.get_primary_email()


def get_offer_email_recipients(customer):
    """Λίστα παραληπτών email προσφοράς με το σωστό πεδίο Υπόψιν ανά παραλήπτη."""
    recipients = []

    if customer.is_company:
        primary_email = (customer.contact_email or '').strip()
        if primary_email:
            recipients.append({
                'email': primary_email,
                'contact_recipient': '1',
            })

        second_email = (customer.contact_person_2_email or '').strip()
        if second_email:
            if not any(entry['email'].lower() == second_email.lower() for entry in recipients):
                recipients.append({
                    'email': second_email,
                    'contact_recipient': '2',
                })
    else:
        email = (customer.get_primary_email() or '').strip()
        if email:
            recipients.append({
                'email': email,
                'contact_recipient': None,
            })

    return recipients


def get_offer_attention_display(customer, contact_recipient=None):
    if not customer.is_company:
        return ''
    if contact_recipient == '2':
        return customer.contact_person_2_display()
    return customer.contact_person_display()


class ProductWarehouseEmailForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        label='Παραλήπτης',
        empty_label='Επιλέξτε πελάτη...',
        widget=forms.Select(attrs={
            'class': 'warehouse-product-select',
            'id': 'id_email_customer',
        }),
    )
    message = forms.CharField(
        required=False,
        label='Μήνυμα',
        widget=forms.Textarea(attrs={
            'class': 'warehouse-email-message',
            'id': 'id_email_message',
            'rows': 3,
            'placeholder': 'Προαιρετικό μήνυμα στο email...',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by(
            'last_name', 'first_name', 'company_name',
        )
        self.fields['customer'].label_from_instance = lambda customer: (
            f'{customer.display_name()} ({get_customer_delivery_email(customer) or "χωρίς email"})'
        )

    def clean_customer(self):
        customer = self.cleaned_data['customer']
        if not get_customer_delivery_email(customer):
            raise forms.ValidationError('Ο πελάτης δεν έχει καταχωρημένο email.')
        return customer


class OfferForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        label='Πελάτης',
        empty_label='Επιλέξτε πελάτη...',
        widget=forms.Select(attrs={
            'class': 'offer-customer-select',
            'id': 'id_offer_customer',
        }),
    )

    class Meta:
        model = Offer
        fields = [
            'customer',
            'bank_account_group',
            'delivery_time',
            'delivery_place',
            'delivery_method',
            'packaging',
            'payment_method',
            'notes',
        ]
        labels = {
            'notes': 'Σημείωση',
            'bank_account_group': 'Τραπεζικοί λογαριασμοί',
        }
        widgets = {
            'bank_account_group': forms.RadioSelect(attrs={
                'class': 'offer-bank-group-options',
            }),
            'delivery_time': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'delivery_place': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'delivery_method': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'packaging': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Προαιρετική σημείωση στην προσφορά...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by(
            'last_name', 'first_name', 'company_name',
        )
        self.fields['customer'].label_from_instance = lambda customer: customer.display_name()
        self.fields['notes'].required = False

        if not self.instance.pk:
            settings = OfferSettings.get_solo()
            self.fields['delivery_time'].initial = settings.delivery_time
            self.fields['delivery_place'].initial = settings.delivery_place
            self.fields['delivery_method'].initial = settings.delivery_method
            self.fields['packaging'].initial = settings.packaging
            self.fields['payment_method'].initial = settings.payment_method


class OfferItemForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ['product', 'quantity', 'unit_price']
        labels = {
            'product': 'Προϊόν',
            'quantity': 'Ποσότητα',
            'unit_price': 'Τιμή μονάδας (€)',
        }
        widgets = {
            'product': forms.Select(attrs={'class': 'offer-product-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control offer-quantity-input',
                'min': 1,
                'step': 1,
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control offer-price-input',
                'min': 0,
                'step': '0.01',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = FinishedProduct.objects.order_by('name')
        self.fields['product'].label_from_instance = lambda product: f'{product.code} - {product.name}'


OfferItemFormSet = inlineformset_factory(
    Offer,
    OfferItem,
    form=OfferItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class OfferSettingsForm(forms.ModelForm):
    class Meta:
        model = OfferSettings
        fields = [
            'logo',
            'delivery_time',
            'delivery_place',
            'delivery_method',
            'packaging',
            'payment_method',
        ]
        labels = {
            'logo': 'Λογότυπο',
        }
        widgets = {
            'logo': forms.ClearableFileInput(attrs={
                'class': 'offer-logo-input',
                'accept': 'image/*',
            }),
            'delivery_time': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'delivery_place': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'delivery_method': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'packaging': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if not logo or not hasattr(logo, 'content_type'):
            return logo

        if logo.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Το λογότυπο δεν μπορεί να υπερβαίνει το 2 MB.')

        content_type = getattr(logo, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('Επιτρέπονται μόνο αρχεία εικόνας.')

        return logo


class OfferBankAccountForm(forms.ModelForm):
    class Meta:
        model = OfferBankAccount
        fields = ['bank_name', 'iban']
        labels = {
            'bank_name': 'Τράπεζα',
            'iban': 'IBAN',
        }
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control bank-name-input',
                'placeholder': 'π.χ. ΕΘΝΙΚΗ',
                'autocomplete': 'off',
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control bank-iban-input',
                'placeholder': 'GR...',
                'autocomplete': 'off',
            }),
        }

    def clean_bank_name(self):
        bank_name = self.cleaned_data.get('bank_name', '')
        return bank_name.strip().upper()

    def clean_iban(self):
        iban = self.cleaned_data.get('iban', '')
        return iban.strip().upper()


def _build_bank_account_formset(account_group):
    class BaseOfferBankAccountFormSet(BaseInlineFormSet):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance.pk:
                self.queryset = self.instance.bank_accounts.filter(account_group=account_group)

        def save_new(self, form, commit=True):
            instance = form.save(commit=False)
            instance.account_group = account_group
            if commit:
                instance.save()
            return instance

    return inlineformset_factory(
        OfferSettings,
        OfferBankAccount,
        form=OfferBankAccountForm,
        formset=BaseOfferBankAccountFormSet,
        extra=0,
        can_delete=True,
    )


CompanyBankAccountFormSet = _build_bank_account_formset(OfferBankAccount.GROUP_COMPANY)
IndividualBankAccountFormSet = _build_bank_account_formset(OfferBankAccount.GROUP_INDIVIDUAL)
