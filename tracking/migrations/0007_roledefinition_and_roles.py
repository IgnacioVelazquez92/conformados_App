from django.db import migrations, models


def seed_role_definitions(apps, schema_editor):
    RoleDefinition = apps.get_model("tracking", "RoleDefinition")

    defaults = [
        {
            "code": "deposito",
            "label": "Deposito",
            "can_import_pdf": True,
            "can_review_evidence": False,
            "can_close_hoja": False,
            "can_manage_users": False,
            "share_logistica_default": True,
            "share_cliente_default": False,
            "active": True,
        },
        {
            "code": "ventas",
            "label": "Ventas",
            "can_import_pdf": False,
            "can_review_evidence": False,
            "can_close_hoja": False,
            "can_manage_users": False,
            "share_logistica_default": False,
            "share_cliente_default": True,
            "active": True,
        },
        {
            "code": "jefe",
            "label": "Jefe",
            "can_import_pdf": True,
            "can_review_evidence": True,
            "can_close_hoja": True,
            "can_manage_users": True,
            "share_logistica_default": True,
            "share_cliente_default": True,
            "active": True,
        },
        {
            "code": "otro",
            "label": "Otro",
            "can_import_pdf": False,
            "can_review_evidence": False,
            "can_close_hoja": False,
            "can_manage_users": False,
            "share_logistica_default": False,
            "share_cliente_default": False,
            "active": True,
        },
    ]

    for payload in defaults:
        RoleDefinition.objects.update_or_create(code=payload["code"], defaults=payload)


def unseed_role_definitions(apps, schema_editor):
    RoleDefinition = apps.get_model("tracking", "RoleDefinition")
    RoleDefinition.objects.filter(code__in=["deposito", "ventas", "jefe", "otro"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0006_publicalertrecipient"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoleDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=120)),
                ("can_import_pdf", models.BooleanField(default=False)),
                ("can_review_evidence", models.BooleanField(default=False)),
                ("can_close_hoja", models.BooleanField(default=False)),
                ("can_manage_users", models.BooleanField(default=False)),
                ("share_logistica_default", models.BooleanField(default=False)),
                ("share_cliente_default", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["label"],
            },
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="rol",
            field=models.CharField(default="otro", max_length=50),
        ),
        migrations.RunPython(seed_role_definitions, unseed_role_definitions),
    ]