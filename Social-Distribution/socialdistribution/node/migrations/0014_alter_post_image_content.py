# Generated by Django 5.1.2 on 2024-11-04 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0013_merge_20241104_0021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image_content',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='images/postImages'),
        ),
    ]
