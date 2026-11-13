# SprintDesk — requisitos y límites del laboratorio

## Fuentes de verdad

- **Arquitectura objetivo:** `docs/ARQUITECTURA-OBJETIVO.pdf`.
- **Estado real:** `app/` (se inspecciona y prueba; nunca se asume implementado por estar descrito).
- **Copia inicial:** `.baseline/app/` (no tocar; se usa en el comparador).

## Diez funcionalidades (100 % del alcance funcional)

| ID | Requisito | Estado inicial |
|---|---|---|
| R01 | Listar tareas: GET /api/tasks + mostrar en pantalla | Operativo |
| R02 | Crear tarea: POST /api/tasks + mostrar en pantalla | Operativo |
| R03 | Editar título: PUT /api/tasks/{id} + UI editar/guardar | Pendiente |
| R04 | Marcar tarea como completada/reabrir | Pendiente |
| R05 | Eliminar tarea | Pendiente |
| R06 | Buscar tarea por texto | Pendiente |
| R07 | Filtrar por estado | Pendiente |
| R08 | Asignar prioridad | Pendiente |
| R09 | Asignar categorías | Pendiente |
| R10 | Consultar historial | Pendiente |

El porcentaje **20 % inicial y 30 % objetivo** representa solo 2/10 y 3/10 funcionalidades comprobadas. **No** es un indicador de calidad arquitectónica o cobertura de pruebas.

## ÚNICO incremento autorizado para la demostración

Implementa **R03**, sin R04–R10, respetando R01/R02 y los siguientes criterios:

- `PUT /api/tasks/{id}` recibe `{"title":"Nuevo título"}`.
- Respuesta 200: JSON con `id`, `title`, `done` actualizados.
- Título vacío o espacios en blanco: error 400 con cuerpo JSON.
- ID inexistente: error 404 con cuerpo JSON.
- UI: acción **Editar**, campo para cambiar título, **Guardar** y confirmación visible.
- Después de guardar y **recargar la página**, el título se conserva mientras el proceso de backend continúa activo.
- No exigir persistencia tras reiniciar el servidor en este incremento; SQLite queda para la arquitectura final.
- No desplegar este proyecto públicamente; el backend contiene deficiencias deliberadas.

## Valor de la verificación

1. No basta con que el agente escriba código o afirme que pasó pruebas.
2. El verificador independiente `python check.py` ejecuta solicitudes reales a la API y revisa regresiones R01/R02, R03 éxito y errores 400/404.
3. Si el agente tiene **browser tools** disponibles en VS Code, debe abrir la aplicación y probar R03 visualmente (editar, guardar, recargar). Si no dispone de ellas, declarar **UI no comprobada**, sin simular resultados.
4. El comparador muestra cambios reales `app/` vs `.baseline/app/` y el estado de pruebas; ninguna de esas métricas prueba por sí sola que la arquitectura ya sea óptima.
5. Nunca modificar `comparador/`, `.baseline/`, `check.py`, `run.py` ni `docs/` durante el incremento.
