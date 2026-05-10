from __future__ import annotations

from django.contrib.auth.models import User

from tracking.models import Empresa, RoleDefinition, UserProfile


def get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_user_empresas(user: User):
    if not user.is_authenticated:
        return Empresa.objects.none()
    if user.is_superuser:
        return Empresa.objects.filter(active=True)

    profile = get_or_create_profile(user)
    empresas = profile.empresas.filter(active=True)
    if not empresas.exists() and profile.empresa_principal_id:
        empresas = Empresa.objects.filter(pk=profile.empresa_principal_id, active=True)
    return empresas


def user_can_access_empresa(user: User, empresa: Empresa) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_empresas(user).filter(pk=empresa.pk).exists()


def get_active_empresa_for_user(user: User, requested_slug: str = "") -> Empresa | None:
    empresas = get_user_empresas(user)
    if requested_slug:
        requested = empresas.filter(slug=requested_slug, active=True).first()
        if requested:
            return requested
    profile = get_or_create_profile(user) if user.is_authenticated else None
    if profile and profile.empresa_principal_id and empresas.filter(pk=profile.empresa_principal_id).exists():
        return profile.empresa_principal
    return empresas.order_by("name").first()


def create_user_with_profile(
    *,
    username: str,
    email: str,
    password: str,
    rol: str,
    empresa_principal: Empresa | None,
    empresas: list[Empresa],
    share_logistica: bool,
    share_cliente: bool,
) -> User:
    user = User.objects.create_user(username=username, email=email, password=password)
    profile = UserProfile.objects.create(
        user=user,
        rol=rol,
        empresa_principal=empresa_principal,
        share_logistica=share_logistica,
        share_cliente=share_cliente,
    )
    if empresas:
        profile.empresas.set(empresas)
    return user


def can_manage_users(user: User) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = get_or_create_profile(user)
    return RoleDefinition.permission_map(profile.rol)["can_manage_users"]


def can_import_pdf(user: User) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_or_create_profile(user)
    return RoleDefinition.permission_map(profile.rol)["can_import_pdf"]


def can_review_evidence(user: User) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_or_create_profile(user)
    return RoleDefinition.permission_map(profile.rol)["can_review_evidence"]


def can_close_hoja(user: User) -> bool:
    return can_review_evidence(user)


def can_grant_staff(user: User) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_superuser


def update_user_with_profile(
    *,
    user: User,
    username: str,
    email: str,
    rol: str,
    empresa_principal: Empresa | None,
    empresas: list[Empresa],
    share_logistica: bool,
    share_cliente: bool,
    is_active: bool,
    is_staff: bool,
    password: str = "",
) -> User:
    profile = get_or_create_profile(user)

    user.username = username
    user.email = email
    user.is_active = is_active
    user.is_staff = is_staff
    if password:
        user.set_password(password)
    user.save()

    profile.rol = rol
    profile.empresa_principal = empresa_principal
    profile.share_logistica = share_logistica
    profile.share_cliente = share_cliente
    profile.save()
    profile.empresas.set(empresas)
    return user


def delete_user_and_profile(*, user: User) -> None:
    profile = UserProfile.objects.filter(user=user).first()
    if profile:
        profile.delete()
    user.delete()
