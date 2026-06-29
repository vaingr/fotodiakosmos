import os
import requests
from django.contrib import messages

def get_sms_settings():
    """Διαβάζει τις ρυθμίσεις SMS από το .env αρχείο"""
    sms_settings = {
        'sms_api_url': '',
        'sms_api_key': '',
        'sms_sender_id': '',
        'sms_username': '',
        'sms_password': ''
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
                        if key in sms_settings:
                            sms_settings[key] = value
    except FileNotFoundError:
        pass
    
    return sms_settings

def send_sms(phone_number, message):
    """
    Στέλνει SMS μέσω HTTP API
    
    Args:
        phone_number: Ο αριθμός τηλεφώνου του παραλήπτη
        message: Το μήνυμα που θα σταλεί
    
    Returns:
        tuple: (success: bool, response_message: str)
    """
    sms_settings = get_sms_settings()
    
    # Έλεγχος αν υπάρχουν οι βασικές ρυθμίσεις
    if not sms_settings.get('sms_api_url'):
        return False, 'Το SMS API URL δεν έχει ρυθμιστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS.'
    
    if not sms_settings.get('sms_api_key'):
        return False, 'Το SMS API Key δεν έχει ρυθμιστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS.'
    
    if not sms_settings.get('sms_sender_id'):
        return False, 'Το SMS Sender ID δεν έχει ρυθμιστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS.'
    
    # Καθαρισμός του αριθμού τηλεφώνου (αφαίρεση κενών, χαρακτήρων)
    phone_number = ''.join(filter(str.isdigit, phone_number))
    
    if not phone_number:
        return False, 'Ο αριθμός τηλεφώνου δεν είναι έγκυρος.'
    
    # Προετοιμασία των headers
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': sms_settings['sms_api_key']
    }
    
    # Προετοιμασία των δεδομένων
    data = {
        'to': phone_number,
        'message': message,
        'from': sms_settings['sms_sender_id']
    }
    
    # Προσθήκη authentication αν υπάρχει
    auth = None
    if sms_settings.get('sms_username') and sms_settings.get('sms_password'):
        from requests.auth import HTTPBasicAuth
        auth = HTTPBasicAuth(sms_settings['sms_username'], sms_settings['sms_password'])
    
    try:
        # Αποστολή του SMS
        response = requests.post(
            sms_settings['sms_api_url'],
            json=data,
            headers=headers,
            auth=auth,
            timeout=30
        )
        
        # Έλεγχος της απάντησης
        if response.status_code == 200 or response.status_code == 201:
            return True, 'Το SMS στάλθηκε επιτυχώς!'
        else:
            return False, f'Σφάλμα κατά την αποστολή SMS: {response.status_code} - {response.text}'
    
    except requests.exceptions.Timeout:
        return False, 'Το αίτημα έληξε (timeout). Παρακαλώ δοκιμάστε ξανά.'
    except requests.exceptions.ConnectionError:
        return False, 'Σφάλμα σύνδεσης με το SMS API. Παρακαλώ ελέγξτε τη σύνδεσή σας.'
    except requests.exceptions.RequestException as e:
        return False, f'Σφάλμα κατά την αποστολή SMS: {str(e)}'
    except Exception as e:
        return False, f'Απρόσμενο σφάλμα: {str(e)}'


