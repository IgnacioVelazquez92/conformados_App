from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def hoja_ruta_pdf_upload_to(instance: "HojaRuta", filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".pdf"
    return f"hojas-ruta/{instance.oid}/original{extension}"


def conformado_upload_to(instance: "Evidencia", filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".jpg"
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"conformados/{instance.hoja_ruta.oid}/{instance.remito.remito_uid}/{timestamp}{extension}"


class HojaRuta(models.Model):
    class Estado(models.TextChoices):
        IMPORTADA = "importada", "Importada"
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    oid = models.UUIDField(unique=True)
    nro_entrega = models.CharField(max_length=64)
    fecha = models.DateField()
    transporte_tipo = models.CharField(max_length=100, blank=True)
    flete = models.CharField(max_length=100, blank=True)
    chofer = models.CharField(max_length=120, blank=True)
    acompanante = models.CharField(max_length=120, blank=True)
    transporte = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.IMPORTADA)
    archivo_pdf_original = models.FileField(upload_to=hoja_ruta_pdf_upload_to, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.nro_entrega} ({self.oid})"


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
    remito_uid = models.CharField(max_length=120)
    numero = models.CharField(max_length=50)
    cliente = models.CharField(max_length=180)
    subcliente = models.CharField(max_length=180, blank=True)
    direccion = models.CharField(max_length=250)
    observacion = models.TextField(blank=True)
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
    remito = models.ForeignKey(Remito, on_delete=models.CASCADE, related_name="evidencias")
    canal = models.CharField(max_length=20, choices=Canal.choices)
    archivo = models.FileField(upload_to=conformado_upload_to)
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
    remito = models.ForeignKey(Remito, on_delete=models.CASCADE, related_name="intentos")
    canal = models.CharField(max_length=20, choices=Canal.choices)
    motivo = models.CharField(max_length=120)
    comentario = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)


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
    remito = models.ForeignKey(Remito, on_delete=models.SET_NULL, null=True, blank=True, related_name="eventos")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    canal = models.CharField(max_length=20, blank=True)
    detalle = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_evento"]


class UserProfile(models.Model):
    class Rol(models.TextChoices):
        DEPOSITO = "deposito", "Deposito"
        VENTAS = "ventas", "Ventas"
        JEFE = "jefe", "Jefe"
        OTRO = "otro", "Otro"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.OTRO)
    share_logistica = models.BooleanField(default=False)
    share_cliente = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.rol})"

    def can_share_logistica(self) -> bool:
        return self.share_logistica or self.rol in {self.Rol.DEPOSITO, self.Rol.JEFE}

    def can_share_cliente(self) -> bool:
        return self.share_cliente or self.rol in {self.Rol.VENTAS, self.Rol.JEFE}
