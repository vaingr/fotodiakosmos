def client_name(request):
    """Context processor για το όνομα πελάτη"""
    try:
        with open('client_name.txt', 'r', encoding='utf-8') as f:
            client_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        client_name = 'DataLab'
    
    return {'client_name': client_name}

def app_name(request):
    """Context processor για το όνομα εφαρμογής"""
    try:
        with open('app_name.txt', 'r', encoding='utf-8') as f:
            app_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        app_name = 'DataLab'
    
    return {'app_name': app_name}

def partner_name(request):
    """Context processor για το όνομα συνεργάτη"""
    try:
        with open('partner_name.txt', 'r', encoding='utf-8') as f:
            partner_name = f.read().strip() or 'DataLab'
    except FileNotFoundError:
        partner_name = 'DataLab'
    
    return {'partner_name': partner_name}

def sms_enabled(request):
    """Context processor για έλεγχο αν το SMS είναι ενεργοποιημένο"""
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
                        if key == 'SMS_ENABLED':
                            sms_enabled = value.lower() in ('true', '1', 'yes', 'on')
                            break
    except FileNotFoundError:
        pass
    
    return {'sms_enabled': sms_enabled}

def customers_enabled(request):
    """Context processor για έλεγχο αν το Module Πελατών είναι ενεργοποιημένο"""
    customers_enabled = True  # Default: enabled
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
                            break
    except FileNotFoundError:
        pass
    
    return {'customers_enabled': customers_enabled} 