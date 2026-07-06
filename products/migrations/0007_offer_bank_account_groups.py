from django.db import migrations, models


INDIVIDUAL_BANK_ACCOUNTS = [
    ('ΠΕΙΡΑΙΩΣ', 'GR65 0171 2640 0062 6416 8027 574', 0),
    ('ΕΘΝΙΚΗ', 'GR4001103030000030300337661', 1),
    ('ALPHABANK', 'GR5201406440644002101091456', 2),
    ('EUROBANK', 'GR7502602650000000201492141', 3),
]


def create_individual_bank_accounts(apps, schema_editor):
    OfferSettings = apps.get_model('products', 'OfferSettings')
    OfferBankAccount = apps.get_model('products', 'OfferBankAccount')
    settings, _ = OfferSettings.objects.get_or_create(pk=1)
    for bank_name, iban, display_order in INDIVIDUAL_BANK_ACCOUNTS:
        OfferBankAccount.objects.create(
            settings=settings,
            account_group='individual',
            bank_name=bank_name,
            iban=iban,
            display_order=display_order,
        )


def remove_individual_bank_accounts(apps, schema_editor):
    OfferBankAccount = apps.get_model('products', 'OfferBankAccount')
    OfferBankAccount.objects.filter(account_group='individual').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_offerbankaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='offerbankaccount',
            name='account_group',
            field=models.CharField(
                choices=[('company', 'Εταιρίας'), ('individual', 'Ατομικής')],
                default='company',
                max_length=20,
                verbose_name='Ομάδα',
            ),
        ),
        migrations.AddField(
            model_name='offer',
            name='bank_account_group',
            field=models.CharField(
                choices=[('company', 'Εταιρίας'), ('individual', 'Ατομικής')],
                default='company',
                max_length=20,
                verbose_name='Τραπεζικοί λογαριασμοί',
            ),
        ),
        migrations.RunPython(create_individual_bank_accounts, remove_individual_bank_accounts),
    ]
