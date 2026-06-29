from django.contrib import admin
from .models import Product, MeasurementUnit, StockMovement, WarehouseUserProfile

admin.site.register(Product)
admin.site.register(MeasurementUnit)
admin.site.register(StockMovement)
admin.site.register(WarehouseUserProfile)
