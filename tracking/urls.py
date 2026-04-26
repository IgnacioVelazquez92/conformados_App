from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("panel/", views.panel_home, name="panel-home"),
    path("panel/permisos/", views.panel_permisos, name="panel-permisos"),
    path("panel/usuarios/", views.panel_usuarios, name="panel-usuarios"),
    path("panel/usuarios/nuevo/", views.panel_crear_usuario, name="panel-crear-usuario"),
    path("panel/usuarios/<int:user_id>/editar/", views.panel_editar_usuario, name="panel-editar-usuario"),
    path("panel/usuarios/<int:user_id>/eliminar/", views.panel_eliminar_usuario, name="panel-eliminar-usuario"),
    path("panel/hojas/<uuid:oid>/", views.panel_hoja_detalle, name="panel-hoja-detalle"),
    path("panel/importar/pdf/", views.panel_importar_pdf, name="panel-importar-pdf"),
    path("panel/importar/excel/", views.panel_importar_excel, name="panel-importar-excel"),
    path("panel/evidencias/", views.panel_evidencias, name="panel-evidencias"),
    path("panel/evidencias/<int:evidencia_id>/validar/", views.validar_evidencia, name="panel-validar-evidencia"),
    path("panel/hojas/<uuid:oid>/cerrar/", views.cerrar_hoja, name="panel-cerrar-hoja"),
    path("conformados/<str:canal>/<uuid:oid>/", views.conformados_portal, name="conformados-portal"),
    path("conformados/<str:canal>/<uuid:oid>/subir/", views.subir_evidencia, name="conformados-subir"),
    path("conformados/<str:canal>/<uuid:oid>/no-entregado/", views.no_entregado, name="conformados-no-entregado"),
]
