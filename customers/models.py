from decimal import Decimal, ROUND_HALF_UP

from django.db import models

# Create your models here.

class Customer(models.Model):
    TYPE_INDIVIDUAL = 'individual'
    TYPE_COMPANY = 'company'
    TYPE_CHOICES = [
        (TYPE_COMPANY, 'Εταιρία / Δήμος'),
        (TYPE_INDIVIDUAL, 'Ιδιώτης'),
    ]

    customer_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_COMPANY,
        verbose_name='Τύπος πελάτη',
    )
    last_name = models.CharField(max_length=100, blank=True, default='', verbose_name="Επώνυμο")
    first_name = models.CharField(max_length=100, blank=True, default='', verbose_name="Όνομα")
    company_name = models.CharField(
        max_length=200, blank=True, default='', verbose_name="Όνομα εταιρείας / Δήμου"
    )
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name="Τηλέφωνο")
    email = models.EmailField(blank=True, default='', verbose_name="Email")
    contact_person = models.CharField(
        max_length=200, blank=True, default='', verbose_name="Υπεύθυνος επικοινωνίας"
    )
    CONTACT_GENDER_MALE = 'male'
    CONTACT_GENDER_FEMALE = 'female'
    CONTACT_GENDER_CHOICES = [
        (CONTACT_GENDER_MALE, 'Άνδρας'),
        (CONTACT_GENDER_FEMALE, 'Γυναίκα'),
    ]
    contact_person_gender = models.CharField(
        max_length=10,
        choices=CONTACT_GENDER_CHOICES,
        blank=True,
        default='',
        verbose_name='Φύλο υπεύθυνου επικοινωνίας',
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, default='', verbose_name="Τηλέφωνο υπεύθυνου"
    )
    contact_email = models.EmailField(
        blank=True, default='', verbose_name="Email υπεύθυνου"
    )
    contact_person_2 = models.CharField(
        max_length=200, blank=True, default='', verbose_name='2ος υπεύθυνος επικοινωνίας',
    )
    contact_person_2_gender = models.CharField(
        max_length=10,
        choices=CONTACT_GENDER_CHOICES,
        blank=True,
        default='',
        verbose_name='Φύλο 2ου υπεύθυνου',
    )
    contact_person_2_phone = models.CharField(
        max_length=20, blank=True, default='', verbose_name='Τηλέφωνο 2ου υπεύθυνου',
    )
    contact_person_2_email = models.EmailField(
        blank=True, default='', verbose_name='Email 2ου υπεύθυνου',
    )
    VAT_RATE_24 = '24'
    VAT_RATE_17 = '17'
    VAT_RATE_0 = '0'
    VAT_RATE_CHOICES = [
        (VAT_RATE_24, '24%'),
        (VAT_RATE_17, '17%'),
        (VAT_RATE_0, 'Μηδενικό'),
    ]
    vat_rate = models.CharField(
        max_length=5,
        choices=VAT_RATE_CHOICES,
        default=VAT_RATE_24,
        verbose_name='ΦΠΑ',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")

    class Meta:
        verbose_name = "Πελάτης"
        verbose_name_plural = "Πελάτες"
        ordering = ['last_name', 'first_name', 'company_name']

    def __str__(self):
        return self.display_name()

    @property
    def is_individual(self):
        return self.customer_type == self.TYPE_INDIVIDUAL

    @property
    def is_company(self):
        return self.customer_type == self.TYPE_COMPANY

    def display_name(self):
        if self.is_company:
            return self.company_name
        return f"{self.last_name} {self.first_name}".strip()

    def full_name(self):
        return self.display_name()

    def get_type_display_label(self):
        return dict(self.TYPE_CHOICES).get(self.customer_type, self.customer_type)

    def contact_person_display(self):
        return self._format_contact_person_display(self.contact_person, self.contact_person_gender)

    def contact_person_2_display(self):
        return self._format_contact_person_display(self.contact_person_2, self.contact_person_2_gender)

    def _format_contact_person_display(self, name, gender):
        if not name:
            return ''
        if gender == self.CONTACT_GENDER_MALE:
            return f'Κος {name}'
        if gender == self.CONTACT_GENDER_FEMALE:
            return f'Κα {name}'
        return name

    def get_primary_phone(self):
        if self.is_company:
            return self.contact_phone or ''
        return self.phone or ''

    def get_primary_email(self):
        if self.is_company:
            return self.contact_email or ''
        return self.email or ''

    def get_vat_rate_label(self):
        return dict(self.VAT_RATE_CHOICES).get(self.vat_rate, f'{self.vat_rate}%')

    def calculate_vat_amount(self, net_amount):
        rate = Decimal(self.vat_rate) / Decimal('100')
        return (Decimal(net_amount) * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_total_with_vat(self, net_amount):
        net = Decimal(net_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return net + self.calculate_vat_amount(net)
