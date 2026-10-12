# Tutorial completo — Taller 3: Introducción a APIs con DRF
**Proyecto:** tienda Django del Taller 2  
**Objetivo:** pasar de una compra iniciada desde una vista HTML a una compra iniciada por una API REST, reutilizando la misma capa de servicio.

## 1. Inspección del Taller 2 y punto de partida

La entrega recibida ya contiene buena parte de la implementación solicitada por el PDF:

| Archivo | Estado encontrado / función |
|---|---|
| `requirements.txt` | Django y Django REST Framework ya estaban declarados. Se añadieron `markdown` y `django-filter`, que menciona el tutorial de clase. |
| `Tienda/settings.py` | `rest_framework` ya estaba en `INSTALLED_APPS`. |
| `tienda_app/api/serializers.py` | Ya contiene `LibroSerializer` y `OrdenInputSerializer`. Este último valida ID del libro, dirección y cantidad. |
| `tienda_app/api/views.py` | Ya contiene `CompraAPIView`; llama a `PaymentFactory` y reutiliza `CompraService`. |
| `tienda_app/urls.py` | Ya publica `api/v1/comprar/`. |
| `tienda_app/services.py` | La lógica de compra está centralizada aquí; no se reescribió para la API. |
| `tienda_app/infra/factories.py` y `gateways.py` | La fábrica elige el procesador de pagos y el gateway predeterminado escribe un log. |
| `tienda_app/models.py` | Define libros, inventario y órdenes. No se modificaron modelos ni migraciones para este taller. |
| `db.sqlite3` | Se conservó byte por byte la base recibida, incluidos libros, inventario y órdenes existentes. |

Por lo tanto, el trabajo no requería reemplazar la aplicación: se mantuvo la API existente, se completó la documentación y se agregaron pruebas específicas del endpoint.

### Flujo que debe demostrarse

1. El cliente envía un `POST` JSON a `/api/v1/comprar/`.
2. `OrdenInputSerializer` valida los datos.
3. `CompraAPIView` obtiene el procesador de pagos desde `PaymentFactory`.
4. La vista llama a `CompraService.ejecutar_compra(...)`.
5. El servicio crea la orden con el `OrdenBuilder`, calcula el total con IVA y valida el inventario.
6. El procesador de pagos devuelve el resultado y, con el gateway predeterminado, añade una línea al log.
7. Si la compra es exitosa, el servicio descuenta existencias.
8. La misma base de datos es leída por la página HTML de la tienda; por eso el nuevo stock debe verse allí también.

La demostración arquitectónica es que HTML y API son dos entradas diferentes que reutilizan el mismo servicio de compra.

## 2. Precaución: no perder la base de datos

El archivo `db.sqlite3` está incluido en esta entrega. **No lo borres, no lo reemplaces y no ejecutes `python manage.py flush`.** Tampoco borres las migraciones.

Antes de hacer una compra manual de prueba, abre CMD en la carpeta del proyecto y crea un respaldo:

```cmd
copy db.sqlite3 db.sqlite3.respaldo
```

El comando crea una copia del archivo; no altera la base original. Conserva ambos archivos mientras terminas la práctica. No incluyas el respaldo en una entrega pública si contiene datos que no deban compartirse.

La base de datos incluida en el ZIP original contenía estos libros al inspeccionarla:

| ID | Título | Precio guardado | Stock guardado |
|---:|---|---:|---:|
| 1 | Clean Code | 85000 | 9 |
| 2 | Patrones de diseño | 72000 | 8 |
| 3 | Python para todos | 60000 | 12 |

Estos valores describen la copia recibida, no garantizan el stock actual después de las compras que ejecutes. Anota el stock real en tu aplicación justo antes de la prueba.

## 3. Preparar el proyecto desde CMD (sin BAT ni ejecutables)

1. Descomprime el ZIP en una carpeta normal de Windows.
2. Entra a esa carpeta desde el Explorador, haz clic en la barra de dirección, escribe `cmd` y presiona Enter. Debes quedar en la carpeta que contiene `manage.py`.
3. Confirma la ubicación:

```cmd
dir
```

Debes ver `manage.py`, `db.sqlite3`, `requirements.txt`, `Tienda` y `tienda_app`.

4. Si ya tienes un entorno virtual y funciona, actívalo. Si no tienes uno, créalo y actívalo:

```cmd
python -m venv venv
venv\Scripts\activate
```

5. Instala las dependencias:

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si `python` no se reconoce en CMD, instala Python y marca la opción para añadirlo al PATH, o prueba el lanzador `py` sustituyendo `python` por `py`.

## 4. Verificar sin borrar datos

Ejecuta los siguientes comandos, uno por uno:

```cmd
python manage.py check
python manage.py showmigrations
python manage.py migrate
python manage.py test
```

- `check` revisa errores de configuración.
- `showmigrations` muestra las migraciones conocidas.
- `migrate` aplica solo las migraciones que falten; no es un comando para vaciar los libros.
- `test` ejecuta las pruebas sobre una base temporal separada. No debe descontar el inventario de la base real.

En la entrega se añadieron pruebas para estos casos:
- Compra exitosa: responde `201`, crea una orden y reduce stock.
- Datos de entrada inválidos: responde `400` y no cambia el stock.
- Cantidad superior al stock: responde `409` y no crea una orden.

Guarda una captura de CMD mostrando el resultado final de `python manage.py test`, especialmente si termina con `OK`.

## 5. Iniciar Django

En CMD:

```cmd
python manage.py runserver
```

No cierres esa ventana mientras haces la prueba. Abre el navegador en:

- Tienda HTML: `http://127.0.0.1:8000/`
- Endpoint API: `http://127.0.0.1:8000/api/v1/comprar/`

En la página principal localiza el libro que usarás y registra su stock antes de la compra. El ID es el número que aparece en la base de datos, no necesariamente la posición visual de la tarjeta. Si la interfaz no muestra el ID, puedes comprobarlo desde CMD en otra ventana:

```cmd
python manage.py shell
```

Dentro de la consola Python de Django escribe:

```python
from tienda_app.models import Libro, Inventario
for libro in Libro.objects.all().order_by("id"):
    inv = Inventario.objects.filter(libro=libro).first()
    print(libro.id, libro.titulo, libro.precio, inv.cantidad if inv else 0)
```

Para salir de la consola escribe `exit()`.

## 6. Enviar el POST con Postman

La guía de clase permite Postman o la interfaz navegable de DRF. En Postman:

1. Crea una petición nueva.
2. Método: `POST`.
3. URL: `http://127.0.0.1:8000/api/v1/comprar/`.
4. Abre **Body → raw → JSON**.
5. Introduce el siguiente cuerpo. Cambia el ID si vas a comprar otro libro; utiliza cantidad `1` para reducir el impacto sobre los datos existentes.

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 123",
  "cantidad": 1
}
```

6. Pulsa **Send**.
7. Para una compra aprobada, verifica el código HTTP `201 Created` y una respuesta similar a:

```json
{
  "estado": "exito",
  "mensaje": "Orden creada. Total: 101150.00"
}
```

El total depende del precio del libro y del cálculo de IVA implementado en el proyecto; el ejemplo de respuesta corresponde a un libro con precio base de 85000 y una unidad.

**Toma una captura** en la que se vean el método POST, la URL, el JSON enviado y la respuesta `201`. No recortes el código de estado.

### Alternativa: interfaz navegable de DRF

Con el servidor en marcha, abre `http://127.0.0.1:8000/api/v1/comprar/`. Si se muestra la interfaz navegable, selecciona `POST`, rellena los campos equivalentes y envía la petición. Si no aparece un formulario apropiado o tienes problemas con el navegador, usa Postman.

## 7. Comprobar el inventario HTML

Después de que el POST devuelva `201`:

1. Vuelve a la página `http://127.0.0.1:8000/`.
2. Actualízala.
3. Busca el mismo libro.
4. Confirma que su stock disminuyó en la cantidad enviada.
5. Toma una captura de la página HTML con el stock actualizado.

Esta evidencia es fundamental: demuestra que la API no mantiene un inventario paralelo, sino que utiliza la misma capa de negocio y los mismos datos que la tienda HTML.

## 8. Comprobar el log de pagos

El procesador predeterminado `BancoNacionalProcesador` escribe en el archivo:

`pagos_locales_NICOLAS_MORENO.log`

El archivo se crea en el directorio de trabajo desde el que ejecutaste `python manage.py runserver` (normalmente la carpeta raíz donde está `manage.py`). Después de la compra:

1. Detén el servidor con `Ctrl+C` en CMD.
2. Busca el archivo con:

```cmd
dir pagos_locales_NICOLAS_MORENO.log
type pagos_locales_NICOLAS_MORENO.log
```

3. Toma una captura de CMD en la que se vea la ruta/nombre del archivo y la línea de transacción correspondiente.

No confundas una compra real de prueba con las pruebas automáticas: estas últimas sustituyen el procesador por uno simulado y no necesitan escribir en el log. Si habías configurado `PAYMENT_PROVIDER=MOCK` en esa ventana de CMD, el gateway bancario no se usará; para la evidencia del log, utiliza el procesador predeterminado (sin definir `PAYMENT_PROVIDER=MOCK`) y reinicia el servidor.

## 9. Respuestas de error que puedes verificar opcionalmente

- `400 Bad Request`: por ejemplo, `libro_id` no entero o campo requerido ausente.
- `409 Conflict`: el libro no tiene unidades suficientes o el pago es rechazado.
- `201 Created`: compra aceptada.

No hace falta hacer una compra adicional para demostrar el error de stock; la prueba automática incluida ya verifica el caso sin cambiar la base de datos real. Si haces una prueba manual, evita modificar innecesariamente los datos que quieres conservar.

## 10. Archivos y capturas que debes entregar

La sección **“Entrega de Resultados”** del PDF del curso solicita:
1. **Archivo de log de pagos**, que evidencie que el sistema procesó el pago.
2. **Captura del POST** enviado a `/api/v1/comprar/` desde Postman o la interfaz web de DRF.
3. En la evidencia, debe poder comprobarse que el inventario se descontó y que la vista HTML refleja el cambio.

Para que la entrega sea más sólida, también recomiendo adjuntar:
4. Captura de CMD con `python manage.py test` finalizando correctamente.
5. Captura de la página HTML con el stock antes o después de la compra (idealmente el stock posterior; si tomas ambas, nómbralas claramente).
6. El código fuente del proyecto comprimido, conservando `db.sqlite3`.

Nombres sugeridos para organizar las evidencias (son nombres de archivos normales, no scripts):
- `01_pruebas_django.png`
- `02_post_api_respuesta_201.png`
- `03_inventario_html_actualizado.png`
- `04_log_pagos.png`

Sube los archivos a la asignación indicada por el docente: **“tutorial0-3 DRF&API”** (verifica en la plataforma que el nombre siga siendo ese).

## 11. Qué se modificó en esta entrega

- Se conservó la base `db.sqlite3` del ZIP de Taller 2, sin recrearla ni editar sus registros.
- Se mantuvo el endpoint API y la lógica de compra ya presentes.
- Se añadieron dependencias `markdown` y `django-filter` indicadas en el tutorial de clase.
- Se añadieron tres pruebas automatizadas de la API.
- Se documentaron la instalación, las pruebas, el POST, el log y las evidencias.
- No se incluyeron archivos `.bat`, instaladores ni ejecutables.

## 12. Lista final de verificación

- [ ] Hice una copia de seguridad de `db.sqlite3`.
- [ ] `python manage.py check` no reporta errores.
- [ ] `python manage.py test` termina con `OK`.
- [ ] El servidor inicia desde CMD.
- [ ] El POST a `/api/v1/comprar/` devuelve `201`.
- [ ] El inventario disminuye y la página HTML muestra el nuevo valor.
- [ ] Existe `pagos_locales_NICOLAS_MORENO.log` y contiene el registro.
- [ ] Guardé la captura del POST, la captura del inventario y la captura del log.
- [ ] Adjunté el código fuente y los archivos solicitados por el docente.


## Evidencia visible del descuento de inventario (actualización)

La página principal ahora muestra **Stock disponible** para cada libro. La vista de compra también muestra el stock antes de confirmar y el stock restante después de comprar. La respuesta exitosa del endpoint `POST /api/v1/comprar/` incluye `stock_antes`, `stock_despues` e `inventario_descontado`. El log de pagos registra el pago, no el inventario; para demostrar el descuento usa la respuesta JSON y la tienda HTML.

### Prueba recomendada

1. Inicia Django con `python manage.py runserver`.
2. Abre `http://127.0.0.1:8000/` y toma una captura del stock inicial del libro que usarás.
3. En Postman envía un `POST` a `http://127.0.0.1:8000/api/v1/comprar/`, con `Body > raw > JSON`, por ejemplo:

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 123",
  "cantidad": 1
}
```

4. Guarda una captura de la respuesta `201 Created`; debe mostrar `stock_antes`, `stock_despues` e `inventario_descontado`.
5. Recarga `http://127.0.0.1:8000/` y toma una segunda captura donde se vea el stock actualizado.
6. Conserva el archivo `pagos_locales_NICOLAS_MORENO.log` como evidencia adicional del pago.

No es necesario crear migraciones: estos cambios solo modifican vistas, respuesta API y plantillas. Se conserva la base de datos existente.
