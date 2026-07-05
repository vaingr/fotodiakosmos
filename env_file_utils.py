from pathlib import Path


EMAIL_ENV_KEY_MAP = {
    'SMTP_SERVER': 'smtp_server',
    'SMTP_PORT': 'smtp_port',
    'SMTP_USERNAME': 'smtp_username',
    'SMTP_PASSWORD': 'smtp_password',
    'SMTP_USE_TLS': 'smtp_use_tls',
    'SMTP_USE_SSL': 'smtp_use_ssl',
    'FROM_EMAIL': 'from_email',
    'FROM_NAME': 'from_name',
}

EMAIL_ENV_LINES = tuple(EMAIL_ENV_KEY_MAP.keys())


def get_env_path():
    try:
        from django.conf import settings
        return Path(settings.BASE_DIR) / '.env'
    except Exception:
        return Path(__file__).resolve().parent / '.env'


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('true', '1', 'yes', 'on')


def default_email_settings():
    return {
        'smtp_server': '',
        'smtp_port': '587',
        'smtp_username': '',
        'smtp_password': '',
        'smtp_use_tls': True,
        'smtp_use_ssl': False,
        'from_email': '',
        'from_name': '',
    }


def load_email_settings():
    settings = default_email_settings()
    env_path = get_env_path()

    if not env_path.exists():
        return settings

    with env_path.open('r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            dict_key = EMAIL_ENV_KEY_MAP.get(key)
            if not dict_key:
                continue
            if dict_key in ('smtp_use_tls', 'smtp_use_ssl'):
                settings[dict_key] = _parse_bool(value)
            else:
                settings[dict_key] = value

    return settings


def save_email_settings(email_settings):
    env_path = get_env_path()
    existing_lines = []

    if env_path.exists():
        existing_lines = env_path.read_text(encoding='utf-8').splitlines()

    filtered_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith('# Email Settings'):
            continue
        if any(stripped.startswith(f'{env_key}=') for env_key in EMAIL_ENV_LINES):
            continue
        filtered_lines.append(line)

    while filtered_lines and not filtered_lines[-1].strip():
        filtered_lines.pop()

    with env_path.open('w', encoding='utf-8') as env_file:
        for line in filtered_lines:
            env_file.write(line + '\n')
        if filtered_lines:
            env_file.write('\n')
        env_file.write('# Email Settings\n')
        env_file.write(f"SMTP_SERVER={email_settings['smtp_server']}\n")
        env_file.write(f"SMTP_PORT={email_settings['smtp_port']}\n")
        env_file.write(f"SMTP_USERNAME={email_settings['smtp_username']}\n")
        env_file.write(f"SMTP_PASSWORD={email_settings['smtp_password']}\n")
        env_file.write(f"SMTP_USE_TLS={str(email_settings['smtp_use_tls']).lower()}\n")
        env_file.write(f"SMTP_USE_SSL={str(email_settings['smtp_use_ssl']).lower()}\n")
        env_file.write(f"FROM_EMAIL={email_settings['from_email']}\n")
        env_file.write(f"FROM_NAME={email_settings['from_name']}\n")
