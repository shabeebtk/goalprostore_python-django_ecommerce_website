# Generated by Django 4.2.3 on 2023-08-22 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_razorpay_orders'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupons',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon_code', models.CharField(max_length=20)),
                ('discount', models.PositiveIntegerField()),
                ('discount_type', models.CharField(choices=[('percentage', 'percentage'), ('amount', 'amount')], max_length=20)),
                ('valid_from', models.DateField()),
                ('valid_to', models.DateField()),
                ('active', models.BooleanField()),
            ],
        ),
    ]
