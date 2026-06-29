"""
SMS Utility Module for Liveall.eu API
Documentation: https://docs.liveall.eu/en/v20/httpapi/xwwwformurlencoded/smssendout.html
"""
import os
import requests
from urllib.parse import urlencode
from typing import Dict, Optional, List, Tuple


def get_sms_settings() -> Dict[str, str]:
    """Get SMS settings from .env file"""
    settings = {
        'api_token': '',
        'sender_id': '',
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
                        if key == 'SMS_API_KEY' or key == 'SMS_API_TOKEN':
                            settings['api_token'] = value
                        elif key == 'SMS_SENDER_ID':
                            settings['sender_id'] = value
    except FileNotFoundError:
        pass
    
    return settings


def send_sms(
    destination: str,
    message: str,
    sender_id: Optional[str] = None,
    sendon: Optional[int] = None,
    user_ref_id: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Send SMS via Liveall.eu API
    
    Args:
        destination: Phone number (without leading zeros or +), e.g., 306912345678
        message: SMS text
        sender_id: Optional sender ID (overrides settings)
        sendon: Optional unix timestamp for scheduled sending
        user_ref_id: Optional custom reference ID for scheduled messages
    
    Returns:
        Tuple of (success: bool, message: str, sms_id: Optional[str])
    """
    settings = get_sms_settings()
    
    if not settings['api_token']:
        return False, "Το API token δεν έχει οριστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS.", None
    
    if not settings['sender_id'] and not sender_id:
        return False, "Το Sender ID δεν έχει οριστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS.", None
    
    # Clean destination number (remove +, spaces, leading zeros)
    destination = destination.replace('+', '').replace(' ', '').replace('-', '').strip()
    if destination.startswith('00'):
        destination = destination[2:]
    if destination.startswith('0'):
        destination = '30' + destination[1:]  # Default to Greece if starts with 0
    
    # Prepare data
    data = {
        'apitoken': settings['api_token'],
        'destination': destination,
        'senderid': sender_id or settings['sender_id'],
        'message': message
    }
    
    if sendon:
        data['sendon'] = str(sendon)
    if user_ref_id:
        data['user_ref_id'] = user_ref_id
    
    try:
        response = requests.post(
            'https://sms.liveall.eu/apiext/Sendout/SendSMS',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.text.strip()
        
        if result.startswith('OK'):
            # Extract SMS ID(s)
            if 'ID:' in result:
                # Single SMS: "OK ID:123456789"
                sms_id = result.split('ID:')[1].strip()
                return True, "Το SMS στάλθηκε επιτυχώς!", sms_id
            else:
                # Multiple SMS: "OK ID:123456787|OK ID:123456788|OK ID:123456789"
                sms_ids = [id_part.split('ID:')[1] for id_part in result.split('|') if 'ID:' in id_part]
                return True, f"Στάλθηκαν {len(sms_ids)} SMS επιτυχώς!", ','.join(sms_ids)
        elif result.startswith('Error:'):
            error_msg = result.replace('Error:', '').strip()
            # Translate common error codes to Greek
            if '64' in error_msg and 'sender' in error_msg.lower():
                error_msg = "Το Sender ID δεν είναι στη λίστα των επιτρεπόμενων. Παρακαλώ ελέγξτε τις ρυθμίσεις SMS ή χρησιμοποιήστε ένα εγκεκριμένο Sender ID."
            elif '65' in error_msg:
                error_msg = "Το Sender ID είναι κενό. Παρακαλώ ορίστε ένα Sender ID στις ρυθμίσεις SMS."
            return False, f"Σφάλμα: {error_msg}", None
        else:
            return False, f"Απρόσμενη απάντηση: {result}", None
            
    except requests.exceptions.RequestException as e:
        return False, f"Σφάλμα σύνδεσης: {str(e)}", None
    except Exception as e:
        return False, f"Απρόσμενο σφάλμα: {str(e)}", None


def send_bulk_sms(
    destinations: List[str],
    message: str,
    sender_id: Optional[str] = None
) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Send SMS to multiple destinations
    
    Args:
        destinations: List of phone numbers
        message: SMS text
        sender_id: Optional sender ID
    
    Returns:
        Tuple of (success: bool, message: str, sms_ids: Optional[List[str]])
    """
    if not destinations:
        return False, "Δεν δόθηκαν προορισμοί", None
    
    # Clean and format destinations
    cleaned_destinations = []
    for dest in destinations:
        dest = dest.replace('+', '').replace(' ', '').replace('-', '').strip()
        if dest.startswith('00'):
            dest = dest[2:]
        if dest.startswith('0'):
            dest = '30' + dest[1:]  # Default to Greece
        cleaned_destinations.append(dest)
    
    # Join destinations with semicolon (recommended delimiter)
    destination_str = ';'.join(cleaned_destinations)
    
    success, msg, sms_id_str = send_sms(destination_str, message, sender_id)
    
    if success and sms_id_str:
        sms_ids = sms_id_str.split(',')
        return True, msg, sms_ids
    
    return success, msg, None


def check_sms_status(sms_ids: List[str]) -> Tuple[bool, str, Optional[List[Dict]]]:
    """
    Check the status of submitted SMS messages
    
    Args:
        sms_ids: List of SMS IDs to check
    
    Returns:
        Tuple of (success: bool, message: str, statuses: Optional[List[Dict]])
    """
    settings = get_sms_settings()
    
    if not settings['api_token']:
        return False, "Το API token δεν έχει οριστεί.", None
    
    if not sms_ids:
        return False, "Δεν δόθηκαν SMS IDs", None
    
    # Join SMS IDs with comma
    sms_ids_str = ','.join([str(sid) for sid in sms_ids])
    
    try:
        response = requests.post(
            'https://sms.liveall.eu/apiext/Sendout/GetSMSStatus',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'apitoken': settings['api_token'],
                'smsids': sms_ids_str
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.text.strip()
        
        if result.startswith('Error:'):
            error_msg = result.replace('Error:', '').strip()
            return False, f"Σφάλμα: {error_msg}", None
        
        # Parse results
        statuses = []
        for status_line in result.split('|'):
            if ':' in status_line:
                parts = status_line.split(':')
                if len(parts) >= 8:
                    statuses.append({
                        'sms_id': parts[0],
                        'submitted_on': parts[1],
                        'last_status_datetime': parts[2],
                        'destination': parts[3],
                        'status_number': parts[4],
                        'status_text': parts[5],
                        'quantity': parts[6],
                        'charge': parts[7]
                    })
        
        return True, "Επιτυχής ανάκτηση κατάστασης", statuses
        
    except requests.exceptions.RequestException as e:
        return False, f"Σφάλμα σύνδεσης: {str(e)}", None
    except Exception as e:
        return False, f"Απρόσμενο σφάλμα: {str(e)}", None


def check_account_balance(country_prefix: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check account balance
    
    Args:
        country_prefix: Optional country code (e.g., '30' for Greece)
    
    Returns:
        Tuple of (success: bool, message: str, balance_info: Optional[Dict])
    """
    settings = get_sms_settings()
    
    if not settings['api_token']:
        return False, "Το API token δεν έχει οριστεί.", None
    
    data = {'apitoken': settings['api_token']}
    if country_prefix:
        data['countryprefix'] = country_prefix
    
    try:
        response = requests.post(
            'https://sms.liveall.eu/apiext/Sendout/GetAccountBalance',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.text.strip()
        
        if result.startswith('Error:'):
            error_msg = result.replace('Error:', '').strip()
            return False, f"Σφάλμα: {error_msg}", None
        
        if result.startswith('OK'):
            # Parse: "OK Balance:169.64|SmsRemainCount:4475|LCSmsRemainCount:5317"
            balance_info = {}
            parts = result.replace('OK ', '').split('|')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    try:
                        balance_info[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        balance_info[key] = value
            
            return True, "Επιτυχής ανάκτηση υπολοίπου", balance_info
        
        return False, f"Απρόσμενη απάντηση: {result}", None
        
    except requests.exceptions.RequestException as e:
        return False, f"Σφάλμα σύνδεσης: {str(e)}", None
    except Exception as e:
        return False, f"Απρόσμενο σφάλμα: {str(e)}", None


def get_sms_history(
    submit_date: str,
    timezone_offset: Optional[int] = None,
    senderid: Optional[str] = None,
    destination: Optional[str] = None,
    sms_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    gt_sms_id: Optional[int] = None
) -> Tuple[bool, str, Optional[List[Dict]]]:
    """
    Extract message log for a specific date
    
    Args:
        submit_date: Date in format yyyyMMdd (e.g., '20210524')
        timezone_offset: Optional timezone offset from UTC
        senderid: Optional filter by sender ID
        destination: Optional filter by destination
        sms_id: Optional filter by SMS ID
        batch_id: Optional filter by batch ID
        gt_sms_id: Optional filter for SMS IDs greater than this value
    
    Returns:
        Tuple of (success: bool, message: str, history: Optional[List[Dict]])
    """
    settings = get_sms_settings()
    
    if not settings['api_token']:
        return False, "Το API token δεν έχει οριστεί.", None
    
    data = {
        'apitoken': settings['api_token'],
        'submit_date': submit_date
    }
    
    if timezone_offset is not None:
        data['timezone_offset'] = str(timezone_offset)
    if senderid:
        data['senderid'] = senderid
    if destination:
        data['destination'] = destination
    if sms_id:
        data['sms_id'] = str(sms_id)
    if batch_id:
        data['batch_id'] = str(batch_id)
    if gt_sms_id:
        data['gt_sms_id'] = str(gt_sms_id)
    
    try:
        response = requests.post(
            'https://sms.liveall.eu/apiext/Sendout/GetSMSHistory',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.text.strip()
        
        if result.startswith('Error:'):
            error_msg = result.replace('Error:', '').strip()
            return False, f"Σφάλμα: {error_msg}", None
        
        if not result:
            return True, "Δεν βρέθηκαν καταγραφές", []
        
        # Parse history lines
        history = []
        for line in result.split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 8:
                    history.append({
                        'sms_id': parts[0],
                        'batch_id': parts[1],
                        'sender_id': parts[2],
                        'destination': parts[3],
                        'last_status_datetime': parts[4],
                        'status': parts[5],
                        'quantity': parts[6],
                        'charge': parts[7]
                    })
        
        return True, f"Βρέθηκαν {len(history)} καταγραφές", history
        
    except requests.exceptions.RequestException as e:
        return False, f"Σφάλμα σύνδεσης: {str(e)}", None
    except Exception as e:
        return False, f"Απρόσμενο σφάλμα: {str(e)}", None


