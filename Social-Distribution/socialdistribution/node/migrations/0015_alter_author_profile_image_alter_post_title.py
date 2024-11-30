# Generated by Django 5.1.2 on 2024-11-28 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0014_alter_author_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='profile_image',
            field=models.ImageField(blank=True, default=None, max_length=500, null=True, upload_to='images/profilePictures'),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=100),
        ),
    ]
