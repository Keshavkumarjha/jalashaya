from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_update_contact_message_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerAddress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("customer_name", models.CharField(max_length=200)),
                ("customer_email", models.EmailField(db_index=True, max_length=254)),
                ("customer_mobile", models.CharField(blank=True, max_length=20, null=True)),
                ("label", models.CharField(blank=True, max_length=80, null=True)),
                ("address_line", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["customer_email", "is_active"], name="store_custo_custome_5fd969_idx")],
            },
        ),
    ]
