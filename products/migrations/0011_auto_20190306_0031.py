# Generated by Django 2.1.7 on 2019-03-06 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_amazoncategory_highest_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amazoncategory',
            name='category_id',
            field=models.BigIntegerField(),
        ),
    ]
