from django import template

register = template.Library()

MONTHS_GR = [
    '', 'Ιανουαρίου', 'Φεβρουαρίου', 'Μαρτίου', 'Απριλίου', 'Μαΐου', 'Ιουνίου',
    'Ιουλίου', 'Αυγούστου', 'Σεπτεμβρίου', 'Οκτωβρίου', 'Νοεμβρίου', 'Δεκεμβρίου'
]

@register.filter
def greek_date(value):
    """Επιστρέφει ημερομηνία σε μορφή '17 Ιουνίου 2025'"""
    if not value:
        return ''
    try:
        day = value.day
        month = MONTHS_GR[value.month]
        year = value.year
        return f"{day} {month} {year}"
    except Exception:
        return value 