# Ejecucion de la API y pruebas

## Requisitos previos

- Estar situado en la raiz del proyecto.
- Tener Python 3.10 o superior disponible.
- Haber creado el entorno virtual `.venv`.

## 1. Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar dependencias

Si todavia no estan instaladas:

```powershell
python -m pip install -e .[dev]
```

Si venias de una instalacion anterior de dependencias, conviene reinstalarlas para que MediaPipe quede en una version compatible con la API actual:

```powershell
python -m pip install --force-reinstall -e .[dev]
```

## 3. Arrancar la API

Para ejecutar la API en local:

```powershell
python -m app.main
```

La API quedara disponible por defecto en:

```text
http://127.0.0.1:8000
```

Documentacion interactiva:

```text
http://127.0.0.1:8000/docs
```

## 4. Probar que la API responde

Puedes comprobar el endpoint de salud desde el navegador o con una peticion HTTP:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

## 5. Ejecutar el cliente de prueba con webcam

Con la API arrancada, en otra terminal dentro del proyecto:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py
```

Ese script:

- abre la webcam;
- captura frames periodicamente;
- envia cada frame al endpoint `POST /api/v1/inference/frame`;
- abre una ventana con el video en vivo;
- dibuja los landmarks y la respuesta del backend sobre la imagen;
- muestra tambien por consola la prediccion principal.

## 6. Parametros utiles del script de webcam

Seleccionar otra camara:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py --camera-index 1
```

Cambiar intervalo entre envios:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py --interval 0.5
```

Apuntar a otra URL base:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py --base-url http://127.0.0.1:8000
```

## 7. Ejecutar con HTTPS

Si configuras estas variables en tu `.env`:

```env
SIGNCAPTURE_SSL_ENABLED=true
SIGNCAPTURE_SSL_CERTFILE=certs/server.crt
SIGNCAPTURE_SSL_KEYFILE=certs/server.key
```

puedes arrancar la API igual:

```powershell
python -m app.main
```

En ese caso la URL sera:

```text
https://127.0.0.1:8000
```

Si el certificado es autofirmado, ejecuta el cliente de prueba asi:

```powershell
.\.venv\Scripts\python scripts\webcam_inference_client.py --base-url https://127.0.0.1:8000 --insecure
```

## 8. Ejecutar validaciones del proyecto

Pruebas automatizadas:

```powershell
python -m pytest
```

Chequeo de estilo:

```powershell
python -m ruff check .
```

## 9. Flujo recomendado de uso

1. Activar `.venv`.
2. Arrancar la API con `python -m app.main`.
3. Abrir `http://127.0.0.1:8000/docs` para revisar endpoints.
4. Lanzar el cliente `scripts/webcam_inference_client.py`.
5. Revisar la ventana y las predicciones devueltas.
6. Cerrar con `q` o `ESC`.
