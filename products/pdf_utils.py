from io import BytesIO
from pathlib import Path

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_CANDIDATES = [
    Path('C:/Windows/Fonts/arial.ttf'),
    Path('C:/Windows/Fonts/arialuni.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'),
]

FONT_NAME = 'WarehousePdfFont'
_font_registered = False


def _register_font():
    global _font_registered
    if _font_registered:
        return FONT_NAME if FONT_NAME in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
            _font_registered = True
            return FONT_NAME

    _font_registered = True
    return 'Helvetica'


def _get_client_name():
    client_name_path = Path('client_name.txt')
    if client_name_path.exists():
        name = client_name_path.read_text(encoding='utf-8').strip()
        if name:
            return name
    return ''


def _get_product_image_cell(item, cell_style):
    thumb_size = 1.35 * cm
    if item.product.photo and item.product.photo.name:
        try:
            photo_path = item.product.photo.path
            if Path(photo_path).exists():
                image = Image(photo_path, width=thumb_size, height=thumb_size, kind='proportional')
                image.hAlign = 'CENTER'
                return image
        except (ValueError, OSError):
            pass
    return Paragraph('—', cell_style)


def generate_warehouse_pdf(warehouse_items):
    font_name = _register_font()
    buffer = BytesIO()
    printed_at = timezone.localtime(timezone.now())

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    title_style = ParagraphStyle(
        'Title',
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        'Meta',
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#444444'),
    )
    cell_style = ParagraphStyle(
        'Cell',
        fontName=font_name,
        fontSize=9,
        leading=12,
    )

    story = [
        Paragraph('Αποθήκη Έτοιμων Προϊόντων', title_style),
    ]

    client_name = _get_client_name()
    if client_name:
        story.append(Paragraph(f'<b>{client_name}</b>', meta_style))

    story.extend([
        Paragraph(f'Ημερομηνία εκτύπωσης: {printed_at.strftime("%d/%m/%Y %H:%M")}', meta_style),
        Paragraph(f'Σύνολο προϊόντων: {warehouse_items.count()}', meta_style),
        Spacer(1, 0.5 * cm),
    ])

    table_data = [[
        Paragraph('<b>#</b>', cell_style),
        Paragraph('<b>Φωτο</b>', cell_style),
        Paragraph('<b>Κωδικός</b>', cell_style),
        Paragraph('<b>Όνομα</b>', cell_style),
        Paragraph('<b>Ποσότητα</b>', cell_style),
    ]]

    for index, item in enumerate(warehouse_items, start=1):
        table_data.append([
            Paragraph(str(index), cell_style),
            _get_product_image_cell(item, cell_style),
            Paragraph(item.product.code, cell_style),
            Paragraph(item.product.name, cell_style),
            Paragraph(str(item.quantity), cell_style),
        ])

    if warehouse_items.count() == 0:
        table_data.append([
            Paragraph('Δεν υπάρχουν προϊόντα στην αποθήκη.', cell_style),
            '', '', '', '',
        ])

    table = Table(
        table_data,
        colWidths=[0.8 * cm, 1.6 * cm, 2.5 * cm, 8.5 * cm, 2.1 * cm],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
    ]))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()


def generate_offer_pdf(offer, request):
    from django.urls import reverse

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            'Το Playwright δεν είναι εγκατεστημένο. '
            'Εκτελέστε: pip install playwright && playwright install chromium'
        ) from exc

    print_url = request.build_absolute_uri(
        reverse('products:offer_print', args=[offer.pk]) + '?pdf=1'
    )
    base_url = request.build_absolute_uri('/')

    auth_cookies = []
    for name in ('sessionid', 'csrftoken'):
        value = request.COOKIES.get(name)
        if value:
            auth_cookies.append({
                'name': name,
                'value': value,
                'url': base_url,
            })

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        if auth_cookies:
            context.add_cookies(auth_cookies)
        page = context.new_page()
        page.goto(print_url, wait_until='networkidle', timeout=60000)
        page.wait_for_selector('[data-pages-ready="true"]', timeout=60000)
        page.wait_for_timeout(300)
        pdf_bytes = page.pdf(
            format='A4',
            print_background=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            prefer_css_page_size=True,
        )
        browser.close()

    return pdf_bytes
