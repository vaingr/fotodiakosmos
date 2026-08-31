from django.db import transaction
from django.db.models import F

from products.models import ProductStock, ProductStockMovement
from .models import ScheduledTaskItem


def get_complete_stocks_for_product(product_id, exclude_item=None):
    stocks = (
        ProductStock.objects
        .filter(
            product_id=product_id,
            construction_stage__in=[
                ProductStock.STAGE_COMPLETE,
                ProductStock.STAGE_SKELETON,
            ],
            quantity__gt=0,
        )
        .select_related('product')
        .order_by('construction_stage', 'carpet', 'bulb', 'dimensions')
    )
    result = []
    for stock in stocks:
        available = stock.available_quantity
        if (
            exclude_item
            and exclude_item.pk
            and exclude_item.reserved_stock_id == stock.pk
            and exclude_item.has_active_reservation()
        ):
            available += exclude_item.quantity
        if available <= 0:
            continue
        result.append({
            'id': stock.pk,
            'carpet': stock.carpet,
            'bulb': stock.bulb,
            'photocell': stock.photocell,
            'dimensions': stock.dimensions,
            'stage': stock.construction_stage,
            'stage_label': stock.get_construction_stage_display(),
            'label': stock.variant_label(),
            'product_code': stock.product.code,
            'product_name': stock.product.name,
            'product_label': f'{stock.product.code} - {stock.product.name}',
            'quantity': stock.quantity,
            'reserved_quantity': stock.reserved_quantity,
            'available': available,
        })
    return result


def _adjust_reserved_quantity(stock_or_id, delta):
    if not stock_or_id or delta == 0:
        return
    stock_id = stock_or_id.pk if hasattr(stock_or_id, 'pk') else stock_or_id
    ProductStock.objects.filter(pk=stock_id).update(
        reserved_quantity=F('reserved_quantity') + delta,
    )
    ProductStock.objects.filter(pk=stock_id, reserved_quantity__lt=0).update(
        reserved_quantity=0,
    )


def release_reservation_counters(stock_id, quantity):
    if stock_id and quantity:
        _adjust_reserved_quantity(stock_id, -quantity)


def reserve_stock(stock, quantity, previous_stock_id=None, previous_quantity=0):
    """
    Move reservation counters from previous stock/qty to new stock/qty.
    Returns the stock instance.
    """
    stock = ProductStock.objects.select_for_update().get(pk=stock.pk)

    if previous_stock_id == stock.pk:
        available = stock.available_quantity + previous_quantity
        delta = quantity - previous_quantity
    else:
        if previous_stock_id:
            release_reservation_counters(previous_stock_id, previous_quantity)
        available = stock.available_quantity
        delta = quantity

    if quantity > available:
        raise ValueError(
            f'Διαθέσιμα μόνο {available} τεμάχια για δέσμευση '
            f'({stock.product.code} - {stock.variant_label()}).'
        )

    _adjust_reserved_quantity(stock, delta)
    return stock


@transaction.atomic
def consume_item_reservation(item, user=None):
    """Αφαίρεση δεσμευμένου αποθέματος κατά την αποστολή. Κρατάει το FK για δυνατότητα αναίρεσης."""
    stock = item.reserved_stock
    if not stock:
        return False

    stock = ProductStock.objects.select_for_update().get(pk=stock.pk)
    amount = min(item.quantity, stock.quantity)
    quantity_before = stock.quantity
    stock.quantity = max(0, stock.quantity - amount)
    stock.reserved_quantity = max(0, stock.reserved_quantity - item.quantity)
    stock.save(update_fields=['quantity', 'reserved_quantity', 'updated_at'])

    if amount > 0:
        ProductStockMovement.objects.create(
            stock=stock,
            movement_type=ProductStockMovement.REMOVE,
            amount=amount,
            quantity_before=quantity_before,
            quantity_after=stock.quantity,
            note=f'Αποστολή δεσμευμένης εργασίας #{item.task_id}',
            created_by=user,
        )
    return True


@transaction.atomic
def restore_item_shipment(item, user=None):
    """Επαναφορά αποθέματος όταν ακυρώνεται η αποστολή."""
    stock = item.reserved_stock
    if not stock:
        return False

    stock = ProductStock.objects.select_for_update().get(pk=stock.pk)
    quantity_before = stock.quantity
    stock.quantity = stock.quantity + item.quantity
    stock.reserved_quantity = stock.reserved_quantity + item.quantity
    stock.save(update_fields=['quantity', 'reserved_quantity', 'updated_at'])

    ProductStockMovement.objects.create(
        stock=stock,
        movement_type=ProductStockMovement.ADD,
        amount=item.quantity,
        quantity_before=quantity_before,
        quantity_after=stock.quantity,
        note=f'Αναίρεση αποστολής εργασίας #{item.task_id}',
        created_by=user,
    )
    return True
