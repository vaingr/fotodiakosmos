from django.db import models

# Create your models here.

class Customer(models.Model):
    last_name = models.CharField(max_length=100, verbose_name="Επώνυμο")
    first_name = models.CharField(max_length=100, verbose_name="Όνομα")
    phone = models.CharField(max_length=20, verbose_name="Τηλέφωνο")
    email = models.EmailField(verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")

    class Meta:
        verbose_name = "Πελάτης"
        verbose_name_plural = "Πελάτες"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def full_name(self):
        return f"{self.last_name} {self.first_name}"
