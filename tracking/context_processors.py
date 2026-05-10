from __future__ import annotations

from tracking.models import Empresa
from tracking.services.authz import get_active_empresa_for_user, get_user_empresas


def empresa_theme(request):
    empresa = getattr(request, "active_empresa", None)
    empresas_usuario = Empresa.objects.none()

    if request.user.is_authenticated:
        empresas_usuario = get_user_empresas(request.user)
        requested_slug = request.GET.get("empresa", "").strip()
        session_slug = request.session.get("active_empresa_slug", "")
        empresa = empresa or get_active_empresa_for_user(request.user, requested_slug or session_slug)
        if empresa:
            request.session["active_empresa_slug"] = empresa.slug

    return {
        "active_empresa": empresa,
        "empresas_usuario": empresas_usuario,
        "bootstrap_css_path": empresa.theme_css if empresa else "vendor/bootstrap/css/bootstrap.min.css",
        "brand_name": f"{empresa.name} Conformados" if empresa else "Conformados",
    }
