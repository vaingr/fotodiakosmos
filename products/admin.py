from django.contrib import admin

from .models import FinishedProduct, Offer, OfferItem, OfferBankAccount, OfferSettings, ProductMaterial, ProductStock


class OfferItemInline(admin.TabularInline):
    model = OfferItem
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('offer_number', 'customer', 'total_amount', 'created_at', 'created_by')
    search_fields = ('offer_number', 'customer__company_name', 'customer__last_name', 'customer__first_name')
    ordering = ('-created_at',)
    inlines = [OfferItemInline]


class OfferBankAccountInline(admin.TabularInline):
    model = OfferBankAccount
    extra = 0


@admin.register(OfferSettings)
class OfferSettingsAdmin(admin.ModelAdmin):
    list_display = ('updated_at',)
    readonly_fields = ('updated_at',)
    inlines = [OfferBankAccountInline]

    def has_add_permission(self, request):
        return not OfferSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class ProductMaterialInline(admin.TabularInline):
    model = ProductMaterial
    extra = 1


@admin.register(FinishedProduct)
class FinishedProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at', 'updated_at')
    search_fields = ('code', 'name', 'description')
    ordering = ('name',)
    inlines = [ProductMaterialInline]


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ('product', 'material', 'quantity')
    list_filter = ('product',)
    search_fields = ('product__name', 'product__code', 'material__name', 'material__code')


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'construction_stage', 'quantity', 'carpet', 'bulb',
        'photocell', 'dimensions', 'low_stock_threshold', 'created_at', 'updated_at',
    )
    list_filter = ('construction_stage',)
    search_fields = ('product__name', 'product__code')
    ordering = ('product__name', 'construction_stage')
