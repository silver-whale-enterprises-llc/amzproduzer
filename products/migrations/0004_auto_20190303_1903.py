# Generated by Django 2.1.7 on 2019-03-03 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_product_sold_by_amazon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]