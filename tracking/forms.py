from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ImportPdfForm(forms.Form):
    pdf_file = forms.FileField(label="PDF de Hoja de Ruta")

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data["pdf_file"]
        name = (pdf_file.name or "").lower()
        content_type = getattr(pdf_file, "content_type", "") or ""
        if not name.endswith(".pdf") and content_type != "application/pdf":
            raise forms.ValidationError("El archivo debe ser un PDF.")
        return pdf_file


class ImportSpreadsheetForm(forms.Form):
    archivo = forms.FileField(label="Excel o CSV de Hoja de Ruta")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        name = (archivo.name or "").lower()
        content_type = getattr(archivo, "content_type", "") or ""
        allowed_extensions = (".xlsx", ".xlsm", ".csv")
        allowed_types = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
            "application/csv",
        )
        if not any(name.endswith(ext) for ext in allowed_extensions) and content_type not in allowed_types:
            raise forms.ValidationError("El archivo debe ser Excel (.xlsx) o CSV.")
        return archivo


class EvidenciaForm(forms.Form):
    archivo = forms.FileField(label="Foto o archivo de conformado")
    comentario = forms.CharField(label="Comentario", required=False, widget=forms.Textarea)
    origen = forms.CharField(label="Origen", required=False)
    confirmar_duplicada = forms.BooleanField(label="Confirmo que deseo cargar otra evidencia", required=False)

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        name = (archivo.name or "").lower()
        content_type = getattr(archivo, "content_type", "") or ""
        if not any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".pdf")) and not content_type.startswith(("image/", "application/pdf")):
            raise forms.ValidationError("El archivo debe ser una imagen o PDF.")
        return archivo


NO_ENTREGADO_CHOICES = [
    ("cliente_ausente", "Cliente ausente"),
    ("fuera_de_horario", "Fuera de horario"),
    ("direccion_incorrecta", "Direccion incorrecta"),
    ("cliente_rechaza_entrega", "Cliente rechaza entrega"),
    ("falta_documentacion", "Falta documentacion"),
    ("acceso_restringido", "Acceso restringido"),
    ("otro", "Otro"),
]


class NoEntregadoForm(forms.Form):
    motivo = forms.ChoiceField(choices=NO_ENTREGADO_CHOICES)
    comentario = forms.CharField(label="Comentario", required=False, widget=forms.Textarea)


class ValidacionEvidenciaForm(forms.Form):
    estado = forms.ChoiceField(
        choices=[
            ("validada", "Validada"),
            ("observada", "Observada"),
            ("rechazada", "Rechazada"),
        ]
    )
    comentario = forms.CharField(label="Comentario", required=False, widget=forms.Textarea)

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get("estado")
        comentario = (cleaned_data.get("comentario") or "").strip()
        if estado in {"observada", "rechazada"} and not comentario:
            raise forms.ValidationError("El comentario es obligatorio para observaciones o rechazos.")
        return cleaned_data


class CierreHojaForm(forms.Form):
    comentario = forms.CharField(label="Comentario", required=False, widget=forms.Textarea)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label="Contrasena", strip=False, widget=forms.PasswordInput)


class UserCreateForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    email = forms.EmailField(label="Email", required=False)
    password1 = forms.CharField(label="Contrasena", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)
    rol = forms.ChoiceField(
        label="Rol",
        choices=[
            ("deposito", "Deposito"),
            ("ventas", "Ventas"),
            ("jefe", "Jefe"),
            ("otro", "Otro"),
        ],
    )
    share_logistica = forms.BooleanField(label="Permitir compartir link logistica", required=False)
    share_cliente = forms.BooleanField(label="Permitir compartir link cliente", required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Las contrasenas no coinciden.")
        return cleaned_data


class UserUpdateForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    email = forms.EmailField(label="Email", required=False)
    password = forms.CharField(label="Nueva contrasena (opcional)", required=False, widget=forms.PasswordInput)
    rol = forms.ChoiceField(
        label="Rol",
        choices=[
            ("deposito", "Deposito"),
            ("ventas", "Ventas"),
            ("jefe", "Jefe"),
            ("otro", "Otro"),
        ],
    )
    share_logistica = forms.BooleanField(label="Permitir compartir link logistica", required=False)
    share_cliente = forms.BooleanField(label="Permitir compartir link cliente", required=False)
    is_active = forms.BooleanField(label="Usuario activo", required=False)
    is_staff = forms.BooleanField(label="Acceso staff", required=False)


class UserDeleteForm(forms.Form):
    confirm = forms.BooleanField(label="Confirmo eliminar este usuario")