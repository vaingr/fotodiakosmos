from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from email_utils import get_email_settings, is_email_configured, send_email_with_attachment
from warehouse.decorators import require_module_perm

from warehouse.models import Product as WarehouseProduct

from .forms import (
    FinishedProductForm,
    OfferForm,
    OfferItemFormSet,
    OfferSettingsForm,
    CompanyBankAccountFormSet,
    IndividualBankAccountFormSet,
    ProductMaterialFormSet,
    ProductWarehouseAddForm,
    ProductWarehouseEmailForm,
    ProductWarehouseRemoveForm,
    get_customer_delivery_email,
    get_offer_attention_display,
    get_offer_email_recipients,
)
from .models import FinishedProduct, Offer, OfferSettings, ProductStock, ProductStockMovement
from .pdf_utils import generate_offer_pdf, generate_warehouse_pdf


def _get_warehouse_materials_data():
    materials = []
    for material in WarehouseProduct.objects.select_related('measurement_unit').order_by('name'):
        unit = material.measurement_unit.name if material.measurement_unit_id else ''
        materials.append({
            'id': material.pk,
            'code': material.code,
            'name': material.name,
            'unit': unit,
            'label': f'{material.code} - {material.name} ({unit})'.strip(),
        })
    return materials


def _get_catalog_products_data():
    stock_map = {
        stock.product_id: stock.quantity
        for stock in ProductStock.objects.filter(quantity__gt=0).select_related('product')
    }
    products = []
    for product in FinishedProduct.objects.order_by('name'):
        stock_quantity = stock_map.get(product.pk)
        label = f'{product.code} - {product.name}'
        if stock_quantity is not None:
            label += f' (απόθεμα: {stock_quantity})'
        products.append({
            'id': product.pk,
            'code': product.code,
            'name': product.name,
            'label': label,
            'stock_quantity': stock_quantity,
            'in_warehouse': stock_quantity is not None,
        })
    return products


def _get_warehouse_products_data():
    products = []
    for stock in (
        ProductStock.objects
        .filter(quantity__gt=0)
        .select_related('product')
        .order_by('product__name')
    ):
        product = stock.product
        products.append({
            'id': product.pk,
            'code': product.code,
            'name': product.name,
            'label': f'{product.code} - {product.name} (απόθεμα: {stock.quantity})',
            'stock_quantity': stock.quantity,
        })
    return products


def _get_customers_email_data():
    from customers.models import Customer

    customers = []
    for customer in Customer.objects.all().order_by('last_name', 'first_name', 'company_name'):
        email = get_customer_delivery_email(customer)
        if not email:
            continue
        customers.append({
            'id': customer.pk,
            'name': customer.display_name(),
            'email': email,
            'label': f'{customer.display_name()} ({email})',
        })
    return customers


def _get_all_customers_data():
    from customers.models import Customer

    customers = []
    for customer in Customer.objects.all().order_by('last_name', 'first_name', 'company_name'):
        customers.append({
            'id': customer.pk,
            'name': customer.display_name(),
            'label': customer.display_name(),
            'vat_rate': customer.vat_rate,
            'vat_label': customer.get_vat_rate_label(),
        })
    return customers


def _get_warehouse_stock_items():
    first_add_user = ProductStockMovement.objects.filter(
        stock_id=OuterRef('pk'),
        movement_type=ProductStockMovement.ADD,
    ).order_by('created_at')

    return (
        ProductStock.objects
        .filter(quantity__gt=0)
        .select_related('product')
        .annotate(
            added_by_username=Subquery(
                first_add_user.values('created_by__username')[:1]
            ),
        )
        .order_by('product__name')
    )


def _add_product_to_warehouse(product, quantity, user):
    stock, _created = ProductStock.objects.get_or_create(
        product=product,
        defaults={'quantity': 0},
    )
    quantity_before = stock.quantity
    quantity_after = quantity_before + quantity
    stock.quantity = quantity_after
    stock.save(update_fields=['quantity', 'updated_at'])

    ProductStockMovement.objects.create(
        stock=stock,
        movement_type=ProductStockMovement.ADD,
        amount=quantity,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        created_by=user,
    )
    return stock, quantity_before == 0


def _remove_product_from_warehouse(product, quantity, user):
    stock = ProductStock.objects.get(product=product)
    quantity_before = stock.quantity
    quantity_after = quantity_before - quantity
    fully_removed = quantity_after <= 0

    ProductStockMovement.objects.create(
        stock=stock,
        movement_type=ProductStockMovement.REMOVE,
        amount=quantity,
        quantity_before=quantity_before,
        quantity_after=max(quantity_after, 0),
        created_by=user,
    )

    if fully_removed:
        stock.delete()
    else:
        stock.quantity = quantity_after
        stock.save(update_fields=['quantity', 'updated_at'])

    return fully_removed


def _product_form_context(form, formset, title, product=None):
    return {
        'form': form,
        'formset': formset,
        'title': title,
        'product': product,
        'warehouse_materials': _get_warehouse_materials_data(),
    }


@require_module_perm('perm_products')
def product_list(request):
    products = FinishedProduct.objects.all().order_by('name')
    search_query = request.GET.get('search', '').strip().upper()

    if search_query:
        products = products.filter(
            Q(code__icontains=search_query)
            | Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'products/product_list.html', {
        'products': page_obj,
        'search_query': search_query,
    })


@require_module_perm('perm_products')
def product_create(request):
    if request.method == 'POST':
        form = FinishedProductForm(request.POST, request.FILES)
        formset = ProductMaterialFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, 'Το προϊόν δημιουργήθηκε επιτυχώς!')
            return redirect('products:product_list')
    else:
        form = FinishedProductForm()
        formset = ProductMaterialFormSet()

    return render(request, 'products/product_form.html', _product_form_context(
        form, formset, 'Νέο Προϊόν',
    ))


@require_module_perm('perm_products')
def product_edit(request, pk):
    product = get_object_or_404(FinishedProduct, pk=pk)

    if request.method == 'POST':
        form = FinishedProductForm(request.POST, request.FILES, instance=product)
        formset = ProductMaterialFormSet(request.POST, instance=product)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Το προϊόν ενημερώθηκε επιτυχώς!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = FinishedProductForm(instance=product)
        formset = ProductMaterialFormSet(instance=product)

    return render(request, 'products/product_form.html', _product_form_context(
        form, formset, 'Επεξεργασία Προϊόντος', product,
    ))


@require_module_perm('perm_products')
def product_detail(request, pk):
    product = get_object_or_404(
        FinishedProduct.objects.prefetch_related(
            'materials__material__measurement_unit'
        ),
        pk=pk,
    )
    return render(request, 'products/product_detail.html', {
        'product': product,
    })


@require_module_perm('perm_products')
def product_delete(request, pk):
    product = get_object_or_404(FinishedProduct, pk=pk)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Το προϊόν διαγράφηκε επιτυχώς!')
        return redirect('products:product_list')

    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
    })


@require_module_perm('perm_finished_products_warehouse')
def product_warehouse(request):
    add_form = ProductWarehouseAddForm()
    remove_form = ProductWarehouseRemoveForm()

    if request.method == 'POST':
        action = request.POST.get('warehouse_action', 'add')

        if action == 'remove':
            remove_form = ProductWarehouseRemoveForm(request.POST)
            if remove_form.is_valid():
                product = remove_form.cleaned_data['product']
                quantity = remove_form.cleaned_data['quantity']
                fully_removed = _remove_product_from_warehouse(product, quantity, request.user)
                if fully_removed:
                    messages.success(
                        request,
                        f'Το προϊόν «{product.name}» αφαιρέθηκε εντελώς από την αποθήκη.',
                    )
                else:
                    messages.success(
                        request,
                        f'Αφαιρέθηκαν {quantity} τεμάχια από το προϊόν «{product.name}».',
                    )
                return redirect('products:product_warehouse')
        else:
            add_form = ProductWarehouseAddForm(request.POST)
            if add_form.is_valid():
                product = add_form.cleaned_data['product']
                quantity = add_form.cleaned_data['quantity']
                _stock, is_new = _add_product_to_warehouse(product, quantity, request.user)
                if is_new:
                    messages.success(
                        request,
                        f'Το προϊόν «{product.name}» προστέθηκε στην αποθήκη με ποσότητα {quantity}.',
                    )
                else:
                    messages.success(
                        request,
                        f'Προστέθηκαν {quantity} τεμάχια στο προϊόν «{product.name}».',
                    )
                return redirect('products:product_warehouse')

    warehouse_items = _get_warehouse_stock_items()

    return render(request, 'products/product_warehouse.html', {
        'add_form': add_form,
        'remove_form': remove_form,
        'email_form': ProductWarehouseEmailForm(),
        'warehouse_items': warehouse_items,
        'catalog_products': _get_catalog_products_data(),
        'warehouse_products': _get_warehouse_products_data(),
        'customers_email_data': _get_customers_email_data(),
        'email_configured': is_email_configured(),
    })


@require_module_perm('perm_finished_products_warehouse')
def product_warehouse_print(request):
    warehouse_items = _get_warehouse_stock_items()

    return render(request, 'products/product_warehouse_print.html', {
        'warehouse_items': warehouse_items,
        'total_count': warehouse_items.count(),
        'printed_at': timezone.localtime(timezone.now()),
    })


@require_module_perm('perm_finished_products_warehouse')
def product_warehouse_email(request):
    if request.method != 'POST':
        return redirect('products:product_warehouse')

    email_form = ProductWarehouseEmailForm(request.POST)
    if not email_form.is_valid():
        for field_errors in email_form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect('products:product_warehouse')

    if not is_email_configured():
        messages.error(
            request,
            'Οι ρυθμίσεις email δεν έχουν ολοκληρωθεί. Ρυθμίστε τον SMTP server από τις ρυθμίσεις συστήματος.',
        )
        return redirect('products:product_warehouse')

    warehouse_items = _get_warehouse_stock_items()
    if not warehouse_items.exists():
        messages.error(request, 'Δεν υπάρχουν προϊόντα στην αποθήκη για αποστολή.')
        return redirect('products:product_warehouse')

    customer = email_form.cleaned_data['customer']
    recipient_email = get_customer_delivery_email(customer)
    recipient_name = customer.display_name()
    custom_message = email_form.cleaned_data.get('message', '').strip()
    printed_at = timezone.localtime(timezone.now())
    pdf_bytes = generate_warehouse_pdf(warehouse_items)
    filename = f'apothiki-etimon-proionton-{printed_at.strftime("%Y%m%d")}.pdf'

    email_settings = get_email_settings()
    sender_name = email_settings.get('from_name') or 'Fotodiakosmos'
    subject = (
        f'{sender_name} - Αποθήκη έτοιμων προϊόντων '
        f'({printed_at.strftime("%d/%m/%Y")})'
    )

    if custom_message:
        body = custom_message
    else:
        body_lines = [
            'Σας αποστέλλουμε συνημμένο το PDF με τα προϊόντα της αποθήκης έτοιμων προϊόντων.',
            f'Ημερομηνία κατάστασης: {printed_at.strftime("%d/%m/%Y %H:%M")}',
            '',
            'Με εκτίμηση,',
        ]
        body = '\n'.join(body_lines)

    success, response_message = send_email_with_attachment(
        recipient_email,
        subject,
        body,
        pdf_bytes,
        filename,
    )

    if success:
        messages.success(
            request,
            f'Το PDF στάλθηκε στο email {recipient_email} (πελάτης: {customer.display_name()}).',
        )
    else:
        messages.error(request, response_message)

    return redirect('products:product_warehouse')


@require_module_perm('perm_offers')
def offers(request):
    offer_list = (
        Offer.objects
        .select_related('customer', 'created_by')
        .prefetch_related('items')
        .order_by('-created_at')
    )
    search_query = request.GET.get('search', '').strip()
    if search_query:
        offer_list = offer_list.filter(
            Q(offer_number__icontains=search_query)
            | Q(customer__company_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
            | Q(customer__last_name__icontains=search_query)
        )

    return render(request, 'products/offers.html', {
        'offers': offer_list,
        'search_query': search_query,
    })


@require_module_perm('perm_offers')
def offer_create(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        formset = OfferItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            offer = form.save(commit=False)
            offer.created_by = request.user
            offer.save()
            formset.instance = offer
            formset.save()
            offer.recalculate_total()
            messages.success(
                request,
                f'Η προσφορά {offer.offer_number} δημιουργήθηκε επιτυχώς.',
            )
            return redirect('products:offers')
    else:
        form = OfferForm()
        formset = OfferItemFormSet(prefix='items')

    return render(request, 'products/offer_form.html', {
        'form': form,
        'formset': formset,
        'catalog_products': _get_catalog_products_data(),
        'customers_data': _get_all_customers_data(),
        'page_title': 'Νέα Προσφορά',
        'is_edit': False,
    })


@require_module_perm('perm_offers')
def offer_edit(request, pk):
    offer = get_object_or_404(
        Offer.objects.prefetch_related('items__product'),
        pk=pk,
    )
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        formset = OfferItemFormSet(request.POST, instance=offer, prefix='items')
        if form.is_valid() and formset.is_valid():
            offer = form.save()
            formset.save()
            if hasattr(offer, '_prefetched_objects_cache'):
                offer._prefetched_objects_cache.pop('items', None)
            offer.recalculate_total()
            messages.success(
                request,
                f'Η προσφορά {offer.offer_number} ενημερώθηκε επιτυχώς.',
            )
            return redirect('products:offers')
    else:
        form = OfferForm(instance=offer)
        formset = OfferItemFormSet(instance=offer, prefix='items')

    return render(request, 'products/offer_form.html', {
        'form': form,
        'formset': formset,
        'catalog_products': _get_catalog_products_data(),
        'customers_data': _get_all_customers_data(),
        'page_title': f'Επεξεργασία Προσφοράς {offer.offer_number}',
        'offer': offer,
        'is_edit': True,
    })


@require_module_perm('perm_offers')
def offer_settings(request):
    settings_obj = OfferSettings.get_solo()
    if request.method == 'POST':
        form = OfferSettingsForm(request.POST, request.FILES, instance=settings_obj)
        company_bank_formset = CompanyBankAccountFormSet(
            request.POST,
            instance=settings_obj,
            prefix='company_banks',
        )
        individual_bank_formset = IndividualBankAccountFormSet(
            request.POST,
            instance=settings_obj,
            prefix='individual_banks',
        )
        if form.is_valid() and company_bank_formset.is_valid() and individual_bank_formset.is_valid():
            form.save()
            company_bank_formset.save()
            individual_bank_formset.save()
            messages.success(request, 'Οι ρυθμίσεις προσφορών αποθηκεύτηκαν επιτυχώς.')
            return redirect('products:offer_settings')
    else:
        form = OfferSettingsForm(instance=settings_obj)
        company_bank_formset = CompanyBankAccountFormSet(
            instance=settings_obj,
            prefix='company_banks',
        )
        individual_bank_formset = IndividualBankAccountFormSet(
            instance=settings_obj,
            prefix='individual_banks',
        )

    return render(request, 'products/offer_settings.html', {
        'form': form,
        'company_bank_formset': company_bank_formset,
        'individual_bank_formset': individual_bank_formset,
        'settings': settings_obj,
        'logo_section_open': request.method == 'POST' and 'logo' in form.errors,
        'terms_section_open': request.method == 'POST' and any(
            field in form.errors for field in (
                'delivery_time', 'delivery_place', 'delivery_method', 'packaging', 'payment_method',
            )
        ),
        'company_bank_section_open': request.method == 'POST' and (
            bool(company_bank_formset.non_form_errors())
            or any(bank_form.errors for bank_form in company_bank_formset)
        ),
        'individual_bank_section_open': request.method == 'POST' and (
            bool(individual_bank_formset.non_form_errors())
            or any(bank_form.errors for bank_form in individual_bank_formset)
        ),
    })


@require_module_perm('perm_offers')
def offer_print(request, pk):
    offer = get_object_or_404(
        Offer.objects.select_related('customer', 'created_by').prefetch_related('items__product'),
        pk=pk,
    )
    email_recipients = get_offer_email_recipients(offer.customer)
    contact_recipient = request.GET.get('contact', '1')
    if contact_recipient not in ('1', '2'):
        contact_recipient = '1'
    attention_display = get_offer_attention_display(offer.customer, contact_recipient)
    offer_settings = OfferSettings.get_solo()
    offer_bank_accounts = offer_settings.bank_accounts.filter(
        account_group=offer.bank_account_group,
    )
    return render(request, 'products/offer_print.html', {
        'offer': offer,
        'offer_settings': offer_settings,
        'offer_bank_accounts': offer_bank_accounts,
        'printed_at': timezone.localtime(timezone.now()),
        'email_configured': is_email_configured(),
        'customer_email': email_recipients[0]['email'] if email_recipients else '',
        'can_send_offer_email': bool(email_recipients),
        'attention_display': attention_display,
        'pdf_export': request.GET.get('pdf') == '1',
    })


@require_module_perm('perm_offers')
def offer_email(request, pk):
    if request.method != 'POST':
        return redirect('products:offer_print', pk=pk)

    offer = get_object_or_404(
        Offer.objects.select_related('customer').prefetch_related('items__product'),
        pk=pk,
    )

    if not is_email_configured():
        messages.error(
            request,
            'Οι ρυθμίσεις email δεν έχουν ολοκληρωθεί. Ρυθμίστε τον SMTP server από τις ρυθμίσεις συστήματος.',
        )
        return redirect('products:offer_print', pk=pk)

    email_recipients = get_offer_email_recipients(offer.customer)
    if not email_recipients:
        messages.error(request, 'Ο πελάτης δεν έχει καταχωρημένο email.')
        return redirect('products:offer_print', pk=pk)

    filename = f'prosfora-{offer.offer_number}.pdf'

    email_settings = get_email_settings()
    sender_name = email_settings.get('from_name') or 'Fotodiakosmos'
    subject = f'{sender_name} - Προσφορά {offer.offer_number}'

    body_lines = [
        f'Σας αποστέλλουμε συνημμένη την οικονομική προσφορά {offer.offer_number}.',
        '',
        'Με εκτίμηση,',
    ]
    body = '\n'.join(body_lines)

    sent_emails = []
    last_error = ''

    for recipient in email_recipients:
        try:
            pdf_bytes = generate_offer_pdf(
                offer,
                request,
                contact_recipient=recipient.get('contact_recipient'),
            )
        except Exception as exc:
            messages.error(request, f'Αποτυχία δημιουργίας PDF: {exc}')
            return redirect('products:offer_print', pk=pk)

        success, response_message = send_email_with_attachment(
            recipient['email'],
            subject,
            body,
            pdf_bytes,
            filename,
        )

        if success:
            sent_emails.append(recipient['email'])
        else:
            last_error = response_message

    if sent_emails and not last_error:
        if len(sent_emails) == 1:
            messages.success(
                request,
                f'Η προσφορά στάλθηκε στο email {sent_emails[0]} '
                f'(πελάτης: {offer.customer.display_name()}).',
            )
        else:
            messages.success(
                request,
                f'Η προσφορά στάλθηκε στα emails {", ".join(sent_emails)} '
                f'(πελάτης: {offer.customer.display_name()}).',
            )
    elif sent_emails:
        messages.warning(
            request,
            f'Η προσφορά στάλθηκε σε {", ".join(sent_emails)}, '
            f'αλλά απέτυχε για άλλους παραλήπτες: {last_error}',
        )
    else:
        messages.error(request, last_error or 'Αποτυχία αποστολής email.')

    return redirect('products:offer_print', pk=pk)


@require_module_perm('perm_offers')
def offer_delete(request, pk):
    offer = get_object_or_404(
        Offer.objects.select_related('customer'),
        pk=pk,
    )
    if request.method == 'POST':
        offer_number = offer.offer_number
        offer.delete()
        messages.success(request, f'Η προσφορά {offer_number} διαγράφηκε επιτυχώς.')
        return redirect('products:offers')

    return render(request, 'products/offer_confirm_delete.html', {
        'offer': offer,
    })
