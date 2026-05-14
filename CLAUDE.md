# CLAUDE.md

> **Sincronización obligatoria:** Este archivo es una copia de `AGENTS.md`. Cada vez que se actualice uno, se debe actualizar el otro de forma inmediata y con el mismo contenido. Son documentos gemelos.

---

## 📚 Regla general de documentación viva

Antes de crear, modificar o eliminar código, el agente debe consultar la documentación viva del proyecto.

No asumir nombres de funciones, clases, endpoints, modelos, archivos o flujos sin verificar primero la documentación vigente.

La consulta previa es obligatoria especialmente sobre:

- estructura del proyecto
- modelos de datos
- contratos de API
- reglas de negocio
- flujos frontend
- integraciones
- convenciones de nombres
- decisiones técnicas vigentes

Si el agente crea un archivo nuevo o modifica uno existente, debe actualizar inmediatamente la documentación correspondiente.

---

## 🧠 Regla de memoria estructural del proyecto

El proyecto debe mantener una documentación técnica viva y resumida de cada archivo importante.

Cada archivo relevante debe figurar con:

- ruta del archivo
- responsabilidad principal
- clases principales
- funciones principales
- una línea breve por función o clase explicando qué hace

Objetivo:

> Que cualquier agente o desarrollador entienda rápidamente qué hace cada archivo y qué no debe duplicarse.

---

## 🔒 Regla de consistencia de nombres

El agente no debe renombrar clases, funciones, endpoints, serializers, vistas, componentes o módulos sin actualizar en el mismo cambio toda la documentación asociada.

Todo cambio de nombre debe reflejarse en:

- documentación de estructura
- contratos de API
- flujos afectados
- referencias cruzadas entre backend y frontend

Si una función o clase ya existe y cumple una responsabilidad, debe reutilizarse o extenderse antes de crear una nueva con propósito similar.

---

## 🗂️ Regla sobre estructura del proyecto

La estructura debe documentarse por archivo importante, excluyendo archivos triviales de entorno.

Documentar principalmente:

- modelos
- servicios
- vistas
- formularios
- templates
- endpoints
- utilidades
- parsers
- integraciones
- tareas de almacenamiento
- validaciones de negocio

No documentar en detalle archivos mínimos salvo que afecten arquitectura o comportamiento funcional.

---

## 🧱 Regla de modularización obligatoria

Cuando un archivo concentre varias responsabilidades, el agente debe dividirlo.

Prioridades:

- separar por dominio funcional
- mover lógica de negocio a servicios
- mantener vistas HTTP delgadas
- separar parsing de PDF/CSV de la lógica de negocio
- separar almacenamiento de archivos de modelos y vistas
- evitar archivos monolíticos

---

## ✍️ Formato obligatorio de documentación por archivo

Cada archivo importante debe documentarse así:

### tracking/services/import_pdf.py

Extrae e interpreta datos de una Hoja de Ruta PDF.

- extract_text_from_pdf(...): obtiene texto plano del PDF cargado.
- extract_oid_from_qr(...): obtiene el oid desde el QR embebido en el PDF.
- parse_hoja_ruta_pdf(...): transforma el texto extraído en datos estructurados.

---

## 🧠 Contexto funcional definitivo

Este proyecto construye un sistema externo de trazabilidad y captura de conformados.

El ERP sigue siendo la fuente de verdad inicial.

El sistema externo:

- NO reemplaza al ERP
- NO crea remitos desde cero
- NO crea hojas de ruta manuales desde cero
- SÍ importa hojas de ruta emitidas por el ERP
- SÍ captura evidencia de conformados
- SÍ registra intentos fallidos
- SÍ permite validación administrativa
- SÍ permite cierre operativo de hojas

---

## 🏗️ Decisiones técnicas vigentes

### Backend

- Django
- Django REST Framework si se exponen APIs
- Templates Django para MVP web responsive

### Base de datos

- PostgreSQL en Railway
- No usar SQLite para desarrollo funcional compartido ni producción
- SQLite queda permitido solo para desarrollo local individual

### Archivos

- Railway Storage Bucket
- No guardar PDFs ni fotos en filesystem local como destino final

### Frontend inicial

- Web responsive en Django
- Bootstrap o Tailwind
- Scanner QR desde navegador móvil

### Frontend futuro

- React
- React Native / Expo

---

## 📦 Almacenamiento de archivos

Los archivos deben almacenarse en bucket.

Tipos de archivos:

- PDF original de hoja de ruta
- fotos de conformados
- evidencias adicionales

Estructura recomendada:

```text
hojas-ruta/{oid}/original.pdf
conformados/{oid}/{remito_uid}/{timestamp}.jpg
```

La base de datos solo debe guardar:

- ruta del archivo
- URL si corresponde
- tipo
- tamaño
- fecha de carga
- usuario/canal
- relación con hoja/remito

---

## 🧩 Fuentes de datos

El sistema debe soportar dos formas de nutrirse.

---

### Opción 1 — PDF de Hoja de Ruta

Uso inmediato.

El usuario interno sube el PDF generado por el ERP.

El PDF debe contener:

- datos visibles de la hoja
- tabla de remitos
- QR con URL de conformados
- dentro de esa URL debe venir el `oid`

Ejemplo:

```text
/conformados/logistica/{oid}
```

Regla crítica:

> Si el PDF no contiene el QR con el `oid`, el sistema puede leer datos visibles, pero no puede vincular la hoja al identificador real del ERP.

---

### Opción 2 — CSV/Excel

Uso futuro recomendado.

El archivo debe contener una columna obligatoria:

```text
oid
```

Columnas esperadas:

- oid
- nro_entrega
- fecha
- cliente
- subcliente
- remito
- remito_oid
- direccion
- observacion
- transporte_tipo
- flete
- chofer
- acompanante
- transporte

---

## 🔑 Identificación de Hoja de Ruta

El identificador principal será el `oid` del ERP.

Ejemplo:

```text
66D4FF99-0081-4D15-B04D-37B51C26DBAE
```

URLs públicas iniciales:

```text
/conformados/logistica/{oid}
```

```text
/conformados/cliente/{oid}
```

Regla:

> El `oid` identifica la hoja, pero la hoja solo acepta cargas si existe en el sistema y está abierta.

---

## 🔐 Seguridad

Versión inicial:

- acceso público por canal + oid
- hoja debe existir
- hoja debe estar abierta
- toda evidencia queda pendiente de validación

Versión futura:

```text
/conformados/{canal}/{oid}/{access_key}
```

El sistema debe estar preparado para endurecer acceso sin rediseñar el dominio.

---

## 🧾 Entidades principales

### HojaRuta

Agrupador logístico importado desde ERP.

Campos conceptuales:

- oid
- nro_entrega
- fecha
- transporte_tipo
- flete
- chofer
- acompanante
- transporte
- estado
- archivo_pdf_original

Estados:

- importada
- abierta
- cerrada

---

### Remito

Documento incluido dentro de una Hoja de Ruta.

Campos conceptuales:

- remito_uid
- hoja_ruta
- numero
- cliente
- subcliente
- direccion
- observacion
- estado

Estados:

- pendiente
- evidencia_cargada
- intento_fallido
- validado
- observado
- rechazado
- cerrado

---

### Evidencia

Archivo cargado como respaldo de conformado.

Campos conceptuales:

- hoja_ruta
- remito
- canal
- archivo
- fecha_carga
- estado_validacion
- comentario
- origen

Canales:

- logistica
- cliente
- interno

Estados:

- pendiente_revision
- validada
- observada
- rechazada

---

### IntentoEntrega

Registro de una entrega no concretada.

Campos conceptuales:

- hoja_ruta
- remito
- canal
- motivo
- comentario
- fecha_evento

Motivos sugeridos:

- cliente ausente
- fuera de horario
- dirección incorrecta
- cliente rechaza entrega
- falta documentación
- acceso restringido
- otro

---

### EventoTrazabilidad

Bitácora auditable del circuito.

Debe registrar:

- importación
- apertura de link
- carga de evidencia
- intento fallido
- validación
- rechazo
- cierre

---

## 📲 Flujo interno

Actor: usuario interno con login.

Flujo:

1. ingresa al panel
2. sube PDF o CSV/Excel
3. sistema extrae datos
4. sistema valida estructura
5. sistema crea HojaRuta
6. sistema crea Remitos
7. hoja queda abierta para recibir conformados
8. administración revisa evidencias
9. administración cierra hoja

---

## 🚚 Flujo logístico

URL:

```text
/conformados/logistica/{oid}
```

Flujo:

1. operador abre link
2. sistema valida que la hoja exista y esté abierta
3. operador ve remitos de la hoja
4. toca "Agregar conformado"
5. escanea QR del remito físico
6. sistema busca el remito dentro de esa hoja
7. si existe, muestra cliente y dirección
8. operador carga foto o informa no entregado

Regla:

> El QR del remito solo filtra dentro de la hoja. No abre una URL. Su valor debe coincidir con `remito_uid`, cargado desde la columna `remito_oid` del Excel/CSV.

Regla critica:

> Si el QR fisico del remito contiene solo el OID del remito, el PDF de Hoja de Ruta no alcanza como unica fuente operativa. La importacion debe complementarse o reemplazarse por Excel/CSV con columna `remito_oid`.

---

## 👤 Flujo cliente

URL:

```text
/conformados/cliente/{oid}
```

Flujo:

1. cliente abre link compartido manualmente
2. sistema valida hoja abierta
3. cliente selecciona o busca remito
4. carga foto del conformado
5. evidencia queda registrada con canal `cliente`

---

## 📸 Carga de evidencia

Antes de subir una foto:

- mostrar vista previa obligatoria
- advertir que debe ser legible
- pedir confirmación

Texto recomendado:

```text
Verifique que el conformado se lea correctamente.
Si la imagen está borrosa, cortada, ilegible o no corresponde al documento,
la evidencia será rechazada.
```

Regla:

> Subir evidencia no implica validación.

---

## 🔁 Evidencias repetidas

Si ya existe evidencia para un remito:

- advertir
- permitir nueva carga si el usuario confirma
- registrar todas las cargas

Regla:

> Es preferible recibir evidencia repetida antes que perder un conformado válido.

---

## ❌ No entregado

El operador logístico puede informar no entrega.

Cada evento debe guardarse como IntentoEntrega.

No cierra el remito.

El mismo link sigue habilitado mientras la hoja esté abierta.

---

## 🧑‍💼 Validación administrativa

Actor: usuario interno con login.

Puede marcar evidencia como:

- validada
- observada
- rechazada

Si se rechaza, debe registrar motivo.

---

## 🧾 Reglas obligatorias para agentes

- No usar SQLite en produccion ni desarrollo funcional compartido.
- No guardar archivos en filesystem local como destino final.
- No crear remitos externos desde cero.
- No crear hojas de ruta manuales sin origen ERP.
- Toda evidencia debe estar asociada a hoja y remito.
- El canal debe registrarse siempre.
- El PDF es fuente inmediata.
- CSV/Excel es fuente operativa para vincular el QR fisico del remito cuando el PDF no trae `remito_oid`.
- El oid en PDF debe obtenerse desde QR.
- El QR del remito solo sirve como filtro dentro de la hoja y debe buscarse contra `remito_uid`/`remito_oid`.
- Una hoja cerrada no acepta cargas externas.
- Subir evidencia no valida el conformado.
- Toda acción relevante debe crear EventoTrazabilidad.
- Si se modifica un flujo, actualizar documentación viva.

### Regla frontend obligatoria

- Todo frontend debe implementarse con Bootstrap como base (grid, componentes, utilidades).
- Evitar CSS custom complejo o difícil de mantener; solo se permite CSS propio mínimo para branding puntual.
- No introducir frameworks CSS adicionales ni patrones visuales paralelos al sistema Bootstrap.
- Prioridad mobile-first: todas las vistas deben funcionar correctamente en celular antes que en escritorio.

---

## 🧩 Endpoints / rutas mínimas

### Internas

```text
/panel/
/panel/importar/pdf/
/panel/importar/csv/
/panel/hojas/{oid}/
/panel/evidencias/
/panel/evidencias/{id}/validar/
/panel/hojas/{oid}/cerrar/
```

### Públicas

```text
/conformados/logistica/{oid}
/conformados/cliente/{oid}
/conformados/{canal}/{oid}/subir/
/conformados/{canal}/{oid}/no-entregado/
```

---

## 🖥️ Pantallas mínimas

### Panel interno

- importar PDF
- importar CSV/Excel
- ver hojas
- ver remitos
- revisar evidencias
- validar/rechazar
- cerrar hoja

### Portal logístico

- abrir hoja
- listar remitos
- escanear QR de remito
- cargar conformado
- informar no entregado

### Portal cliente

- abrir hoja
- buscar/seleccionar remito
- cargar conformado

---

## 🧠 Prompt base para nuevas tareas

Actúa como arquitecto de software senior y copiloto de implementación.

El proyecto es un sistema Django para trazabilidad de conformados.

Decisiones vigentes:

- Django como backend
- PostgreSQL en Railway
- Railway Storage Bucket para archivos
- PDF como ingesta inmediata
- CSV/Excel como ingesta futura
- Web responsive como frontend inicial
- React/React Native como evolución futura

El ERP es la fuente de verdad inicial.

El sistema externo importa hojas de ruta, remitos y datos logísticos. Luego permite que logística o cliente carguen evidencia de conformados por rutas públicas diferenciadas por canal.

Reglas:

- no usar SQLite
- no guardar archivos localmente como destino final
- no reemplazar al ERP
- no crear remitos externos desde cero
- todo conformado debe vincularse a una hoja y remito
- canal obligatorio: logistica, cliente o interno
- toda evidencia queda pendiente de validación
- toda acción relevante debe auditarse
- mantener documentación viva actualizada

Output esperado:

1. aplicar cambios mínimos y correctos
2. documentar archivos modificados
3. respetar decisiones técnicas vigentes
4. no introducir tecnologías nuevas sin justificación
5. priorizar código mantenible y funcional
