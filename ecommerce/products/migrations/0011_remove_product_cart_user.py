# Generated by Django 4.2.3 on 2023-08-04 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_alter_product_cart_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product_cart',
            name='user',
        ),
    ]
