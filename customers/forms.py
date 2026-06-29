from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Όνομα',
                'autocomplete': 'off'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Επώνυμο',
                'autocomplete': 'off'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Τηλέφωνο (προαιρετικό)',
                'autocomplete': 'off'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email (προαιρετικό)',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'first_name': 'Όνομα',
            'last_name': 'Επώνυμο',
            'phone': 'Τηλέφωνο',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make phone field optional
        self.fields['phone'].required = False

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Convert to uppercase and remove extra spaces
            first_name = first_name.strip().upper()
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Convert to uppercase and remove extra spaces
            last_name = last_name.strip().upper()
        return last_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters and format
            import re
            phone = re.sub(r'[^\d]', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError('Το τηλέφωνο πρέπει να έχει τουλάχιστον 10 ψηφία.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Convert to lowercase and remove extra spaces
            email = email.strip().lower()
            # Check if email already exists (excluding current instance if editing)
            existing_customer = Customer.objects.filter(email=email)
            if self.instance.pk:
                existing_customer = existing_customer.exclude(pk=self.instance.pk)
            
            if existing_customer.exists():
                raise forms.ValidationError('Υπάρχει ήδη πελάτης με αυτό το email.')
        return email 