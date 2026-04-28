from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import fitz  # PyMuPDF
import numpy as np
from django.db import transaction

from tracking.models import EventoTrazabilidad, HojaRuta, Remito

UUID_PATTERN_TEXT = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
OID_PATTERN = re.compile(rf"(?P<oid>{UUID_PATTERN_TEXT})")
CANAL_PATH_PATTERN = re.compile(
    rf"/conformados/(?:logistica|cliente|interno)/(?P<oid>{UUID_PATTERN_TEXT})/?",
    re.IGNORECASE,
)
HEADER_PATTERNS = {
    "nro_entrega": re.compile(r"(?mi)^\s*(?:n[úu]mero\s*de\s*entrega|nro\.?\s*entrega)[ \t]*:[ \t]*(?P<value>[^\n\r]+)"),
    "transporte_tipo": re.compile(r"(?mi)^\s*(?:transporte\s*tipo|tipo\s*de\s*transporte)[ \t]*:[ \t]*(?P<value>[^\n\r]*)"),
    "flete": re.compile(r"(?mi)^\s*flete[ \t]*:[ \t]*(?P<value>[^\n\r]+)"),
    "chofer": re.compile(r"(?mi)^\s*chofer[ \t]*:[ \t]*(?P<value>[^\n\r]+)"),
    "acompanante": re.compile(r"(?mi)^\s*(?:acompa[nñ]ante|acomapa[nñ]ante)[ \t]*:[ \t]*(?P<value>[^\n\r]+)"),
    "transporte": re.compile(r"(?mi)^\s*(?:transporte|operador\s*log[ií]stico)[ \t]*:[ \t]*(?P<value>[^\n\r]+)"),
}


@dataclass
class RemitoData:
    remito_uid: str
    numero: str
    cliente: str
    subcliente: str = ""
    direccion: str = ""
    observacion: str = ""


MIN_REMITOS_POR_HOJA = int(os.getenv("IMPORT_MIN_REMITOS", "1"))
DATE_PATTERN = re.compile(r"(?P<date>(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}))")
REMITO_PATTERN = re.compile(r"\b(?P<numero>\d{5}-\d{8})\b")
REMITO_OID_PATTERN = re.compile(rf"\b(?P<remito_oid>{UUID_PATTERN_TEXT})\b")
ROW_PATTERN = re.compile(
    r"^(?P<fecha>(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}))\s+"
    r"(?P<cliente>.+?)\s+"
    r"(?P<remito>\d{5}-\d{8})\s+"
    rf"(?:(?P<remito_oid>{UUID_PATTERN_TEXT})\s+)?"
    r"(?P<resto>.+)$"
)


def _read_pdf_bytes(pdf_file: Any) -> bytes:
    if hasattr(pdf_file, "read"):
        position = None
        if hasattr(pdf_file, "tell") and hasattr(pdf_file, "seek"):
            try:
                position = pdf_file.tell()
                pdf_file.seek(0)
            except Exception:
                position = None
        data = pdf_file.read()
        if position is not None:
            try:
                pdf_file.seek(position)
            except Exception:
                pass
        return data
    if isinstance(pdf_file, (bytes, bytearray)):
        return bytes(pdf_file)
    if isinstance(pdf_file, (str, Path)):
        return Path(pdf_file).read_bytes()
    raise TypeError("Tipo de archivo PDF no soportado")


def extract_text_from_pdf(pdf_file: Any) -> str:
    pdf_bytes = _read_pdf_bytes(pdf_file)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    parts: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _decode_qr_from_page(page: fitz.Page) -> list[str]:
    detector = cv2.QRCodeDetector()
    decoded: list[str] = []
    for zoom in (2, 3, 4, 6, 8):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        image = cv2.imdecode(
            np.frombuffer(pixmap.tobytes("png"), dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )
        if image is None:
            continue
        try:
            success, decoded_info, _, _ = detector.detectAndDecodeMulti(image)
            if success:
                decoded.extend([value for value in decoded_info if value])
        except Exception:
            pass
        try:
            value, _, _ = detector.detectAndDecode(image)
            if value:
                decoded.append(value)
        except Exception:
            pass
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            value, _, _ = detector.detectAndDecode(gray)
            if value:
                decoded.append(value)
        except Exception:
            pass
        if decoded:
            return list(dict.fromkeys(decoded))
    return list(dict.fromkeys(decoded))


def extract_oid_from_qr(pdf_file: Any) -> uuid.UUID:
    pdf_bytes = _read_pdf_bytes(pdf_file)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    candidates: list[str] = []
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if uri:
                candidates.append(uri)
        page_text = page.get_text("text") or ""
        candidates.extend(CANAL_PATH_PATTERN.findall(page_text))
        candidates.extend(_decode_qr_from_page(page))

    for candidate in candidates:
        match = OID_PATTERN.search(candidate) or CANAL_PATH_PATTERN.search(candidate)
        if match:
            return uuid.UUID(match.group("oid"))

    raise ValueError("No se pudo extraer el oid desde el QR del PDF.")


def _normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _merge_wrapped_uuid_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        if current.endswith("-") and index + 1 < len(lines):
            candidate = current + lines[index + 1]
            if REMITO_OID_PATTERN.fullmatch(candidate):
                merged.append(candidate)
                index += 2
                continue
        merged.append(current)
        index += 1
    return merged


def _parse_date(value: str) -> datetime.date:
    value = _normalize_value(value)
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha no reconocida: {value}")


def _extract_labelled_value(text: str, key: str, default: str = "") -> str:
    match = HEADER_PATTERNS[key].search(text)
    if match:
        value = _normalize_value(match.group("value"))
        if value:
            return value

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            if key.replace("_", " ") in line.lower() and ":" in line:
                if idx + 1 < len(lines):
                    candidate = _normalize_value(lines[idx + 1])
                    if candidate and ":" not in candidate and not re.search(r"^[a-záéíóúñ ]+\s*:\s*$", candidate, re.IGNORECASE):
                        return candidate
    return default


def _infer_transporte_tipo(text: str) -> str:
    lowered = text.lower()
    if "propio" in lowered:
        return "Propio"
    if "tercero" in lowered or "tercerizado" in lowered:
        return "Tercero"
    return ""


def _extract_date_value(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if re.search(r"\bfecha\b", line, re.IGNORECASE):
            match = DATE_PATTERN.search(line)
            if match:
                return _normalize_value(match.group("date"))

    match = DATE_PATTERN.search(text)
    if match:
        return _normalize_value(match.group("date"))

    return ""


def _split_cliente_subcliente(client_lines: list[str]) -> tuple[str, str]:
    if not client_lines:
        return "", ""

    cliente_parts = [client_lines[0]]
    subcliente_parts: list[str] = []
    for line in client_lines[1:]:
        lowered = line.lower()
        is_cliente_continuation = (
            line.startswith("(")
            or lowered.startswith(("y ", "e "))
            or cliente_parts[-1].endswith((" DE", " DEL", " PARA", " Y"))
        )
        if is_cliente_continuation and not subcliente_parts:
            cliente_parts.append(line)
        else:
            subcliente_parts.append(line)

    return " ".join(cliente_parts), " ".join(subcliente_parts)


def _extract_remitos(text: str) -> list[RemitoData]:
    lines = _merge_wrapped_uuid_lines([line.strip() for line in text.splitlines() if line.strip()])

    remitos: list[RemitoData] = []
    for line in lines:
        normalized_line = _normalize_value(line)
        match = ROW_PATTERN.match(normalized_line)
        if not match:
            continue

        numero = match.group("remito")
        remito_uid = match.group("remito_oid") or numero
        cliente = _normalize_value(match.group("cliente"))
        resto = _normalize_value(match.group("resto"))
        direccion = resto
        observacion = ""

        if cliente.lower() in {"fecha", "cliente", "subcliente", "remito", "direccion", "observacion"}:
            continue

        remitos.append(
            RemitoData(
                remito_uid=remito_uid,
                numero=numero,
                cliente=cliente,
                direccion=direccion,
                observacion=observacion,
            )
        )

    if remitos:
        return remitos

    lowered = [line.lower() for line in lines]
    table_start = None
    headers = ["fecha", "cliente", "subcliente", "remito", "direccion", "observacion"]
    for idx in range(len(lowered) - len(headers) + 1):
        if lowered[idx : idx + len(headers)] == headers:
            table_start = idx + len(headers)
            break
    if table_start is None:
        for idx, line in enumerate(lowered):
            header_block = lowered[idx : idx + 8]
            if line == "fecha" and "cliente" in header_block and "remito" in header_block and "direccion" in header_block:
                table_start = idx + next(
                    (offset + 1 for offset, header in enumerate(header_block) if header == "observacion"),
                    len(header_block),
                )
                break

    if table_start is not None:
        body: list[str] = []
        for line in lines[table_start:]:
            if line.lower().startswith("observaciones internas"):
                break
            body.append(_normalize_value(line))

        for idx, line in enumerate(body):
            remito_match = REMITO_PATTERN.search(line)
            if not remito_match:
                continue

            numero = remito_match.group("numero")

            cliente = ""
            subcliente = ""
            previous_remito_idx = max(
                (prev_idx for prev_idx in range(0, idx) if REMITO_PATTERN.search(body[prev_idx])),
                default=-1,
            )
            row_start = previous_remito_idx + 1
            date_idx = next(
                (candidate_idx for candidate_idx in range(idx - 1, row_start - 1, -1) if DATE_PATTERN.search(body[candidate_idx])),
                None,
            )
            client_lines: list[str] = []
            if date_idx is not None:
                client_lines = [
                    value
                    for value in body[date_idx + 1 : idx]
                    if not REMITO_OID_PATTERN.fullmatch(value) and value.lower() not in headers
                ]

            if client_lines:
                cliente, subcliente = _split_cliente_subcliente(client_lines)
            else:
                prev = body[idx - 1] if idx - 1 >= 0 else ""
                prevprev = body[idx - 2] if idx - 2 >= 0 else ""

                if prev and not DATE_PATTERN.search(prev) and not REMITO_OID_PATTERN.fullmatch(prev):
                    if prevprev and not DATE_PATTERN.search(prevprev) and not REMITO_OID_PATTERN.fullmatch(prevprev):
                        cliente = prevprev
                        subcliente = prev
                    else:
                        cliente = prev

            direccion = ""
            next_line = body[idx + 1] if idx + 1 < len(body) else ""
            remito_uid = numero
            if date_idx is not None:
                row_prefix = body[row_start:date_idx]
                oid_before_date = next((value for value in row_prefix if REMITO_OID_PATTERN.fullmatch(value)), "")
                if oid_before_date:
                    remito_uid = oid_before_date
            if next_line:
                oid_match = REMITO_OID_PATTERN.search(next_line)
                if oid_match:
                    remito_uid = oid_match.group("remito_oid")
                    next_line = body[idx + 2] if idx + 2 < len(body) else ""

            if next_line and not REMITO_PATTERN.search(next_line) and next_line.lower() not in headers:
                direccion = next_line

            if cliente and direccion:
                remitos.append(
                    RemitoData(
                        remito_uid=remito_uid,
                        numero=numero,
                        cliente=cliente,
                        subcliente=subcliente,
                        direccion=direccion,
                        observacion="",
                    )
                )

        if remitos:
            return remitos

    fallback_number = REMITO_PATTERN.search(text)
    if fallback_number:
        numero = fallback_number.group("numero")
        return [RemitoData(remito_uid=numero, numero=numero, cliente="", direccion="")]

    return []


def _validate_parsed_hoja(parsed: dict[str, Any]) -> None:
    errors: list[str] = []

    if not parsed.get("oid"):
        errors.append("No se detecto OID en el QR de la hoja.")
    if not parsed.get("nro_entrega"):
        errors.append("No se detecto numero de entrega en el PDF.")
    if not parsed.get("fecha"):
        errors.append("No se detecto fecha valida en el PDF.")

    remitos: list[RemitoData] = parsed.get("remitos", [])
    if len(remitos) < MIN_REMITOS_POR_HOJA:
        errors.append(
            f"La hoja debe contener al menos {MIN_REMITOS_POR_HOJA} remito(s). Detectados: {len(remitos)}."
        )

    seen: set[str] = set()
    for idx, remito in enumerate(remitos, start=1):
        if not remito.numero.strip():
            errors.append(f"Remito #{idx}: falta numero de remito.")
        if not remito.cliente.strip():
            errors.append(f"Remito {remito.numero or '#'+str(idx)}: falta cliente.")
        if not remito.direccion.strip():
            errors.append(f"Remito {remito.numero or '#'+str(idx)}: falta direccion.")

        key = remito.remito_uid.strip() or remito.numero.strip()
        if key:
            if key in seen:
                errors.append(f"Remito duplicado detectado: {key}.")
            seen.add(key)

    if errors:
        raise ValueError("Validacion de hoja fallida:\n- " + "\n- ".join(errors))


def parse_hoja_ruta_pdf(text: str, oid: uuid.UUID | None = None) -> dict[str, Any]:
    header = {
        "nro_entrega": _extract_labelled_value(text, "nro_entrega"),
        "fecha": _extract_date_value(text),
        "transporte_tipo": _extract_labelled_value(text, "transporte_tipo"),
        "flete": _extract_labelled_value(text, "flete"),
        "chofer": _extract_labelled_value(text, "chofer"),
        "acompanante": _extract_labelled_value(text, "acompanante"),
        "transporte": _extract_labelled_value(text, "transporte"),
    }

    if not header["transporte_tipo"]:
        header["transporte_tipo"] = _infer_transporte_tipo(text)

    if not header["nro_entrega"]:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        header["nro_entrega"] = first_line

    parsed_date = _parse_date(header["fecha"]) if header["fecha"] else None
    remitos = _extract_remitos(text)

    return {
        "oid": oid,
        "nro_entrega": header["nro_entrega"],
        "fecha": parsed_date,
        "transporte_tipo": header["transporte_tipo"],
        "flete": header["flete"],
        "chofer": header["chofer"],
        "acompanante": header["acompanante"],
        "transporte": header["transporte"],
        "remitos": remitos,
    }


def _import_parsed_hoja(parsed: dict[str, Any], pdf_file: Any) -> HojaRuta:
    hoja, _ = HojaRuta.objects.update_or_create(
        oid=parsed["oid"],
        defaults={
            "nro_entrega": parsed["nro_entrega"],
            "fecha": parsed["fecha"],
            "transporte_tipo": parsed["transporte_tipo"],
            "flete": parsed["flete"],
            "chofer": parsed["chofer"],
            "acompanante": parsed["acompanante"],
            "transporte": parsed["transporte"],
            "estado": HojaRuta.Estado.ABIERTA,
            "archivo_pdf_original": pdf_file,
        },
    )

    for remito_data in parsed["remitos"]:
        remito, _ = Remito.objects.update_or_create(
            hoja_ruta=hoja,
            remito_uid=remito_data.remito_uid,
            defaults={
                "numero": remito_data.numero,
                "cliente": remito_data.cliente,
                "subcliente": remito_data.subcliente,
                "direccion": remito_data.direccion,
                "observacion": remito_data.observacion,
            },
        )
        EventoTrazabilidad.objects.create(
            hoja_ruta=hoja,
            remito=remito,
            tipo=EventoTrazabilidad.Tipo.IMPORTACION,
            detalle="Remito importado desde archivo.",
        )

    EventoTrazabilidad.objects.create(
        hoja_ruta=hoja,
        tipo=EventoTrazabilidad.Tipo.IMPORTACION,
        detalle=f"Hoja importada desde archivo con {len(parsed['remitos'])} remitos.",
    )
    return hoja


@transaction.atomic
def import_hoja_ruta_pdf(pdf_file: Any) -> HojaRuta:
    text = extract_text_from_pdf(pdf_file)
    oid = extract_oid_from_qr(pdf_file)
    parsed = parse_hoja_ruta_pdf(text, oid=oid)
    _validate_parsed_hoja(parsed)
    return _import_parsed_hoja(parsed, pdf_file)
