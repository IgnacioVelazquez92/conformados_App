# Estructura tecnica viva

## manage.py

Punto de entrada para comandos administrativos de Django.

- `main()`: carga `DJANGO_SETTINGS_MODULE` (default `config.settings.development`) y ejecuta comandos.

## requirements.txt

Dependencias base del backend Django.

- `Django`: framework web principal.
- `psycopg[binary]`: conexion PostgreSQL.
- `dj-database-url`: lectura de `DATABASE_URL` para Railway/PostgreSQL.
- `django-storages` + `boto3`: integracion con bucket object storage.
- `gunicorn`: servidor WSGI de produccion.
- `whitenoise`: servicio de archivos estaticos en produccion.
- `openpyxl`: lectura de Excel.
- `PyMuPDF`, `numpy`, `opencv-python-headless`: lectura de PDF y QR sin dependencias graficas.

## Procfile

Comando de arranque para Railway.

- ejecuta migraciones.
- asegura el superusuario inicial con `ensure_initial_admin`.
- ejecuta `collectstatic`.
- levanta Gunicorn contra `config.wsgi:application`.

## railway.json

Configuracion declarativa de Railway.

- `build.buildCommand`: ejecuta `python manage.py collectstatic --noinput` durante el build.
- `deploy.startCommand`: ejecuta migraciones, asegura el admin inicial y levanta Gunicorn.

## .env.example

Variables de entorno de referencia para configuracion local y despliegue.

- `DJANGO_SETTINGS_MODULE`: selecciona settings de `development` o `production`.
- `SQLITE_PATH`: ruta opcional de base local SQLite.
- `DB_*`: conexion PostgreSQL para produccion.
- `DATABASE_URL`: conexion PostgreSQL completa usada por Railway.
- `PG*`: variables PostgreSQL generadas por Railway cuando no se usa `DATABASE_URL`.
- `DB_SSL_REQUIRE`: activa SSL al parsear `DATABASE_URL`.
- `DJANGO_SECURE_*`: controles de redireccion HTTPS y HSTS en produccion.
- `DJANGO_RUN_STARTUP_COMMANDS`: permite ejecutar migraciones/admin desde WSGI como respaldo.
- `WHITENOISE_USE_FINDERS`: permite servir estaticos desde finders si no existe `staticfiles`.
- `RAILWAY_CHECK_DB_ON_READY`: activa diagnostico opcional de DB en `AppConfig.ready`.
- `INITIAL_ADMIN_*`: credenciales privadas del superusuario idempotente; no se documentan con valores reales en `.env.example`.
- `AWS_*`: parametros para storage bucket en produccion.
- `BUCKET_*`: variables del bucket generadas por Railway, equivalentes a `AWS_*`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origenes HTTPS confiables separados por coma.

## config/settings/base.py

Configuracion comun de Django para todos los entornos.

- apps, middleware, templates e internacionalizacion.
- static/media y defaults globales.
- `STATICFILES_DIRS`: incluye `static/` del proyecto para servir assets frontend versionados localmente.
- usa WhiteNoise middleware para servir archivos estaticos en produccion.
- `EVIDENCIA_MAX_IMAGE_SIZE_MB`, `EVIDENCIA_MAX_PDF_SIZE_MB`: limites de tamano para evidencias.
- `EVIDENCIA_RATE_LIMIT_COUNT`, `EVIDENCIA_RATE_LIMIT_WINDOW_SECONDS`: limite de frecuencia para cargas de evidencia (default 10 por minuto).
- `NO_ENTREGADO_RATE_LIMIT_COUNT`, `NO_ENTREGADO_RATE_LIMIT_WINDOW_SECONDS`: limite de frecuencia para intentos no entregados.
- `PUBLIC_LINK_INVALID_RATE_LIMIT_COUNT`, `PUBLIC_LINK_INVALID_RATE_LIMIT_WINDOW_SECONDS`: limite suave para probes invalidos a links publicos.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_HOST_USER`, `EMAIL_FROM`, `PUBLIC_ALERT_RECIPIENTS`: configuracion SMTP para avisos.
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REFRESH_TOKEN`, `GOOGLE_OAUTH_TOKEN_URL`: credenciales OAuth para autenticar el envio SMTP de alertas.

## static/vendor/bootstrap/css/bootstrap.min.css

Bootstrap CSS local del proyecto (sin dependencia CDN en runtime).

## static/vendor/bootstrap/js/bootstrap.bundle.min.js

Bootstrap JS local del proyecto (incluye componentes interactivos).

## static/css/app.css

Estilos globales de interfaz del proyecto.

- variables visuales, cards y layout compartido.
- dashboard operativo con encabezado sobrio, tarjetas KPI, accesos rapidos, grafico de hojas cargadas y progreso por hoja.
- asegura contraste legible en fondos claros y mantiene componentes Bootstrap como base visual.
- ajustes mobile-first para contenedores y tablas en pantallas chicas.
- estilos del visor administrativo de evidencias para imagenes y PDF.
- estilos del marco de escaneo QR con guia central y sombreado externo.
- estilos de la previsualizacion de evidencia antes de subir.

## static/js/app.js

Inicializacion frontend global para templates Django.

- aplica clases Bootstrap a campos de formularios renderizados con `as_p`.

## static/vendor/jsqr/jsQR.js

Libreria local para decodificar QR desde frames de camara cuando el navegador no soporta `BarcodeDetector`.

## config/settings/development.py

Configuracion local para desarrollo.

- `DEBUG` activo por defecto.
- base de datos SQLite.
- almacenamiento local de archivos.

## config/settings/production.py

Configuracion para despliegue.

- base de datos PostgreSQL.
- usa `DATABASE_URL` si esta disponible y cae a `DB_*` o `PG*` si no.
- storage bucket S3 compatible.
- acepta credenciales de bucket con nombres `AWS_*` o `BUCKET_*`.
- archivos estaticos con `CompressedStaticFilesStorage` para evitar 500 si falta el manifest de `collectstatic`.
- cookies seguras, redireccion HTTPS configurable, HSTS configurable y cabecera proxy https.

## config/settings/railway.py

Configuracion de despliegue especifica para Railway.

- extiende `production.py`.
- usa hosts por defecto de Railway y `RAILWAY_PUBLIC_DOMAIN` para CSRF.
- permite configurar origenes CSRF adicionales con `DJANGO_CSRF_TRUSTED_ORIGINS`.
- usa `WHITENOISE_USE_FINDERS` activo por defecto para servir estaticos aunque Railway no ejecute `collectstatic`.

## config/urls.py

Router principal del proyecto.

- `urlpatterns`: conecta `admin/` y rutas de `tracking`.
- en modo debug sirve `MEDIA_URL` para ver archivos cargados localmente.

## config/wsgi.py

Inicializacion WSGI para Gunicorn/Railway.

- registra logs tempranos de arranque.
- carga la aplicacion Django.
- en `config.settings.railway`, ejecuta migraciones y `ensure_initial_admin` al arrancar si `DJANGO_RUN_STARTUP_COMMANDS=1`.

## tracking/forms.py

Formulario de carga del PDF de Hoja de Ruta.

- `ImportPdfForm`: valida que el archivo recibido sea un PDF.
- `ImportSpreadsheetForm`: valida que el archivo recibido sea Excel o CSV.
- `EvidenciaForm`: permite sacar foto desde camara o subir imagen/PDF de conformado, valida comentario y confirmacion de duplicada.
- `EvidenciaForm`: valida tamano maximo de imagen/PDF antes de persistir evidencia.
- `NoEntregadoForm`: valida el motivo y comentario de un intento fallido.
- `ValidacionEvidenciaForm`: valida estado y comentario para revision administrativa.
- `CierreHojaForm`: valida comentario opcional para cierre operativo.
- `LoginForm`: formulario de autenticacion para panel interno.
- `UserCreateForm`: alta de usuario interno con rol y permisos de compartir links.
- `UserUpdateForm`: edicion de datos de usuario interno, estado y rol.
- `UserDeleteForm`: confirmacion de borrado de usuario.

## tracking/services/authz.py

Servicio de autenticacion/autorizacion de usuario interno.

- `get_or_create_profile(...)`: asegura perfil de rol para el usuario autenticado.
- `create_user_with_profile(...)`: crea usuario y su `UserProfile` asociado.
- `can_manage_users(...)`: permiso para CRUD de usuarios internos.
- `can_import_pdf(...)`: permiso para importar hojas desde PDF.
- `can_review_evidence(...)`: permiso para revisar/validar evidencias.
- `can_close_hoja(...)`: permiso para cierre operativo de hoja.
- `can_grant_staff(...)`: permiso para otorgar o quitar flag staff.
- `update_user_with_profile(...)`: actualiza usuario y perfil de rol.
- `delete_user_and_profile(...)`: elimina usuario y su perfil.

## tracking/management/commands/ensure_initial_admin.py

Comando idempotente para crear el usuario administrador inicial durante deploy.

- `Command.handle(...)`: lee `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD` e `INITIAL_ADMIN_EMAIL`; si falta password no crea nada, si el usuario ya existe no modifica nada, si no existe crea superusuario.

## tracking/apps.py

Configuracion de la app `tracking`.

- `TrackingConfig.ready(...)`: permite diagnostico opcional de DB solo si `RAILWAY_CHECK_DB_ON_READY=1`.

## tracking/services/import_pdf.py

Servicio de importacion y parseo de PDF de Hoja de Ruta.

- `extract_text_from_pdf(...)`: obtiene texto plano del PDF.
- `extract_oid_from_qr(...)`: decodifica el QR o extrae el oid desde la URL embebida, priorizando QR/link de hoja sobre UUID visibles de remitos.
- `_decode_qr_from_page(...)`: intenta decodificar QR con varios niveles de resolucion y escala de grises para PDFs donde el QR sale chico.
- `_extract_labelled_value(...)`: extrae cabeceras por etiqueta (nro, flete, chofer, acompanante, transporte) con fallback de linea siguiente.
- `_extract_labelled_value(...)`: evita tomar la linea siguiente como valor cuando una etiqueta viene vacia, como `Transporte Tipo:` antes de `Peso Total:`.
- `_merge_wrapped_uuid_lines(...)`: reconstruye UUID de remitos cortados en dos lineas por el PDF.
- `_infer_transporte_tipo(...)`: infiere tipo de transporte cuando el PDF no trae valor junto a la etiqueta.
- `_extract_date_value(...)`: extrae una fecha real evitando falsos positivos como encabezados.
- `_split_cliente_subcliente(...)`: separa lineas de cliente y subcliente, manteniendo continuaciones como parentesis o `Y ...` dentro del cliente.
- `_extract_remitos(...)`: interpreta filas de la tabla de remitos a partir de la linea con fecha + remito; extrae fecha individual de cada remito.
- `_extract_remitos(...)`: soporta tambien tablas PDF donde cada columna llega en lineas separadas (`oid`, fecha, cliente, remito, direccion).
- `parse_hoja_ruta_pdf(...)`: interpreta los datos visibles de la hoja y remitos, incluida fecha de envio por remito.
- `_validate_parsed_hoja(...)`: valida OID, fecha, cantidad minima y campos obligatorios de remitos.
- `_import_parsed_hoja(...)`: crea o actualiza `HojaRuta`, actualiza remitos existentes por `remito_uid` o por `numero` para incorporar OID de remito en reimportaciones; asigna `Remito.fecha` desde datos extraidos.
- `import_hoja_ruta_pdf(...)`: crea o actualiza `HojaRuta`, `Remito` y eventos de trazabilidad.

## tracking/services/import_tabular.py

Servicio de importacion de hojas de ruta desde Excel o CSV.

- `parse_csv_file(...)`: transforma CSV en estructura de hoja + remitos, incluyendo fecha individual de remito.
- `parse_xlsx_file(...)`: transforma Excel en estructura de hoja + remitos, incluyendo fecha individual de remito.
- `parse_tabular_file(...)`: selecciona parser CSV/XLSX segun extension para reutilizar en previsualizacion.
- `import_tabular_file(...)`: persiste la importacion tabular usando la misma logica de dominio.
- exige columna `remito_oid`, la valida como UUID y la guarda como `Remito.remito_uid` para filtrar por QR fisico del remito.
- acepta columna `fecha` para asignar fecha individual a cada remito.

## tracking/services/conformados.py

Servicio de alta de evidencias y registros de no entrega.

- `registrar_evidencia(...)`: crea `Evidencia`, actualiza `Remito` y audita la carga.
- `registrar_intento_no_entregado(...)`: crea `IntentoEntrega`, actualiza `Remito` y audita el evento.
- `registrar_intento_acceso_portal(...)`: crea `IntentoAccesoPortal` para registrar accesos a oids invalidos o inexistentes.

## tracking/services/email_alerts.py

Servicio de envio de alertas por correo usando Gmail OAuth.

- `send_public_access_alert(...)`: envia un email al detectar acceso a una hoja inexistente, con deduplicacion por canal+oid y destinatarios activos leidos desde `PublicAlertRecipient`.

## tracking/services/admin_ops.py

Servicio de operaciones administrativas sobre evidencias y hojas.

- `validar_evidencia(...)`: actualiza la validacion de la evidencia y el estado del remito.
- `cerrar_hoja_ruta(...)`: cambia la hoja a cerrada solo si todos los remitos estan conformados u observados y luego registra el evento.

## tracking/models.py

Define entidades del dominio de trazabilidad y conformados.

- `HojaRuta`: representa hoja importada del ERP y su estado operativo.
- `Remito`: representa cada documento asociado a una hoja; incluye fecha individual del remito (distinta de la fecha general de la hoja).
- `Evidencia`: guarda archivos cargados por canal y estado de validacion.
- `IntentoEntrega`: registra intentos no concretados y motivo.
- `IntentoAccesoPortal`: registra accesos publicos invalidados o a hojas inexistentes para auditoria y alertas.
- `PublicAlertRecipient`: destinatarios activos para alertas publicas configurables desde admin.
- `EventoTrazabilidad`: bitacora auditable de eventos del circuito.
- `UserProfile`: perfil interno con rol y permisos de compartir links por canal.
- `hoja_ruta_pdf_upload_to(...)`: construye ruta `hojas-ruta/{oid}/original.ext` para PDF.
- `conformado_upload_to(...)`: construye ruta `conformados/{oid}/{remito_uid}/{timestamp}.ext`.
- `_delete_file_field(...)`: elimina del storage el archivo asociado a un `FileField`.
- `delete_evidencia_file(...)`: borra del storage la imagen/PDF de una evidencia cuando se elimina desde admin o codigo.
- `delete_hoja_ruta_pdf(...)`: borra del storage el PDF original de una hoja cuando se elimina desde admin o codigo.

## tracking/views.py

Vistas HTTP iniciales para panel y portales publicos.

- `root_redirect(...)`: redirige `/` hacia panel interno.
- `login_view(...)`: autentica usuarios internos.
- `logout_view(...)`: cierra sesion de usuario.
- `panel_usuarios(...)`: listado de usuarios internos con acciones CRUD.
- `panel_permisos(...)`: muestra matriz de permisos por rol.
- `panel_crear_usuario(...)`: alta de usuarios internos.
- `panel_editar_usuario(...)`: edicion de usuarios internos.
- `panel_eliminar_usuario(...)`: eliminacion de usuarios internos.
- `dashboard(...)`: muestra dashboard principal en `/dashboard/` con filtros de fecha/estado/entrega, KPIs de hojas/remitos/evidencias y grafico diario de hojas cargadas.
- `panel_home(...)`: muestra panel operativo en `/panel/` con accesos de gestion, listado paginado de hojas de ruta y filtros por entrega/estado sin filtro de fecha implicito.
- `panel_hoja_detalle(...)`: muestra detalle de hoja con filtros de remitos y contexto operativo.
- `panel_evidencias(...)`: lista evidencias recientes para revision administrativa.
- `panel_auditoria_hr_no_cargadas(...)`: lista intentos de acceso a hojas de ruta no cargadas, con filtros por fecha, canal e identificador.
- `panel_auditoria_remitos(...)`: lista transversal de remitos de todas las hojas con filtros de estado y conformado.
- `panel_auditoria_remito_detalle(...)`: muestra cronologia de eventos, evidencias e intentos de un remito.
- `conformados_portal(...)`: valida acceso publico por canal/oid y registra intentos a oids invalidos o inexistentes.
- `panel_importar_pdf(...)`: recibe el PDF, llama al servicio de importacion y redirige al panel.
- `panel_importar_pdf(...)`: permite previsualizar cabecera/remitos del PDF, guarda una copia temporal en storage y luego confirma la importacion sin volver a seleccionar archivo.
- `panel_importar_excel(...)`: permite previsualizar cabecera/remitos de Excel/CSV, guarda una copia temporal en storage y luego confirma la importacion sin volver a seleccionar archivo.
- `panel_exportar_excel(...)`: exporta en una sola planilla el listado de hojas de ruta filtradas por estado, numero de entrega y fechas opcionales elegidas al exportar, con conteos de remitos/evidencias para comparacion operativa.
- `_save_import_preview_file(...)`: guarda un archivo previsualizado en storage bajo `import-preview/{usuario}/{token}/`.
- `_open_import_preview_file(...)`: reabre el archivo temporal asociado al token guardado en sesion.
- `_delete_import_preview_file(...)`: elimina el archivo temporal tras una importacion exitosa.
- `_get_client_ip(...)`: obtiene IP de cliente considerando `X-Forwarded-For`.
- `_check_rate_limit(...)`: limita intentos por ventana usando cache de Django.
- `_rate_limit_key(...)`: construye clave de limite por accion, IP, canal, hoja y remito.
- `_evidencia_limits_context(...)`: expone limites de tamano al template publico.
- `conformados_portal(...)`: valida existencia/estado de hoja y lista remitos por canal.
- `conformados_portal(...)`: agrega flujo por pasos (buscar/escaneo de remito, seleccion y accion unica).
- `_format_manual_remito(...)`: valida la busqueda manual con formato `00009-00022221` o 13 digitos sin guion, informando digitos faltantes o sobrantes.
- `_extract_remito_oid_from_qr(...)`: extrae un UUID desde el payload escaneado por QR.
- `_find_remito_in_hoja(...)`: valida remito dentro de la hoja; busqueda manual contra `Remito.numero` y QR contra `Remito.remito_uid`.
- `_build_evidencia_file_context(...)`: prepara URL, nombre y tipo visualizable del archivo para revision administrativa.
- `subir_evidencia(...)`: recibe archivo de conformado y crea la evidencia.
- `subir_evidencia(...)`: aplica rate limit solo cuando el formulario ya es valido, evitando contar intentos incompletos sin archivo.
- `no_entregado(...)`: registra un intento de entrega no concretada.
- `no_entregado(...)`: aplica rate limit solo cuando el formulario ya es valido.
- `validar_evidencia(...)`: permite validar, observar o rechazar una evidencia.
- `validar_evidencia(...)`: entrega contexto de visor para revisar imagenes o PDF antes de guardar la validacion.
- `cerrar_hoja(...)`: cierra operativamente una hoja de ruta solo cuando todos los remitos estan conformados u observados.

## tracking/urls.py

Define endpoints iniciales del modulo tracking.

- ``: redireccion raiz hacia panel.
- `accounts/login/`: login del panel interno.
- `accounts/logout/`: cierre de sesion.
- `dashboard/`: dashboard interno de auditoria y KPIs.
- `panel/`: panel operativo interno.
- `panel/permisos/`: matriz de permisos por rol.
- `panel/usuarios/`: listado de usuarios internos.
- `panel/usuarios/nuevo/`: alta de usuario interno con rol.
- `panel/usuarios/<id>/editar/`: edicion de usuario interno.
- `panel/usuarios/<id>/eliminar/`: eliminacion de usuario interno.
- `panel/hojas/<oid>/`: detalle de hoja con filtros.
- `panel/importar/pdf/`: formulario y procesamiento de importacion de PDF.
- `panel/exportar/excel/`: descarga Excel del listado de hojas de ruta aplicando los filtros vigentes.
- `panel/evidencias/`: listado de evidencias para revision.
- `panel/evidencias/<id>/validar/`: formulario de validacion administrativa.
- `panel/auditoria/hr-no-cargadas/`: auditoria interna de intentos a hojas de ruta inexistentes.
- `panel/auditoria/remitos/`: listado transversal de remitos con filtros y acceso a cronologia.
- `panel/auditoria/remitos/<id>/`: detalle del remito con linea de tiempo y evidencias historicas.
- `panel/hojas/<oid>/cerrar/`: confirmacion de cierre de hoja.
- `conformados/<canal>/<oid>/`: portal publico por canal y hoja.
- `conformados/<canal>/<oid>/subir/`: alta publica de evidencia.
- `conformados/<canal>/<oid>/no-entregado/`: alta publica de intento fallido.

## tracking/admin.py

Configuracion del admin para operacion interna de entidades principales.

- `RemitoInline`: muestra remitos dentro de la hoja con numero, OID/remito_uid y datos operativos.
- `EvidenciaInline`: muestra evidencias relacionadas dentro de la hoja.
- `IntentoEntregaInline`: muestra intentos fallidos relacionados dentro de la hoja.
- `EventoTrazabilidadInline`: muestra eventos de auditoria relacionados dentro de la hoja.
- `HojaRutaAdmin`: muestra todos los datos principales de la hoja, archivo PDF, auditoria e inlines relacionados.
- `RemitoAdmin`: muestra y permite buscar por numero, OID/remito_uid, cliente, direccion y hoja.
- `EvidenciaAdmin`: revision rapida de evidencias por canal/estado con OID del remito visible.
- `IntentoEntregaAdmin`: consulta de no entregados con OID del remito visible.
- `IntentoAccesoPortalAdmin`: consulta de accesos publicos invalidados o a hojas inexistentes.
- `PublicAlertRecipientAdmin`: gestion de destinatarios de alertas por correo desde admin.
- `EventoTrazabilidadAdmin`: auditoria de eventos con OID del remito visible.
- `UserProfileAdmin`: administracion de roles y permisos de compartir links.

## tracking/migrations/0001_initial.py

Migracion inicial del dominio `tracking`.

- crea tablas para `HojaRuta`, `Remito`, `Evidencia`, `IntentoEntrega`, `EventoTrazabilidad`.

## tracking/migrations/0002_alter_evidencia_archivo_and_more.py

Migracion de ajuste para rutas de almacenamiento de archivos.

- actualiza `Evidencia.archivo` y `HojaRuta.archivo_pdf_original` para usar funciones `upload_to` alineadas al dominio.

## tracking/migrations/0003_userprofile.py

Migracion de perfiles de usuario y roles internos.

- crea `UserProfile` vinculado a `User` con rol y permisos de compartir links.

## tracking/migrations/0005_intentoaccesoportal.py

Migracion de auditoria de accesos publicos.

- crea `IntentoAccesoPortal` para registrar oids invalidos y hojas inexistentes.

## tracking/migrations/0006_publicalertrecipient.py

Migracion de destinatarios dinamicos para alertas publicas.

- crea `PublicAlertRecipient` para administrar correos activos desde admin.

## templates/tracking/panel_home.html

Template del panel operativo interno.

- agrupa accesos operativos a importacion PDF, evidencias, auditoria de remitos, HR no cargadas y usuarios.
- mantiene tabla de hojas de ruta paginada de a 20, con busqueda por numero de entrega y accesos rapidos a todas/abiertas/cerradas.
- permite exportar el listado filtrado a Excel con fechas opcionales solo en el formulario de exportacion.
- enlaza al dashboard para lectura de KPIs sin mezclar responsabilidades operativas.

## templates/tracking/dashboard.html

Template del dashboard interno de auditoria.

- muestra filtros por fecha, estado y numero de entrega.
- muestra KPIs de hojas de ruta cargadas, remitos totales, remitos con evidencia, evidencia aprobada y evidencias sin auditar.
- separa el KPI de `HR no cargadas` como auditoria externa al circuito operativo y enlaza a su detalle.
- renderiza con Chart.js un grafico de barras de hojas cargadas por dia.

## templates/tracking/panel_auditoria_hr_no_cargadas.html

Template de auditoria interna para hojas de ruta no cargadas.

- lista intentos de acceso a hojas inexistentes registrados como `IntentoAccesoPortal`.
- permite filtrar por fecha, identificador solicitado y canal.
- muestra totales de intentos y HR unicas.

## templates/tracking/panel_hoja_detalle.html

Template de detalle de hoja con filtros de remitos, evidencias e intentos recientes.

## templates/tracking/panel_crear_usuario.html

Template para alta de usuario interno con rol.

## templates/tracking/panel_usuarios.html

Template para listar usuarios internos y navegar al CRUD.

## templates/tracking/panel_permisos.html

Template de referencia con matriz de permisos por rol.

## templates/tracking/panel_editar_usuario.html

Template para editar datos y rol de un usuario interno.

## templates/tracking/panel_eliminar_usuario.html

Template para confirmar y ejecutar la eliminacion de un usuario.

## templates/tracking/panel_evidencias.html

Template basico para listar evidencias y acceder a su revision.

- muestra la fecha del remito con fallback `-` cuando el dato no fue importado o aun no existe.

## templates/tracking/validar_evidencia.html

Template para validar, observar o rechazar una evidencia.

- muestra visor embebido de imagen o PDF cargado antes del formulario de validacion.
- permite abrir el archivo original en una pestaña nueva cuando se necesita inspeccion ampliada.

## templates/tracking/cerrar_hoja.html

Template para confirmar el cierre operativo de una hoja con alerta cuando existen remitos pendientes.

## templates/tracking/importar_pdf.html

Template Bootstrap para subir PDF, previsualizar datos detectados y confirmar importacion.

- despues de previsualizar muestra el archivo temporal listo para importar sin re-seleccionarlo.
- muestra `remito_uid`/OID de remito en la previsualizacion cuando el PDF lo trae.

## templates/tracking/importar_excel.html

Template Bootstrap para subir Excel/CSV, previsualizar datos detectados y confirmar importacion.

- informa que el archivo debe incluir `oid` de hoja y `remito_oid` por cada remito.
- muestra `remito_uid` en la previsualizacion para validar el dato que se usara al escanear QR.
- despues de previsualizar muestra el archivo temporal listo para importar sin re-seleccionarlo.

## templates/tracking/estado_hoja.html

Template Bootstrap de estado para hoja inexistente o cerrada en portal publico.

## templates/tracking/conformados_portal.html

Template Bootstrap responsivo con UX por pasos para canal publico:

- filtro por remito (manual o escaneo QR desde camara del navegador).
- busqueda manual por numero de remito con ayuda de formato `00009-00022221`; el QR se resuelve por OID interno del remito.
- al escanear QR envia `origen=qr` para que el backend busque exclusivamente contra `Remito.remito_uid`.
- guia visual para centrar el QR del remito dentro de un cuadro de escaneo.
- escaneo con recorte central usando `jsQR` para priorizar el QR apuntado e ignorar ruido alrededor.
- fallback de escaneo con `BarcodeDetector` cuando el recorte central no detecta codigo.
- solicita camara trasera con mayor resolucion ideal y aplica enfoque/exposicion continuos o luz cuando el navegador lo soporta.
- remito seleccionado con detalle visible.
- flujo de evidencia dentro de modal de conformado, con tabs para `cargar conformado` o `no entregado`.
- el modal de conformado se renderiza solo cuando hay `remito_seleccionado`, evitando aperturas vacias al entrar al portal sin escanear.
- boton `Sacar foto` que alterna del modal principal al modal de camara para evitar conflicto de dos modales abiertos en simultaneo.
- boton `Subir archivo` que abre el input real del formulario Django (sin duplicar inputs de archivo).
- inicializacion de modales diferida a `window.load` para asegurar que `bootstrap.bundle.min.js` ya este cargado y evitar errores `bootstrap is not defined`.
- previsualizacion obligatoria de imagen/PDF antes de subir evidencia y validacion cliente de tamano.
- errores del formulario de evidencia visibles dentro del modal (incluye rechazo por evidencia duplicada o archivo invalido).
- confirmacion explicita para permitir evidencia duplicada, sincronizada con `confirmar_duplicada` del formulario.
- el check de duplicada solo se muestra cuando el backend confirma que el remito ya tiene evidencia (`remito_tiene_evidencia`).
- tabla de remitos con semaforo visual por estado: `table-danger` para `pendiente` o `intento_fallido`; `table-success` para remitos con avance de conformado.
- una sola accion activa a la vez: cargar conformado o informar no entregado.

## templates/base.html

Layout base compartido por todos los templates.

- carga Bootstrap CSS/JS desde `static/vendor/bootstrap/`.
- deja `bootstrap-icons` como unica dependencia por CDN.
- centraliza navbar responsive y estilos globales mobile-first.
- expone bloques `extra_head` y `extra_scripts` para assets especificos de cada pagina.
- mantiene accesos simples al panel y a evidencias desde la barra superior.

## templates/registration/login.html

Template de autenticacion para ingreso al panel interno.

## Regla frontend mobile-first

Todos los templates del proyecto deben ser responsive mobile-first.

- priorizar navegacion y formularios para uso en celular.
- no usar dependencias CDN para Bootstrap CSS/JS; se deben servir desde `static/`.
- se permite CDN unicamente para `bootstrap-icons`.
