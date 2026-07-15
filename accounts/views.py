from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Subscription, ScheduledTask, ScheduledTaskItem
from django.db.models import Q, Case, When, IntegerField, Count
from django import forms
from django.urls import reverse
from urllib.parse import urlencode
from django.forms import inlineformset_factory
from .forms import TaskCreateForm, TaskItemFormSet, TaskItemForm, BaseTaskItemFormSet
from products.models import Offer
from datetime import date
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import os
import shutil
from datetime import datetime
import sys

# Import SMS utilities
try:
    from django.conf import settings
    BASE_DIR = str(settings.BASE_DIR)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    from sms_utils import send_sms, send_bulk_sms, check_account_balance, check_sms_status, get_sms_history
except (ImportError, AttributeError) as e:
    try:
        # Fallback: use current working directory
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from sms_utils import send_sms, send_bulk_sms, check_account_balance, check_sms_status, get_sms_history
    except ImportError as e2:
        # Final fallback if import fails
        send_sms = None
        send_bulk_sms = None
        check_account_balance = None
        check_sms_status = None
        get_sms_history = None

from customers.models import Customer

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def _get_task_priority_order():
    return Case(
        When(priority=ScheduledTask.PRIORITY_HIGH, then=0),
        When(priority=ScheduledTask.PRIORITY_MEDIUM, then=1),
        When(priority=ScheduledTask.PRIORITY_LOW, then=2),
        default=3,
        output_field=IntegerField(),
    )


def _get_task_queryset():
    return ScheduledTask.objects.select_related(
        'assigned_to',
        'created_by',
        'customer',
    ).prefetch_related('items__product')


def _build_task_filter_query(
    task_filter='pending',
    search_query='',
    task_type_filter='',
    priority_filter='',
):
    params = {}
    if task_filter:
        params['filter'] = task_filter
    search_query = (search_query or '').strip()
    if search_query:
        params['q'] = search_query
    if task_type_filter in (
        ScheduledTask.TYPE_CONSTRUCTION,
        ScheduledTask.TYPE_REPAIR,
    ):
        params['type'] = task_type_filter
    if priority_filter in (
        ScheduledTask.PRIORITY_LOW,
        ScheduledTask.PRIORITY_MEDIUM,
        ScheduledTask.PRIORITY_HIGH,
    ):
        params['priority'] = priority_filter
    return params


def _task_filter_url(
    task_filter='pending',
    search_query='',
    task_type_filter='',
    priority_filter='',
):
    params = _build_task_filter_query(
        task_filter,
        search_query,
        task_type_filter,
        priority_filter,
    )
    url = reverse('task_scheduling')
    if params:
        return f'{url}?{urlencode(params)}'
    return url


def _get_task_filter_urls(
    task_filter='pending',
    search_query='',
    task_type_filter='',
    priority_filter='',
):
    def make_url(
        filter_value=None,
        type_value=None,
        priority_value=None,
        toggle_type=None,
        toggle_priority=None,
        clear_search=False,
    ):
        current_filter = task_filter if filter_value is None else filter_value
        current_type = task_type_filter
        if toggle_type:
            current_type = (
                ''
                if task_type_filter == toggle_type
                else toggle_type
            )
        elif type_value is not None:
            current_type = type_value

        current_priority = priority_filter
        if toggle_priority:
            current_priority = (
                ''
                if priority_filter == toggle_priority
                else toggle_priority
            )
        elif priority_value is not None:
            current_priority = priority_value

        current_search = '' if clear_search else search_query
        return _task_filter_url(
            current_filter,
            current_search,
            current_type,
            current_priority,
        )

    return {
        'all': make_url(filter_value='all'),
        'pending': make_url(filter_value='pending'),
        'overdue': make_url(filter_value='overdue'),
        'completed': make_url(filter_value='completed'),
        'construction': make_url(toggle_type=ScheduledTask.TYPE_CONSTRUCTION),
        'repair': make_url(toggle_type=ScheduledTask.TYPE_REPAIR),
        'priority_high': make_url(toggle_priority=ScheduledTask.PRIORITY_HIGH),
        'priority_medium': make_url(toggle_priority=ScheduledTask.PRIORITY_MEDIUM),
        'priority_low': make_url(toggle_priority=ScheduledTask.PRIORITY_LOW),
        'clear_search': make_url(clear_search=True),
    }


def _filter_tasks(
    queryset,
    task_filter='active',
    search_query='',
    task_type_filter='',
    priority_filter='',
):
    today = timezone.localdate()
    active_statuses = [ScheduledTask.STATUS_PENDING]

    if task_filter == 'pending':
        queryset = queryset.filter(status=ScheduledTask.STATUS_PENDING)
    elif task_filter == 'in_progress':
        queryset = queryset.filter(status=ScheduledTask.STATUS_PENDING)
    elif task_filter == 'completed':
        queryset = queryset.filter(status=ScheduledTask.STATUS_COMPLETED)
    elif task_filter == 'cancelled':
        queryset = queryset.filter(status=ScheduledTask.STATUS_CANCELLED)
    elif task_filter == 'today':
        queryset = queryset.filter(scheduled_date=today, status__in=active_statuses)
    elif task_filter == 'overdue':
        queryset = queryset.filter(scheduled_date__lt=today, status__in=active_statuses)
    elif task_filter == 'all':
        pass
    else:
        queryset = queryset.filter(status__in=active_statuses)

    if task_type_filter == ScheduledTask.TYPE_CONSTRUCTION:
        queryset = queryset.filter(task_type=ScheduledTask.TYPE_CONSTRUCTION)
    elif task_type_filter == ScheduledTask.TYPE_REPAIR:
        queryset = queryset.filter(task_type=ScheduledTask.TYPE_REPAIR)

    if priority_filter in (
        ScheduledTask.PRIORITY_LOW,
        ScheduledTask.PRIORITY_MEDIUM,
        ScheduledTask.PRIORITY_HIGH,
    ):
        queryset = queryset.filter(priority=priority_filter)

    if search_query:
        queryset = queryset.filter(
            Q(description__icontains=search_query)
            | Q(customer__company_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
            | Q(customer__last_name__icontains=search_query)
            | Q(assigned_to__username__icontains=search_query)
            | Q(assigned_to__first_name__icontains=search_query)
            | Q(assigned_to__last_name__icontains=search_query)
        )

    return queryset.annotate(
        priority_order=_get_task_priority_order(),
    ).order_by('scheduled_date', 'priority_order', 'task_type')


def _get_task_customers_data():
    from customers.models import Customer

    return [
        {
            'id': customer.pk,
            'name': customer.display_name(),
            'label': customer.display_name(),
        }
        for customer in Customer.objects.all().order_by(
            'last_name',
            'first_name',
            'company_name',
        )
    ]


def _get_task_stats(queryset):
    today = timezone.localdate()
    active_statuses = [ScheduledTask.STATUS_PENDING]
    return queryset.aggregate(
        pending=Count('id', filter=Q(status=ScheduledTask.STATUS_PENDING)),
        today=Count('id', filter=Q(scheduled_date=today, status__in=active_statuses)),
        overdue=Count('id', filter=Q(scheduled_date__lt=today, status__in=active_statuses)),
        completed=Count('id', filter=Q(status=ScheduledTask.STATUS_COMPLETED)),
    )


def _redirect_task_dashboard(
    task_filter='pending',
    search_query='',
    open_task_id=None,
    task_type_filter='',
    priority_filter='',
):
    params = _build_task_filter_query(
        task_filter,
        search_query,
        task_type_filter,
        priority_filter,
    )
    if open_task_id:
        params['task'] = open_task_id
    url = reverse('task_scheduling')
    if params:
        return redirect(f"{url}?{urlencode(params)}")
    return redirect('task_scheduling')


def _get_task_detail_dict(task):
    return {
        'id': task.pk,
        'task_type': task.task_type,
        'task_type_label': task.get_task_type_display(),
        'under_work_label': task.get_under_work_label(),
        'products_title': (
            'Προϊόντα προς επισκευή'
            if task.task_type == ScheduledTask.TYPE_REPAIR
            else 'Προϊόντα προς κατασκευή'
        ),
        'customer': task.customer.display_name(),
        'scheduled_date': task.scheduled_date.isoformat(),
        'status': task.status,
        'status_label': task.get_status_display(),
        'description': task.description,
        'items': [
            {
                'id': item.pk,
                'product_code': item.product.code,
                'product_name': item.product.name,
                'product_photo_url': (
                    item.product.photo.url if item.product.photo else ''
                ),
                'quantity': item.quantity,
                'item_status': item.item_status,
                'status_label': item.get_status_label(),
            }
            for item in task.items.all()
        ],
    }


def _get_tasks_detail_data(tasks):
    return [_get_task_detail_dict(task) for task in tasks]


def _update_task_item_statuses(task, post_data):
    valid_statuses = {
        ScheduledTaskItem.STATUS_UNDER_WORK,
        ScheduledTaskItem.STATUS_COMPLETED,
    }
    updated = False
    for item in task.items.all():
        new_status = post_data.get(f'item_{item.pk}')
        if new_status in valid_statuses and item.item_status != new_status:
            item.item_status = new_status
            item.save(update_fields=['item_status'])
            updated = True
    task.refresh_status_from_items()
    return updated


def _get_task_products_data():
    from products.models import FinishedProduct

    return [
        {
            'id': product.pk,
            'code': product.code,
            'name': product.name,
            'label': f'{product.code} - {product.name}',
        }
        for product in FinishedProduct.objects.order_by('name')
    ]


def _get_task_print_filter_label(
    task_filter='pending',
    search_query='',
    task_type_filter='',
    priority_filter='',
):
    filter_labels = {
        'all': 'Όλες',
        'pending': 'Σε εκκρεμότητα',
        'overdue': 'Καθυστερημένες',
        'completed': 'Ολοκληρωμένες',
        'cancelled': 'Ακυρωμένες',
        'today': 'Σημερινές',
        'in_progress': 'Σε εκκρεμότητα',
    }
    type_labels = {
        ScheduledTask.TYPE_CONSTRUCTION: 'Κατασκευές',
        ScheduledTask.TYPE_REPAIR: 'Επισκευές',
    }
    priority_labels = dict(ScheduledTask.PRIORITY_CHOICES)
    labels = [filter_labels.get(task_filter, 'Σε εκκρεμότητα')]
    if task_type_filter in type_labels:
        labels.append(type_labels[task_type_filter])
    if priority_filter in priority_labels:
        labels.append(f'Προτεραιότητα: {priority_labels[priority_filter]}')
    search_query = (search_query or '').strip()
    if search_query:
        labels.append(f'Αναζήτηση: {search_query}')
    return ' · '.join(labels)


def _get_pending_construction_products():
    items = ScheduledTaskItem.objects.filter(
        task__task_type=ScheduledTask.TYPE_CONSTRUCTION,
        task__status=ScheduledTask.STATUS_PENDING,
        item_status=ScheduledTaskItem.STATUS_UNDER_WORK,
    ).select_related(
        'product',
        'task',
        'task__customer',
    ).order_by('product__name', 'task__scheduled_date')

    grouped = {}
    for item in items:
        product_id = item.product_id
        if product_id not in grouped:
            grouped[product_id] = {
                'product': item.product,
                'total_quantity': 0,
                'entries': [],
            }
        grouped[product_id]['total_quantity'] += item.quantity
        grouped[product_id]['entries'].append({
            'task': item.task,
            'quantity': item.quantity,
            'customer': item.task.customer.display_name(),
            'scheduled_date': item.task.scheduled_date,
        })

    return sorted(grouped.values(), key=lambda row: row['product'].name.lower())


def _build_task_forms_from_offer(offer):
    offer_items = list(offer.items.select_related('product').order_by('id'))
    description_parts = [f'Από προσφορά {offer.offer_number}']
    if offer.notes.strip():
        description_parts.append(offer.notes.strip())

    task_form = TaskCreateForm(initial={
        'task_type': ScheduledTask.TYPE_CONSTRUCTION,
        'customer': offer.customer_id,
        'description': '\n'.join(description_parts),
    })

    if offer_items:
        OfferTaskItemFormSet = inlineformset_factory(
            ScheduledTask,
            ScheduledTaskItem,
            form=TaskItemForm,
            formset=BaseTaskItemFormSet,
            extra=len(offer_items),
            can_delete=True,
            min_num=0,
            validate_min=False,
        )
        item_formset = OfferTaskItemFormSet()
        for form, item in zip(item_formset.forms, offer_items):
            form.fields['product'].initial = item.product_id
            form.fields['quantity'].initial = item.quantity
    else:
        item_formset = TaskItemFormSet()

    return task_form, item_formset


@login_required
def construction_products_print(request):
    products = _get_pending_construction_products()
    total_quantity = sum(row['total_quantity'] for row in products)

    return render(request, 'accounts/construction_products_print.html', {
        'products': products,
        'total_products': len(products),
        'total_quantity': total_quantity,
        'printed_at': timezone.localtime(timezone.now()),
    })


@login_required
def construction_products_list(request):
    products = _get_pending_construction_products()
    total_quantity = sum(row['total_quantity'] for row in products)

    return render(request, 'accounts/construction_products_list.html', {
        'products': products,
        'total_products': len(products),
        'total_quantity': total_quantity,
    })


@login_required
def task_scheduling_print(request):
    task_id = request.GET.get('task_id', '').strip()
    if task_id:
        task = get_object_or_404(_get_task_queryset(), pk=task_id)
        tasks = _get_task_queryset().filter(pk=task.pk)
        filter_label = f'Εργασία: {task.display_label()}'
    else:
        task_filter = request.GET.get('filter', 'pending')
        search_query = request.GET.get('q', '').strip()
        task_type_filter = request.GET.get('type', '').strip()
        priority_filter = request.GET.get('priority', '').strip()
        tasks = _filter_tasks(
            _get_task_queryset(),
            task_filter=task_filter,
            search_query=search_query,
            task_type_filter=task_type_filter,
            priority_filter=priority_filter,
        )
        filter_label = _get_task_print_filter_label(
            task_filter,
            search_query,
            task_type_filter,
            priority_filter,
        )

    return render(request, 'accounts/task_scheduling_print.html', {
        'tasks': tasks,
        'total_count': tasks.count(),
        'printed_at': timezone.localtime(timezone.now()),
        'filter_label': filter_label,
        'single_task_print': bool(task_id),
    })


@login_required
def task_scheduling(request):
    base_queryset = _get_task_queryset()
    task_filter = request.GET.get('filter', 'pending')
    search_query = request.GET.get('q', '').strip()
    task_type_filter = request.GET.get('type', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    task_form = TaskCreateForm()
    item_formset = TaskItemFormSet()
    open_task_modal = False
    editing_task = False
    from_offer = None

    if request.method == 'POST':
        task_action = request.POST.get('task_action', 'create')
        task_filter = request.POST.get('redirect_filter', task_filter)
        search_query = request.POST.get('redirect_q', search_query).strip()
        task_type_filter = request.POST.get('redirect_type', task_type_filter).strip()
        priority_filter = request.POST.get('redirect_priority', priority_filter).strip()

        if task_action == 'create':
            task_form = TaskCreateForm(request.POST)
            item_formset = TaskItemFormSet(request.POST)
            if task_form.is_valid() and item_formset.is_valid():
                task = task_form.save(commit=False)
                task.created_by = request.user
                task.save()
                item_formset.instance = task
                item_formset.save()
                messages.success(request, 'Η εργασία καταχωρήθηκε επιτυχώς.')
                return _redirect_task_dashboard(
                    task_filter,
                    search_query,
                    task_type_filter=task_type_filter,
                    priority_filter=priority_filter,
                )
            open_task_modal = True
        elif task_action == 'update':
            task = get_object_or_404(base_queryset, pk=request.POST.get('task_id'))
            task_form = TaskCreateForm(request.POST, instance=task)
            item_formset = TaskItemFormSet(request.POST, instance=task)
            if task_form.is_valid() and item_formset.is_valid():
                task = task_form.save()
                item_formset.save()
                task.refresh_status_from_items()
                messages.success(request, 'Η εργασία ενημερώθηκε επιτυχώς.')
                return _redirect_task_dashboard(
                    task_filter,
                    search_query,
                    task_type_filter=task_type_filter,
                    priority_filter=priority_filter,
                )
            open_task_modal = True
            editing_task = True
        elif task_action == 'update_items':
            task = get_object_or_404(base_queryset, pk=request.POST.get('task_id'))
            _update_task_item_statuses(task, request.POST)
            task.refresh_from_db()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                if task.status == ScheduledTask.STATUS_COMPLETED:
                    message = 'Ολοκληρώθηκε'
                else:
                    message = 'Αποθηκεύτηκε'
                return JsonResponse({
                    'success': True,
                    'task': _get_task_detail_dict(task),
                    'message': message,
                })
            if task.status == ScheduledTask.STATUS_COMPLETED:
                messages.success(request, 'Όλα τα προϊόντα ολοκληρώθηκαν. Η εργασία θεωρείται ολοκληρωμένη.')
            else:
                messages.success(request, 'Οι καταστάσεις των προϊόντων ενημερώθηκαν.')
            return _redirect_task_dashboard(
                task_filter,
                search_query,
                task_type_filter=task_type_filter,
                priority_filter=priority_filter,
            )
        elif task_action == 'set_status':
            task = get_object_or_404(base_queryset, pk=request.POST.get('task_id'))
            new_status = request.POST.get('status')
            valid_statuses = {choice[0] for choice in ScheduledTask.STATUS_CHOICES}
            if new_status in valid_statuses:
                task.status = new_status
                task.save(update_fields=['status', 'updated_at'])
                messages.success(request, 'Η κατάσταση της εργασίας ενημερώθηκε.')
            return _redirect_task_dashboard(
                task_filter,
                search_query,
                task_type_filter=task_type_filter,
                priority_filter=priority_filter,
            )
        elif task_action == 'delete':
            task = get_object_or_404(base_queryset, pk=request.POST.get('task_id'))
            task_title = task.display_label()
            task.delete()
            messages.success(request, f'Η εργασία «{task_title}» διαγράφηκε.')
            return _redirect_task_dashboard(
                task_filter,
                search_query,
                task_type_filter=task_type_filter,
                priority_filter=priority_filter,
            )

    elif request.GET.get('edit'):
        edit_task = get_object_or_404(base_queryset, pk=request.GET.get('edit'))
        task_form = TaskCreateForm(instance=edit_task)
        item_formset = TaskItemFormSet(instance=edit_task)
        open_task_modal = True
        editing_task = True
    elif request.GET.get('from_offer'):
        from_offer = get_object_or_404(
            Offer.objects.select_related('customer').prefetch_related('items__product'),
            pk=request.GET.get('from_offer'),
        )
        task_form, item_formset = _build_task_forms_from_offer(from_offer)
        open_task_modal = True

    tasks = _filter_tasks(
        base_queryset,
        task_filter=task_filter,
        search_query=search_query,
        task_type_filter=task_type_filter,
        priority_filter=priority_filter,
    )
    stats = _get_task_stats(base_queryset)
    open_task_detail_id = request.GET.get('task', '')
    filter_urls = _get_task_filter_urls(
        task_filter,
        search_query,
        task_type_filter,
        priority_filter,
    )
    list_query_string = urlencode(_build_task_filter_query(
        task_filter,
        search_query,
        task_type_filter,
        priority_filter,
    ))

    customers_data = _get_task_customers_data()
    catalog_products = _get_task_products_data()
    tasks_detail_data = _get_tasks_detail_data(tasks)

    return render(request, 'accounts/task_scheduling.html', {
        'task_form': task_form,
        'item_formset': item_formset,
        'tasks': tasks,
        'tasks_detail_data': tasks_detail_data,
        'stats': stats,
        'task_filter': task_filter,
        'search_query': search_query,
        'task_type_filter': task_type_filter,
        'priority_filter': priority_filter,
        'filter_urls': filter_urls,
        'list_query_string': list_query_string,
        'status_choices': ScheduledTask.STATUS_CHOICES,
        'priority_choices': ScheduledTask.PRIORITY_CHOICES,
        'open_task_modal': open_task_modal,
        'editing_task': editing_task,
        'from_offer': from_offer,
        'open_task_detail_id': open_task_detail_id,
        'customers_data': customers_data,
        'catalog_products': catalog_products,
    })

def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func

@superuser_required
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/create_user.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Αντικατάσταση του default error message στα ελληνικά
        form.error_messages = {
            'invalid_login': 'Λάθος όνομα χρήστη ή κωδικός πρόσβασης.',
            'inactive': 'Αυτός ο λογαριασμός είναι ανενεργός.',
        }
        return form

    def form_valid(self, form):
        user = form.get_user()
        # Αν δεν είναι superuser, έλεγξε τη συνδρομή
        if not user.is_superuser:
            subscription = getattr(user, 'subscription', None)
            if not subscription or not subscription.is_active():
                # Δημιουργία νέου form με custom error
                form.add_error(None, 'Η συνδρομή σας έχει λήξει. Παρακαλώ επικοινωνήστε με τον διαχειριστή για ανανέωση.')
                return self.form_invalid(form)
            else:
                days_left = (subscription.expiry_date - date.today()).days
                if days_left < 30:
                    messages.warning(self.request, f'Προσοχή. Η συνδρομή σας θα λήξει σε {days_left} ημέρες. Προχωρήστε σε ανανέωση.')
        return super().form_valid(form)

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'})
        }

@superuser_required
def manage_subscriptions(request):
    users = User.objects.all().order_by('username')
    SubscriptionFormSet = forms.modelform_factory(Subscription, form=SubscriptionForm, fields=['expiry_date'])
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            subscription = Subscription(user=user)
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
    user_forms = []
    for user in users:
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            subscription = None
        form = SubscriptionForm(instance=subscription)
        days_left = None
        if subscription:
            days_left = (subscription.expiry_date - date.today()).days
        user_forms.append((user, form, subscription, days_left))
    return render(request, 'accounts/manage_subscriptions.html', {'user_forms': user_forms})

@superuser_required
def manage_users(request):
    users = User.objects.filter(is_superuser=False).order_by('username')
    message = ''
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        if 'delete_user' in request.POST:
            user.delete()
            return HttpResponseRedirect(request.path_info + '?deleted=1')
        elif 'set_password' in request.POST:
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                message = f'Ο κωδικός του χρήστη {user.username} άλλαξε!'
    if request.GET.get('deleted'):
        message = 'Ο χρήστης διαγράφηκε επιτυχώς.'
    user_forms = []
    for user in users:
        form = SetPasswordForm(user)
        user_forms.append((user, form))
    return render(request, 'accounts/manage_users.html', {'user_forms': user_forms, 'message': message})

@superuser_required
def database_backup(request):
    """Δημιουργεί backup της βάσης δεδομένων"""
    if request.method == 'POST':
        try:
            # Δημιουργία timestamp για το όνομα του αρχείου
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"db_backup_{timestamp}.sqlite3"
            
            # Δημιουργία του backup
            db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            backup_path = os.path.join(settings.BASE_DIR, backup_filename)
            
            # Αντιγραφή του αρχείου βάσης
            shutil.copy2(db_path, backup_path)
            
            # Δημιουργία response για download
            with open(backup_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{backup_filename}"'
            
            # Διαγραφή του προσωρινού αρχείου από τον server
            os.remove(backup_path)
            
            return response
            
        except Exception as e:
            messages.error(request, f'Σφάλμα κατά τη δημιουργία του backup: {str(e)}')
            return redirect('database_management')
    
    return redirect('database_management')

@superuser_required
def database_restore(request):
    """Επαναφέρει τη βάση δεδομένων από backup"""
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('backup_file')
            
            if not uploaded_file:
                messages.error(request, 'Δεν επιλέχθηκε αρχείο backup.')
                return redirect('database_management')
            
            # Έλεγχος αν το αρχείο είναι sqlite3
            if not uploaded_file.name.endswith('.sqlite3'):
                messages.error(request, 'Το αρχείο πρέπει να είναι τύπου .sqlite3')
                return redirect('database_management')
            
            # Δημιουργία backup της τρέχουσας βάσης πριν το restore
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = f"db_before_restore_{timestamp}.sqlite3"
            db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            current_backup_path = os.path.join(settings.BASE_DIR, current_backup)
            
            # Δημιουργία backup της τρέχουσας βάσης
            shutil.copy2(db_path, current_backup_path)
            
            # Αντικατάσταση της τρέχουσας βάσης
            with open(db_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # Διαγραφή του προσωρινού backup
            os.remove(current_backup_path)
            
            messages.success(request, 'Η βάση δεδομένων επαναφέρθηκε επιτυχώς!')
            
        except Exception as e:
            messages.error(request, f'Σφάλμα κατά το restore: {str(e)}')
        
        return redirect('database_management')
    
    return redirect('database_management')

@superuser_required
def database_management(request):
    """Σελίδα διαχείρισης backup/restore"""
    return render(request, 'accounts/database_management.html')

@superuser_required
def manage_client_name(request):
    # Διάβασε το τρέχον όνομα από το settings ή χρησιμοποίησε default
    current_name = getattr(settings, 'CLIENT_NAME', 'DataLab')
    
    if request.method == 'POST':
        new_name = request.POST.get('client_name', '').strip()
        if new_name:
            # Αποθήκευση στο settings (θα χρειαστεί restart για να εφαρμοστεί)
            # Για τώρα θα το αποθηκεύουμε σε ένα αρχείο
            try:
                with open('client_name.txt', 'w', encoding='utf-8') as f:
                    f.write(new_name)
                messages.success(request, f'Το όνομα πελάτη άλλαξε σε: {new_name}')
            except Exception as e:
                messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')
        else:
            messages.error(request, 'Το όνομα πελάτη δεν μπορεί να είναι κενό.')
    
    # Διάβασε το τρέχον όνομα από το αρχείο ή χρησιμοποίησε default
    try:
        with open('client_name.txt', 'r', encoding='utf-8') as f:
            current_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        current_name = 'DataLab'
    
    return render(request, 'accounts/manage_client_name.html', {'current_name': current_name})

@superuser_required
def manage_app_name(request):
    # Διάβασε το τρέχον όνομα από το αρχείο ή χρησιμοποίησε default
    try:
        with open('app_name.txt', 'r', encoding='utf-8') as f:
            current_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        current_name = 'DataLab'
    
    if request.method == 'POST':
        new_name = request.POST.get('app_name', '').strip()
        if new_name:
            try:
                with open('app_name.txt', 'w', encoding='utf-8') as f:
                    f.write(new_name)
                messages.success(request, f'Το όνομα εφαρμογής άλλαξε σε: {new_name}')
            except Exception as e:
                messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')
        else:
            messages.error(request, 'Το όνομα εφαρμογής δεν μπορεί να είναι κενό.')
    
    return render(request, 'accounts/manage_app_name.html', {'current_name': current_name})

@superuser_required
def manage_partner_name(request):
    # Διάβασε το τρέχον όνομα από το αρχείο ή χρησιμοποίησε default
    try:
        with open('partner_name.txt', 'r', encoding='utf-8') as f:
            current_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        current_name = 'DataLab'
    
    if request.method == 'POST':
        new_name = request.POST.get('partner_name', '').strip()
        if new_name:
            try:
                with open('partner_name.txt', 'w', encoding='utf-8') as f:
                    f.write(new_name)
                messages.success(request, f'Το όνομα συνεργάτη άλλαξε σε: {new_name}')
            except Exception as e:
                messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')
        else:
            messages.error(request, 'Το όνομα συνεργάτη δεν μπορεί να είναι κενό.')
    
    return render(request, 'accounts/manage_partner_name.html', {'current_name': current_name})

@superuser_required
def manage_email_settings(request):
    from env_file_utils import load_email_settings, save_email_settings

    email_settings = load_email_settings()

    if request.method == 'POST':
        email_settings['smtp_server'] = request.POST.get('smtp_server', '').strip()
        email_settings['smtp_port'] = request.POST.get('smtp_port', '').strip()
        email_settings['smtp_username'] = request.POST.get('smtp_username', '').strip()
        email_settings['smtp_password'] = request.POST.get('smtp_password', '').strip()
        email_settings['smtp_use_tls'] = request.POST.get('smtp_use_tls') == 'on'
        email_settings['smtp_use_ssl'] = request.POST.get('smtp_use_ssl') == 'on'
        email_settings['from_email'] = request.POST.get('from_email', '').strip()
        email_settings['from_name'] = request.POST.get('from_name', '').strip()

        try:
            save_email_settings(email_settings)
            messages.success(request, 'Οι ρυθμίσεις email αποθηκεύτηκαν επιτυχώς!')
        except Exception as e:
            messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')

    return render(request, 'accounts/manage_email_settings.html', {'email_settings': email_settings})

@superuser_required
def manage_sms_settings(request):
    # Διάβασε τα τρέχοντα settings από το .env αρχείο
    sms_settings = {
        'sms_api_token': '',
        'sms_sender_id': '',
        'sms_enabled': True,  # Default: enabled
    }
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == 'SMS_API_TOKEN' or key == 'SMS_API_KEY':
                            sms_settings['sms_api_token'] = value
                        elif key == 'SMS_SENDER_ID':
                            sms_settings['sms_sender_id'] = value
                        elif key == 'SMS_ENABLED':
                            sms_settings['sms_enabled'] = value.lower() in ('true', '1', 'yes', 'on')
    except FileNotFoundError:
        pass
    
    if request.method == 'POST':
        # Λάβε τα δεδομένα από τη φόρμα
        sms_settings['sms_api_token'] = request.POST.get('sms_api_token', '').strip()
        sms_settings['sms_sender_id'] = request.POST.get('sms_sender_id', '').strip()
        sms_settings['sms_enabled'] = request.POST.get('sms_enabled', 'off') == 'on'
        
        # Αποθήκευση στο .env αρχείο
        try:
            # Διάβασε το υπάρχον .env αρχείο
            existing_content = ""
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            except FileNotFoundError:
                pass
            
            # Αφαίρεσε τα παλιά SMS settings (διατηρώντας όλα τα άλλα)
            lines = existing_content.splitlines()
            filtered_lines = []
            
            for line in lines:
                stripped = line.strip()
                # Skip comment γραμμές που αφορούν SMS Settings
                if stripped.startswith('# SMS Settings'):
                    continue
                # Skip SMS settings
                elif (stripped.startswith('SMS_API_TOKEN') or stripped.startswith('SMS_API_KEY') or 
                      stripped.startswith('SMS_SENDER_ID') or stripped.startswith('SMS_API_URL') or
                      stripped.startswith('SMS_USERNAME') or stripped.startswith('SMS_PASSWORD') or
                      stripped.startswith('SMS_ENABLED')):
                    continue
                # Κρατάμε όλες τις άλλες γραμμές
                else:
                    filtered_lines.append(line)
            
            # Προσθήκη νέων SMS settings
            with open('.env', 'w', encoding='utf-8') as f:
                # Γράψε όλες τις υπάρχουσες γραμμές
                for line in filtered_lines:
                    f.write(line + '\n')
                # Προσθήκη SMS settings στο τέλος
                f.write("# SMS Settings (Liveall.eu API)\n")
                f.write(f"SMS_ENABLED={'true' if sms_settings['sms_enabled'] else 'false'}\n")
                f.write(f"SMS_API_TOKEN={sms_settings['sms_api_token']}\n")
                f.write(f"SMS_SENDER_ID={sms_settings['sms_sender_id']}\n")
            
            messages.success(request, 'Οι ρυθμίσεις SMS αποθηκεύτηκαν επιτυχώς!')
        except Exception as e:
            messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')
    
    return render(request, 'accounts/manage_sms_settings.html', {'sms_settings': sms_settings})


@superuser_required
def manage_customers_module(request):
    """Διαχείριση Module Πελατών - Ενεργοποίηση/Απενεργοποίηση"""
    customers_enabled = True  # Default: enabled
    sms_enabled = True  # Default: enabled
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == 'CUSTOMERS_ENABLED':
                            customers_enabled = value.lower() in ('true', '1', 'yes', 'on')
                        elif key == 'SMS_ENABLED':
                            sms_enabled = value.lower() in ('true', '1', 'yes', 'on')
    except FileNotFoundError:
        pass
    
    if request.method == 'POST':
        customers_enabled = request.POST.get('customers_enabled', 'off') == 'on'
        sms_enabled = request.POST.get('sms_enabled', 'off') == 'on'
        
        # Αποθήκευση στο .env αρχείο
        try:
            # Διάβασε το υπάρχον .env αρχείο
            existing_content = ""
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            except FileNotFoundError:
                pass
            
            # Αφαίρεσε τα παλιά settings (διατηρώντας όλα τα άλλα)
            lines = existing_content.splitlines()
            filtered_lines = []
            in_customers_section = False
            in_sms_section = False
            
            for line in lines:
                stripped = line.strip()
                # Εντοπίζουμε το Customers Module Settings section
                if stripped.startswith('# Customers Module Settings'):
                    in_customers_section = True
                    in_sms_section = False
                    continue
                # Εντοπίζουμε το SMS Settings section
                elif stripped.startswith('# SMS Settings'):
                    in_sms_section = True
                    in_customers_section = False
                    continue
                # Αν είμαστε σε άλλο section, σταματάμε να είμαστε σε οποιοδήποτε section
                elif stripped.startswith('#'):
                    in_customers_section = False
                    in_sms_section = False
                
                # Skip CUSTOMERS_ENABLED
                if stripped.startswith('CUSTOMERS_ENABLED'):
                    continue
                # Skip SMS_ENABLED αν είναι μέσα στο Customers Module Settings section
                # ή αν είναι μέσα στο SMS Settings section (για να αποφύγουμε διπλότυπα)
                elif stripped.startswith('SMS_ENABLED') and (in_customers_section or in_sms_section):
                    continue
                # Κρατάμε όλες τις άλλες γραμμές
                else:
                    filtered_lines.append(line)
            
            # Προσθήκη νέων settings
            with open('.env', 'w', encoding='utf-8') as f:
                # Γράψε όλες τις υπάρχουσες γραμμές
                for line in filtered_lines:
                    f.write(line + '\n')
                # Προσθήκη Customers Module Settings στο τέλος
                f.write("# Customers Module Settings\n")
                f.write(f"CUSTOMERS_ENABLED={'true' if customers_enabled else 'false'}\n")
                f.write(f"SMS_ENABLED={'true' if sms_enabled else 'false'}\n")
            
            messages.success(request, 'Οι ρυθμίσεις Module Πελατών και SMS αποθηκεύτηκαν επιτυχώς!')
        except Exception as e:
            messages.error(request, f'Σφάλμα κατά την αποθήκευση: {str(e)}')
    
    return render(request, 'accounts/manage_customers_module.html', {
        'customers_enabled': customers_enabled,
        'sms_enabled': sms_enabled
    })


@superuser_required
def send_sms_view(request):
    """View for sending SMS"""
    if not send_sms:
        messages.error(request, 'Το SMS module δεν είναι διαθέσιμο.')
        return redirect('dashboard')
    
    balance_info = None
    balance_error = None
    
    # Try to get account balance
    try:
        success, msg, info = check_account_balance('30')  # Greece prefix
        if success and info:
            balance_info = info
        else:
            balance_error = msg
    except:
        pass
    
    if request.method == 'POST':
        destination = request.POST.get('destination', '').strip()
        message = request.POST.get('message', '').strip()
        sender_id_input = request.POST.get('sender_id', '').strip()
        
        # Get default sender_id from settings if not provided
        sender_id = sender_id_input if sender_id_input else None
        
        if not destination:
            messages.error(request, 'Παρακαλώ εισάγετε αριθμό τηλεφώνου.')
        elif not message:
            messages.error(request, 'Παρακαλώ εισάγετε μήνυμα.')
        else:
            success, msg, sms_id = send_sms(destination, message, sender_id)
            if success:
                messages.success(request, msg)
                if sms_id:
                    messages.info(request, f'SMS ID: {sms_id}')
            else:
                # Check if it's a sender ID error and provide helpful message
                if 'Sender ID' in msg or 'sender' in msg.lower():
                    messages.error(request, msg)
                    messages.warning(request, 'Συμβουλή: Βεβαιωθείτε ότι το Sender ID είναι εγκεκριμένο από τον πάροχο SMS. Ελέγξτε τις ρυθμίσεις SMS.')
                else:
                    messages.error(request, msg)
            
            return redirect('send_sms')
    
    return render(request, 'accounts/send_sms.html', {
        'balance_info': balance_info,
        'balance_error': balance_error
    })


@superuser_required
def send_bulk_sms_view(request):
    """View for sending bulk SMS"""
    if not send_bulk_sms:
        messages.error(request, 'Το SMS module δεν είναι διαθέσιμο.')
        return redirect('dashboard')
    
    balance_info = None
    balance_error = None
    
    # Try to get account balance
    try:
        success, msg, info = check_account_balance('30')
        if success and info:
            balance_info = info
        else:
            balance_error = msg
    except:
        pass
    
    customers = Customer.objects.filter(phone__isnull=False).exclude(phone='').order_by('first_name', 'last_name')
    
    if request.method == 'POST':
        destinations = request.POST.getlist('destinations')
        message = request.POST.get('message', '').strip()
        sender_id = request.POST.get('sender_id', '').strip() or None
        
        if not destinations:
            messages.error(request, 'Παρακαλώ επιλέξτε τουλάχιστον έναν παραλήπτη.')
        elif not message:
            messages.error(request, 'Παρακαλώ εισάγετε μήνυμα.')
        else:
            # Get phone numbers from customer IDs
            phone_numbers = []
            for customer_id in destinations:
                try:
                    customer = Customer.objects.get(pk=customer_id)
                    if customer.get_primary_phone():
                        phone_numbers.append(customer.get_primary_phone())
                except Customer.DoesNotExist:
                    pass
            
            if phone_numbers:
                success, msg, sms_ids = send_bulk_sms(phone_numbers, message, sender_id)
                if success:
                    messages.success(request, msg)
                    if sms_ids:
                        messages.info(request, f'Στάλθηκαν {len(sms_ids)} SMS. IDs: {", ".join(sms_ids[:5])}{"..." if len(sms_ids) > 5 else ""}')
                else:
                    # Check if it's a sender ID error and provide helpful message
                    if 'Sender ID' in msg or 'sender' in msg.lower():
                        messages.error(request, msg)
                        messages.warning(request, 'Συμβουλή: Βεβαιωθείτε ότι το Sender ID είναι εγκεκριμένο από τον πάροχο SMS. Ελέγξτε τις ρυθμίσεις SMS.')
                    else:
                        messages.error(request, msg)
            else:
                messages.error(request, 'Δεν βρέθηκαν έγκυροι αριθμοί τηλεφώνου.')
            
            return redirect('send_bulk_sms')
    
    return render(request, 'accounts/send_bulk_sms.html', {
        'customers': customers,
        'balance_info': balance_info,
        'balance_error': balance_error
    })


@superuser_required
def check_sms_balance(request):
    """AJAX view to check SMS account balance"""
    if not check_account_balance:
        return JsonResponse({
            'success': False,
            'message': 'Το SMS module δεν είναι διαθέσιμο.'
        })
    
    country_prefix = request.GET.get('country', '30')
    success, msg, balance_info = check_account_balance(country_prefix)
    
    if success:
        return JsonResponse({
            'success': True,
            'message': msg,
            'balance': balance_info
        })
    else:
        return JsonResponse({
            'success': False,
            'message': msg
        })


@superuser_required
def get_sms_history_view(request):
    """AJAX view to get SMS history"""
    if not get_sms_history:
        return JsonResponse({
            'success': False,
            'message': 'Το SMS module δεν είναι διαθέσιμο.'
        })
    
    try:
        from datetime import datetime, timedelta
        
        days = int(request.GET.get('days', 7))
        days = min(days, 30)  # Limit to 30 days max
        
        history_list = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            success, msg, history = get_sms_history(date_str)
            if success and history:
                history_list.extend(history)
        
        # Sort by SMS ID (newest first)
        if history_list:
            try:
                history_list.sort(key=lambda x: int(x.get('sms_id', 0)), reverse=True)
            except:
                pass
        
        # Limit results
        limit = int(request.GET.get('limit', 50))
        history_list = history_list[:limit]
        
        return JsonResponse({
            'success': True,
            'message': f'Βρέθηκαν {len(history_list)} καταγραφές',
            'history': history_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Σφάλμα: {str(e)}'
        })


@superuser_required
def sms_dashboard(request):
    """SMS Dashboard with balance, send SMS, and reports"""
    balance_info = None
    balance_error = None
    
    # Try to get account balance
    if check_account_balance:
        try:
            success, msg, info = check_account_balance('30')  # Greece prefix
            if success and info:
                balance_info = info
            else:
                balance_error = msg
        except Exception as e:
            balance_error = f"Σφάλμα: {str(e)}"
    
    # Get recent SMS history (last 7 days)
    recent_history = []
    history_error = None
    if get_sms_history:
        try:
            from datetime import datetime, timedelta
            today = datetime.now()
            # Get history for last 7 days
            history_list = []
            for i in range(7):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y%m%d')
                success, msg, history = get_sms_history(date_str)
                if success and history:
                    history_list.extend(history)
            
            # Sort by SMS ID (newest first) and limit to 10
            if history_list:
                try:
                    history_list.sort(key=lambda x: int(x.get('sms_id', 0)), reverse=True)
                except:
                    pass
                recent_history = history_list[:10]
        except Exception as e:
            history_error = f"Σφάλμα ανάκτησης ιστορικού: {str(e)}"
    
    return render(request, 'accounts/sms_dashboard.html', {
        'balance_info': balance_info,
        'balance_error': balance_error,
        'recent_history': recent_history,
        'history_error': history_error
    })
