# Simulación de Sistema Web con Auto-Escalado

## Finalidad de la Aplicación

Esta es una simulación desarrollada para la cátedra de **Teoría del Control** de la carrera de Grado de Ingeniería en Sistemas de Información de la Universidad Tecnológica Nacional, Facultad Regional Buenos Aires (UTN-FRBA).

El objetivo principal del proyecto es recrear el comportamiento de un sistema distribuido (como una aplicación web) que responde a peticiones de clientes. La simulación busca implementar un sistema de control con auto-escalado, donde la variable a controlar es la **latencia de respuesta** (definida como el tiempo que transcurre desde que el sistema recibe una petición hasta que termina de procesarla).

Para mantener la latencia en torno a un valor nominal deseado, la variable que se manipulará es la **cantidad de instancias de procesamiento activas**, escalando el sistema hacia arriba (agregando instancias) o hacia abajo (quitando instancias) según la carga de trabajo y el rendimiento medido.

Actualmente, el proyecto cuenta con la infraestructura base para la simulación: la generación de peticiones, la gestión de una cola de trabajo y el procesamiento de dichas peticiones por parte de instancias trabajadoras, todo sincronizado de manera eficiente mediante primitivas de concurrencia.

---

## Funcionamiento de los Módulos

El sistema está dividido en varios módulos, cada uno con una responsabilidad clara dentro de la simulación.

### `main.py`

Es el punto de entrada de la aplicación. Su función es orquestar el inicio y el final de la simulación.

1.  Configura el sistema de logging para poder observar los eventos en la consola.
2.  Crea una instancia del `SystemManager`, que actuará como el cerebro del sistema.
3.  Crea una o más instancias de procesamiento iniciales.
4.  Crea una instancia del `Cliente`, que generará la carga de trabajo.
5.  Inicia la simulación, permitiendo que el cliente comience a enviar peticiones.
6.  Espera a que el cliente termine de enviar todas sus peticiones y a que el `SystemManager` termine de procesarlas.
7.  Inicia el proceso de apagado controlado de todas las instancias y finaliza la simulación.

### `Cliente.py`

Este módulo simula la llegada de peticiones de usuarios o servicios externos.

- **Generación de Carga**: Contiene una lista pre-programada de peticiones, donde cada una tiene definido un tiempo de espera desde la anterior y una duración de procesamiento.
- **Hilo Independiente**: Se ejecuta en un hilo separado para no bloquear el resto de la aplicación. Recorre la lista de peticiones, espera el tiempo indicado y envía la solicitud al `SystemManager`.

### `SystemManager.py`

Es el componente central del sistema, actuando como un **balanceador de carga** y **despachador (dispatcher)**.

- **Cola de Peticiones**: Mantiene una cola (`peticiones_pendientes`) donde se encolan las peticiones recibidas del cliente de forma inmediata y no bloqueante.
- **Hilo Despachador**: Su lógica principal reside en el `_bucle_despachador`, un hilo que se encarga de asignar el trabajo.
- **Sincronización Eficiente**: Utiliza dos semáforos para una coordinación sin consumo de CPU innecesario:
    1.  `peticiones_nuevas_sem`: El despachador espera en este semáforo hasta que el cliente le avisa que ha llegado una nueva petición.
    2.  `instancias_libres_sem`: El despachador espera en este semáforo hasta que una instancia le avisa que ha quedado libre.
- **Gestión de Instancias**: Contiene la lógica para crear nuevas instancias (`create_instance`) y preparará el terreno para el escalado.

### `instancia.py`

Representa una unidad de procesamiento individual, como un servidor, un contenedor o un proceso trabajador.

- **Procesamiento Secuencial**: Cada instancia se ejecuta en su propio hilo y puede procesar **una única petición a la vez**.
- **Estado de Ocupación**: Mantiene un estado interno (`_ocupado`) protegido por un `Lock` para saber si está trabajando o libre.
- **Comunicación con el Manager**: Al finalizar una tarea, libera el semáforo `instancias_libres_sem` para notificar al `SystemManager` que está disponible para recibir nuevo trabajo.
- **Ciclo de Vida**: Su hilo principal espera en una cola interna (`peticiones`) hasta que el `SystemManager` le asigna una tarea. Una vez procesada, vuelve a esperar.

### `README.md`

Este mismo archivo. Contiene la documentación principal del proyecto, su finalidad y la descripción de su arquitectura.

---

## Cómo Ejecutar la Simulación

Siga estos pasos para poner en marcha la simulación en un entorno local.

### Prerrequisitos

1.  Tener **Python 3** instalado en el sistema.
2.  Haber clonado o descargado el código fuente de este repositorio.

### Pasos para la Ejecución

1.  Abra una terminal o línea de comandos (como `cmd`, `PowerShell` o `Terminal`).
2.  Navegue hasta el directorio raíz del proyecto, donde se encuentra el archivo `main.py`.
3.  Ejecute el siguiente comando:
    ```sh
    python main.py
    ```
4.  Observe la salida en la consola. Verá en tiempo real los logs que indican el envío de peticiones por parte del cliente, el despacho por parte del `SystemManager` y el procesamiento por parte de cada `Instancia`. La simulación finalizará automáticamente una vez que todas las peticiones hayan sido procesadas.