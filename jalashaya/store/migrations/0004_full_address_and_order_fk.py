from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0003_customeraddress"),
    ]

    operations = [
        migrations.RenameField(
            model_name="customeraddress",
            old_name="address_line",
            new_name="address_line_1",
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="address_line_2",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="city",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="country",
            field=models.CharField(default="India", max_length=80),
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="landmark",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="postal_code",
            field=models.CharField(default="", max_length=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customeraddress",
            name="state_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="customer_address",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="store.customeraddress"),
        ),
    ]
