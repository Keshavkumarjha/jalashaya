from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contactmessage",
            name="name",
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="city",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="first_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="last_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="phone",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
