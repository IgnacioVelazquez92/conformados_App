import re
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CierreHojaForm, EvidenciaForm, ImportPdfForm, ImportSpreadsheetForm, LoginForm, NoEntregadoForm, UserCreateForm, UserDeleteForm, UserUpdateForm, ValidacionEvidenciaForm
from .models import Evidencia, HojaRuta, Remito
from .services.authz import (
    can_close_hoja,
    can_grant_staff,
    can_import_pdf,
    can_manage_users,
    can_review_evidence,
    create_user_with_profile,
    delete_user_and_profile,
    get_or_create_profile,
    update_user_with_profile,
)
from .services.admin_ops import cerrar_hoja_ruta, validar_evidencia as validar_evidencia_service
from .services.conformados import registrar_evidencia, registrar_intento_no_entregado
from .services.import_pdf import _validate_parsed_hoja, extract_oid_from_qr, extract_text_from_pdf, import_hoja_ruta_pdf, parse_hoja_ruta_pdf
from .services.import_tabular import import_tabular_file, parse_tabular_file

REMITO_PATTERN = re.compile(r"\d{5}-\d{8}")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
PDF_EXTENSIONS = {".pdf"}


def _normalize_code(value: str) -> str:
    return re.sub(r"\W+", "", (value or "").upper())


def _find_remito_in_hoja(*, hoja: HojaRuta, remito_input: str) -> Remito:
    raw = (remito_input or "").strip()
    if not raw:
        raise ValueError("Debes informar un remito para continuar.")

    candidates: list[str] = [raw]

    hyphenated = REMITO_PATTERN.search(raw)
    if hyphenated:
        candidates.append(hyphenated.group(0))

    digits = re.sub(r"\D+", "", raw)
    if len(digits) >= 13:
        for seq in re.findall(r"\d{13}", digits):
            candidates.append(f"{seq[:5]}-{seq[5:]}")

    normalized_candidates = {_normalize_code(value) for value in candidates if value}

    for candidate in candidates:
        exact = hoja.remitos.filter(remito_uid=candidate).first() or hoja.remitos.filter(numero=candidate).first()
        if exact:
            return exact

    for remito in hoja.remitos.only("id", "remito_uid", "numero"):
        remito_uid_norm = _normalize_code(remito.remito_uid)
        remito_num_norm = _normalize_code(remito.numero)
        if remito_uid_norm in normalized_candidates or remito_num_norm in normalized_candidates:
            return remito

    raise ValueError("El remito indicado no pertenece a esta hoja de ruta.")


def _build_evidencia_file_context(evidencia: Evidencia) -> dict[str, str | bool]:
    archivo = evidencia.archivo
    if not archivo:
        return {"available": False, "url": "", "name": "", "is_image": False, "is_pdf": False}

    name = Path(archivo.name).name
    extension = Path(archivo.name).suffix.lower()
    try:
        url = archivo.url
    except ValueError:
        return {"available": False, "url": "", "name": name, "is_image": False, "is_pdf": False}

    return {
        "available": True,
        "url": url,
        "name": name,
        "is_image": extension in IMAGE_EXTENSIONS,
        "is_pdf": extension in PDF_EXTENSIONS,
    }


def root_redirect(request: HttpRequest) -> HttpResponse:
    return redirect("panel-home")


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("panel-home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("panel-home")
    else:
        form = LoginForm(request)
    return render(request, "registration/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


@login_required
@user_passes_test(can_manage_users)
def panel_crear_usuario(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            try:
                create_user_with_profile(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data.get("email", ""),
                    password=form.cleaned_data["password1"],
                    rol=form.cleaned_data["rol"],
                    share_logistica=bool(form.cleaned_data.get("share_logistica")),
                    share_cliente=bool(form.cleaned_data.get("share_cliente")),
                )
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Usuario creado correctamente.")
                return redirect("panel-home")
    else:
        form = UserCreateForm()

    return render(request, "tracking/panel_crear_usuario.html", {"form": form})


@login_required
@user_passes_test(can_manage_users)
def panel_usuarios(request: HttpRequest) -> HttpResponse:
    users = User.objects.order_by("username")
    rows = [{"user": user, "profile": get_or_create_profile(user)} for user in users]
    return render(
        request,
        "tracking/panel_usuarios.html",
        {
            "rows": rows,
            "can_grant_staff": can_grant_staff(request.user),
        },
    )


@login_required
@user_passes_test(can_manage_users)
def panel_permisos(request: HttpRequest) -> HttpResponse:
    permisos = [
        {
            "accion": "Importar PDF",
            "deposito": "Si",
            "ventas": "No",
            "jefe": "Si",
            "otro": "No",
        },
        {
            "accion": "Revisar y validar evidencias",
            "deposito": "No",
            "ventas": "No",
            "jefe": "Si",
            "otro": "No",
        },
        {
            "accion": "Cerrar hoja",
            "deposito": "No",
            "ventas": "No",
            "jefe": "Si",
            "otro": "No",
        },
        {
            "accion": "Gestionar usuarios",
            "deposito": "No",
            "ventas": "No",
            "jefe": "Si",
            "otro": "No",
        },
        {
            "accion": "Compartir link logistica",
            "deposito": "Si",
            "ventas": "No",
            "jefe": "Si",
            "otro": "No",
        },
        {
            "accion": "Compartir link cliente",
            "deposito": "No",
            "ventas": "Si",
            "jefe": "Si",
            "otro": "No",
        },
    ]
    return render(request, "tracking/panel_permisos.html", {"permisos": permisos})


@login_required
@user_passes_test(can_manage_users)
def panel_editar_usuario(request: HttpRequest, user_id: int) -> HttpResponse:
    usuario = get_object_or_404(User, pk=user_id)
    profile = get_or_create_profile(usuario)
    actor_can_grant_staff = can_grant_staff(request.user)

    if request.method == "POST":
        form = UserUpdateForm(request.POST)
        if not actor_can_grant_staff:
            form.fields.pop("is_staff", None)
        if form.is_valid():
            is_staff_target = bool(form.cleaned_data.get("is_staff")) if actor_can_grant_staff else usuario.is_staff
            try:
                update_user_with_profile(
                    user=usuario,
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data.get("email", ""),
                    rol=form.cleaned_data["rol"],
                    share_logistica=bool(form.cleaned_data.get("share_logistica")),
                    share_cliente=bool(form.cleaned_data.get("share_cliente")),
                    is_active=bool(form.cleaned_data.get("is_active")),
                    is_staff=is_staff_target,
                    password=form.cleaned_data.get("password", ""),
                )
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect("panel-usuarios")
    else:
        form = UserUpdateForm(
            initial={
                "username": usuario.username,
                "email": usuario.email,
                "rol": profile.rol,
                "share_logistica": profile.share_logistica,
                "share_cliente": profile.share_cliente,
                "is_active": usuario.is_active,
                "is_staff": usuario.is_staff,
            }
        )
        if not actor_can_grant_staff:
            form.fields.pop("is_staff", None)

    return render(
        request,
        "tracking/panel_editar_usuario.html",
        {
            "form": form,
            "usuario": usuario,
            "actor_can_grant_staff": actor_can_grant_staff,
        },
    )


@login_required
@user_passes_test(can_manage_users)
def panel_eliminar_usuario(request: HttpRequest, user_id: int) -> HttpResponse:
    usuario = get_object_or_404(User, pk=user_id)
    if usuario == request.user:
        messages.error(request, "No podes eliminar tu propio usuario.")
        return redirect("panel-usuarios")

    if request.method == "POST":
        form = UserDeleteForm(request.POST)
        if form.is_valid():
            delete_user_and_profile(user=usuario)
            messages.success(request, "Usuario eliminado correctamente.")
            return redirect("panel-usuarios")
    else:
        form = UserDeleteForm()

    return render(request, "tracking/panel_eliminar_usuario.html", {"form": form, "usuario": usuario})


@login_required
def panel_home(request: HttpRequest) -> HttpResponse:
    estado = request.GET.get("estado", "").strip()
    q = request.GET.get("q", "").strip()

    hojas_qs = HojaRuta.objects.order_by("-fecha")
    if estado:
        hojas_qs = hojas_qs.filter(estado=estado)
    if q:
        hojas_qs = hojas_qs.filter(nro_entrega__icontains=q)

    hojas = hojas_qs[:50]
    return render(
        request,
        "tracking/panel_home.html",
        {
            "hojas": hojas,
            "estado": estado,
            "q": q,
            "estados": HojaRuta.Estado.choices,
            "can_import_pdf": can_import_pdf(request.user),
            "can_review_evidence": can_review_evidence(request.user),
            "can_manage_users": can_manage_users(request.user),
            "can_close_hoja": can_close_hoja(request.user),
        },
    )


@login_required
def panel_hoja_detalle(request: HttpRequest, oid: str) -> HttpResponse:
    hoja = get_object_or_404(HojaRuta, oid=oid)
    remito_estado = request.GET.get("remito_estado", "").strip()
    q = request.GET.get("q", "").strip()

    remitos_qs = hoja.remitos.order_by("id")
    if remito_estado:
        remitos_qs = remitos_qs.filter(estado=remito_estado)
    if q:
        remitos_qs = remitos_qs.filter(numero__icontains=q)

    remitos = remitos_qs[:200]
    evidencias = Evidencia.objects.filter(hoja_ruta=hoja).select_related("remito").order_by("-fecha_carga")[:30]
    intentos = hoja.intentos.select_related("remito").order_by("-fecha_evento")[:30]
    profile = get_or_create_profile(request.user)
    logistica_url = request.build_absolute_uri(f"/conformados/logistica/{hoja.oid}/")
    cliente_url = request.build_absolute_uri(f"/conformados/cliente/{hoja.oid}/")
    return render(
        request,
        "tracking/panel_hoja_detalle.html",
        {
            "hoja": hoja,
            "remitos": remitos,
            "evidencias": evidencias,
            "intentos": intentos,
            "remito_estado": remito_estado,
            "q": q,
            "remito_estados": Remito.Estado.choices,
            "profile": profile,
            "can_share_logistica": profile.can_share_logistica(),
            "can_share_cliente": profile.can_share_cliente(),
            "logistica_url": logistica_url,
            "cliente_url": cliente_url,
        },
    )


@login_required
def panel_evidencias(request: HttpRequest) -> HttpResponse:
    if not can_review_evidence(request.user):
        messages.error(request, "No tenes permisos para revisar evidencias.")
        return redirect("panel-home")

    evidencias = Evidencia.objects.select_related("hoja_ruta", "remito").order_by("-fecha_carga")[:50]
    return render(
        request,
        "tracking/panel_evidencias.html",
        {
            "evidencias": evidencias,
        },
    )


@login_required
def panel_importar_pdf(request: HttpRequest) -> HttpResponse:
    if not can_import_pdf(request.user):
        messages.error(request, "No tenes permisos para importar PDF.")
        return redirect("panel-home")

    preview = None
    if request.method == "POST":
        form = ImportPdfForm(request.POST, request.FILES)
        if form.is_valid():
            action = request.POST.get("action", "preview")
            pdf_file = form.cleaned_data["pdf_file"]
            try:
                text = extract_text_from_pdf(pdf_file)
                oid = extract_oid_from_qr(pdf_file)
                parsed = parse_hoja_ruta_pdf(text, oid=oid)
                _validate_parsed_hoja(parsed)
            except Exception as exc:
                form.add_error("pdf_file", str(exc))
            else:
                preview = parsed
                if action == "import":
                    hoja = import_hoja_ruta_pdf(pdf_file)
                    messages.success(request, f"Hoja {hoja.nro_entrega} importada correctamente.")
                    return redirect("panel-home")
    else:
        form = ImportPdfForm()

    return render(request, "tracking/importar_pdf.html", {"form": form, "preview": preview})


@login_required
def panel_importar_excel(request: HttpRequest) -> HttpResponse:
    if not can_import_pdf(request.user):
        messages.error(request, "No tenes permisos para importar archivos.")
        return redirect("panel-home")

    preview = None
    if request.method == "POST":
        form = ImportSpreadsheetForm(request.POST, request.FILES)
        if form.is_valid():
            action = request.POST.get("action", "preview")
            archivo = form.cleaned_data["archivo"]
            try:
                parsed = parse_tabular_file(archivo)
                _validate_parsed_hoja(parsed)
            except Exception as exc:
                form.add_error("archivo", str(exc))
            else:
                preview = parsed
                if action == "import":
                    hojas, remitos = import_tabular_file(archivo, archivo)
                    messages.success(request, f"Importacion completada: {hojas} hoja(s), {remitos} remito(s).")
                    return redirect("panel-home")
    else:
        form = ImportSpreadsheetForm()

    return render(request, "tracking/importar_excel.html", {"form": form, "preview": preview})


def conformados_portal(request: HttpRequest, canal: str, oid: str) -> HttpResponse:
    hoja = HojaRuta.objects.filter(oid=oid).first()
    if not hoja:
        return render(request, "tracking/estado_hoja.html", {"estado": "inexistente", "canal": canal, "oid": oid})
    if hoja.estado == HojaRuta.Estado.CERRADA:
        return render(request, "tracking/estado_hoja.html", {"estado": "cerrada", "canal": canal, "oid": oid})

    remito_query = request.GET.get("remito", "").strip()
    modo = request.GET.get("modo", "evidencia").strip()
    if modo not in {"evidencia", "no_entregado"}:
        modo = "evidencia"

    remito_seleccionado = None
    remito_error = ""
    if remito_query:
        try:
            remito_seleccionado = _find_remito_in_hoja(hoja=hoja, remito_input=remito_query)
        except ValueError as exc:
            remito_error = str(exc)

    remitos = hoja.remitos.order_by("id")
    return render(
        request,
        "tracking/conformados_portal.html",
        {
            "hoja": hoja,
            "remitos": remitos,
            "evidencia_form": EvidenciaForm(),
            "no_entregado_form": NoEntregadoForm(),
            "canal": canal,
            "remito_query": remito_query,
            "remito_seleccionado": remito_seleccionado,
            "remito_error": remito_error,
            "modo": modo,
        },
    )


def subir_evidencia(request: HttpRequest, canal: str, oid: str) -> HttpResponse:
    hoja = get_object_or_404(HojaRuta, oid=oid)
    if hoja.estado == HojaRuta.Estado.CERRADA:
        return render(request, "tracking/estado_hoja.html", {"estado": "cerrada", "canal": canal, "oid": oid})

    form = EvidenciaForm(request.POST, request.FILES)
    try:
        remito = _find_remito_in_hoja(hoja=hoja, remito_input=request.POST.get("remito_uid", ""))
    except ValueError as exc:
        messages.error(request, str(exc))
        remito_query = request.POST.get("remito_uid", "").strip()
        return redirect(f"/conformados/{canal}/{oid}/?remito={remito_query}&modo=evidencia")

    if form.is_valid():
        try:
            registrar_evidencia(
                hoja=hoja,
                remito=remito,
                canal=canal,
                archivo=form.cleaned_data["archivo_final"],
                comentario=form.cleaned_data.get("comentario", ""),
                origen=form.cleaned_data.get("origen", ""),
                permitir_duplicada=bool(form.cleaned_data.get("confirmar_duplicada")),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Evidencia cargada correctamente.")
            return redirect("conformados-portal", canal=canal, oid=oid)

    remitos = hoja.remitos.order_by("id")
    return render(
        request,
        "tracking/conformados_portal.html",
        {
            "hoja": hoja,
            "remitos": remitos,
            "evidencia_form": form,
            "no_entregado_form": NoEntregadoForm(),
            "canal": canal,
            "remito_query": remito.remito_uid,
            "remito_seleccionado": remito,
            "remito_error": "",
            "modo": "evidencia",
        },
    )


def no_entregado(request: HttpRequest, canal: str, oid: str) -> HttpResponse:
    hoja = get_object_or_404(HojaRuta, oid=oid)
    if hoja.estado == HojaRuta.Estado.CERRADA:
        return render(request, "tracking/estado_hoja.html", {"estado": "cerrada", "canal": canal, "oid": oid})

    form = NoEntregadoForm(request.POST)
    try:
        remito = _find_remito_in_hoja(hoja=hoja, remito_input=request.POST.get("remito_uid", ""))
    except ValueError as exc:
        messages.error(request, str(exc))
        remito_query = request.POST.get("remito_uid", "").strip()
        return redirect(f"/conformados/{canal}/{oid}/?remito={remito_query}&modo=no_entregado")

    if form.is_valid():
        try:
            registrar_intento_no_entregado(
                hoja=hoja,
                remito=remito,
                canal=canal,
                motivo=form.cleaned_data["motivo"],
                comentario=form.cleaned_data.get("comentario", ""),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Intento de no entrega registrado.")
            return redirect("conformados-portal", canal=canal, oid=oid)

    remitos = hoja.remitos.order_by("id")
    return render(
        request,
        "tracking/conformados_portal.html",
        {
            "hoja": hoja,
            "remitos": remitos,
            "evidencia_form": EvidenciaForm(),
            "no_entregado_form": form,
            "canal": canal,
            "remito_query": remito.remito_uid,
            "remito_seleccionado": remito,
            "remito_error": "",
            "modo": "no_entregado",
        },
    )


@login_required
def validar_evidencia(request: HttpRequest, evidencia_id: int) -> HttpResponse:
    if not can_review_evidence(request.user):
        messages.error(request, "No tenes permisos para validar evidencias.")
        return redirect("panel-home")

    evidencia = get_object_or_404(Evidencia.objects.select_related("hoja_ruta", "remito"), pk=evidencia_id)
    if request.method == "POST":
        form = ValidacionEvidenciaForm(request.POST)
        if form.is_valid():
            try:
                validar_evidencia_service(
                    evidencia=evidencia,
                    estado=form.cleaned_data["estado"],
                    comentario=form.cleaned_data.get("comentario", ""),
                )
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Evidencia validada correctamente.")
                return redirect("panel-evidencias")
    else:
        form = ValidacionEvidenciaForm(initial={"estado": evidencia.estado_validacion})

    return render(
        request,
        "tracking/validar_evidencia.html",
        {"evidencia": evidencia, "form": form, "archivo": _build_evidencia_file_context(evidencia)},
    )


@login_required
def cerrar_hoja(request: HttpRequest, oid: str) -> HttpResponse:
    if not can_close_hoja(request.user):
        messages.error(request, "No tenes permisos para cerrar hojas.")
        return redirect("panel-home")

    hoja = get_object_or_404(HojaRuta, oid=oid)
    if request.method == "POST":
        form = CierreHojaForm(request.POST)
        if form.is_valid():
            try:
                cerrar_hoja_ruta(hoja=hoja, comentario=form.cleaned_data.get("comentario", ""))
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Hoja cerrada correctamente.")
                return redirect("panel-home")
    else:
        form = CierreHojaForm()

    return render(
        request,
        "tracking/cerrar_hoja.html",
        {"hoja": hoja, "form": form},
    )
