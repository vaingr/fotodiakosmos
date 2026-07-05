import smtplib
from email.header import Header
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

from env_file_utils import load_email_settings


def get_email_settings():
    return load_email_settings()


def is_email_configured():
    settings = get_email_settings()
    return bool(
        settings['smtp_server']
        and settings['from_email']
        and settings['smtp_port']
    )


def _get_client_name():
    client_name_path = Path('client_name.txt')
    if client_name_path.exists():
        name = client_name_path.read_text(encoding='utf-8').strip()
        if name:
            return name
    return ''


def _get_from_domain(from_email):
    if '@' in from_email:
        return from_email.split('@', 1)[1]
    return 'localhost'


def _build_html_body(body_plain, settings):
    sender_name = settings.get('from_name') or _get_client_name() or 'Η εταιρεία μας'
    paragraphs = []
    for line in body_plain.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('Με εκτίμηση'):
            paragraphs.append(
                f'<p style="margin:24px 0 0 0;">Με εκτίμηση,<br><strong>{sender_name}</strong></p>'
            )
        else:
            paragraphs.append(f'<p style="margin:0 0 12px 0;">{stripped}</p>')

    body_content = ''.join(paragraphs)

    return f"""<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Αποθήκη Έτοιμων Προϊόντων</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;color:#222;line-height:1.6;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f5f5;padding:24px 0;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:24px;">
                    <tr>
                        <td style="font-size:16px;">
                            {body_content}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def send_email_with_attachment(
    to_email,
    subject,
    body_plain,
    attachment_bytes,
    filename,
):
    settings = get_email_settings()

    if not settings['smtp_server']:
        return False, 'Ο SMTP server δεν έχει ρυθμιστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις email.'
    if not settings['from_email']:
        return False, 'Η διεύθυνση αποστολέα δεν έχει ρυθμιστεί. Παρακαλώ ελέγξτε τις ρυθμίσεις email.'
    if not to_email:
        return False, 'Δεν υπάρχει έγκυρη διεύθυνση email παραλήπτη.'

    from_email = settings['from_email'].strip()
    from_name = (settings.get('from_name') or _get_client_name() or '').strip()
    smtp_username = settings.get('smtp_username', '').strip()
    from_domain = _get_from_domain(from_email)

    message = EmailMessage()
    message['Date'] = formatdate(localtime=True)
    message['Message-ID'] = make_msgid(domain=from_domain)
    message['From'] = formataddr((from_name, from_email)) if from_name else from_email
    message['To'] = to_email
    message['Subject'] = str(Header(subject, 'utf-8'))
    message['Reply-To'] = from_email
    message['MIME-Version'] = '1.0'
    message['X-Priority'] = '3'
    message['Importance'] = 'Normal'

    if smtp_username and '@' in smtp_username and smtp_username.lower() != from_email.lower():
        message['Sender'] = smtp_username

    message.set_content(body_plain, subtype='plain', charset='utf-8')
    message.add_alternative(
        _build_html_body(body_plain, settings),
        subtype='html',
        charset='utf-8',
    )
    message.add_attachment(
        attachment_bytes,
        maintype='application',
        subtype='pdf',
        filename=filename,
    )

    envelope_from = smtp_username if '@' in smtp_username else from_email

    try:
        port = int(settings['smtp_port'] or 587)
        if settings['smtp_use_ssl']:
            server = smtplib.SMTP_SSL(settings['smtp_server'], port, timeout=30)
        else:
            server = smtplib.SMTP(settings['smtp_server'], port, timeout=30)
            if settings['smtp_use_tls']:
                server.starttls()

        if smtp_username:
            server.login(smtp_username, settings['smtp_password'])

        server.sendmail(envelope_from, [to_email], message.as_bytes())
        server.quit()
        return True, 'Το email στάλθηκε επιτυχώς.'
    except smtplib.SMTPAuthenticationError:
        return False, 'Σφάλμα ταυτοποίησης SMTP. Ελέγξτε username/password.'
    except smtplib.SMTPException as exc:
        return False, f'Σφάλμα SMTP: {exc}'
    except OSError as exc:
        return False, 'Σφάλμα σύνδεσης με τον mail server: {0}'.format(exc)
    except Exception as exc:
        return False, 'Απρόσμενο σφάλμα κατά την αποστολή email: {0}'.format(exc)
