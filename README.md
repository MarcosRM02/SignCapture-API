# SignCapture API

API en Python preparada para recibir frames individuales o videos completos y procesarlos con un pipeline orientado a MediaPipe y un clasificador de lenguaje de signos.

## Objetivo

El proyecto proporciona una base mantenible para una API de inferencia de lenguaje de signos a partir de vision por computador. La solucion esta pensada para crecer de forma incremental:

- hoy: recepcion de frames y videos, extraccion de landmarks y clasificacion desacoplada;
- siguiente fase: integracion de un clasificador real;
- fases posteriores: persistencia, trazabilidad operativa, observabilidad y versionado de modelos.

## Arquitectura

Se sigue una estructura MVC adaptada a una API:

- `controllers`: coordinan los casos de uso expuestos por HTTP.
- `models`: definen los esquemas de entrada y salida.
- `views`: formatean las respuestas HTTP.
- `services`: contienen la logica de negocio y el pipeline de procesamiento.

Documentacion ampliada:

- [docs/architecture.md](./docs/architecture.md)
- [docs/traceability.md](./docs/traceability.md)

## Puesta en marcha

1. Crear y activar el entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Si ya tenias dependencias instaladas de una iteracion anterior y notas errores de MediaPipe, reinstalalas:

```powershell
python -m pip install --force-reinstall -e .[dev]
```

3. Arrancar la API:

```powershell
python -m app.main
```

## Endpoints principales

- `GET /api/v1/health`
- `POST /api/v1/inference/frame`
- `POST /api/v1/inference/video`

## Flujo funcional

1. El cliente envia un frame o un video mediante `multipart/form-data`.
2. La ruta HTTP delega en el controlador.
3. El controlador invoca el servicio de inferencia.
4. El servicio valida tamanos y delega en MediaPipe para extraer landmarks.
5. El clasificador transforma la secuencia de landmarks en una prediccion.
6. La vista construye una respuesta serializable y estable.

## Configuracion

Las variables de entorno disponibles se documentan en [`.env.example`](./.env.example):

- `SIGNCAPTURE_HOST`
- `SIGNCAPTURE_PORT`
- `SIGNCAPTURE_SSL_ENABLED`
- `SIGNCAPTURE_SSL_CERTFILE`
- `SIGNCAPTURE_SSL_KEYFILE`
- `SIGNCAPTURE_MAX_VIDEO_FRAMES`
- `SIGNCAPTURE_MAX_FRAME_BYTES`
- `SIGNCAPTURE_MAX_VIDEO_BYTES`

## HTTPS

La API puede exponerse por HTTPS directamente desde Uvicorn para desarrollo o entornos simples. Para ello:

1. Genera o coloca un certificado y su clave privada dentro del proyecto.
2. Configura en `.env`:

```env
SIGNCAPTURE_SSL_ENABLED=true
SIGNCAPTURE_SSL_CERTFILE=certs/server.crt
SIGNCAPTURE_SSL_KEYFILE=certs/server.key
```

3. Arranca la API normalmente:

```powershell
python -m app.main
```

Si usas un certificado autofirmado, el cliente de pruebas puede desactivar la verificacion TLS. En produccion, lo recomendable sigue siendo terminar HTTPS en un proxy inverso como Nginx, Traefik o un balanceador.

## Script de prueba con webcam

Se ha incluido un cliente de prueba en [scripts/webcam_inference_client.py](./scripts/webcam_inference_client.py) para capturar frames de la webcam y enviarlos al endpoint `POST /api/v1/inference/frame`.

El cliente abre una ventana con la imagen en vivo y superpone:

- la prediccion devuelta por el backend;
- la confianza y metadatos principales;
- los landmarks que devuelve la API;
- el ultimo error HTTP, si existe.

Ejemplo basico:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py
```

Ejemplo contra HTTPS con certificado autofirmado:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py --base-url https://127.0.0.1:8000 --insecure
```

Parametros utiles:

- `--camera-index`: selecciona la webcam.
- `--interval`: segundos entre envios.
- `--jpeg-quality`: calidad de compresion del frame.
- `--insecure`: desactiva verificacion TLS para pruebas.

Controles:

- `q`: salir del cliente.
- `ESC`: salir del cliente.

## Notas

- La persistencia no esta implementada por ahora.
- El clasificador actual es un placeholder para poder evolucionar despues hacia un modelo real.
- MediaPipe esta encapsulado en un servicio para facilitar cambios de implementacion.
- La documentacion del codigo se ha dejado en forma de docstrings para favorecer trazabilidad y mantenimiento.

## Calidad

Validaciones recomendadas sobre la base actual:

- `pytest`
- `ruff check .`
