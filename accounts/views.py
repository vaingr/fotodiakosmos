from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Subscription
from django import forms
from datetime import date
from django.http import HttpResponseRedirect
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
                    if customer.phone:
                        phone_numbers.append(customer.phone)
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
