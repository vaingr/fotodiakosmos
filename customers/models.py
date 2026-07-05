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
        if not self.contact_person:
            return ''
        if self.contact_person_gender == self.CONTACT_GENDER_MALE:
            return f'Κος {self.contact_person}'
        if self.contact_person_gender == self.CONTACT_GENDER_FEMALE:
            return f'Κα {self.contact_person}'
        return self.contact_person
