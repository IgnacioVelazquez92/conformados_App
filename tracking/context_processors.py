from __future__ import annotations

from tracking.models import Empresa
from tracking.services.authz import get_active_empresa_for_user


def empresa_theme(request):
    empresa = getattr(request, "active_empresa", None)
    if empresa is None and request.user.is_authenticated:
        empresa = get_active_empresa_for_user(request.user, request.GET.get("empresa", ""))
    if empresa is None:
        empresa = Empresa.objects.filter(active=True).order_by("name").first()

    return {
        "active_empresa": empresa,
        "empresas_usuario": get_user_empresas(request.user) if request.user.is_authenticated else Empresa.objects.none(),
        "bootstrap_css_path": empresa.theme_css if empresa else "vendor/bootstrap/css/bootstrap.min.css",
        "brand_name": f"{empresa.name} Conformados" if empresa else "Conformados",
    }
