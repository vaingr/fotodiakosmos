import re

from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type',
            'first_name', 'last_name', 'company_name',
            'phone', 'email',
            'contact_person', 'contact_person_gender', 'contact_phone', 'contact_email',
            'contact_person_2', 'contact_person_2_gender', 'contact_person_2_phone', 'contact_person_2_email',
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
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Τηλέφωνο (προαιρετικό)',
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
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Τηλέφωνο υπεύθυνου',
                'autocomplete': 'off',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email υπεύθυνου',
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
            'contact_person_2_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Τηλέφωνο 2ου υπεύθυνου',
                'autocomplete': 'off',
            }),
            'contact_person_2_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email 2ου υπεύθυνου',
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
            'phone': 'Τηλέφωνο',
            'email': 'Email',
            'contact_person': 'Όνομα',
            'contact_person_gender': 'Φύλο',
            'contact_phone': 'Τηλέφωνο',
            'contact_email': 'Email',
            'contact_person_2': 'Όνομα',
            'contact_person_2_gender': 'Φύλο',
            'contact_person_2_phone': 'Τηλέφωνο 2ου υπεύθυνου',
            'contact_person_2_email': 'Email 2ου υπεύθυνου',
            'vat_rate': 'ΦΠΑ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = [
            'phone', 'email', 'first_name', 'last_name', 'company_name',
            'contact_person', 'contact_person_gender', 'contact_phone', 'contact_email',
            'contact_person_2', 'contact_person_2_gender', 'contact_person_2_phone', 'contact_person_2_email',
        ]
        for field_name in optional_fields:
            self.fields[field_name].required = False

        for gender_field_name in ('contact_person_gender', 'contact_person_2_gender'):
            gender_field = self.fields[gender_field_name]
            gender_field.choices = [
                choice for choice in gender_field.choices if choice[0]
            ]

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

    def clean_phone(self):
        return self._clean_phone_field(self.cleaned_data.get('phone'))

    def clean_contact_phone(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_phone'))

    def clean_contact_person_2_phone(self):
        return self._clean_phone_field(self.cleaned_data.get('contact_person_2_phone'))

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
        phone = cleaned_data.get(f'contact_person{prefix}_phone')
        email = cleaned_data.get(f'contact_person{prefix}_email')
        has_any = any([name, gender, phone, email])

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
            instance.contact_person = ''
            instance.contact_person_gender = ''
            instance.contact_phone = ''
            instance.contact_email = ''
            instance.contact_person_2 = ''
            instance.contact_person_2_gender = ''
            instance.contact_person_2_phone = ''
            instance.contact_person_2_email = ''
        else:
            instance.first_name = ''
            instance.last_name = ''
            instance.phone = ''
            instance.email = ''

        if commit:
            instance.save()
        return instance
