from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Έλεγχος εγκατάστασης Playwright/Chromium για PDF προσφορών'

    def handle(self, *args, **options):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'Το πακέτο playwright δεν είναι εγκατεστημένο.\n'
                'Εκτελέστε: pip install playwright'
            ))
            return

        self.stdout.write('Έλεγχος Chromium...')
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                browser.close()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f'Αποτυχία εκκίνησης Chromium: {exc}\n\n'
                'Εκτελέστε στον server (ως ο ίδιος χρήστης που τρέχει το gunicorn):\n'
                '  python -m playwright install chromium\n\n'
                'Αν λείπουν system libraries (Linux):\n'
                '  python -m playwright install-deps chromium'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            'OK — το Chromium είναι έτοιμο για δημιουργία PDF προσφορών.'
        ))
