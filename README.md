# Django Project

## Εγκατάσταση

1. Δημιουργήστε ένα virtual environment:
```bash
python -m venv venv
```

2. Ενεργοποιήστε το virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Εγκαταστήστε τις απαιτήσεις:
```bash
pip install -r requirements.txt
```

4. Δημιουργήστε το Django project:
```bash
django-admin startproject config .
```

5. Εκτελέστε τις migrations:
```bash
python manage.py migrate
```

6. Εκκινήστε τον development server:
```bash
python manage.py runserver
```

## Δομή Project
- `config/`: Κύριο directory του project
- `manage.py`: Αρχείο διαχείρισης του Django project
- `requirements.txt`: Αρχείο με τις απαιτήσεις του project 