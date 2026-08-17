# Generated migration for adding class_designation field to CustomUser

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0002_alter_customuser_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='class_designation',
            field=models.CharField(blank=True, help_text='Class or grade designation (e.g., Grade 10-A, CS101)', max_length=100, null=True),
        ),
    ]
