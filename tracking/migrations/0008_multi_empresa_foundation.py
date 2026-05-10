from django.db import migrations, models
import django.db.models.deletion


EMPRESAS_SEED = [
    {
        "code": "pharmacenter",
        "name": "Pharmacenter",
        "slug": "pharmacenter",
        "theme_css": "vendor/bootstrap/css/pharma.css",
    },
    {
        "code": "salud_renal",
        "name": "Salud Renal",
        "slug": "salud-renal",
        "theme_css": "vendor/bootstrap/css/sr.css",
    },
    {
        "code": "dynamic",
        "name": "Dynamic",
        "slug": "dynamic",
        "theme_css": "vendor/bootstrap/css/dyn.css",
    },
]


def seed_empresas(apps, schema_editor):
    Empresa = apps.get_model("tracking", "Empresa")
    for data in EMPRESAS_SEED:
        Empresa.objects.update_or_create(
            code=data["code"],
            defaults={
                "name": data["name"],
                "slug": data["slug"],
                "active": True,
                "theme_css": data["theme_css"],
            },
        )


def assign_existing_rows(apps, schema_editor):
    Empresa = apps.get_model("tracking", "Empresa")
    HojaRuta = apps.get_model("tracking", "HojaRuta")
    Remito = apps.get_model("tracking", "Remito")
    Evidencia = apps.get_model("tracking", "Evidencia")
    IntentoEntrega = apps.get_model("tracking", "IntentoEntrega")
    IntentoAccesoPortal = apps.get_model("tracking", "IntentoAccesoPortal")
    EventoTrazabilidad = apps.get_model("tracking", "EventoTrazabilidad")
    UserProfile = apps.get_model("tracking", "UserProfile")

    default_empresa = Empresa.objects.get(code="pharmacenter")

    HojaRuta.objects.filter(empresa__isnull=True).update(empresa=default_empresa)
    for remito in Remito.objects.select_related("hoja_ruta").filter(empresa__isnull=True):
        remito.empresa_id = remito.hoja_ruta.empresa_id
        remito.save(update_fields=["empresa"])
    for evidencia in Evidencia.objects.select_related("hoja_ruta").filter(empresa__isnull=True):
        evidencia.empresa_id = evidencia.hoja_ruta.empresa_id
        evidencia.save(update_fields=["empresa"])
    for intento in IntentoEntrega.objects.select_related("hoja_ruta").filter(empresa__isnull=True):
        intento.empresa_id = intento.hoja_ruta.empresa_id
        intento.save(update_fields=["empresa"])
    for evento in EventoTrazabilidad.objects.select_related("hoja_ruta").filter(empresa__isnull=True):
        evento.empresa_id = evento.hoja_ruta.empresa_id
        evento.save(update_fields=["empresa"])

    IntentoAccesoPortal.objects.filter(empresa__isnull=True).update(empresa=default_empresa)
    for profile in UserProfile.objects.filter(empresa_principal__isnull=True):
        profile.empresa_principal = default_empresa
        profile.save(update_fields=["empresa_principal"])
        profile.empresas.add(default_empresa)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0007_roledefinition_and_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=60, unique=True)),
                ("active", models.BooleanField(default=True)),
                ("theme_css", models.CharField(default="vendor/bootstrap/css/bootstrap.min.css", max_length=120)),
                ("brand_color", models.CharField(blank=True, max_length=20)),
                ("accent_color", models.CharField(blank=True, max_length=20)),
                ("erp_identifier", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_empresas, noop_reverse),
        migrations.AlterField(
            model_name="hojaruta",
            name="oid",
            field=models.UUIDField(),
        ),
        migrations.AddField(
            model_name="hojaruta",
            name="empresa",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="hojas_ruta", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="remito",
            name="empresa",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="remitos", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="empresa",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="evidencias", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="intentoentrega",
            name="empresa",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="intentos", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="intentoaccesoportal",
            name="empresa",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="intentos_acceso", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="eventotrazabilidad",
            name="empresa",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="eventos", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="empresa_principal",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="usuarios_principales", to="tracking.empresa"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="empresas",
            field=models.ManyToManyField(blank=True, related_name="usuarios", to="tracking.empresa"),
        ),
        migrations.RunPython(assign_existing_rows, noop_reverse),
        migrations.AlterField(
            model_name="hojaruta",
            name="empresa",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="hojas_ruta", to="tracking.empresa"),
        ),
        migrations.AlterField(
            model_name="remito",
            name="empresa",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="remitos", to="tracking.empresa"),
        ),
        migrations.AlterField(
            model_name="evidencia",
            name="empresa",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="evidencias", to="tracking.empresa"),
        ),
        migrations.AlterField(
            model_name="intentoentrega",
            name="empresa",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="intentos", to="tracking.empresa"),
        ),
        migrations.AlterField(
            model_name="eventotrazabilidad",
            name="empresa",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="eventos", to="tracking.empresa"),
        ),
        migrations.AddConstraint(
            model_name="hojaruta",
            constraint=models.UniqueConstraint(fields=("empresa", "oid"), name="unique_hoja_ruta_empresa_oid"),
        ),
    ]
