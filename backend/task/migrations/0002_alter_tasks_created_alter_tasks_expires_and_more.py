# Generated by Django 4.2.1 on 2025-01-02 05:08

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasks',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='tasks',
            name='expires',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='tasks',
            name='image',
            field=cloudinary.models.CloudinaryField(default='c40te5wgb08lfd5em1pq', max_length=255, verbose_name='images'),
        ),
    ]
