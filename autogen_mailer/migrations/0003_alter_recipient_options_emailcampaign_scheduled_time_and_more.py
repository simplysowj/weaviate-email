# Generated by Django 5.2 on 2025-04-07 17:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autogen_mailer', '0002_remove_emailcampaign_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipient',
            options={'verbose_name': 'Recipient', 'verbose_name_plural': 'Recipients'},
        ),
        migrations.AddField(
            model_name='emailcampaign',
            name='scheduled_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='emailcampaign',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('sending', 'Sending'), ('sent', 'Sent'), ('failed', 'Failed')], default='draft', max_length=10),
        ),
        migrations.AddField(
            model_name='emailcampaign',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='emailcampaign',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recipient',
            name='error',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='recipient',
            name='message_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.CreateModel(
            name='EmailAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('display_name', models.CharField(blank=True, max_length=255)),
                ('smtp_server', models.CharField(max_length=255)),
                ('smtp_port', models.IntegerField(default=587)),
                ('imap_server', models.CharField(blank=True, max_length=255)),
                ('imap_port', models.IntegerField(blank=True, default=993)),
                ('protocol', models.CharField(choices=[('imap', 'IMAP'), ('pop3', 'POP3')], default='imap', max_length=4)),
                ('use_ssl', models.BooleanField(default=True)),
                ('use_oauth', models.BooleanField(default=False)),
                ('oauth_token', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='emailcampaign',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='autogen_mailer.emailaccount'),
        ),
        migrations.CreateModel(
            name='EmailAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='email_attachments/')),
                ('original_filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='autogen_mailer.emailcampaign')),
            ],
        ),
        migrations.CreateModel(
            name='ReceivedEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(max_length=255, unique=True)),
                ('subject', models.CharField(max_length=255)),
                ('body_text', models.TextField()),
                ('body_html', models.TextField(blank=True)),
                ('sender', models.EmailField(max_length=254)),
                ('recipients', models.TextField()),
                ('received_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('unread', 'Unread'), ('read', 'Read'), ('archived', 'Archived'), ('deleted', 'Deleted')], default='unread', max_length=10)),
                ('labels', models.CharField(blank=True, max_length=255)),
                ('raw_headers', models.TextField(blank=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autogen_mailer.emailaccount')),
            ],
            options={
                'ordering': ['-received_at'],
            },
        ),
        migrations.CreateModel(
            name='ReceivedAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='received_attachments/')),
                ('original_filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.IntegerField()),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='autogen_mailer.receivedemail')),
            ],
        ),
    ]
