from __future__ import annotations

from django.db import transaction

from tracking.models import Evidencia, EventoTrazabilidad, HojaRuta, IntentoEntrega, Remito


@transaction.atomic
def registrar_evidencia(*, hoja: HojaRuta, remito: Remito, canal: str, archivo, comentario: str = "", origen: str = "", permitir_duplicada: bool = False) -> Evidencia:
    if hoja.estado != HojaRuta.Estado.ABIERTA:
        raise ValueError("La hoja no esta abierta.")

    if not permitir_duplicada and remito.evidencias.exists():
        raise ValueError("Ya existe una evidencia para este remito.")

    evidencia = Evidencia.objects.create(
        hoja_ruta=hoja,
        remito=remito,
        canal=canal,
        archivo=archivo,
        comentario=comentario,
        origen=origen,
    )

    remito.estado = Remito.Estado.EVIDENCIA_CARGADA
    remito.save(update_fields=["estado"])

    EventoTrazabilidad.objects.create(
        hoja_ruta=hoja,
        remito=remito,
        tipo=EventoTrazabilidad.Tipo.CARGA_EVIDENCIA,
        canal=canal,
        detalle="Evidencia cargada desde portal publico.",
    )
    return evidencia


@transaction.atomic
def registrar_intento_no_entregado(*, hoja: HojaRuta, remito: Remito, canal: str, motivo: str, comentario: str = "") -> IntentoEntrega:
    if hoja.estado != HojaRuta.Estado.ABIERTA:
        raise ValueError("La hoja no esta abierta.")

    intento = IntentoEntrega.objects.create(
        hoja_ruta=hoja,
        remito=remito,
        canal=canal,
        motivo=motivo,
        comentario=comentario,
    )

    remito.estado = Remito.Estado.INTENTO_FALLIDO
    remito.save(update_fields=["estado"])

    EventoTrazabilidad.objects.create(
        hoja_ruta=hoja,
        remito=remito,
        tipo=EventoTrazabilidad.Tipo.INTENTO_FALLIDO,
        canal=canal,
        detalle=f"No entregado: {motivo}",
    )
    return intento
