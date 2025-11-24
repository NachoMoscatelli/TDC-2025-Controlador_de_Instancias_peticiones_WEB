# Simulación de Sistema Web con Auto-Escalado

## Finalidad de la Aplicación

Esta es una simulación desarrollada para la cátedra de **Teoría del Control** de la carrera de Grado en Ingeniería en Sistemas de Información de la Universidad Tecnológica Nacional, Facultad Regional Buenos Aires (UTN-FRBA).

El objetivo principal del proyecto es recrear el comportamiento de un sistema distribuido (como una aplicación web) que responde a peticiones de clientes. La simulación busca implementar un sistema de control con auto-escalado, donde la variable a controlar es la **latencia de respuesta** (definida como el tiempo que transcurre desde que el sistema recibe una petición hasta que termina de procesarla).

Para mantener la latencia en torno a un valor nominal deseado, la variable que se manipulará es la **cantidad de instancias de procesamiento activas**, escalando el sistema hacia arriba (agregando instancias) o hacia abajo (quitando instancias) según la carga de trabajo y el rendimiento medido.

El proyecto implementa un bucle de control de realimentación completo, donde un `Medidor` (sensor) observa la latencia del sistema, un `Controlador` PID calcula una acción correctiva, y un `SystemManager` (actuador) ejecuta dicha acción, modificando la cantidad de recursos para estabilizar la latencia.

---

## Funcionamiento de los Módulos

El sistema está dividido en varios módulos, cada uno con una responsabilidad clara dentro de la simulación.

### `main.py`

Es el punto de entrada de la aplicación. Su función es orquestar el inicio y el final de la simulación.

1.  Inicializa todos los componentes principales: `SystemManager`, `Cliente`, `Controlador`, `Medidor` y `DataCollector`.
2.  Inicia los hilos de la simulación (`Cliente` y `Medidor`).
3.  Espera a que el cliente termine de enviar todas las peticiones y, crucialmente, a que el `SystemManager` termine de procesar toda la carga de trabajo.
4.  Detiene los componentes de forma controlada.
5.  Invoca al `Plotter` para generar un gráfico con los resultados de la simulación.

### `Cliente.py`

Este módulo simula la llegada de peticiones de usuarios o servicios externos.

- **Generación de Carga**: Lee el archivo `peticiones.csv` para cargar una secuencia de peticiones, haciendo que la carga de trabajo sea fácilmente configurable sin modificar el código.
- **Hilo Independiente**: Se ejecuta en un hilo separado para no bloquear el resto de la aplicación. Recorre la lista de peticiones, espera el tiempo indicado y envía la solicitud al `SystemManager`.

### `SystemManager.py`

Actúa como el **actuador** del sistema de control y como un **despachador (dispatcher)** de peticiones.

- **Cola de Peticiones**: Mantiene una cola (`peticiones_pendientes`) donde se encolan las peticiones recibidas del cliente de forma inmediata y no bloqueante.
- **Hilo Despachador**: Su lógica principal reside en el `_bucle_despachador`, un hilo que se encarga de asignar el trabajo.
- **Sincronización Eficiente**: Utiliza dos semáforos para una coordinación sin consumo de CPU innecesario:
    1.  `peticiones_nuevas_sem`: El despachador espera en este semáforo hasta que el cliente le avisa que ha llegado una nueva petición.
    2.  `instancias_libres_sem`: El despachador espera en este semáforo hasta que una instancia le avisa que ha quedado libre.
- **Actuador del Control**: Implementa el método `scale(pid_signal)`, que interpreta la señal del `Controlador`. Si la señal es negativa (alta latencia), crea una nueva instancia (`create_instance`). Si es positiva (baja latencia), destruye una instancia ociosa (`destroy_instance`).

### `instancia.py`

Representa una unidad de procesamiento individual, como un servidor, un contenedor o un proceso trabajador.

- **Procesamiento Secuencial**: Cada instancia se ejecuta en su propio hilo y puede procesar **una única petición a la vez**.
- **Estado de Ocupación**: Almacena el tiempo de llegada de la petición actual y mantiene un estado (`_ocupado`) para saber si está trabajando o libre.
- **Comunicación con el Manager**: Al finalizar una tarea, libera el semáforo `instancias_libres_sem` para notificar al `SystemManager` que está disponible para recibir nuevo trabajo.

### `Medidor.py`

Es el **sensor** del sistema de control.

- Se ejecuta en un hilo separado, midiendo el estado del sistema a intervalos regulares (ej. cada 20ms).
- **Cálculo de Latencia**: Su método `get_system_metrics` calcula la latencia promedio real del sistema, considerando tanto las peticiones que están siendo procesadas por las instancias como las que están esperando en la cola del `SystemManager`.
- **Generación de Error**: Compara la latencia medida con la latencia deseada (`setpoint`) y calcula la señal de error (`error = deseada - medida`), que envía al `Controlador`.

### `Controlador.py`

Implementa la lógica de decisión del sistema de control.

- **Controlador PID**: Está estructurado como un controlador Proporcional-Integral-Derivativo. Actualmente, utiliza principalmente el componente **Proporcional (P)**.
- **Cálculo de Señal**: Recibe la señal de error del `Medidor` y la multiplica por la ganancia `Kp` para generar una señal de control (`pid_signal`).
- **Comunicación con el Actuador**: Envía la `pid_signal` al método `scale()` del `SystemManager` para que este ejecute la acción de escalado correspondiente.

### `DataCollector.py` y `Plotter.py`

- `DataCollector`: Es una clase simple que actúa como un registro. El `Medidor` la utiliza para almacenar en cada intervalo de tiempo la latencia, el número de instancias y la cantidad de peticiones activas.
- `Plotter`: Al finalizar la simulación, esta clase utiliza la librería `matplotlib` para leer los datos del `DataCollector` y generar un archivo de imagen (`simulacion_plot.png`) con tres gráficos que permiten analizar visualmente el comportamiento del sistema.

### `peticiones.csv`

Un archivo de valores separados por comas (CSV) que define la carga de trabajo de la simulación. Cada línea contiene `tiempo_desde_ultima_peticion_ms,tiempo_procesamiento_ms`, permitiendo configurar diferentes escenarios de prueba sin alterar el código.

---

## Guía de Instalación y Ejecución

Sigue estos pasos para descargar y ejecutar el programa en tu computadora.

### 1. Requisitos Previos

Asegúrate de tener instalado **Python 3.8 o una versión más reciente**. Puedes descargarlo desde python.org.

Para verificar si tienes Python, abre una terminal (o `cmd` / `PowerShell` en Windows) y ejecuta:
```bash
python --version
```

### 2. Descargar el Repositorio

Puedes obtener el código de dos maneras:

**Opción A: Clonar con Git (Recomendado)**

Si tienes Git instalado, clona el repositorio con el siguiente comando:
```bash
git clone <URL_DEL_REPOSITORIO_AQUI>
cd <NOMBRE_DE_LA_CARPETA_DEL_REPOSITORIO>
```

**Opción B: Descargar como ZIP**

1.  Ve a la página principal del repositorio.
2.  Haz clic en el botón "Code" y luego en "Download ZIP".
3.  Descomprime el archivo en la ubicación que prefieras y abre una terminal en esa carpeta.

### 3. Instalar Dependencias

Este proyecto necesita las librerías `matplotlib` y `numpy` para funcionar. La forma más sencilla de instalarlas es usando `pip`, el gestor de paquetes de Python.

En tu terminal, dentro de la carpeta del proyecto, ejecuta:
```bash
pip install matplotlib numpy
```

### 4. Ejecutar el Programa

Una vez instaladas las dependencias, puedes iniciar la simulación ejecutando el archivo `main.py`:
```bash
python main.py
```

Al ejecutarlo, se abrirá una ventana con los gráficos de la simulación. Para finalizar, simplemente cierra la ventana del gráfico.