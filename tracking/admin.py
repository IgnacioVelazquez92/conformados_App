from django.contrib import admin

from .models import Evidencia, EventoTrazabilidad, HojaRuta, IntentoEntrega, Remito, UserProfile


@admin.register(HojaRuta)
class HojaRutaAdmin(admin.ModelAdmin):
    list_display = ("oid", "nro_entrega", "fecha", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("oid", "nro_entrega", "chofer", "transporte")


@admin.register(Remito)
class RemitoAdmin(admin.ModelAdmin):
    list_display = ("numero", "hoja_ruta", "cliente", "estado")
    list_filter = ("estado",)
    search_fields = ("numero", "cliente", "remito_uid")


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "hoja_ruta", "remito", "canal", "estado_validacion", "fecha_carga")
    list_filter = ("canal", "estado_validacion")


@admin.register(IntentoEntrega)
class IntentoEntregaAdmin(admin.ModelAdmin):
    list_display = ("id", "hoja_ruta", "remito", "canal", "motivo", "fecha_evento")
    list_filter = ("canal",)


@admin.register(EventoTrazabilidad)
class EventoTrazabilidadAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "hoja_ruta", "remito", "canal", "fecha_evento")
    list_filter = ("tipo", "canal")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "share_logistica", "share_cliente")
    list_filter = ("rol", "share_logistica", "share_cliente")
    search_fields = ("user__username", "user__email")
