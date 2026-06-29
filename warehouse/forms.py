from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

from .models import Product, MeasurementUnit, WarehouseUserProfile
from .permissions import WAREHOUSE_PERMISSION_FIELDS, WAREHOUSE_PERMISSION_KEYS

LOWERCASE_ENGLISH_RE = re.compile(r'^[a-z]+$')
LOWERCASE_ALNUM_RE = re.compile(r'^[a-z0-9]+$')
LOWERCASE_LATIN_INPUT_ATTRS = {
    'pattern': '[a-z]*',
    'autocapitalize': 'off',
    'autocorrect': 'off',
    'spellcheck': 'false',
    'autocomplete': 'off',
    'data-lowercase-latin': 'true',
    'data-lpignore': 'true',
    'data-1p-ignore': '',
}
LOWERCASE_ALNUM_INPUT_ATTRS = {
    'pattern': '[a-z0-9]*',
    'autocapitalize': 'off',
    'autocorrect': 'off',
    'spellcheck': 'false',
    'autocomplete': 'new-password',
    'data-lowercase-alnum': 'true',
    'data-lpignore': 'true',
    'data-1p-ignore': '',
}


def _validate_lowercase_english(value, field_label):
    if not value:
        return value
    if not LOWERCASE_ENGLISH_RE.match(value):
        raise forms.ValidationError(
            f'Το πεδίο «{field_label}» δέχεται μόνο αγγλικά πεζά γράμματα (a-z).'
        )
    return value


def _validate_lowercase_alnum(value, field_label):
    if not value:
        return value
    if not LOWERCASE_ALNUM_RE.match(value):
        raise forms.ValidationError(
            f'Το πεδίο «{field_label}» δέχεται μόνο αγγλικά πεζά γράμματα και αριθμούς (a-z, 0-9).'
        )
    return value


class MeasurementUnitForm(forms.ModelForm):
    class Meta:
        model = MeasurementUnit
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'style': 'text-transform: uppercase;',
            }),
        }
        labels = {
            'name': 'Όνομα Μονάδας',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not str(name).strip():
            raise forms.ValidationError('Το όνομα είναι υποχρεωτικό.')

        name = name.upper().strip()

        qs = MeasurementUnit.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"Η μονάδα '{name}' υπάρχει ήδη.")

        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code', 'barcode', 'name', 'description', 'measurement_unit', 'low_stock_threshold']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'autocomplete': 'off',
                'style': 'text-transform: uppercase;',
            }),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'measurement_unit': forms.RadioSelect(attrs={'class': 'unit-radio-input'}),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control threshold-input',
                'min': '0',
                'step': '1',
                'required': True,
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'placeholder': 'π.χ. 10',
            }),
        }
        labels = {
            'code': 'Κωδικός',
            'barcode': 'QR/Bar Code',
            'name': 'Όνομα Υλικού',
            'description': 'Περιγραφή',
            'measurement_unit': 'Μονάδα Μέτρησης',
            'low_stock_threshold': 'Όριο Χαμηλού Αποθέματος',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['measurement_unit'].queryset = MeasurementUnit.objects.all()
        self.fields['measurement_unit'].empty_label = None
        if not self.instance.pk:
            default_unit = MeasurementUnit.objects.filter(name='ΤΕΜΑΧΙΑ').first()
            if default_unit:
                self.fields['measurement_unit'].initial = default_unit.pk
            self.fields['low_stock_threshold'].initial = None

        self.fields['low_stock_threshold'].required = True

    def clean_low_stock_threshold(self):
        value = self.cleaned_data.get('low_stock_threshold')
        if value is None:
            raise forms.ValidationError('Το όριο χαμηλού αποθέματος είναι υποχρεωτικό.')
        return value

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code or not str(code).strip():
            raise forms.ValidationError('Ο κωδικός είναι υποχρεωτικός.')

        code = code.upper().strip()

        if self.instance and self.instance.pk:
            existing_product = Product.objects.filter(code=code).exclude(pk=self.instance.pk).first()
            if existing_product:
                raise forms.ValidationError(f"Ο κωδικός '{code}' υπάρχει ήδη. Χρησιμοποιείται από το υλικό: {existing_product.name}")
        else:
            existing_product = Product.objects.filter(code=code).first()
            if existing_product:
                raise forms.ValidationError(f"Ο κωδικός '{code}' υπάρχει ήδη. Χρησιμοποιείται από το υλικό: {existing_product.name}")

        return code


class QuantityAdjustmentForm(forms.Form):
    amount = forms.IntegerField(
        min_value=1,
        label='Ποσότητα',
        widget=forms.NumberInput(attrs={
            'class': 'form-control qty-input',
            'min': '1',
            'step': '1',
            'required': True,
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': 'π.χ. 5',
        }),
    )
    note = forms.CharField(
        required=False,
        label='Σημείωση',
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Προαιρετική σημείωση...',
        }),
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount < 1:
            raise forms.ValidationError('Η ποσότητα πρέπει να είναι τουλάχιστον 1.')
        return amount


class WarehouseUserCreateForm(forms.Form):
    username = forms.CharField(
        label='Όνομα Χρήστη',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            **LOWERCASE_LATIN_INPUT_ATTRS,
        }),
    )
    password1 = forms.CharField(
        label='Κωδικός',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            **LOWERCASE_ALNUM_INPUT_ATTRS,
        }),
    )
    password2 = forms.CharField(
        label='Επιβεβαίωση Κωδικού',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            **LOWERCASE_ALNUM_INPUT_ATTRS,
        }),
    )
    role = forms.ChoiceField(
        label='Ρόλος',
        choices=WarehouseUserProfile.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio-input'}),
        initial=WarehouseUserProfile.ROLE_USER,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for perm_key, label in WAREHOUSE_PERMISSION_FIELDS:
            self.fields[perm_key] = forms.BooleanField(
                label=label,
                required=False,
                initial=perm_key in ('perm_dashboard', 'perm_view_products'),
                widget=forms.CheckboxInput(),
            )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError('Το όνομα χρήστη είναι υποχρεωτικό.')
        username = _validate_lowercase_english(username, 'Όνομα Χρήστη')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Αυτό το όνομα χρήστη υπάρχει ήδη.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        return _validate_lowercase_alnum(password, 'Κωδικός')

    def clean_password2(self):
        password = self.cleaned_data.get('password2')
        return _validate_lowercase_alnum(password, 'Επιβεβαίωση Κωδικού')

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Οι κωδικοί δεν ταιριάζουν.')
        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                raise forms.ValidationError(list(exc.messages))
        return cleaned


class WarehouseUserEditForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label='Νέος Κωδικός',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            **LOWERCASE_ALNUM_INPUT_ATTRS,
        }),
    )
    new_password2 = forms.CharField(
        label='Επιβεβαίωση Νέου Κωδικού',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            **LOWERCASE_ALNUM_INPUT_ATTRS,
        }),
    )

    class Meta:
        model = WarehouseUserProfile
        fields = ['role'] + [key for key, _ in WAREHOUSE_PERMISSION_FIELDS]
        widgets = {
            'role': forms.RadioSelect(attrs={'class': 'role-radio-input'}),
            **{key: forms.CheckboxInput() for key, _ in WAREHOUSE_PERMISSION_FIELDS},
        }
        labels = {
            'role': 'Ρόλος',
            **{key: label for key, label in WAREHOUSE_PERMISSION_FIELDS},
        }

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            return _validate_lowercase_alnum(password, 'Νέος Κωδικός')
        return password

    def clean_new_password2(self):
        password = self.cleaned_data.get('new_password2')
        if password:
            return _validate_lowercase_alnum(password, 'Επιβεβαίωση Νέου Κωδικού')
        return password

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('new_password1')
        password2 = cleaned.get('new_password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Οι νέοι κωδικοί δεν ταιριάζουν.')
            try:
                validate_password(password1, self.instance.user)
            except ValidationError as exc:
                raise forms.ValidationError(list(exc.messages))
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.role == WarehouseUserProfile.ROLE_USER:
            for perm_key in WAREHOUSE_PERMISSION_KEYS:
                setattr(profile, perm_key, self.cleaned_data.get(perm_key, False))
        if commit:
            profile.save()
            password = self.cleaned_data.get('new_password1')
            if password:
                user = profile.user
                user.set_password(password)
                user.save()
        return profile
