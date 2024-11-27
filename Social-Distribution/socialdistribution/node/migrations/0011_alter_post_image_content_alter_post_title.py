# Generated by Django 5.1.2 on 2024-11-27 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0010_alter_post_image_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image_content',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='images/postImages'),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=500),
        ),
    ]
