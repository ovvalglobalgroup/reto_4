# SIGA - Sistema Integral de Gestión Académica

Proyecto correspondiente al **Reto 4 de Programación II**, desarrollado en Python para integrar estructuras de datos enlazadas en un sistema de gestión académica.

El programa permite administrar inscripciones, cupos, listas de espera, estudiantes prioritarios e historiales académicos. También incorpora operaciones para deshacer cambios, guardar y recuperar información, realizar pruebas unitarias y analizar el rendimiento de las estructuras implementadas.

## 1. Requisitos y ejecución

Para ejecutar el proyecto se necesita:

- Python 3.10 o superior.
- Una terminal de Windows (CMD o PowerShell).
- No se requiere instalar paquetes externos.

Desde la carpeta principal `SIGA_Reto4`, ejecutar:

`py index.py`

En otros sistemas donde esté disponible el comando `python`, se puede utilizar:

`python index.py`

La aplicación muestra un menú con **11 opciones**. Antes de registrar estudiantes o gestionar inscripciones, es necesario configurar un curso mediante la opción 1, indicando su nombre y cantidad de cupos.

También se encuentran disponibles los siguientes comandos:

| Comando | Función |
|---|---|
| `py index.py` | Inicia el menú interactivo. |
| `py index.py --demo` | Ejecuta una demostración de los principales escenarios del sistema. |
| `py index.py --benchmark` | Realiza las mediciones de rendimiento y genera un archivo CSV. |
| `py -m unittest discover -s tests -v` | Ejecuta las pruebas unitarias disponibles. |

## 2. Estructura del proyecto

El programa está organizado en módulos para separar las estructuras de datos, las reglas académicas y las operaciones de almacenamiento.

```text
SIGA_Reto4/
├── index.py
├── src/
│   ├── __init__.py
│   ├── estructuras.py
│   ├── modelos.py
│   ├── sistema.py
│   ├── persistencia.py
│   └── benchmarks.py
├── tests/
│   ├── __init__.py
│   ├── test_estructuras.py
│   └── test_sistema.py
├── data/
│   ├── inscritos.csv
│   ├── historial.json
│   ├── esperas.json
│   └── benchmarks.csv
└── README.md
```

**Nota:** la carpeta `data/` se crea automáticamente cuando se realiza una exportación o se ejecutan los benchmarks. Los archivos que contiene se generan según las operaciones realizadas. Los directorios y archivos mostrados deben coincidir con los incluidos en la entrega.

### Responsabilidad de los módulos

| Archivo | Función |
|---|---|
| `index.py` | Contiene el menú principal, las validaciones de entrada, la demostración y el acceso a benchmarks. |
| `estructuras.py` | Implementa nodos, pilas, colas y listas enlazadas. |
| `modelos.py` | Define las entidades Estudiante, Materia y Semestre. |
| `sistema.py` | Coordina las inscripciones, cupos, retiros, historiales y operaciones de deshacer. |
| `persistencia.py` | Permite exportar e importar información mediante CSV y JSON. |
| `benchmarks.py` | Ejecuta las mediciones de rendimiento y guarda sus resultados. |
| `tests/` | Contiene las pruebas automatizadas del proyecto. |

## 3. Estructuras de datos implementadas

Las estructuras se desarrollaron mediante nodos propios, sin utilizar `list` ni `deque` como contenedores base.

- **Pila:** utiliza el principio LIFO para almacenar y recuperar registros de acciones.
- **ColaSimple:** administra estudiantes normales según el orden de llegada (FIFO).
- **ColaCircular:** mantiene a los estudiantes normales que pasan a espera cuando no existen cupos.
- **ColaPrioridad:** trabaja con cinco niveles de prioridad, donde 5 es el mayor. Conserva el orden FIFO entre estudiantes del mismo nivel.
- **ListaSimple:** almacena estudiantes inscritos y materias académicas.
- **ListaDoble:** organiza los semestres cronológicamente y permite recorrerlos en ambos sentidos.

Las listas y diccionarios nativos de Python se utilizan como representaciones temporales para operaciones como la serialización, la validación, los mensajes y las mediciones, pero no sustituyen a las estructuras enlazadas principales.

## 4. Reglas de funcionamiento

1. El usuario debe configurar el curso antes de gestionar estudiantes, indicando su nombre y la cantidad de cupos disponibles.

2. Los estudiantes sin prioridad ingresan a `ColaSimple`. Los que tienen una prioridad del 1 al 5 ingresan a `ColaPrioridad`.

3. Al procesar los turnos, se atiende primero a los estudiantes con mayor prioridad. Si no existen turnos prioritarios pendientes, se continúa con los estudiantes normales.

4. Cuando el curso está lleno, los turnos normales que se procesan pasan a `ColaCircular`. Los prioritarios permanecen en `ColaPrioridad` hasta que pueda asignárseles un cupo.

5. Cuando un estudiante inscrito se retira, el sistema intenta reasignar su cupo siguiendo este orden: **ColaPrioridad → ColaCircular → ColaSimple**.

6. El sistema valida los identificadores para evitar que un mismo estudiante figure simultáneamente en varias estructuras activas.

7. Los historiales académicos almacenan períodos, materias y calificaciones. Para este ejercicio se utiliza una escala de notas de 0 a 20 y términos académicos del 1 al 4.

8. La opción DESHACER recupera el estado anterior de la última operación registrada mediante una pila de acciones.

9. Configurar nuevamente un curso reinicia sus registros activos. Esta operación puede deshacerse mientras su registro permanezca en la pila.

## 5. Persistencia de datos

El programa permite guardar y recuperar información mediante archivos CSV y JSON.

Los archivos se almacenan dentro de la carpeta `data/`:

| Archivo | Contenido |
|---|---|
| `inscritos.csv` | Identificador, nombre, correo, curso y prioridad de los estudiantes inscritos. |
| `historial.json` | Períodos académicos, materias y calificaciones. |
| `esperas.json` | Configuración del curso y estudiantes pendientes en las diferentes colas. |
| `benchmarks.csv` | Resultados de las mediciones de rendimiento. |

La carpeta se crea automáticamente cuando se ejecuta una exportación o una medición de rendimiento.

### Exportación

Desde el menú principal:

- Seleccionar la opción 9.
- Introducir `E` para exportar.
- El programa genera o actualiza los archivos correspondientes.

**Importante:** la información no se guarda automáticamente al cerrar el programa. Para conservar los cambios, es necesario utilizar la opción de exportación.

### Importación

Para recuperar registros guardados:

- Iniciar el programa y configurar primero un curso.
- Seleccionar la opción 9.
- Introducir `I` para importar.
- El programa lee los archivos existentes y valida su contenido.

La importación comprueba la estructura de los archivos, los identificadores, las prioridades y los cupos disponibles antes de reemplazar la información activa.

Si se detectan datos incorrectos, se cancela la operación y se conserva el estado anterior del sistema.

## 6. Pruebas unitarias

El proyecto utiliza el módulo `unittest` de Python para comprobar el comportamiento de las estructuras de datos y las operaciones académicas.

Para ejecutar todas las pruebas desde la raíz del proyecto:

`py -m unittest discover -s tests -v`

Las pruebas comprueban aspectos como:

- Funcionamiento LIFO y FIFO.
- Atención de estudiantes según prioridad.
- Inserciones, búsquedas y eliminaciones.
- Saturación de cupos y listas de espera.
- Retiros y reasignaciones.
- Recuperación de estados mediante DESHACER.
- Organización de historiales académicos.
- Exportación, importación y validación de archivos.
- Manejo de situaciones límite.

El resultado mostrado por `unittest` permite identificar las pruebas satisfactorias y aquellas que requieren revisión.

## 7. Análisis de eficiencia

El módulo `benchmarks.py` utiliza `time.perf_counter()` para medir el rendimiento de las estructuras de datos.

Se realizan cinco ejecuciones por escenario y se calculan el tiempo promedio y la desviación estándar en milisegundos.

Las mediciones incluyen:

- Inserción de 1.000, 5.000 y 10.000 elementos en `ListaSimple`.
- Búsqueda de elementos al inicio, medio y final de `ListaSimple`.
- Eliminación de elementos en `ListaSimple` y `ListaDoble`.
- Procesamiento de 10.000 inserciones y 10.000 extracciones en cada una de las tres colas.

Para ejecutar las mediciones:

`py index.py --benchmark`

Los resultados se muestran en consola y se guardan automáticamente en `data/benchmarks.csv`.

Los tiempos pueden variar dependiendo de las características del equipo y las condiciones de ejecución.

## 8. Demostración del funcionamiento

El programa incluye un modo de demostración que permite observar los principales escenarios sin introducir manualmente todos los datos.

Ejecutar:

`py index.py --demo`

La demostración presenta situaciones relacionadas con inscripciones, prioridades, cupos, listas de espera, retiros, deshacer operaciones, historiales y persistencia.

Para la defensa académica se recomienda complementar esta demostración con una ejecución manual del menú, mostrando las operaciones y sus resultados directamente desde la consola.

## 9. Documentación del proyecto

El informe académico del SIGA presenta el planteamiento del problema, los objetivos, el diseño de la solución, las estructuras implementadas, el análisis de complejidad, las pruebas funcionales y los resultados de eficiencia.

El código se encuentra organizado en módulos Python para facilitar su lectura, mantenimiento y ejecución.

**Proyecto académico — Reto 4 de Programación II.**