# Generated by Django 4.2.3 on 2023-08-17 04:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_orders_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='return_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
