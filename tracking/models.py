from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


def hoja_ruta_pdf_upload_to(instance: "HojaRuta", filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".pdf"
    empresa = instance.empresa.slug if instance.empresa_id else "sin-empresa"
    return f"hojas-ruta/{empresa}/{instance.oid}/original{extension}"


def conformado_upload_to(instance: "Evidencia", filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".jpg"
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    empresa = instance.empresa.slug if instance.empresa_id else instance.hoja_ruta.empresa.slug
    return f"conformados/{empresa}/{instance.hoja_ruta.oid}/{instance.remito.remito_uid}/{timestamp}{extension}"


class Empresa(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    active = models.BooleanField(default=True)
    theme_css = models.CharField(max_length=120, default="vendor/bootstrap/css/bootstrap.min.css")
    brand_color = models.CharField(max_length=20, blank=True)
    accent_color = models.CharField(max_length=20, blank=True)
    erp_identifier = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HojaRuta(models.Model):
    class Estado(models.TextChoices):
        IMPORTADA = "importada", "Importada"
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="hojas_ruta")
    oid = models.UUIDField()
    nro_entrega = models.CharField(max_length=64)
    fecha = models.DateField()
    transporte_tipo = models.CharField(max_length=100, blank=True)
    flete = models.CharField(max_length=100, blank=True)
    chofer = models.CharField(max_length=120, blank=True)
    acompanante = models.CharField(max_length=120, blank=True)
    transporte = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.IMPORTADA)
    archivo_pdf_original = models.FileField(upload_to=hoja_ruta_pdf_upload_to, blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["empresa", "oid"], name="unique_hoja_ruta_empresa_oid"),
        ]

    def __str__(self) -> str:
        return f"{self.empresa.name} - {self.nro_entrega} ({self.oid})"


class RoleDefinition(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120)
    can_import_pdf = models.BooleanField(default=False)
    can_review_evidence = models.BooleanField(default=False)
    can_audit_remitos = models.BooleanField(default=False)
    can_close_hoja = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    share_logistica_default = models.BooleanField(default=False)
    share_cliente_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["label"]

    def __str__(self) -> str:
        return f"{self.label} ({self.code})"

    def permission_flags(self) -> dict[str, bool]:
        return {
            "can_import_pdf": self.can_import_pdf,
            "can_review_evidence": self.can_review_evidence,
            "can_audit_remitos": self.can_audit_remitos,
            "can_close_hoja": self.can_close_hoja,
            "can_manage_users": self.can_manage_users,
            "share_logistica_default": self.share_logistica_default,
            "share_cliente_default": self.share_cliente_default,
        }

    @classmethod
    def active_definitions(cls) -> list["RoleDefinition"]:
        return list(cls.objects.filter(active=True).order_by("label"))

    @classmethod
    def for_code(cls, code: str) -> "RoleDefinition | None":
        return cls.objects.filter(code=code).first()

    @classmethod
    def permission_map(cls, code: str) -> dict[str, bool]:
        definition = cls.for_code(code)
        if definition:
            return definition.permission_flags()
        return {
            "can_import_pdf": False,
            "can_review_evidence": False,
            "can_audit_remitos": False,
            "can_close_hoja": False,
            "can_manage_users": False,
            "share_logistica_default": False,
            "share_cliente_default": False,
        }


class Remito(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EVIDENCIA_CARGADA = "evidencia_cargada", "Evidencia cargada"
        INTENTO_FALLIDO = "intento_fallido", "Intento fallido"
        VALIDADO = "validado", "Validado"
        OBSERVADO = "observado", "Observado"
        RECHAZADO = "rechazado", "Rechazado"
        CERRADO = "cerrado", "Cerrado"

    hoja_ruta = models.ForeignKey(HojaRuta, on_delete=models.CASCADE, related_name="remitos")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="remitos")
    remito_uid = models.CharField(max_length=120)
    numero = models.CharField(max_length=50)
    cliente = models.CharField(max_length=180)
    subcliente = models.CharField(max_length=180, blank=True)
    direccion = models.CharField(max_length=250)
    observacion = models.TextField(blank=True)
    fecha = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("hoja_ruta", "remito_uid")

    def __str__(self) -> str:
        return f"{self.numero} - {self.cliente}"


class Evidencia(models.Model):
    class Canal(models.TextChoices):
        LOGISTICA = "logistica", "Logistica"
        CLIENTE = "cliente", "Cliente"
        INTERNO = "interno", "Interno"

    class EstadoValidacion(models.TextChoices):
        PENDIENTE = "pendiente_revision", "Pendiente revision"
        VALIDADA = "validada", "Validada"
        OBSERVADA = "observada", "Observada"
        RECHAZADA = "rechazada", "Rechazada"

    hoja_ruta = models.ForeignKey(HojaRuta, on_delete=models.CASCADE, related_name="evidencias")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="evidencias")
    remito = models.ForeignKey(Remito, on_delete=models.CASCADE, related_name="evidencias")
    canal = models.CharField(max_length=20, choices=Canal.choices)
    archivo = models.FileField(upload_to=conformado_upload_to, max_length=200)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    estado_validacion = models.CharField(
        max_length=20,
        choices=EstadoValidacion.choices,
        default=EstadoValidacion.PENDIENTE,
    )
    comentario = models.TextField(blank=True)
    origen = models.CharField(max_length=120, blank=True)


class IntentoEntrega(models.Model):
    class Canal(models.TextChoices):
        LOGISTICA = "logistica", "Logistica"
        CLIENTE = "cliente", "Cliente"
        INTERNO = "interno", "Interno"

    hoja_ruta = models.ForeignKey(HojaRuta, on_delete=models.CASCADE, related_name="intentos")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="intentos")
    remito = models.ForeignKey(Remito, on_delete=models.CASCADE, related_name="intentos")
    canal = models.CharField(max_length=20, choices=Canal.choices)
    motivo = models.CharField(max_length=120)
    comentario = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)


class IntentoAccesoPortal(models.Model):
    class Motivo(models.TextChoices):
        OID_INVALIDO = "oid_invalido", "OID invalido"
        HOJA_INEXISTENTE = "hoja_inexistente", "Hoja inexistente"

    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="intentos_acceso")
    canal = models.CharField(max_length=20)
    oid = models.CharField(max_length=64)
    motivo = models.CharField(max_length=30, choices=Motivo.choices)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=255, blank=True)
    detalle = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_evento"]


class PublicAlertRecipient(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=180, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.email} ({'activo' if self.active else 'inactivo'})"


class EventoTrazabilidad(models.Model):
    class Tipo(models.TextChoices):
        IMPORTACION = "importacion", "Importacion"
        APERTURA_LINK = "apertura_link", "Apertura link"
        CARGA_EVIDENCIA = "carga_evidencia", "Carga evidencia"
        INTENTO_FALLIDO = "intento_fallido", "Intento fallido"
        VALIDACION = "validacion", "Validacion"
        RECHAZO = "rechazo", "Rechazo"
        CIERRE = "cierre", "Cierre"

    hoja_ruta = models.ForeignKey(HojaRuta, on_delete=models.CASCADE, related_name="eventos")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="eventos")
    remito = models.ForeignKey(Remito, on_delete=models.SET_NULL, null=True, blank=True, related_name="eventos")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    canal = models.CharField(max_length=20, blank=True)
    detalle = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_evento"]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    rol = models.CharField(max_length=50, default="otro")
    empresa_principal = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios_principales")
    empresas = models.ManyToManyField(Empresa, blank=True, related_name="usuarios")
    share_logistica = models.BooleanField(default=False)
    share_cliente = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.rol})"

    def can_share_logistica(self) -> bool:
        permissions = RoleDefinition.permission_map(self.rol)
        return self.share_logistica or permissions["share_logistica_default"]

    def can_share_cliente(self) -> bool:
        permissions = RoleDefinition.permission_map(self.rol)
        return self.share_cliente or permissions["share_cliente_default"]


def _delete_file_field(file_field) -> None:
    if file_field and file_field.name:
        file_field.delete(save=False)


@receiver(post_delete, sender=Evidencia)
def delete_evidencia_file(sender, instance: Evidencia, **kwargs) -> None:
    _delete_file_field(instance.archivo)


@receiver(post_delete, sender=HojaRuta)
def delete_hoja_ruta_pdf(sender, instance: HojaRuta, **kwargs) -> None:
    _delete_file_field(instance.archivo_pdf_original)
