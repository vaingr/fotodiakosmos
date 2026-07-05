from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

class ProductCodeCounter(models.Model):
    """Model to track the last used product code counter"""
    last_code = models.IntegerField(default=-1, verbose_name="Τελευταίος Χρησιμοποιημένος Κωδικός")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")
    
    class Meta:
        verbose_name = "Μετρητής Κωδικών Υλικών"
        verbose_name_plural = "Μετρητής Κωδικών Υλικών"
    
    @classmethod
    def get_next_code(cls):
        """Get the next available code and increment the counter"""
        counter, created = cls.objects.get_or_create(pk=1, defaults={'last_code': -1})
        counter.last_code += 1
        # Ensure it doesn't exceed 99999
        if counter.last_code > 99999:
            counter.last_code = 0
        counter.save()
        return f"{counter.last_code:05d}"
    
    def __str__(self):
        return f"Last code: {self.last_code:05d}"


class MeasurementUnit(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Όνομα")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")

    class Meta:
        verbose_name = "Μονάδα Μέτρησης"
        verbose_name_plural = "Μονάδες Μέτρησης"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField(max_length=100, unique=True, verbose_name="Κωδικός")
    barcode = models.CharField(max_length=200, blank=True, null=True, verbose_name="QR/Bar Code")
    name = models.CharField(max_length=200, verbose_name="Όνομα")
    description = models.TextField(blank=True, null=True, verbose_name="Περιγραφή")
    quantity = models.IntegerField(validators=[MinValueValidator(0)], default=0, verbose_name="Ποσότητα")
    low_stock_threshold = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Όριο Χαμηλού Αποθέματος",
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="Μονάδα Μέτρησης",
    )
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")

    class Meta:
        verbose_name = "Υλικό"
        verbose_name_plural = "Υλικά"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def is_low_stock(self):
        """Returns True if quantity is at or below this material's threshold."""
        return self.quantity <= self.low_stock_threshold

    @property
    def quantity_display(self):
        unit = self.measurement_unit.name if self.measurement_unit_id else 'ΤΕΜΑΧΙΑ'
        return f"{self.quantity} {unit}"


class StockMovement(models.Model):
    ADD = 'add'
    REMOVE = 'remove'
    MOVEMENT_TYPES = [
        (ADD, 'Προσθήκη'),
        (REMOVE, 'Αφαίρεση'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name="Υλικό",
    )
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, verbose_name="Τύπος")
    amount = models.PositiveIntegerField(verbose_name="Ποσότητα")
    quantity_before = models.IntegerField(verbose_name="Ποσότητα Πριν")
    quantity_after = models.IntegerField(verbose_name="Ποσότητα Μετά")
    note = models.TextField(blank=True, verbose_name="Σημείωση")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name="Καταχωρήθηκε από",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία")

    class Meta:
        verbose_name = "Κίνηση Αποθέματος"
        verbose_name_plural = "Κινήσεις Αποθέματος"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.amount} - {self.product.name}"

    @property
    def movement_type_label(self):
        return self.get_movement_type_display()


class WarehouseUserProfile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Διαχειριστής Αποθήκης'),
        (ROLE_USER, 'Απλός Χρήστης'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='warehouse_profile',
        verbose_name='Χρήστης',
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        verbose_name='Ρόλος',
    )
    perm_dashboard = models.BooleanField(default=True, verbose_name='Αρχική Αποθήκη')
    perm_view_products = models.BooleanField(default=True, verbose_name='Προβολή Υλικών')
    perm_create_products = models.BooleanField(default=False, verbose_name='Δημιουργία Υλικών')
    perm_edit_products = models.BooleanField(default=False, verbose_name='Επεξεργασία Υλικών')
    perm_delete_products = models.BooleanField(default=False, verbose_name='Διαγραφή Υλικών')
    perm_add_quantity = models.BooleanField(default=False, verbose_name='Προσθήκη Ποσότητας')
    perm_remove_quantity = models.BooleanField(default=False, verbose_name='Αφαίρεση Ποσότητας')
    perm_measurement_units = models.BooleanField(default=False, verbose_name='Μονάδες Μέτρησης')
    perm_products = models.BooleanField(default=False, verbose_name='Προϊόντα')
    perm_finished_products_warehouse = models.BooleanField(
        default=False,
        verbose_name='Αποθήκη Έτοιμων Προϊόντων',
    )
    perm_offers = models.BooleanField(default=False, verbose_name='Προσφορές')
    perm_customers = models.BooleanField(default=False, verbose_name='Πελάτες')
    is_managed_user = models.BooleanField(
        default=False,
        verbose_name='Δημιουργήθηκε από Διαχείριση Αποθήκης',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Δημιουργίας')

    class Meta:
        verbose_name = 'Προφίλ Χρήστη Αποθήκης'
        verbose_name_plural = 'Προφίλ Χρηστών Αποθήκης'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.role == self.ROLE_ADMIN:
            self.perm_dashboard = True
            self.perm_view_products = True
            self.perm_create_products = True
            self.perm_edit_products = True
            self.perm_delete_products = True
            self.perm_add_quantity = True
            self.perm_remove_quantity = True
            self.perm_measurement_units = True
            self.perm_products = True
            self.perm_finished_products_warehouse = True
            self.perm_offers = True
            self.perm_customers = True
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
