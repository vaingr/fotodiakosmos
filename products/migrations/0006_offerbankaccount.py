from django.db import migrations, models
import django.db.models.deletion


DEFAULT_BANK_ACCOUNTS = [
    ('ΕΘΝΙΚΗ', 'GR4701103030000030301714256', 0),
    ('ΠΕΙΡΑΙΩΣ', 'GR 5001712640006264170336444', 1),
    ('ALPHA', 'GR 8501402200220002002033741', 2),
]


def create_default_bank_accounts(apps, schema_editor):
    OfferSettings = apps.get_model('products', 'OfferSettings')
    OfferBankAccount = apps.get_model('products', 'OfferBankAccount')
    settings, _ = OfferSettings.objects.get_or_create(pk=1)
    for bank_name, iban, display_order in DEFAULT_BANK_ACCOUNTS:
        OfferBankAccount.objects.create(
            settings=settings,
            bank_name=bank_name,
            iban=iban,
            display_order=display_order,
        )


def remove_default_bank_accounts(apps, schema_editor):
    OfferBankAccount = apps.get_model('products', 'OfferBankAccount')
    OfferBankAccount.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_offersettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfferBankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(max_length=100, verbose_name='Τράπεζα')),
                ('iban', models.CharField(max_length=40, verbose_name='IBAN')),
                ('display_order', models.PositiveSmallIntegerField(default=0, verbose_name='Σειρά')),
                ('settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to='products.offersettings', verbose_name='Ρυθμίσεις')),
            ],
            options={
                'verbose_name': 'Τραπεζικός λογαριασμός',
                'verbose_name_plural': 'Τραπεζικοί λογαριασμοί',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.RunPython(create_default_bank_accounts, remove_default_bank_accounts),
    ]
