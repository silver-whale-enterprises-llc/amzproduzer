# Generated by Django 2.1.7 on 2019-03-16 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CategorySalesRank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default='', max_length=255)),
                ('max_allowed', models.IntegerField(default=200000)),
                ('preferred', models.IntegerField(default=100000)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
