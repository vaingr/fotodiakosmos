from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, ProtectedError, F, Max
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import Subscription
from .decorators import (
    require_warehouse_access,
    require_warehouse_perm,
    require_warehouse_admin,
    require_warehouse_dashboard_access,
)
from .models import Product, MeasurementUnit, StockMovement, WarehouseUserProfile
from .forms import (
    ProductForm,
    MeasurementUnitForm,
    QuantityAdjustmentForm,
    WarehouseUserCreateForm,
    WarehouseUserEditForm,
)
from .permissions import WAREHOUSE_PERMISSION_FIELDS, WAREHOUSE_PERMISSION_KEYS


def _permission_form_fields(form):
    return [(form[perm_key], label) for perm_key, label in WAREHOUSE_PERMISSION_FIELDS]


def _get_filtered_products(request):
    products = Product.objects.select_related('measurement_unit').order_by('name')
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    low_stock = request.GET.get('low_stock', '')
    if low_stock == 'true':
        products = products.filter(quantity__lte=F('low_stock_threshold'))

    return products, search_query, low_stock


def _get_products_version():
    stats = Product.objects.aggregate(
        total=Count('pk'),
        latest_updated=Max('updated_at'),
        latest_created=Max('created_at'),
        max_id=Max('pk'),
    )
    latest = stats['latest_updated']
    if stats['latest_created'] and (not latest or stats['latest_created'] > latest):
        latest = stats['latest_created']
    latest_ts = int(latest.timestamp()) if latest else 0
    return f"{stats['total']}-{stats['max_id'] or 0}-{latest_ts}"


def _get_movements_version():
    stats = StockMovement.objects.aggregate(
        total=Count('pk'),
        latest=Max('created_at'),
        max_id=Max('pk'),
    )
    latest_ts = int(stats['latest'].timestamp()) if stats['latest'] else 0
    return f"{stats['total']}-{stats['max_id'] or 0}-{latest_ts}"


def _get_dashboard_live_version():
    low_stock = Product.objects.filter(quantity__lte=F('low_stock_threshold')).count()
    return f"{_get_products_version()}|{_get_movements_version()}|{low_stock}"


def _get_recent_movements():
    return StockMovement.objects.select_related(
        'product',
        'product__measurement_unit',
        'created_by',
    ).order_by('-created_at')[:30]


@require_warehouse_perm('perm_view_products')
def product_list(request):
    """List all products with search functionality"""
    products, search_query, low_stock = _get_filtered_products(request)

    if request.GET.get('version') == '1':
        return JsonResponse({'version': _get_products_version()})

    if request.GET.get('live') == '1':
        paginator = Paginator(products, 20)
        if search_query:
            live_products = list(products[:100])
        else:
            page_number = request.GET.get('page', 1)
            live_products = list(paginator.get_page(page_number))

        render_context = {
            'products': live_products,
            'search_query': search_query,
            'low_stock': low_stock,
        }
        return JsonResponse({
            'cards_html': render_to_string(
                'warehouse/_product_list_cards.html',
                render_context,
                request=request,
            ),
            'table_html': render_to_string(
                'warehouse/_product_list_table_rows.html',
                render_context,
                request=request,
            ),
            'count': products.count(),
            'version': _get_products_version(),
        })
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'low_stock': low_stock,
        'list_version': _get_products_version(),
    }
    return render(request, 'warehouse/product_list.html', context)


@require_warehouse_perm('perm_view_products')
def product_list_print(request):
    """Printable list of all filtered products."""
    products, search_query, low_stock = _get_filtered_products(request)

    return render(request, 'warehouse/product_list_print.html', {
        'products': products,
        'search_query': search_query,
        'low_stock': low_stock,
        'total_count': products.count(),
        'printed_at': timezone.localtime(timezone.now()),
    })


@require_warehouse_perm('perm_create_products')
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Set created_at to current time (in Athens timezone)
            product.created_at = timezone.now()
            
            product.save()
            messages.success(request, 'Το υλικό δημιουργήθηκε επιτυχώς!')
            
            # Return to next page if provided, otherwise go to product_list
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('warehouse:product_list')
    else:
        form = ProductForm()
    
    # Get next URL from query parameter
    next_url = request.GET.get('next', '')
    
    return render(request, 'warehouse/product_form.html', {
        'form': form,
        'title': 'Νέο Υλικό',
        'action': 'Δημιουργία',
        'next_url': next_url
    })


@require_warehouse_perm('perm_edit_products')
def product_edit(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product.objects.select_related('measurement_unit'), pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Το υλικό ενημερώθηκε επιτυχώς!')
            
            # Return to next page if provided, otherwise go to product_list
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('warehouse:product_list')
    else:
        form = ProductForm(instance=product)
    
    # Get next URL from query parameter
    next_url = request.GET.get('next', '')
    
    return render(request, 'warehouse/product_form.html', {
        'form': form,
        'product': product,
        'title': 'Επεξεργασία Υλικού',
        'action': 'Ενημέρωση',
        'next_url': next_url
    })


@require_warehouse_perm('perm_view_products')
def product_detail(request, pk):
    """View product details"""
    product = get_object_or_404(Product.objects.select_related('measurement_unit'), pk=pk)
    recent_movements = product.stock_movements.select_related('created_by').order_by('-created_at')[:20]

    return render(request, 'warehouse/product_detail.html', {
        'product': product,
        'recent_movements': recent_movements,
    })


def _quantity_adjustment_view(request, pk, movement_type):
    product = get_object_or_404(Product.objects.select_related('measurement_unit'), pk=pk)
    is_add = movement_type == StockMovement.ADD
    unit_name = product.measurement_unit.name if product.measurement_unit_id else ''

    if is_add:
        title = 'Προσθήκη Ποσότητας'
        submit_label = 'Προσθήκη'
        action_class = 'add'
    else:
        title = 'Αφαίρεση Ποσότητας'
        submit_label = 'Αφαίρεση'
        action_class = 'remove'

    if request.method == 'POST':
        form = QuantityAdjustmentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            note = form.cleaned_data.get('note', '').strip()

            with transaction.atomic():
                product = Product.objects.select_for_update().select_related('measurement_unit').get(pk=pk)
                quantity_before = product.quantity

                if not is_add and amount > quantity_before:
                    form.add_error(
                        'amount',
                        f'Η ποσότητα δεν μπορεί να υπερβαίνει το διαθέσιμο απόθεμα ({quantity_before} {unit_name}).',
                    )
                else:
                    quantity_after = quantity_before + amount if is_add else quantity_before - amount
                    product.quantity = quantity_after
                    product.save(update_fields=['quantity', 'updated_at'])
                    StockMovement.objects.create(
                        product=product,
                        movement_type=movement_type,
                        amount=amount,
                        quantity_before=quantity_before,
                        quantity_after=quantity_after,
                        note=note,
                        created_by=request.user,
                    )

                    if is_add:
                        messages.success(
                            request,
                            f'Προστέθηκαν {amount} {unit_name}. Νέο απόθεμα: {quantity_after} {unit_name}.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Αφαιρέθηκαν {amount} {unit_name}. Νέο απόθεμα: {quantity_after} {unit_name}.',
                        )

                    next_url = request.POST.get('next') or request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('warehouse:product_detail', pk=pk)
    else:
        form = QuantityAdjustmentForm()

    next_url = request.GET.get('next', '')

    return render(request, 'warehouse/quantity_adjust.html', {
        'form': form,
        'product': product,
        'title': title,
        'submit_label': submit_label,
        'action_class': action_class,
        'is_add': is_add,
        'next_url': next_url,
    })


@require_warehouse_perm('perm_add_quantity')
def product_add_quantity(request, pk):
    """Add quantity to a product"""
    return _quantity_adjustment_view(request, pk, StockMovement.ADD)


@require_warehouse_perm('perm_remove_quantity')
def product_remove_quantity(request, pk):
    """Remove quantity from a product"""
    return _quantity_adjustment_view(request, pk, StockMovement.REMOVE)


@require_warehouse_perm('perm_delete_products')
def product_delete(request, pk):
    """Delete a product"""
    product = get_object_or_404(Product.objects.select_related('measurement_unit'), pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Το υλικό "{product_name}" διαγράφηκε επιτυχώς!')
        return redirect('warehouse:product_list')
    
    return render(request, 'warehouse/product_confirm_delete.html', {
        'product': product
    })


@require_warehouse_dashboard_access
def warehouse_dashboard(request):
    """Warehouse dashboard with statistics"""
    if request.GET.get('version') == '1':
        return JsonResponse({'version': _get_dashboard_live_version()})

    if request.GET.get('live') == '1':
        recent_movements = _get_recent_movements()
        return JsonResponse({
            'movements_html': render_to_string(
                'warehouse/_dashboard_movements.html',
                {'recent_movements': recent_movements},
                request=request,
            ),
            'total_products': Product.objects.count(),
            'low_stock_products': Product.objects.filter(
                quantity__lte=F('low_stock_threshold'),
            ).count(),
            'version': _get_dashboard_live_version(),
        })

    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=F('low_stock_threshold')).count()
    recent_movements = _get_recent_movements()

    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
        'dashboard_version': _get_dashboard_live_version(),
    }
    return render(request, 'warehouse/dashboard.html', context)


def _quantity_select_product(request, is_add):
    search_query = request.GET.get('search', '').strip()
    products = Product.objects.select_related('measurement_unit').order_by('name')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    if is_add:
        title = 'Προσθήκη Ποσότητας'
        subtitle = 'Επιλέξτε υλικό για προσθήκη ποσότητας'
        action_url_name = 'warehouse:product_add_quantity'
        action_class = 'add'
    else:
        title = 'Αφαίρεση Ποσότητας'
        subtitle = 'Επιλέξτε υλικό για αφαίρεση ποσότητας'
        action_url_name = 'warehouse:product_remove_quantity'
        action_class = 'remove'

    render_context = {
        'products': products,
        'search_query': search_query,
        'title': title,
        'subtitle': subtitle,
        'action_url_name': action_url_name,
        'action_class': action_class,
        'is_add': is_add,
    }

    if request.GET.get('version') == '1':
        return JsonResponse({'version': _get_products_version()})

    if request.GET.get('live') == '1':
        return JsonResponse({
            'html': render_to_string(
                'warehouse/_quantity_select_list.html',
                render_context,
                request=request,
            ),
            'version': _get_products_version(),
        })

    return render(request, 'warehouse/quantity_select.html', {
        **render_context,
        'list_version': _get_products_version(),
    })


@require_warehouse_perm('perm_add_quantity')
def quantity_select_add(request):
    """Select product for quantity addition"""
    return _quantity_select_product(request, is_add=True)


@require_warehouse_perm('perm_remove_quantity')
def quantity_select_remove(request):
    """Select product for quantity removal"""
    return _quantity_select_product(request, is_add=False)


@require_warehouse_perm('perm_view_products')
def product_search_api(request):
    """API endpoint for product search by name, code, or barcode (case-insensitive)"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'products': []})
    
    from django.db.models.functions import Lower
    
    query_lower = query.lower()
    
    products = Product.objects.select_related('measurement_unit').annotate(
        name_lower=Lower('name'),
        code_lower=Lower('code'),
        barcode_lower=Lower('barcode')
    ).filter(
        Q(name_lower__contains=query_lower) | 
        Q(code_lower__contains=query_lower) | 
        Q(barcode_lower__contains=query_lower)
    ).order_by('name')[:20]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'code': p.code,
        'barcode': p.barcode or '',
        'quantity': p.quantity,
        'measurement_unit': p.measurement_unit.name if p.measurement_unit_id else '',
    } for p in products]
    
    return JsonResponse({'products': results})


@require_warehouse_access
def warehouse_settings(request):
    """Warehouse settings page"""
    return render(request, 'warehouse/settings.html')


@require_warehouse_perm('perm_measurement_units')
def measurement_unit_list(request):
    """List all measurement units"""
    units = MeasurementUnit.objects.annotate(product_count=Count('products')).order_by('name')

    return render(request, 'warehouse/measurement_unit_list.html', {
        'units': units,
    })


@require_warehouse_perm('perm_measurement_units')
def measurement_unit_create(request):
    """Create a new measurement unit"""
    if request.method == 'POST':
        form = MeasurementUnitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Η μονάδα μέτρησης δημιουργήθηκε επιτυχώς!')
            return redirect('warehouse:measurement_unit_list')
    else:
        form = MeasurementUnitForm()

    return render(request, 'warehouse/measurement_unit_form.html', {
        'form': form,
        'title': 'Νέα Μονάδα Μέτρησης',
    })


@require_warehouse_perm('perm_measurement_units')
def measurement_unit_edit(request, pk):
    """Edit a measurement unit"""
    unit = get_object_or_404(MeasurementUnit, pk=pk)

    if request.method == 'POST':
        form = MeasurementUnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Η μονάδα μέτρησης ενημερώθηκε επιτυχώς!')
            return redirect('warehouse:measurement_unit_list')
    else:
        form = MeasurementUnitForm(instance=unit)

    return render(request, 'warehouse/measurement_unit_form.html', {
        'form': form,
        'unit': unit,
        'title': 'Επεξεργασία Μονάδας Μέτρησης',
    })


@require_warehouse_perm('perm_measurement_units')
def measurement_unit_delete(request, pk):
    """Delete a measurement unit"""
    unit = get_object_or_404(MeasurementUnit, pk=pk)

    if request.method == 'POST':
        unit_name = unit.name
        try:
            unit.delete()
            messages.success(request, f'Η μονάδα "{unit_name}" διαγράφηκε επιτυχώς!')
            return redirect('warehouse:measurement_unit_list')
        except ProtectedError:
            messages.error(
                request,
                f'Δεν μπορεί να διαγραφεί η μονάδα "{unit_name}" επειδή χρησιμοποιείται από υλικά.',
            )
            return redirect('warehouse:measurement_unit_list')

    product_count = unit.products.count()

    return render(request, 'warehouse/measurement_unit_confirm_delete.html', {
        'unit': unit,
        'product_count': product_count,
    })


@require_warehouse_admin
def warehouse_user_list(request):
    profiles = (
        WarehouseUserProfile.objects
        .filter(is_managed_user=True)
        .select_related('user')
        .order_by('user__username')
    )
    return render(request, 'warehouse/warehouse_user_list.html', {
        'profiles': profiles,
    })


@require_warehouse_admin
def warehouse_user_create(request):
    if request.method == 'POST':
        form = WarehouseUserCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
            )
            Subscription.objects.create(
                user=user,
                expiry_date=date.today() + timedelta(days=3650),
            )
            role = form.cleaned_data['role']
            profile = WarehouseUserProfile(user=user, role=role, is_managed_user=True)
            if role == WarehouseUserProfile.ROLE_USER:
                for perm_key in WAREHOUSE_PERMISSION_KEYS:
                    setattr(profile, perm_key, form.cleaned_data.get(perm_key, False))
            profile.save()
            messages.success(request, f'Ο χρήστης "{user.username}" δημιουργήθηκε επιτυχώς!')
            return redirect('warehouse:warehouse_user_list')
    else:
        form = WarehouseUserCreateForm()

    return render(request, 'warehouse/warehouse_user_form.html', {
        'form': form,
        'title': 'Νέος Χρήστης Αποθήκης',
        'permission_form_fields': _permission_form_fields(form),
        'is_create': True,
    })


@require_warehouse_admin
def warehouse_user_edit(request, pk):
    profile = get_object_or_404(
        WarehouseUserProfile.objects.select_related('user'),
        pk=pk,
        is_managed_user=True,
    )

    if request.method == 'POST':
        form = WarehouseUserEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ο χρήστης "{profile.user.username}" ενημερώθηκε επιτυχώς!')
            return redirect('warehouse:warehouse_user_list')
    else:
        form = WarehouseUserEditForm(instance=profile)

    return render(request, 'warehouse/warehouse_user_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Επεξεργασία Χρήστη',
        'permission_form_fields': _permission_form_fields(form),
        'is_create': False,
    })


@require_warehouse_admin
def warehouse_user_delete(request, pk):
    profile = get_object_or_404(
        WarehouseUserProfile.objects.select_related('user'),
        pk=pk,
        is_managed_user=True,
    )

    if profile.user_id == request.user.id:
        messages.error(request, 'Δεν μπορείτε να διαγράψετε τον δικό σας λογαριασμό.')
        return redirect('warehouse:warehouse_user_list')

    if request.method == 'POST':
        username = profile.user.username
        profile.user.delete()
        messages.success(request, f'Ο χρήστης "{username}" διαγράφηκε επιτυχώς!')
        return redirect('warehouse:warehouse_user_list')

    return render(request, 'warehouse/warehouse_user_confirm_delete.html', {
        'profile': profile,
    })
