import django.db.models.deletion
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('accounts', '0003_task_type_and_customer'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledTaskItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Ποσότητα')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='task_items', to='products.finishedproduct', verbose_name='Προϊόν')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='accounts.scheduledtask', verbose_name='Εργασία')),
            ],
            options={
                'verbose_name': 'Προϊόν εργασίας',
                'verbose_name_plural': 'Προϊόντα εργασίας',
                'ordering': ['id'],
            },
        ),
    ]
