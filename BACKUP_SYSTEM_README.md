# Σύστημα Backup και Restore Βάσης Δεδομένων

## Περιγραφή
Το σύστημα επιτρέπει στους superusers να δημιουργούν backups της βάσης δεδομένων SQLite και να επαναφέρουν τη βάση από προηγούμενα backups.

## Χαρακτηριστικά

### 🔄 Backup
- **Δημιουργία backup**: Οι superusers μπορούν να δημιουργήσουν backup της τρέχουσας βάσης
- **Timestamp στο όνομα**: Τα αρχεία backup έχουν timestamp (π.χ. `db_backup_20241201_143022.sqlite3`)
- **Αυτόματο download**: Το αρχείο κατεβαίνει αυτόματα στον υπολογιστή του χρήστη
- **Αρχική μορφή**: Τα αρχεία δεν συμπιέζονται, παραμένουν στην αρχική τους μορφή

### 🔙 Restore
- **Επιλογή αρχείου**: Ο χρήστης επιλέγει ένα αρχείο .sqlite3 για επαναφορά
- **Έλεγχος τύπου**: Μόνο αρχεία .sqlite3 επιτρέπονται
- **Αυτόματο backup πριν restore**: Δημιουργείται backup της τρέχουσας βάσης πριν την αντικατάσταση
- **Overwrite**: Η νέα βάση αντικαθιστά την παλιά (δεν δημιουργείται φάκελος)

## Πρόσβαση

### Στο Dashboard
Για τους superusers, στο dashboard εμφανίζεται μια νέα ενότητα "Διαχείριση Συστήματος" με:
- Δημιουργία Χρήστη
- Διαχείριση Χρηστών  
- Διαχείριση Συνδρομών
- **Διαχείριση Βάσης** (νέο)

### Στο Sidebar
Προστέθηκε link "Διαχείριση Βάσης" στο sidebar για τους superusers.

## URLs
- `/database-management/` - Σελίδα διαχείρισης backup/restore
- `/database-backup/` - Endpoint για δημιουργία backup
- `/database-restore/` - Endpoint για επαναφορά

## Ασφάλεια
- Μόνο οι superusers έχουν πρόσβαση
- Χρήση του decorator `@superuser_required`
- CSRF protection σε όλα τα forms
- Έλεγχος τύπου αρχείου για restore

## Mobile Responsive
- Το dashboard έχει βελτιωθεί για κινητά
- Αφαιρέθηκαν τα κενά αριστερά και δεξιά
- Προσαρμοσμένα μεγέθη για μικρές οθόνες

## Αρχεία που τροποποιήθηκαν

### Views
- `accounts/views.py` - Προσθήκη των views `database_backup`, `database_restore`, `database_management`

### URLs
- `config/urls.py` - Προσθήκη των URL patterns

### Templates
- `accounts/templates/accounts/database_management.html` - Νέο template για τη διαχείριση
- `accounts/templates/accounts/dashboard.html` - Προσθήκη link για superusers
- `accounts/templates/accounts/base.html` - Προσθήκη στο sidebar και mobile responsive

### Settings
- `config/settings.py` - Ρυθμίσεις για file uploads

## Χρήση

1. **Backup**: 
   - Πηγαίνετε στο Dashboard → Διαχείριση Βάσης
   - Πατήστε "Δημιουργία Backup"
   - Το αρχείο θα κατεβαίνει αυτόματα

2. **Restore**:
   - Πηγαίνετε στο Dashboard → Διαχείριση Βάσης
   - Επιλέξτε αρχείο .sqlite3
   - Πατήστε "Επαναφορά Βάσης"
   - Επιβεβαιώστε την ενέργεια

## Σημειώσεις
- Κατά το restore, δημιουργείται αυτόματα backup της τρέχουσας βάσης
- Τα προσωρινά αρχεία διαγράφονται μετά τη χρήση
- Μέγιστο μέγεθος αρχείου: 50MB
- Το σύστημα είναι απλό και εύκολο στη χρήση 