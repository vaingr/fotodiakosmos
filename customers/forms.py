import re

from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type',
            'first_name', 'last_name', 'company_name',
            'phone', 'email', 'contact_person', 'contact_person_gender',
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
                'placeholder': 'Υπεύθυνος επικοινωνίας',
                'autocomplete': 'off',
            }),
            'contact_person_gender': forms.RadioSelect(attrs={
                'class': 'contact-person-gender-radio',
            }),
        }
        labels = {
            'customer_type': 'Τύπος πελάτη',
            'first_name': 'Όνομα',
            'last_name': 'Επώνυμο',
            'company_name': 'Όνομα εταιρείας / Δήμου',
            'phone': 'Τηλέφωνο',
            'email': 'Email',
            'contact_person': 'Υπεύθυνος επικοινωνίας',
            'contact_person_gender': 'Φύλο',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['company_name'].required = False
        self.fields['contact_person'].required = False
        self.fields['contact_person_gender'].required = False

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
        phone = self.cleaned_data.get('phone')
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            existing_customer = Customer.objects.filter(email=email)
            if self.instance.pk:
                existing_customer = existing_customer.exclude(pk=self.instance.pk)

            if existing_customer.exists():
                raise forms.ValidationError('Υπάρχει ήδη πελάτης με αυτό το email.')
        return email

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
            if not cleaned_data.get('contact_person'):
                self.add_error('contact_person', 'Ο υπεύθυνος επικοινωνίας είναι υποχρεωτικός.')
            if not cleaned_data.get('contact_person_gender'):
                self.add_error('contact_person_gender', 'Επιλέξτε αν ο υπεύθυνος είναι άνδρας ή γυναίκα.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.customer_type == Customer.TYPE_INDIVIDUAL:
            instance.company_name = ''
            instance.contact_person = ''
            instance.contact_person_gender = ''
            instance.contact_phone = ''
            instance.contact_email = ''
        else:
            instance.first_name = ''
            instance.last_name = ''
            instance.contact_phone = ''
            instance.contact_email = ''

        if commit:
            instance.save()
        return instance
