from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Empresa, Evidencia, EventoTrazabilidad, HojaRuta, IntentoAccesoPortal, IntentoEntrega, PublicAlertRecipient, Remito, RoleDefinition, UserProfile


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "slug", "active", "theme_css", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "code", "slug", "erp_identifier")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


class RemitoInline(admin.TabularInline):
    model = Remito
    extra = 0
    fields = ("numero", "remito_uid", "cliente", "subcliente", "direccion", "estado", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


class EvidenciaInline(admin.TabularInline):
    model = Evidencia
    extra = 0
    fields = ("remito", "canal", "archivo", "estado_validacion", "fecha_carga", "origen", "comentario")
    readonly_fields = ("fecha_carga",)
    show_change_link = True


class IntentoEntregaInline(admin.TabularInline):
    model = IntentoEntrega
    extra = 0
    fields = ("remito", "canal", "motivo", "comentario", "fecha_evento")
    readonly_fields = ("fecha_evento",)
    show_change_link = True


class EventoTrazabilidadInline(admin.TabularInline):
    model = EventoTrazabilidad
    extra = 0
    fields = ("tipo", "remito", "canal", "detalle", "fecha_evento")
    readonly_fields = ("fecha_evento",)
    show_change_link = True


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    max_num = 1
    filter_horizontal = ("empresas",)
    fields = ("rol", "empresa_principal", "empresas", "share_logistica", "share_cliente")


class MultiEmpresaUserCreationForm(UserCreationForm):
    rol = forms.ChoiceField(label="Rol", choices=())
    empresa_principal = forms.ModelChoiceField(
        label="Empresa principal",
        queryset=Empresa.objects.none(),
        empty_label=None,
    )
    empresas = forms.ModelMultipleChoiceField(
        label="Empresas autorizadas",
        queryset=Empresa.objects.none(),
        required=False,
        widget=forms.SelectMultiple,
    )
    share_logistica = forms.BooleanField(label="Permitir compartir link logistica", required=False)
    share_cliente = forms.BooleanField(label="Permitir compartir link cliente", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].choices = list(
            RoleDefinition.objects.filter(active=True).order_by("label").values_list("code", "label")
        )
        empresas = Empresa.objects.filter(active=True).order_by("name")
        self.fields["empresa_principal"].queryset = empresas
        self.fields["empresas"].queryset = empresas

    def clean(self):
        cleaned_data = super().clean()
        empresa_principal = cleaned_data.get("empresa_principal")
        empresas = list(cleaned_data.get("empresas") or [])
        if empresa_principal and empresa_principal not in empresas:
            empresas.append(empresa_principal)
            cleaned_data["empresas"] = empresas
        return cleaned_data

    def save(self, commit=True):
        return super().save(commit=commit)


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = MultiEmpresaUserCreationForm
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "is_active",
        "is_staff",
        "empresa_principal",
        "empresas_autorizadas",
    )
    list_select_related = ("profile__empresa_principal",)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "rol",
                    "empresa_principal",
                    "empresas",
                    "share_logistica",
                    "share_cliente",
                ),
            },
        ),
    )

    @admin.display(description="Empresa principal")
    def empresa_principal(self, obj: User) -> str:
        profile = getattr(obj, "profile", None)
        return profile.empresa_principal.name if profile and profile.empresa_principal else "-"

    @admin.display(description="Empresas autorizadas")
    def empresas_autorizadas(self, obj: User) -> str:
        profile = getattr(obj, "profile", None)
        if not profile:
            return "-"
        empresas = list(profile.empresas.order_by("name").values_list("name", flat=True))
        return ", ".join(empresas) if empresas else "-"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and isinstance(form, MultiEmpresaUserCreationForm):
            profile = UserProfile.objects.create(
                user=obj,
                rol=form.cleaned_data["rol"],
                empresa_principal=form.cleaned_data["empresa_principal"],
                share_logistica=bool(form.cleaned_data.get("share_logistica")),
                share_cliente=bool(form.cleaned_data.get("share_cliente")),
            )
            profile.empresas.set(form.cleaned_data.get("empresas") or [])


@admin.register(HojaRuta)
class HojaRutaAdmin(admin.ModelAdmin):
    list_display = (
        "oid",
        "empresa",
        "nro_entrega",
        "fecha",
        "estado",
        "transporte_tipo",
        "flete",
        "chofer",
        "acompanante",
        "transporte",
        "archivo_pdf_original",
        "created_at",
        "updated_at",
    )
    list_filter = ("empresa", "estado", "fecha", "transporte_tipo", "created_at")
    search_fields = ("oid", "nro_entrega", "chofer", "transporte", "empresa__name", "empresa__code")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Identificacion",
            {"fields": ("empresa", "oid", "nro_entrega", "fecha", "estado", "archivo_pdf_original")},
        ),
        (
            "Transporte",
            {"fields": ("transporte_tipo", "flete", "chofer", "acompanante", "transporte")},
        ),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    inlines = (RemitoInline, EvidenciaInline, IntentoEntregaInline, EventoTrazabilidadInline)


@admin.register(Remito)
class RemitoAdmin(admin.ModelAdmin):
    list_display = ("numero", "remito_uid", "empresa", "hoja_ruta", "fecha", "cliente", "subcliente", "direccion", "estado", "created_at")
    list_filter = ("empresa", "estado", "fecha", "hoja_ruta__estado", "created_at")
    search_fields = ("numero", "remito_uid", "cliente", "subcliente", "direccion", "hoja_ruta__oid", "hoja_ruta__nro_entrega")
    readonly_fields = ("created_at",)


@admin.register(RoleDefinition)
class RoleDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "code",
        "active",
        "can_import_pdf",
        "can_review_evidence",
        "can_audit_remitos",
        "can_close_hoja",
        "can_manage_users",
        "share_logistica_default",
        "share_cliente_default",
    )
    list_editable = (
        "active",
        "can_import_pdf",
        "can_review_evidence",
        "can_audit_remitos",
        "can_close_hoja",
        "can_manage_users",
        "share_logistica_default",
        "share_cliente_default",
    )
    list_filter = ("active",)
    search_fields = ("code", "label")
    ordering = ("label",)


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "hoja_ruta", "remito", "remito_uid", "canal", "estado_validacion", "fecha_carga", "archivo")
    list_filter = ("empresa", "canal", "estado_validacion", "fecha_carga")
    search_fields = ("remito__numero", "remito__remito_uid", "hoja_ruta__oid", "hoja_ruta__nro_entrega", "comentario", "origen")
    readonly_fields = ("fecha_carga",)

    @admin.display(description="OID remito")
    def remito_uid(self, obj: Evidencia) -> str:
        return obj.remito.remito_uid


@admin.register(IntentoEntrega)
class IntentoEntregaAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "hoja_ruta", "remito", "remito_uid", "canal", "motivo", "fecha_evento")
    list_filter = ("empresa", "canal", "motivo", "fecha_evento")
    search_fields = ("remito__numero", "remito__remito_uid", "hoja_ruta__oid", "hoja_ruta__nro_entrega", "comentario")
    readonly_fields = ("fecha_evento",)

    @admin.display(description="OID remito")
    def remito_uid(self, obj: IntentoEntrega) -> str:
        return obj.remito.remito_uid


@admin.register(IntentoAccesoPortal)
class IntentoAccesoPortalAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "canal", "oid", "motivo", "ip_address", "fecha_evento")
    list_filter = ("empresa", "canal", "motivo", "fecha_evento")
    search_fields = ("oid", "ip_address", "user_agent", "path", "detalle")
    readonly_fields = ("fecha_evento",)


@admin.register(PublicAlertRecipient)
class PublicAlertRecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("email", "name")
    readonly_fields = ("created_at",)


@admin.register(EventoTrazabilidad)
class EventoTrazabilidadAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "tipo", "hoja_ruta", "remito", "remito_uid", "canal", "fecha_evento")
    list_filter = ("empresa", "tipo", "canal", "fecha_evento")
    search_fields = ("hoja_ruta__oid", "hoja_ruta__nro_entrega", "remito__numero", "remito__remito_uid", "detalle")
    readonly_fields = ("fecha_evento",)

    @admin.display(description="OID remito")
    def remito_uid(self, obj: EventoTrazabilidad) -> str:
        return obj.remito.remito_uid if obj.remito else ""


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "empresa_principal", "share_logistica", "share_cliente")
    list_filter = ("rol", "empresa_principal", "share_logistica", "share_cliente")
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("empresas",)
