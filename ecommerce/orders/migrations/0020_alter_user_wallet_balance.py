# Generated by Django 4.2.3 on 2023-08-26 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0019_wallet_transaction_user_wallet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_wallet',
            name='balance',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
