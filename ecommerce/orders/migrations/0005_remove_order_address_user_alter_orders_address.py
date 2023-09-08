# Generated by Django 4.2.3 on 2023-08-14 06:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order_address',
            name='user',
        ),
        migrations.AlterField(
            model_name='orders',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.order_address'),
        ),
    ]
