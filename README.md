# Taller 3 — API REST con Django REST Framework

Este proyecto parte de la entrega del Taller 2. Se conserva la arquitectura y la base de datos `db.sqlite3` recibida; no se eliminó ni se regeneró.

## Qué implementa el Taller 3

- `tienda_app/api/serializers.py`: adapta el modelo `Libro` a JSON y valida los datos recibidos para crear una compra (`libro_id`, `direccion_envio` y `cantidad`).
- `tienda_app/api/views.py`: expone `CompraAPIView`, que valida la entrada, obtiene el procesador mediante `PaymentFactory` y llama a `CompraService.ejecutar_compra`.
- `tienda_app/urls.py`: publica `POST /api/v1/comprar/`.
- `tienda_app/services.py`: se reutiliza sin duplicar la lógica de negocio. El servicio crea la orden, calcula el total con IVA, verifica el inventario, registra el pago a través del gateway y descuenta existencias.
- `tienda_app/infra/gateways.py`: el procesador predeterminado genera el archivo `pagos_locales_NICOLAS_MORENO.log`.
- `tienda_app/tests.py`: se añadieron pruebas del endpoint API para compra exitosa, entrada inválida y falta de inventario.

## Importante: preservar los libros

La base de datos original se encuentra en `db.sqlite3`. **No ejecutes `python manage.py flush`, no borres `db.sqlite3` y no crees otra base de datos encima.** Antes de probar una compra real, haz una copia:

```cmd
copy db.sqlite3 db.sqlite3.respaldo
```

`python manage.py test` utiliza una base de datos temporal de pruebas; no debe borrar los libros de la base real. Una compra enviada manualmente al servidor sí cambia el inventario y crea una orden, por lo que se recomienda hacer una sola compra de prueba y guardar evidencia antes y después.

## Ejecutar en Windows CMD

Abre CMD en la carpeta que contiene `manage.py`.

Si ya tienes un entorno virtual funcional, actívalo. Si no, créalo:

```cmd
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Comprueba la configuración y las migraciones pendientes sin borrar datos:

```cmd
python manage.py check
python manage.py showmigrations
python manage.py migrate
python manage.py test
```

Inicia el servidor:

```cmd
python manage.py runserver
```

No se incluyen archivos `.bat` ni ejecutables; todos los comandos se escriben directamente en CMD.

## Probar el endpoint

Endpoint: `http://127.0.0.1:8000/api/v1/comprar/`

Método HTTP: `POST`

Cuerpo JSON de ejemplo (cambia `libro_id` por el ID de un libro que exista y tenga stock):

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 123",
  "cantidad": 1
}
```

Puedes probarlo con Postman (Body → raw → JSON) o con la interfaz navegable de DRF en el navegador. Una compra real reduce el inventario y crea una orden. La respuesta exitosa usa HTTP `201 Created`; datos inválidos producen `400 Bad Request`; falta de stock o rechazo del pago produce `409 Conflict`.

## Evidencias para entregar

Consulta `TUTORIAL_TALLER3.md`, que contiene el procedimiento completo, los comandos y la lista de capturas y archivos que debes subir. La guía fuente pide un archivo de log de pagos y una captura del POST a `/api/v1/comprar/` donde se evidencie que el inventario también cambia en la página HTML.


Actualización: la tienda muestra el stock disponible y el POST de compra devuelve stock antes/después e inventario descontado para facilitar las evidencias del Taller 3. No se requieren migraciones.
