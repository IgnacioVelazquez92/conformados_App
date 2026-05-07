from __future__ import annotations

from django.db import transaction

from tracking.models import Evidencia, EventoTrazabilidad, HojaRuta, Remito


@transaction.atomic
def validar_evidencia(*, evidencia: Evidencia, estado: str, comentario: str = "") -> Evidencia:
    if estado not in {
        Evidencia.EstadoValidacion.VALIDADA,
        Evidencia.EstadoValidacion.OBSERVADA,
        Evidencia.EstadoValidacion.RECHAZADA,
    }:
        raise ValueError("Estado de validacion invalido.")

    evidencia.estado_validacion = estado
    evidencia.comentario = comentario
    evidencia.save(update_fields=["estado_validacion", "comentario"])

    if estado == Evidencia.EstadoValidacion.VALIDADA:
        evidencia.remito.estado = Remito.Estado.VALIDADO
    elif estado == Evidencia.EstadoValidacion.OBSERVADA:
        evidencia.remito.estado = Remito.Estado.OBSERVADO
    else:
        evidencia.remito.estado = Remito.Estado.RECHAZADO
    evidencia.remito.save(update_fields=["estado"])

    EventoTrazabilidad.objects.create(
        hoja_ruta=evidencia.hoja_ruta,
        remito=evidencia.remito,
        tipo=EventoTrazabilidad.Tipo.VALIDACION if estado == Evidencia.EstadoValidacion.VALIDADA else EventoTrazabilidad.Tipo.RECHAZO,
        detalle=f"Evidencia {estado}.",
    )
    return evidencia


@transaction.atomic
def cerrar_hoja_ruta(*, hoja: HojaRuta, comentario: str = "") -> HojaRuta:
    if hoja.estado == HojaRuta.Estado.CERRADA:
        raise ValueError("La hoja ya esta cerrada.")

    remitos_pendientes = hoja.remitos.exclude(
        estado__in={Remito.Estado.VALIDADO, Remito.Estado.OBSERVADO}
    )
    if remitos_pendientes.exists():
        cantidad = remitos_pendientes.count()
        raise ValueError(
            f"No se puede cerrar la hoja porque hay {cantidad} remito(s) sin conformar u observar."
        )

    hoja.estado = HojaRuta.Estado.CERRADA
    hoja.save(update_fields=["estado"])

    EventoTrazabilidad.objects.create(
        hoja_ruta=hoja,
        tipo=EventoTrazabilidad.Tipo.CIERRE,
        detalle=comentario or "Cierre operativo de la hoja.",
    )
    return hoja
