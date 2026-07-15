from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_scheduledtaskitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledtaskitem',
            name='item_status',
            field=models.CharField(
                choices=[('under_work', 'Υπό κατασκευή'), ('completed', 'Ολοκληρώθηκε')],
                default='under_work',
                max_length=20,
                verbose_name='Κατάσταση προϊόντος',
            ),
        ),
    ]
