# Generated manually for Lead intake

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('twilio_call_sid', models.CharField(blank=True, db_index=True, max_length=64, null=True, unique=True)),
                ('source', models.CharField(choices=[('web', 'Web chat'), ('phone', 'Phone')], default='web', max_length=16)),
                ('status', models.CharField(choices=[('in_progress', 'In progress'), ('complete', 'Complete')], default='in_progress', max_length=32)),
                ('first_name', models.CharField(blank=True, max_length=120)),
                ('last_name', models.CharField(blank=True, max_length=120)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('job_type', models.CharField(blank=True, choices=[('full_move', 'Full move'), ('partial_move', 'Partial move'), ('few_boxes', 'Few boxes only'), ('moving_lift', 'Moving lift'), ('other', 'Other')], max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('conversation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='lead', to='chatbot.conversation')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
    ]
