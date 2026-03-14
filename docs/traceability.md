# Trazabilidad y mantenimiento

## Responsabilidades por capa

### Rutas

Responsables de exponer endpoints HTTP y declarar dependencias de FastAPI. No deben contener logica de negocio.

### Controladores

Responsables de orquestar casos de uso y transformar errores internos en respuestas HTTP coherentes.

### Servicios

Responsables de la logica funcional del sistema. Aqui viven las reglas de validacion, extraccion y clasificacion.

### Modelos

Responsables de definir contratos de datos estables, validables y tipados.

### Vistas

Responsables de preparar la respuesta final para el cliente.

## Matriz de trazabilidad

| Necesidad funcional | Modulo principal | Elementos implicados |
| --- | --- | --- |
| Recibir un frame | `app/routes/endpoints/inference.py` | `infer_frame`, `InferenceController.infer_frame` |
| Recibir un video | `app/routes/endpoints/inference.py` | `infer_video`, `InferenceController.infer_video` |
| Validar limites de entrada | `app/services/inference.py` | `_validate_size`, `Settings` |
| Extraer landmarks de imagen | `app/services/media.py` | `extract_from_image_bytes` |
| Extraer landmarks de video | `app/services/media.py` | `extract_from_video_file` |
| Clasificar una deteccion | `app/services/classifier.py` | `predict` |
| Formatear respuesta | `app/views/inference_view.py` | `build_inference_response` |
| Configurar limites y host | `app/core/config.py` | `Settings`, `get_settings` |

## Reglas de mantenimiento

- Si cambia el contrato de respuesta, actualizar primero `app/models/inference.py`.
- Si cambia la estrategia de extraccion visual, concentrar los cambios en `app/services/media.py`.
- Si cambia el modelo de clasificacion, mantener estable el contrato de `GestureClassifierService.predict`.
- Si aparecen errores HTTP nuevos, centralizar su traduccion en los controladores.
- Si el sistema incorpora persistencia, evitar introducir acceso a base de datos dentro de rutas o vistas.

## Convenciones de documentacion

- Cada clase debe describir su responsabilidad y su contexto.
- Cada metodo publico debe explicar entradas, salidas y errores esperados.
- Las decisiones de arquitectura deben reflejarse en esta carpeta `docs/`.
- Las variables de entorno y limites operativos deben reflejarse en `README.md` y `.env.example`.

## Checklist para evolucionar el proyecto

1. Revisar si el cambio afecta al contrato HTTP.
2. Revisar si el cambio rompe el desacoplamiento entre capas.
3. Anadir o actualizar docstrings en clases y metodos afectados.
4. Actualizar la documentacion de `docs/` si la arquitectura cambia.
5. Ejecutar `pytest` y `ruff check .`.
