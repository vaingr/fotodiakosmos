from django.core.validators import MinValueValidator
from django.db import models


class FinishedProduct(models.Model):
    code = models.CharField(max_length=100, unique=True, verbose_name='Κωδικός')
    name = models.CharField(max_length=200, verbose_name='Όνομα')
    description = models.TextField(blank=True, default='', verbose_name='Περιγραφή')
    photo = models.ImageField(
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Φωτογραφία',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Δημιουργίας')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ημερομηνία Ενημέρωσης')

    class Meta:
        verbose_name = 'Προϊόν'
        verbose_name_plural = 'Προϊόντα'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class ProductStock(models.Model):
    product = models.OneToOneField(
        FinishedProduct,
        on_delete=models.CASCADE,
        related_name='stock',
        verbose_name='Προϊόν',
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Ποσότητα',
    )
    low_stock_threshold = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='Όριο Χαμηλού Αποθέματος',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Προσθήκης')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ημερομηνία Ενημέρωσης')

    class Meta:
        verbose_name = 'Απόθεμα Προϊόντος'
        verbose_name_plural = 'Αποθέματα Προϊόντων'
        ordering = ['product__name']

    def __str__(self):
        return f'{self.product.name} ({self.quantity})'

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class ProductStockMovement(models.Model):
    ADD = 'add'
    REMOVE = 'remove'
    MOVEMENT_CHOICES = [
        (ADD, 'Προσθήκη'),
        (REMOVE, 'Αφαίρεση'),
    ]

    stock = models.ForeignKey(
        ProductStock,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='Απόθεμα προϊόντος',
    )
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES, verbose_name='Τύπος')
    amount = models.PositiveIntegerField(verbose_name='Ποσότητα')
    quantity_before = models.IntegerField(verbose_name='Ποσότητα Πριν')
    quantity_after = models.IntegerField(verbose_name='Ποσότητα Μετά')
    note = models.TextField(blank=True, default='', verbose_name='Σημείωση')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία')
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_stock_movements',
        verbose_name='Καταχωρήθηκε από',
    )

    class Meta:
        verbose_name = 'Κίνηση Αποθέματος Προϊόντος'
        verbose_name_plural = 'Κινήσεις Αποθέματος Προϊόντων'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.stock.product.name} - {self.get_movement_type_display()} {self.amount}'


class ProductMaterial(models.Model):
    product = models.ForeignKey(
        FinishedProduct,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Προϊόν',
    )
    material = models.ForeignKey(
        'warehouse.Product',
        on_delete=models.PROTECT,
        related_name='product_usages',
        verbose_name='Υλικό',
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Ποσότητα',
    )

    class Meta:
        verbose_name = 'Υλικό προϊόντος'
        verbose_name_plural = 'Υλικά προϊόντος'
        ordering = ['material__name']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'material'],
                name='unique_product_material',
            ),
        ]

    def __str__(self):
        unit = self.material.measurement_unit.name if self.material.measurement_unit_id else ''
        return f'{self.material.name} x {self.quantity} {unit}'.strip()

    @property
    def quantity_display(self):
        unit = self.material.measurement_unit.name if self.material.measurement_unit_id else 'ΤΕΜΑΧΙΑ'
        return f'{self.quantity} {unit}'


class Offer(models.Model):
    offer_number = models.CharField(max_length=30, unique=True, verbose_name='Αριθμός Προσφοράς')
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='offers',
        verbose_name='Πελάτης',
    )
    notes = models.TextField(blank=True, default='', verbose_name='Σημείωση')
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Σύνολο',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ημερομηνία Δημιουργίας')
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_created',
        verbose_name='Δημιουργήθηκε από',
    )

    class Meta:
        verbose_name = 'Προσφορά'
        verbose_name_plural = 'Προσφορές'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.offer_number} - {self.customer.display_name()}'

    def save(self, *args, **kwargs):
        if not self.offer_number:
            from django.utils import timezone

            today = timezone.localdate()
            year_suffix = today.strftime('%y')
            suffix = f'-{year_suffix}'

            max_number = 0
            for offer_number in Offer.objects.filter(
                offer_number__endswith=suffix,
            ).values_list('offer_number', flat=True):
                try:
                    sequence = int(offer_number.split('-', 1)[0])
                except (ValueError, IndexError):
                    continue
                max_number = max(max_number, sequence)

            self.offer_number = f'{max_number + 1:04d}{suffix}'
        super().save(*args, **kwargs)

    def recalculate_total(self):
        total = sum((item.quantity * item.unit_price) for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OfferItem(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Προσφορά',
    )
    product = models.ForeignKey(
        FinishedProduct,
        on_delete=models.PROTECT,
        related_name='offer_items',
        verbose_name='Προϊόν',
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Ποσότητα',
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Τιμή μονάδας',
    )

    class Meta:
        verbose_name = 'Γραμμή προσφοράς'
        verbose_name_plural = 'Γραμμές προσφοράς'
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class OfferSettings(models.Model):
    logo = models.ImageField(
        upload_to='offers/logo/',
        blank=True,
        null=True,
        verbose_name='Λογότυπο προσφοράς',
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Τελευταία ενημέρωση')

    class Meta:
        verbose_name = 'Ρυθμίσεις Προσφορών'
        verbose_name_plural = 'Ρυθμίσεις Προσφορών'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Ρυθμίσεις Προσφορών'
