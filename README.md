# Architecture Guardian · laboratorio SprintDesk

Architecture Guardian es un agente personalizado para GitHub Copilot que implementa cambios autorizados y los evalúa con **verificación basada en riesgos**. No se limita a generar código: localiza la arquitectura del proyecto, identifica comportamientos que podrían romperse, ejecuta comprobaciones observables y entrega una decisión de aceptación basada en evidencia.

Este repositorio incluye SprintDesk, una aplicación local mínima para demostrar ese flujo, y un comparador web que muestra diferencias reales entre el código base y el código actual.

> Uso exclusivamente local y educativo. No publicar ni usar en producción.

## Requisitos

- Windows con PowerShell.
- Python **3.12** disponible como `py -3` o `python`.
- Git, para clonar el repositorio.
- VS Code con GitHub Copilot Chat, solo si se quiere utilizar el agente `guardian`.

No requiere `pip install`, Node.js, Docker, base de datos, Ollama ni servicios externos.

## Clonar en otra computadora

```powershell
git clone https://github.com/Aaron-sd99/apppp.git
cd apppp
```

Abre la carpeta completa `apppp` en VS Code; no abras únicamente `app`.

## Levantar la infraestructura local

En una terminal PowerShell desde la raíz del repositorio:

```powershell
py -3 run.py
```

Si el comando `py` no existe, usa:

```powershell
python run.py
```

El proceso inicia dos servicios con biblioteca estándar de Python:

| Servicio | Dirección | Propósito |
| --- | --- | --- |
| SprintDesk | `http://127.0.0.1:8765` | Aplicación frontend y API local |
| Comparador | `http://127.0.0.1:8766` | Diferencias reales entre `.baseline/app` y `app` |

Mantén esa terminal abierta. Detén ambos servicios con `Ctrl+C`.

Si alguno de los puertos está ocupado, libera el proceso que lo usa o inicia individualmente los servicios con un puerto alternativo:

```powershell
$env:SPRINTDESK_PORT='8876'; py -3 app/backend/server.py
$env:GUARDIAN_COMPARE_PORT='8877'; py -3 comparador/server.py
```

## Comprobar la aplicación

Con SprintDesk levantado o sin él, ejecuta en otra terminal:

```powershell
py -3 check.py
```

El verificador inicia una instancia aislada, realiza peticiones HTTP reales y deja su resultado en `.evidence/check.json`. Comprueba R01, R02 y el contrato de edición R03, incluidos errores de título vacío e ID inexistente.

Para declarar una prueba visual solo después de observar realmente crear → editar → guardar → recargar en el navegador:

```powershell
py -3 check.py --confirm-ui --ui-note "Comprobado en navegador local: crear, editar, guardar y recargar"
```

La declaración visual no sustituye una prueba E2E independiente. Si el código de `app/` cambia, el comparador invalida automáticamente esa evidencia anterior.

## Usar el agente `guardian` en VS Code

El archivo `.github/agents/guardian.agent.md` se descubre automáticamente al abrir este repositorio en VS Code con GitHub Copilot Chat disponible.

1. Abre **Copilot Chat**.
2. Selecciona el modo **Agent**.
3. En el selector de agentes, elige **guardian**. Si no aparece, ejecuta `Developer: Reload Window` y verifica que abriste la raíz del repositorio.
4. Dale un requisito explícitamente autorizado, la ruta de la arquitectura o especificación y los contratos que debe preservar.

Ejemplo de mensaje:

> Implementa el requisito autorizado `<ID o descripción>`. Consulta la arquitectura en `<ruta>`, preserva `<contratos o módulos>`, no modifiques `<rutas protegidas>`. Aplica Architecture Guardian: identifica riesgos, ejecuta las comprobaciones disponibles y entrega una decisión con evidencia.

El agente no instala dependencias, no usa Internet y no modifica pruebas existentes para ocultar fallos. Si no hay criterios de aceptación o arquitectura disponible, debe declararlo y solicitar la información necesaria antes de editar.

## Qué demuestra el comparador

Abre `http://127.0.0.1:8766` después de ejecutar `run.py`. La página muestra:

- archivos modificados frente a `.baseline/app`;
- diferencias de código antes/después;
- estado de verificación HTTP;
- confirmación visual declarada, si existe y sigue vigente.

El comparador es evidencia de cambios y ejecuciones locales; no demuestra por sí solo que una arquitectura sea correcta ni sustituye la revisión técnica.

## Estructura

```text
.github/agents/guardian.agent.md  Agente personalizado reutilizable
app/                              Aplicación local SprintDesk
.baseline/app/                    Estado original protegido para comparación
comparador/                       Página y servidor local de diferencias
docs/                             Requisitos y arquitectura del laboratorio
check.py                          Verificación HTTP independiente
run.py                            Inicio de los servicios locales
```

## Límites del laboratorio

SprintDesk mantiene su estado en memoria: las tareas no persisten tras reiniciar el backend. El proyecto contiene simplificaciones deliberadas y no debe desplegarse públicamente.
