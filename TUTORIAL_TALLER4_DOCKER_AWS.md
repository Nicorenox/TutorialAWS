# Taller 4 — Dockerización y despliegue en AWS Academy (Windows CMD)

Esta guía sigue el PDF `tutorial04_Docker_AWS.pdf` y usa la versión más reciente del Taller 3 (API y stock visible).

## Qué se va a hacer
1. Mantener intacto `db.sqlite3` de tu proyecto local.
2. Construir una imagen Docker de Django.
3. Ejecutar Django y PostgreSQL con Docker Compose en el computador.
4. Copiar el proyecto a un repositorio GitHub (o transferirlo por SCP).
5. Crear una instancia EC2 en AWS Academy y ejecutar allí los mismos contenedores.
6. Abrir `http://IP_PUBLICA:8000/api/v1/comprar/` y tomar la captura solicitada.

**Importante sobre la base de datos:** el proyecto local continúa usando SQLite cuando no se define `DB_HOST`. Docker usa PostgreSQL. Son bases distintas; el `db.sqlite3` original no se borra ni se modifica por Compose. Para que Docker tenga los libros y el inventario originales, exporta Libro e Inventario a un fixture e impórtalo una vez en PostgreSQL (paso 4). El volumen `postgres_data` conserva los datos de PostgreSQL al reiniciar contenedores. No ejecutes `docker compose down -v`.

## Requisitos
- Proyecto extraído y funcional del Taller 3.
- Docker Desktop instalado y abierto en Windows.
- Git instalado (si usarás GitHub).
- Cuenta activa de AWS Academy y laboratorio iniciado.
- Acceso a GitHub o posibilidad de transferir archivos con SCP.

## Paso 0 — Copia de seguridad y comprobación local
Abre CMD en la carpeta donde está `manage.py`. Confirma con `dir` que aparecen `manage.py` y `db.sqlite3`.

Crea una copia de seguridad:

```cmd
copy db.sqlite3 db.sqlite3.respaldo
```

Activa el entorno virtual si ya existe y comprueba el proyecto:

```cmd
venv\Scripts\activate
python manage.py check
python manage.py test
```

No borres `db.sqlite3`. Si no tienes entorno virtual, puedes crear uno con `python -m venv venv` y activarlo.

## Paso 1 — Configuración por variables de entorno
La versión preparada de `Tienda/settings.py` elige SQLite cuando `DB_HOST` no existe y PostgreSQL cuando `DB_HOST` está definido. También lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS` del entorno.

No pegues contraseñas reales en GitHub. En la configuración de ejemplo, la clave de PostgreSQL es solo para el laboratorio; en AWS usa una contraseña propia y configura `DB_PASSWORD`/`DB_PASSWORD` en el entorno de Compose. Para una aplicación real, no expongas la base de datos a Internet.

## Paso 2 — Revisar Dockerfile y requirements.txt
En la raíz del proyecto (mismo nivel que `manage.py`) deben existir:
- `Dockerfile` (sin extensión)
- `docker-compose.yml`
- `.dockerignore`
- `requirements.txt`

`requirements.txt` incluye Django, Django REST Framework y `psycopg2-binary`, necesario para que Django conecte con PostgreSQL.

## Paso 3 — Construir y levantar los contenedores localmente
Abre Docker Desktop y espera a que indique que Docker está en ejecución. En CMD, en la raíz del proyecto, ejecuta:

```cmd
docker --version
docker compose version
docker compose up --build -d
docker compose ps
```

El servicio `web` ejecuta las migraciones automáticamente y luego inicia Django en el puerto 8000. Revisa los logs si no arranca:

```cmd
docker compose logs --tail 100 web
docker compose logs --tail 100 db
```

Abre en el navegador:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/v1/comprar/`

La API puede requerir una petición POST para procesar una compra; para la evidencia final del tutorial se pide que el navegador muestre la respuesta JSON del endpoint desde AWS. La interfaz navegable de DRF depende de la configuración y permisos de la vista.

## Paso 4 — Pasar los libros e inventario de SQLite a PostgreSQL
Haz esto una sola vez si necesitas que el entorno Docker tenga los libros existentes. El archivo `db.sqlite3` seguirá intacto.

1. **Detén solo el servicio web** (la base local de PostgreSQL no se borra):

```cmd
docker compose stop web
```

2. En otra ventana de CMD local, con el entorno Python del proyecto activado y sin `DB_HOST` definido, exporta los libros e inventarios de SQLite. Este comando crea un archivo JSON de datos, no un ejecutable:

```cmd
python manage.py dumpdata tienda_app.Libro tienda_app.Inventario --indent 2 -o datos_libros.json
```

Si el comando indica que no reconoce una etiqueta, revisa los nombres de modelos en `tienda_app/models.py` y utiliza las etiquetas reales. No borres la base SQLite.

3. Copia `datos_libros.json` a la raíz del proyecto, junto a `manage.py`. En CMD ejecuta:

```cmd
docker compose start db
docker compose run --rm web python manage.py loaddata datos_libros.json
```

Si `web` ejecuta `migrate` antes de `loaddata`, eso es normal. Si los libros ya fueron importados anteriormente, no vuelvas a importar el fixture sin revisar duplicados.

4. Inicia el servicio web y verifica:

```cmd
docker compose up -d web
docker compose ps
docker compose logs --tail 50 web
```

Abre `http://127.0.0.1:8000/` y comprueba que se vean los libros y sus existencias. La base PostgreSQL vive en el volumen `postgres_data`; el archivo original SQLite no cambia.

## Paso 5 — Preparar el código para AWS
El PDF asume GitHub. Sube el proyecto a un repositorio tuyo. No subas contraseñas, claves privadas ni archivos `.env`. Para un repositorio público, revisa el contenido antes de publicar.

Desde CMD, en la raíz del proyecto, los comandos generales son:

```cmd
git init
git add .
git commit -m "Taller 4 Docker y AWS"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Reemplaza la URL por la de tu repositorio. Si ya existe un repositorio Git, no repitas `git init` ni `git remote add origin`; verifica primero con `git status` y `git remote -v`.

**No subas `db.sqlite3.respaldo` ni credenciales.** El `.dockerignore` evita copiar la base SQLite a la imagen, y los datos se importan mediante el fixture. Si necesitas conservar el fixture para el despliegue, inclúyelo deliberadamente en el repositorio solo si contiene exclusivamente datos de prueba no sensibles.

## Paso 6 — Crear la instancia EC2 en AWS Academy
1. Entra a AWS Academy LMS y pulsa iniciar/Start Lab. Espera que el indicador esté activo.
2. Abre AWS Console → EC2 → Instances → Launch instance.
3. Name: `Servidor-Django`.
4. AMI: Amazon Linux 2023.
5. Tipo de instancia: selecciona el tipo permitido por el laboratorio (el PDF indica `t2.micro`; si no aparece, utiliza el tipo equivalente permitido por AWS Academy).
6. Key pair: `vockey`, si está disponible y así lo indica el laboratorio.
7. En reglas de red permite SSH (22) desde tu IP y HTTP/HTTPS si los pide el laboratorio. El puerto 8000 se agrega en el paso 9.
8. Lanza la instancia y espera estado `Running` y comprobaciones correctas.

No compartas la clave privada ni credenciales de AWS en capturas.

## Paso 7 — Conectar e instalar Docker en EC2
Selecciona la instancia → Connect → EC2 Instance Connect. En la terminal del navegador ejecuta:

```bash
sudo dnf update -y
sudo dnf install git docker -y
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

Vuelve a conectarte para aplicar el grupo de Docker. Verifica:

```bash
docker --version
docker compose version
```

Si `docker compose version` no está disponible, revisa las instrucciones vigentes de AWS para instalar el complemento Compose o usa el comando Compose que esté disponible en esa AMI. No continúes hasta confirmar que Compose funciona.

## Paso 8 — Clonar y ejecutar el proyecto en AWS
En la terminal de EC2:

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
docker compose up -d --build
docker ps
docker compose logs --tail 100 web
```

Reemplaza los valores de ejemplo por tu URL y nombre de carpeta reales. Si el repositorio es privado, configura un método seguro para acceder; no pegues tokens de acceso en capturas ni en el código.

Si quieres conservar libros específicos en la PostgreSQL de EC2, copia `datos_libros.json` de forma segura a la carpeta del proyecto y ejecuta una sola vez:

```bash
docker compose run --rm web python manage.py loaddata datos_libros.json
```

Si el fixture ya está cargado, no lo vuelvas a importar sin revisar el estado de los datos. El volumen `postgres_data` conserva la base de datos entre reinicios de contenedores.

## Paso 9 — Abrir el puerto 8000
1. AWS Console → EC2 → Instances → selecciona `Servidor-Django`.
2. Abre Security → Security groups → selecciona el grupo asociado.
3. Edit inbound rules → Add rule.
4. Type: `Custom TCP`; Port range: `8000`.
5. Source: para una prueba controlada, tu IP pública `/32`. Si la rúbrica exige acceso desde cualquier lugar, usa `0.0.0.0/0` solo durante la demostración y retira esa regla después.
6. Guarda las reglas.

No abras el puerto 5432 de PostgreSQL al público. Solo el servicio web necesita publicar el puerto 8000.

## Paso 10 — Comprobar la entrega
Copia la IPv4 pública de la instancia desde EC2. En el navegador abre:

`http://IP_PUBLICA_EC2:8000/api/v1/comprar/`

Reemplaza `IP_PUBLICA_EC2` por la dirección real, sin los signos `< >`. Si se abre la interfaz navegable DRF, está bien. Si el endpoint solo acepta POST, puede aparecer `GET method not allowed`; en ese caso prueba también con Postman haciendo un POST y guarda la respuesta. Para cumplir literalmente el PDF, intenta mostrar la respuesta JSON en el navegador según el comportamiento de tu endpoint.

Si no carga:
- `docker ps` debe mostrar los contenedores en ejecución.
- `docker compose logs --tail 100 web` muestra errores de Django.
- Verifica que el grupo de seguridad tenga TCP 8000 permitido desde tu IP.
- Confirma que usaste la IPv4 pública actual de la instancia.
- Comprueba que `DJANGO_ALLOWED_HOSTS` incluya la IP pública de EC2. Puedes definirla en la configuración de Compose antes de reconstruir/reiniciar los contenedores.

## Evidencias que debes entregar
El PDF pide una captura de pantalla del navegador accediendo a `http://<IP-PUBLICA-EC2>:8000/api/v1/comprar/` donde se vea la respuesta de la API servida desde AWS.

Recomendado para demostrar el proceso completo:
1. `01_docker_local.png`: `docker compose ps` con los servicios levantados.
2. `02_ec2_running.png`: instancia EC2 en estado Running (oculta IDs sensibles si lo deseas).
3. `03_api_aws.png`: navegador mostrando la API en la IP pública y puerto 8000 (entregable obligatorio del PDF).
4. `04_postman_aws.png`: POST exitoso desde Postman, si la respuesta GET no está permitida.
5. `05_inventario_aws.png`: tienda HTML mostrando libros y stock, si se puede acceder a la ruta web.

No inventes capturas: deben ser de tu ejecución real.

## Apagar sin borrar los datos
En tu PC, cuando termines, puedes detener contenedores con:

```cmd
docker compose stop
```

Esto conserva el volumen. Evita `docker compose down -v`, porque `-v` elimina volúmenes y puede borrar la base PostgreSQL persistente. En AWS, detén o termina recursos solo según las reglas del laboratorio y recuerda que detener la instancia puede cambiar la IP pública.

## Problemas frecuentes
- `docker` no se reconoce: inicia Docker Desktop y abre un CMD nuevo.
- Puerto 8000 ocupado: cierra el servidor local Django que esté usando ese puerto o cambia el mapeo y la URL de forma consistente.
- Error de PostgreSQL: revisa `docker compose logs db` y que `DB_PASSWORD` coincida en ambos servicios.
- `DisallowedHost`: agrega la IP pública real a `DJANGO_ALLOWED_HOSTS` y recrea el servicio web.
- La base aparece vacía en Docker: importa `datos_libros.json` como se indica en el paso 4.
- No se puede entrar desde fuera: revisa Security Group, IP pública y que `web` publique `8000:8000`.
