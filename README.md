# SIGA - Sistema Integral de Gestión Académica

**Reto 4 de Programación II: estructuras enlazadas, historial académico, persistencia, pruebas y eficiencia.**

## Requisitos y ejecución

- Python **3.10 o superior**; no es necesario instalar paquetes de terceros.
- Abrir una terminal en la carpeta `SIGA_Reto4`.

```bash
python siga.py
```

La aplicación contiene las **11 opciones** solicitadas en el menú. Ejecute también:

```bash
python siga.py --demo
python siga.py --benchmark
python -m unittest discover -s tests -v
```

También se incluye `SIGA_Reto4_Standalone.py`: contiene toda la aplicación en un **único archivo** para entregas que no permitan subir carpetas. Se ejecuta con `python SIGA_Reto4_Standalone.py` y admite `--demo` / `--benchmark`. Para entregar y defender el diseño modular es preferible el proyecto completo.

En Windows, si el comando `python` no funciona, intentar `py siga.py`, `py siga.py --demo` y `py -m unittest discover -s tests -v`.

## Estructura del proyecto

```text
SIGA_Reto4/
├── siga.py                 # Menú CLI, demo y modo benchmark
├── src/
│   ├── estructuras.py      # Nodos, pila, colas y listas propias
│   ├── modelos.py          # Estudiante, Semestre, Materia
│   ├── sistema.py          # Reglas de inscripción, historial y deshacer
│   ├── persistencia.py     # CSV y JSON, carga transaccional
│   └── benchmarks.py       # Cinco ejecuciones y perf_counter()
├── tests/
│   ├── test_estructuras.py
│   └── test_sistema.py
├── data/
│   ├── inscritos.csv
│   ├── historial.json
│   ├── esperas.json
│   └── benchmarks.csv
├── evidencias/             # Salidas reproducibles y capturas
├── GUIA_VIDEO.md
└── README.md
```

## Diseño de las estructuras

- **Pila**: nodos simples enlazados; `push`, `pop`, `peek`, `is_empty`, `size`.
- **ColaSimple**: FIFO mediante referencias al principio y al final.
- **ColaCircular**: lista circular simple con nodo `último`; `último.siguiente` señala el primero.
- **ColaPrioridad**: cinco colas enlazadas (niveles 1 a 5); se explora primero nivel **5**, y el empate se resuelve mediante FIFO.
- **ListaSimple**: inscritos y materias con inserción al final, búsqueda, eliminación y recorrido.
- **ListaDoble**: historial académico ordenado por `(anio, term)`; avance, retroceso, búsqueda y eliminación.
- **Deshacer**: instantáneas del estado lógico anterior en una pila enlazada. Una operación de procesamiento o retiro, aunque involucre varias transferencias, se revierte como una sola transacción.

Las listas nativas de Python **no se usan como contenedor base de las estructuras**. Solo se usan para representar registros al exportar JSON/CSV, preparar mensajes de consola y guardar las mediciones.

## Reglas del sistema

1. El estudiante **sin prioridad** entra en la cola simple. El que indique `p=1..5` entra en la cola de prioridad.
2. Al procesar turnos con cupos, se atiende primero la prioridad más alta y luego la cola simple.
3. Con el curso lleno, los turnos normales pasan a la **cola circular**. Los prioritarios esperan en **ColaPrioridad** hasta un retiro.
4. Un retiro libera una plaza y la reasigna desde **prioridad > circular > simple** (la simple se usa solo como respaldo cuando las otras están vacías).
5. Un mismo ID no puede estar simultáneamente inscrito o en dos colas. El historial puede mantenerse después del retiro.
6. La escala de calificaciones asumida para el ejercicio es **0-20** y los términos admitidos son **1 a 4**. Modificar `src/modelos.py` si el docente usa otra escala.
7. `Configurar curso` reinicia los registros del curso actual y puede revertirse con `Deshacer`.

## Persistencia

`data/inscritos.csv` contiene `id,nombre,correo,cod_curso,prioridad`; el último campo adicional conserva la prioridad original del inscrito al reimportar.

`data/historial.json` contiene `historiales`, con una entrada por estudiante y la clave `semestres` para sus periodos. `data/esperas.json` almacena las colas `simple`, `circular`, `prioridad` además de la configuración del curso. Ambos amplían el formato básico sugerido en la consigna para que se pueda **restaurar todo el estado**, no solo una cola.

La importación valida CSV, JSON, IDs duplicados, cupos, rango de prioridades, notas y organización; **si ocurre un error, se conserva intacto el sistema que estaba en memoria**. Tras una importación correcta, es posible revertirla con la opción 8.

## Pruebas y eficiencia

```bash
python -m unittest discover -s tests -v
python siga.py --benchmark
```

Los benchmarks calculan el **promedio de cinco ejecuciones** y la desviación estándar, en milisegundos. Cubren n=1.000, 5.000 y 10.000 para listas simples y dobles, y 10.000 inserciones + 10.000 extracciones para las tres colas. Las preparaciones de las pruebas de búsqueda y eliminación se realizan **fuera del intervalo cronometrado**.

Los resultados reales dependen de cada computadora y deben regenerarse si se usan cifras en una defensa oral.

## Guía de evaluación

Para el video, seguir `GUIA_VIDEO.md`. El comando `--demo` ejecuta los casos funcionales con resultados reales; `--benchmark` genera la tabla; la suite de `unittest` certifica los casos normales y límite. El informe en PDF incluye introducción, contexto, decisiones, Big-O, casos de prueba, evidencias, mediciones, reflexión, referencias APA y el anexo de código.
