# Generated by Django 4.2.3 on 2023-09-01 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_banners'),
    ]

    operations = [
        migrations.AddField(
            model_name='banners',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
