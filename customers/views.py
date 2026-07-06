from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from warehouse.decorators import require_module_perm
from .models import Customer
from .forms import CustomerForm
from .sms_utils import send_sms

@require_module_perm('perm_customers')
def customer_list(request):
    """List all customers with smart search functionality"""
    customers = Customer.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        # Check if the search query looks like a barcode (contains only letters and numbers, no spaces)
        import re
        if re.match(r'^[Α-Ωα-ωA-Za-z0-9]+$', search_query) and not search_query.isspace():
            # Extract numeric part from the search query
            numeric_part = re.sub(r'[^0-9]', '', search_query)
            if numeric_part:
                # Search for customers whose phone contains the numeric part
                # This allows searching "690" to find customers with "6901234567"
                customers = customers.filter(phone__icontains=numeric_part)
            else:
                # If no numeric part, search in all fields (case-insensitive)
                customers = customers.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(company_name__icontains=search_query) |
                    Q(phone__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(contact_person__icontains=search_query) |
                    Q(contact_phone__icontains=search_query) |
                    Q(contact_email__icontains=search_query) |
                    Q(contact_person_2__icontains=search_query) |
                    Q(contact_person_2_phone__icontains=search_query) |
                    Q(contact_person_2_email__icontains=search_query)
                )
        else:
            # Normal search for names, phones, etc. (case-insensitive)
            # This allows searching "νικ" to find "ΝΙΚΟΛΟΠΟΥΛΟΣ"
            # And searching "690" to find "6901234567"
            customers = customers.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(company_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(contact_person__icontains=search_query) |
                Q(contact_phone__icontains=search_query) |
                Q(contact_email__icontains=search_query) |
                Q(contact_person_2__icontains=search_query) |
                Q(contact_person_2_phone__icontains=search_query) |
                Q(contact_person_2_email__icontains=search_query)
            )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'customers/customer_list.html', {
        'customers': page_obj
    })

@require_module_perm('perm_customers')
def customer_create(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'Ο πελάτης δημιουργήθηκε επιτυχώς!')
            return redirect('customers:customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {
        'form': form, 
        'title': 'Νέος Πελάτης'
    })

@require_module_perm('perm_customers')
def customer_edit(request, pk):
    """Edit existing customer"""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'Ο πελάτης ενημερώθηκε επιτυχώς!')
            return redirect('customers:customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {
        'form': form, 
        'title': f'Επεξεργασία Πελάτη: {customer.full_name()}'
    })

@require_module_perm('perm_customers')
def customer_detail(request, pk):
    """View customer details"""
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'customers/customer_detail.html', {
        'customer': customer
    })

@require_module_perm('perm_customers')
def delete_customer(request, customer_id):
    """Delete customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    offers_count = customer.offers.count()
    has_offers = offers_count > 0

    if request.method == 'POST':
        if has_offers:
            messages.error(
                request,
                f'Ο πελάτης «{customer.display_name()}» έχει {offers_count} '
                f'{"προσφορά" if offers_count == 1 else "προσφορές"} και δεν μπορεί να διαγραφεί. '
                'Διαγράψτε πρώτα τις προσφορές του.',
            )
            return redirect('customers:customer_detail', pk=customer.id)

        try:
            customer_name = customer.full_name()
            customer.delete()
            messages.success(request, f'Ο πελάτης {customer_name} διαγράφηκε επιτυχώς!')
            return redirect('customers:customer_list')
        except ProtectedError:
            messages.error(
                request,
                f'Ο πελάτης «{customer.display_name()}» συνδέεται με προσφορές και δεν μπορεί να διαγραφεί. '
                'Διαγράψτε πρώτα τις προσφορές του.',
            )
            return redirect('customers:customer_detail', pk=customer.id)

    return render(request, 'customers/customer_confirm_delete.html', {
        'customer': customer,
        'offers_count': offers_count,
        'has_offers': has_offers,
    })

@require_module_perm('perm_customers')
def send_sms_to_customer(request, customer_id):
    """Send SMS to a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        
        if not message:
            messages.error(request, 'Παρακαλώ εισάγετε ένα μήνυμα.')
            return redirect('customers:send_sms', customer_id=customer.id)
        
        if not customer.get_primary_phone():
            messages.error(request, 'Ο πελάτης δεν έχει καταχωρημένο αριθμό τηλεφώνου.')
            return redirect('customers:send_sms', customer_id=customer.id)
        
        # Αποστολή SMS
        success, response_message = send_sms(customer.get_primary_phone(), message)
        
        if success:
            messages.success(request, response_message)
        else:
            messages.error(request, response_message)
        
        return redirect('customers:customer_detail', pk=customer.id)
    
    return render(request, 'customers/send_sms.html', {
        'customer': customer
    })
