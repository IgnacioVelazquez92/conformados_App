from django import forms
from django.conf import settings
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
    archivo_camera = forms.FileField(
        label="Sacar foto del conformado",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
    )
    archivo = forms.FileField(
        label="Subir imagen o PDF",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*,.pdf,application/pdf"}),
    )
    comentario = forms.CharField(label="Comentario", required=False, widget=forms.Textarea)
    origen = forms.CharField(label="Origen", required=False)
    confirmar_duplicada = forms.BooleanField(label="Confirmo que deseo cargar otra evidencia", required=False)

    def _validate_evidence_file(self, archivo):
        name = (archivo.name or "").lower()
        content_type = getattr(archivo, "content_type", "") or ""
        is_pdf = name.endswith(".pdf") or content_type == "application/pdf"
        is_image = any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")) or content_type.startswith("image/")
        if not is_image and not is_pdf:
            raise forms.ValidationError("El archivo debe ser una imagen o PDF.")

        max_size_mb = settings.EVIDENCIA_MAX_PDF_SIZE_MB if is_pdf else settings.EVIDENCIA_MAX_IMAGE_SIZE_MB
        max_size_bytes = max_size_mb * 1024 * 1024
        if getattr(archivo, "size", 0) > max_size_bytes:
            raise forms.ValidationError(f"El archivo no puede pesar mas de {max_size_mb} MB.")
        return archivo

    def clean_archivo_camera(self):
        archivo = self.cleaned_data.get("archivo_camera")
        if not archivo:
            return archivo
        name = (archivo.name or "").lower()
        content_type = getattr(archivo, "content_type", "") or ""
        if not any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")) and not content_type.startswith("image/"):
            raise forms.ValidationError("La foto tomada con camara debe ser una imagen.")
        return self._validate_evidence_file(archivo)

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo
        return self._validate_evidence_file(archivo)

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data
        archivo_camera = cleaned_data.get("archivo_camera")
        archivo = cleaned_data.get("archivo")
        if archivo_camera and archivo:
            raise forms.ValidationError("Usa solo una opcion: sacar foto o subir archivo.")
        if not archivo_camera and not archivo:
            raise forms.ValidationError("Debes sacar una foto o subir una imagen/PDF.")
        cleaned_data["archivo_final"] = archivo_camera or archivo
        return cleaned_data


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
