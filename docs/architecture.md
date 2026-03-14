# Arquitectura

## Vision general

La API sigue una estructura MVC adaptada a servicios HTTP. Aunque no existe una capa de persistencia en esta fase, la separacion de responsabilidades ya esta preparada para incorporarla mas adelante sin mezclar logica de dominio, transporte y presentacion.

## Objetivos de diseno

- Mantener el codigo modular y sustituible.
- Facilitar la integracion futura de un clasificador real.
- Hacer trazable el recorrido de una peticion desde la ruta HTTP hasta la respuesta.
- Encapsular las dependencias pesadas como MediaPipe y OpenCV.
- Minimizar el acoplamiento entre framework web y logica de negocio.

## Estructura de carpetas

### `app/main.py`

Punto de entrada de FastAPI. Construye la aplicacion, inyecta el prefijo de API y expone una funcion `run()` para desarrollo local.

### `app/core`

Contiene configuracion transversal del sistema:

- `config.py`: centraliza parametros de despliegue y limites operativos.

### `app/routes`

Define la interfaz HTTP:

- `api.py`: compone el router raiz.
- `endpoints/health.py`: endpoint de salud.
- `endpoints/inference.py`: endpoints de inferencia de frame y video.

### `app/controllers`

Implementa la orquestacion entre la capa HTTP y los servicios de negocio:

- traduce errores de dominio a errores HTTP;
- mantiene delgada la capa de rutas;
- prepara la salida a traves de la vista.

### `app/services`

Contiene la logica principal del sistema:

- `inference.py`: caso de uso principal de inferencia;
- `media.py`: extraccion de landmarks con MediaPipe;
- `classifier.py`: clasificador desacoplado del transporte.

### `app/models`

Define contratos de entrada y salida mediante Pydantic. Estos modelos son la referencia estable del API contract.

### `app/views`

Formatea respuestas de salida para aislar la serializacion del resto del sistema.

### `tests`

Recoge pruebas automatizadas. Actualmente incluye una validacion basica del endpoint de salud.

## Flujo de una peticion

### `POST /api/v1/inference/frame`

1. La ruta recibe un `UploadFile`.
2. FastAPI resuelve la dependencia `InferenceController`.
3. El controlador llama a `InferenceService.process_frame`.
4. El servicio valida el tamano del archivo.
5. `MediaPipeHandLandmarkService` decodifica la imagen y extrae landmarks.
6. `GestureClassifierService` genera una prediccion.
7. La vista transforma el resultado a un diccionario JSON serializable.

### `POST /api/v1/inference/video`

1. La ruta recibe un archivo de video.
2. El servicio valida el tamano maximo configurado.
3. El video se procesa frame a frame hasta `max_video_frames`.
4. Se registran los frames procesados y los frames con mano detectada.
5. El clasificador recibe la secuencia detectada y devuelve una prediccion.

## Decisiones tecnicas

### FastAPI

Se ha elegido por:

- tipado fuerte con Pydantic;
- documentacion OpenAPI automatica;
- buen soporte para subida de ficheros;
- simplicidad para evolucionar hacia dependencias, middlewares y seguridad.

### MediaPipe aislado en servicio

MediaPipe y OpenCV son dependencias especializadas. Se han encapsulado en `media.py` para:

- evitar que el resto del sistema dependa de detalles de vision;
- poder sustituir el motor de extraccion si cambia la estrategia;
- centralizar decisiones de rendimiento y transformacion de imagen.

### Clasificador desacoplado

El clasificador actual es un placeholder, pero ya implementa el contrato que usara el modelo real. Eso reduce el coste de evolucion futura y permite probar el pipeline sin esperar al entrenamiento del modelo.

## Puntos de extension

- Sustituir `GestureClassifierService` por un modelo real cargado en memoria.
- Anadir una capa `repositories` o `adapters` cuando aparezca persistencia.
- Incorporar telemetria y logging estructurado.
- Versionar modelos y respuestas si la semantica de salida cambia.
- Introducir colas o procesamiento asincrono si el tiempo de inferencia crece.

## Riesgos actuales

- El procesamiento de video usa un archivo temporal local.
- No hay autenticacion ni control de cuota.
- La salida devuelve landmarks de todas las detecciones, lo que puede crecer en videos largos.
- El clasificador no representa todavia la logica definitiva del dominio.
