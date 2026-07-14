import re

from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type',
            'first_name', 'last_name', 'company_name',
            'email',
            'contact_person', 'contact_person_gender',
            'contact_mobile', 'contact_landline', 'contact_email',
            'contact_person_2', 'contact_person_2_gender',
            'contact_person_2_mobile', 'contact_person_2_landline', 'contact_person_2_email',
            'vat_rate',
        ]
        widgets = {
            'customer_type': forms.RadioSelect(attrs={
                'class': 'customer-type-radio',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα',
                'autocomplete': 'off',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Επώνυμο',
                'autocomplete': 'off',
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα εταιρείας / Δήμου',
                'autocomplete': 'off',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email (προαιρετικό)',
                'autocomplete': 'off',
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα υπεύθυνου',
                'autocomplete': 'off',
            }),
            'contact_person_gender': forms.RadioSelect(attrs={
                'class': 'contact-person-gender-radio',
            }),
            'contact_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Κινητό',
                'autocomplete': 'off',
            }),
            'contact_landline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Σταθερό',
                'autocomplete': 'off',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'autocomplete': 'off',
            }),
            'contact_person_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα 2ου υπεύθυνου',
                'autocomplete': 'off',
            }),
            'contact_person_2_gender': forms.RadioSelect(attrs={
                'class': 'contact-person-gender-radio',
            }),
            'contact_person_2_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Κινητό',
                'autocomplete': 'off',
            }),
            'contact_person_2_landline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Σταθερό',
                'autocomplete': 'off',
            }),
            'contact_person_2_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'autocomplete': 'off',
            }),
            'vat_rate': forms.RadioSelect(attrs={
                'class': 'vat-rate-radio',
            }),
        }
        labels = {
            'customer_type': 'Τύπος πελάτη',
            'first_name': 'Όνομα',
            'last_name': 'Επώνυμο',
            'company_name': 'Όνομα εταιρείας / Δήμου',
            'email': 'Email',
            'contact_person': 'Όνομα',
            'contact_person_gender': 'Φύλο',
            'contact_mobile': 'Κινητό',
            'contact_landline': 'Σταθερό',
            'contact_email': 'Email',
            'contact_person_2': 'Όνομα',
            'contact_person_2_gender': 'Φύλο',
            'contact_person_2_mobile': 'Κινητό',
            'contact_person_2_landline': 'Σταθερό',
            'contact_person_2_email': 'Email',
            'vat_rate': 'ΦΠΑ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = [
            'email', 'first_name', 'last_name', 'company_name',
            'contact_person', 'contact_person_gender',
            'contact_mobile', 'contact_landline', 'contact_email',
            'contact_person_2', 'contact_person_2_gender',
            'contact_person_2_mobile', 'contact_person_2_landline', 'contact_person_2_email',
        ]
        for field_name in optional_fields:
            self.fields[field_name].required = False

        for gender_field_name in ('contact_person_gender', 'contact_person_2_gender'):
            gender_field = self.fields[gender_field_name]
            gender_field.choices = [
                choice for choice in gender_field.choices if choice[0]
            ]

        if self.instance.pk and self.instance.is_individual:
            if self.instance.phone and not self.instance.contact_mobile:
                self.initial.setdefault('contact_mobile', self.instance.phone)

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip().upper()
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = last_name.strip().upper()
        return last_name

    def clean_company_name(self):
        company_name = self.cleaned_data.get('company_name')
        if company_name:
            company_name = company_name.strip().upper()
        return company_name

    def clean_contact_mobile(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_mobile'))

    def clean_contact_landline(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_landline'))

    def clean_contact_person_2_mobile(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_person_2_mobile'))

    def clean_contact_person_2_landline(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_person_2_landline'))

    def _clean_phone_field(self, phone):
        if phone:
            phone = re.sub(r'[^\d]', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError('Το τηλέφωνο πρέπει να έχει τουλάχιστον 10 ψηφία.')
        return phone

    def clean_contact_person(self):
        contact_person = self.cleaned_data.get('contact_person')
        if contact_person:
            contact_person = contact_person.strip().upper()
        return contact_person

    def clean_contact_person_2(self):
        contact_person_2 = self.cleaned_data.get('contact_person_2')
        if contact_person_2:
            contact_person_2 = contact_person_2.strip().upper()
        return contact_person_2

    def clean_email(self):
        return self._clean_email_field('email', self.cleaned_data.get('email'))

    def clean_contact_email(self):
        return self._clean_email_field('contact_email', self.cleaned_data.get('contact_email'))

    def clean_contact_person_2_email(self):
        return self._clean_email_field('contact_person_2_email', self.cleaned_data.get('contact_person_2_email'))

    def _clean_email_field(self, field_name, email):
        if email:
            email = email.strip().lower()
            if field_name == 'email':
                existing_customer = Customer.objects.filter(email=email)
                if self.instance.pk:
                    existing_customer = existing_customer.exclude(pk=self.instance.pk)
                if existing_customer.exists():
                    raise forms.ValidationError('Υπάρχει ήδη πελάτης με αυτό το email.')
        return email

    def _validate_contact_person(self, prefix, label, cleaned_data, required=False):
        name = cleaned_data.get(f'contact_person{prefix}')
        gender = cleaned_data.get(f'contact_person{prefix}_gender')
        if prefix == '':
            mobile = cleaned_data.get('contact_mobile')
            landline = cleaned_data.get('contact_landline')
            email = cleaned_data.get('contact_email')
        else:
            mobile = cleaned_data.get('contact_person_2_mobile')
            landline = cleaned_data.get('contact_person_2_landline')
            email = cleaned_data.get('contact_person_2_email')
        has_any = any([name, gender, mobile, landline, email])

        if required or has_any:
            if not name:
                self.add_error(f'contact_person{prefix}', f'Το όνομα {label} είναι υποχρεωτικό.')
            if not gender:
                self.add_error(
                    f'contact_person{prefix}_gender',
                    f'Επιλέξτε το φύλο {label}.',
                )

    def clean(self):
        cleaned_data = super().clean()
        customer_type = cleaned_data.get('customer_type')

        if customer_type == Customer.TYPE_INDIVIDUAL:
            if not cleaned_data.get('last_name'):
                self.add_error('last_name', 'Το επώνυμο είναι υποχρεωτικό.')
            if not cleaned_data.get('first_name'):
                self.add_error('first_name', 'Το όνομα είναι υποχρεωτικό.')
        elif customer_type == Customer.TYPE_COMPANY:
            if not cleaned_data.get('company_name'):
                self.add_error('company_name', 'Το όνομα εταιρείας / Δήμου είναι υποχρεωτικό.')
            self._validate_contact_person('', 'του υπεύθυνου επικοινωνίας', cleaned_data, required=True)
            self._validate_contact_person('_2', 'του 2ου υπεύθυνου', cleaned_data, required=False)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.customer_type == Customer.TYPE_INDIVIDUAL:
            instance.company_name = ''
            instance.phone = ''
            instance.contact_person = ''
            instance.contact_person_gender = ''
            instance.contact_email = ''
            instance.contact_person_2 = ''
            instance.contact_person_2_gender = ''
            instance.contact_person_2_mobile = ''
            instance.contact_person_2_landline = ''
            instance.contact_person_2_email = ''
        else:
            instance.first_name = ''
            instance.last_name = ''
            instance.phone = ''
            instance.email = ''

        if commit:
            instance.save()
        return instance
