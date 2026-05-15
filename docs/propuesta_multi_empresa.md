# Propuesta tecnica multiempresa

## Objetivo

Transformar la plataforma en un sistema multiempresa estricto para que:

- cada empresa vea solo sus hojas de ruta, remitos, evidencias y usuarios autorizados,
- los auditores corporativos puedan ver las 4 empresas desde un mismo panel,
- los OID repetidos entre empresas no generen cruces ni ambiguedades,
- el branding visual pueda cambiar por empresa sin afectar la logica de negocio,
- la segmentacion quede garantizada en backend, no solo en la URL.

La meta no es solo mostrar distinto. La meta es aislar el dominio por empresa con reglas duras de acceso, importacion, auditoria y visualizacion.

---

## Contexto tecnico actual

El sistema actual fue construido como un unico dominio global con estas suposiciones:

- una sola fuente operativa de hojas y remitos,
- usuarios internos con permisos por rol,
- URLs publicas por canal + oid,
- importacion de PDF de hoja de ruta como flujo principal,
- evidencia y auditoria centralizadas.

Hoy no existe una entidad de empresa o tenant. Eso significa que el aislamiento tendra que agregarse ahora, no solo configurarse.

Esto importa porque los ERP de cada empresa son independientes aunque compartan tecnologia. En consecuencia, el `oid` no puede seguir tratandose como clave global absoluta.

---

## Problema central

Hay dos riesgos estructurales:

1. Un mismo `oid` puede existir en mas de una empresa.
2. Un usuario de una empresa no debe poder ver ni operar datos de otra, salvo que sea corporativo.

Si el sistema sigue usando solo `oid` y el canal para identificar una hoja, el cruce entre empresas puede ocurrir por accidente o por manipulacion de URL.

La solucion correcta es introducir una identidad compuesta:

```text
empresa + canal + oid
```

Y en algunas rutas operativas, tambien:

```text
empresa + oid + remito_oid
```

---

## Alcance funcional propuesto

### 1. Segmentacion estricta por empresa

Cada hoja de ruta, remito, evidencia e intento de entrega debe pertenecer a una empresa.

### 2. Acceso publico diferenciado

Las rutas publicas deben incorporar empresa en la URL.

Ejemplos:

```text
/conformados/empresa1-logistica/{oid}
/conformados/empresa1-cliente/{oid}
/conformados/empresa2-logistica/{oid}
/conformados/empresa2-cliente/{oid}
```

### 3. Auditoria corporativa

Usuarios corporativos podran observar y auditar las 4 empresas, pero no necesariamente editar sus datos operativos.

### 4. Branding por empresa

Cada empresa puede tener un tema visual propio basado en Bootstrap o Bootswatch.

### 5. Importacion con validacion de pertenencia

La importacion PDF debe asociarse a una empresa concreta antes de persistir.

---

## Propuesta de arquitectura

### Identidad principal

La identidad funcional de una hoja debe ser:

```text
empresa_id + oid_erp
```

No basta con `oid_erp`.

### Estructura de datos sugerida

#### Empresa

Entidad raiz para segmentar todo el dominio.

Campos sugeridos:

- `code`: codigo tecnico estable, por ejemplo `empresa1`
- `name`: nombre visible
- `slug`: usado en URL publica
- `active`: habilitacion operativa
- `theme`: identificador visual o nombre de tema Bootswatch
- `brand_color`, `accent_color`: opcional para ajustes visuales
- `erp_identifier`: referencia tecnica del ERP o base asociada

#### HojaRuta

Debe recibir FK obligatoria a `Empresa`.

#### Remito

Debe heredar la empresa de la hoja y, en consultas, filtrarse por empresa tambien.

#### Evidencia

Debe quedar asociada a la empresa de la hoja y validarse siempre dentro de ese mismo contexto.

#### IntentoEntrega

Debe incluir empresa para auditoria y trazabilidad.

#### Usuario y perfil

Debe asociarse a una o mas empresas segun el rol:

- usuario operativo: una sola empresa,
- usuario corporativo: todas las empresas,
- auditor: una o varias empresas segun permiso,
- superusuario: acceso total tecnico.

---

## Modelo de permisos

La segmentacion no debe depender solo del rol.

Debe existir una combinacion de:

1. rol funcional,
2. empresas autorizadas,
3. alcance de visualizacion,
4. alcance de edicion,
5. canal permitido.

### Ejemplo de matriz

#### Operativo empresa A

- ve solo empresa A,
- importa solo empresa A,
- carga evidencias solo en empresa A,
- no ve auditoria de otras empresas.

#### Corporativo auditor

- ve las 4 empresas,
- accede a auditoria de remitos global,
- no necesariamente edita datos operativos,
- puede filtrar por empresa.

#### Superusuario tecnico

- acceso total del sistema,
- solo para soporte y contingencias.

---

## URLs y riesgo de OID repetido

Este es el punto mas delicado.

Si dos empresas tienen hojas con el mismo `oid`, una URL como:

```text
/conformados/logistica/{oid}
```

no alcanza para distinguir el contexto correcto.

La URL debe incluir empresa:

```text
/conformados/{empresa_slug}-logistica/{oid}/
```

o una variante equivalente donde la empresa forme parte del identificador visible.

### Reglas de seguridad recomendadas

- validar que la empresa exista y este activa,
- validar que el `oid` pertenezca a esa empresa,
- rechazar acceso si el documento existe en otra empresa,
- no inferir empresa solo por el `oid`,
- registrar intentos invalidos como evento de trazabilidad.

### Cuidado importante

Aunque el `oid` sea probabilisticamente unico, no debe asumirse unicidad global entre bases ERP independientes. La seguridad del sistema no puede descansar en esa suposicion.

---

## Importacion PDF multiempresa

La importacion PDF tiene que endurecerse antes de pasar a multiempresa real.

### Validaciones necesarias

1. el usuario selecciona empresa antes de subir,
2. el PDF debe tener QR o URL con `oid` valido,
3. todos los QR/OID detectados en el documento deben corresponder a la misma empresa,
4. si el PDF tiene remitos repartidos en varias paginas, se debe leer la primera pagina como cabecera y el resto como continuidad de remitos,
5. si el PDF contiene mas de un OID de hoja de ruta, debe rechazarse entero.

### Reglas de negocio recomendadas

- cabecera desde pagina 1,
- remitos desde todas las paginas,
- si una pagina secundaria trae otro OID de hoja, error,
- si una pagina secundaria no trae OID pero contiene remitos de la misma hoja, se acepta,
- si el PDF viene unido de dos empresas distintas, se rechaza.

### Implicancia tecnica

No alcanza con ajustar la plantilla. Hay que intervenir el parser, la vista de previsualizacion, la validacion y la persistencia.

---

## Auditoria de remitos multiempresa

El panel `/panel/auditoria/remitos/` debe evolucionar a una vista corporativa con filtro de empresa.

### Recomendacion

- filtro por empresa,
- filtro por estado,
- filtro por conformado,
- filtro por fecha,
- acceso solo a las empresas permitidas para el usuario.

### Ventaja

Los auditores corporativos podran comparar las 4 empresas sin mezclar resultados y sin entrar a paneles operativos ajenos.

---

## Branding por empresa

El branding puede resolverse sin romper la arquitectura.

### Propuesta

- mantener Bootstrap como base unica,
- definir Bootswatch por empresa,
- permitir acentos o variables CSS por empresa,
- dejar el tema como capa de presentacion, nunca como fuente de permisos.

### Ejemplo operativo

- empresa A: tema claro con acento azul,
- empresa B: tema con acento verde,
- empresa C: tema sobrio gris,
- empresa D: tema distinto pero consistente.

### Riesgo

Si el branding empieza a condicionar la logica, se vuelve dificil de mantener. El tema debe ser una configuracion visual, no una bifurcacion de codigo.

---

## Riesgos tecnicos adicionales

### 1. Consultas sin filtro por empresa

Es el riesgo mas probable.

Si una vista no filtra por empresa, la informacion puede verse mezclada aunque las URLs esten bien.

### 2. Formularios sin contexto de empresa

Un formulario de importacion, alta de evidencia o validacion debe recibir empresa como parte del contexto.

### 3. Permisos que dependen solo del rol

Un rol por si solo no alcanza en un sistema multiempresa. Se necesita rol + empresa.

### 4. Datos historicos ya cargados

La migracion de registros existentes tendra que asignar empresa a cada hoja y remito historico.

### 5. OID duplicado entre empresas

Se resuelve con identidad compuesta y validacion estricta en el backend.

### 6. QR unidos o PDFs manipulados

Se debe rechazar cualquier documento que mezcle OIDs de distintas empresas o distintas hojas de ruta incompatibles.

### 7. Sessiones y cache

Si se cachea HTML, querysets o previews, la clave debe incluir empresa para evitar fugas cruzadas.

---

## Estrategia de implementacion

### Fase 1 — Fundacion de empresa

- crear modelo `Empresa`,
- agregar FK obligatoria a `HojaRuta`,
- propagar empresa a `Remito`, `Evidencia` e `IntentoEntrega`,
- definir usuarios con alcance por empresa,
- crear datos semilla de las 4 empresas.

### Fase 2 — Aislamiento de lecturas y escrituras

- filtrar todas las vistas por empresa,
- adaptar auditoria y paneles,
- adaptar forms,
- adaptar admin,
- agregar validacion centralizada de alcance.

### Fase 3 — Importacion y QR

- pedir empresa al importar PDF,
- validar que el PDF corresponda a una sola empresa,
- proteger contra PDF unido de varias empresas,
- mantener cabecera de primera pagina y remitos multipagina.

### Fase 4 — URLs publicas multiempresa

- cambiar rutas publicas,
- actualizar QR de PDF si corresponde,
- mantener compatibilidad temporal si hace falta,
- registrar redireccion o rechazo claro cuando la empresa no coincide.

### Fase 5 — Branding y operacion

- aplicar tema por empresa,
- agregar filtro de empresa en auditoria,
- mostrar contexto visual de la empresa activa,
- documentar el flujo operativo final.

---

## Orden de cambio recomendado

Si se implementa en este repo, el orden deberia ser:

1. `Empresa` y relaciones basicas.
2. Filtro de empresa en backend.
3. Importacion PDF con empresa obligatoria.
4. Auditoria y paneles con filtro de empresa.
5. URLs publicas nuevas.
6. Branding por empresa.
7. Migracion de datos historicos.
8. Pruebas de cruces y seguridad.

---

## Criterios de aceptacion

La implementacion puede considerarse valida cuando se cumpla todo esto:

- una empresa no ve datos de otra por ninguna via publica u operativa,
- un usuario operativo solo opera su empresa,
- un auditor corporativo ve todas las empresas autorizadas,
- un PDF de dos empresas se rechaza,
- un PDF multipagina de la misma empresa se importa correctamente,
- la URL con `oid` repetido no cruza contexto de empresa,
- el panel de auditoria de remitos permite filtrar por empresa,
- el branding cambia segun empresa sin afectar seguridad.

---

## Complejidad estimada

### Bajo impacto

- branding por empresa,
- filtros visuales,
- labels y temas.

### Impacto medio

- auditoria con filtro de empresa,
- usuarios segmentados,
- admin adaptado.

### Impacto alto

- modelo `Empresa`,
- importacion con validacion fuerte,
- URLs publicas multiempresa,
- migracion de datos historicos,
- aislamiento total de consultas.

### Conclusion

No es un cambio inmediato, pero tampoco es un rediseño imposible. Es un refactor estructural serio, viable y recomendable antes de crecer mas.

---

## Recomendacion final

Hacerlo en una rama aislada, primero con la fundacion de empresa y las consultas, luego con importacion y URLs, y por ultimo con branding y ajustes finos.

La prioridad no debe ser el color de la marca, sino la separacion dura de datos.
