import time
import logging
import threading
from Cliente import Cliente
from SystemManager import SystemManager
from Controlador import Controlador
from Medidor import Medidor
from DataCollector import DataCollector
from Plotter import Plotter

def run_simulation(cliente, medidor, manager, start_time):
    """
    Función que contiene la lógica de la simulación para ser ejecutada en un hilo.
    """
    logging.info("Iniciando simulación...")
    medidor.iniciar()
    cliente.iniciar(start_time) # Usamos el tiempo de inicio unificado
    
    # Esperamos a que el cliente termine de enviar peticiones
    cliente.esperar_finalizacion()
    
    # Una vez que el cliente ha enviado todo, esperamos a que el manager procese
    # todas las peticiones pendientes antes de detener al medidor.
    # Esto asegura que medimos durante todo el ciclo de procesamiento.
    manager.detener_instancias()
    medidor.detener()
    logging.info("Simulación finalizada.")

def main():
    """
    Punto de entrada principal: configura los componentes y lanza la UI y la simulación.
    """
    # Configura el logging para guardar todo (nivel DEBUG) en un archivo.
    # 'filemode='w'' asegura que el archivo se sobrescriba en cada ejecución.
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        datefmt='%H:%M:%S',
        filename='simulacion.log',
        filemode='w'
    )

    # Añade un segundo manejador para mostrar solo los mensajes INFO en la consola.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console_handler)

    sim_start_time = time.time()
    latencia_deseada = 200 # en ms

    # --- Configuración de Componentes ---
    manager = SystemManager()
    data_collector = DataCollector(sim_start_time)
    controlador = Controlador(manager, Kp=1.6) # Kp=1.6 para una reacción sensible
    medidor = Medidor(manager, controlador, data_collector, sim_start_time, latencia_deseada_ms=latencia_deseada)
    cliente = Cliente(manager, frecuencia_promedio_hz=15) # Aumentamos la frecuencia para ver mejor el escalado
    plotter = Plotter(data_collector, latencia_deseada)

    manager.create_instance()

    # --- Ejecución ---
    # La simulación se ejecuta en un hilo para no bloquear la interfaz gráfica
    sim_thread = threading.Thread(target=run_simulation, args=(cliente, medidor, manager, sim_start_time))
    sim_thread.start()

    # El hilo principal se encarga de la visualización en tiempo real
    plotter.run_animation()

    # Una vez que la ventana del gráfico se cierra, esperamos a que el hilo de la
    # simulación también haya terminado (si no lo ha hecho ya).
    sim_thread.join() 
    logging.info("Programa finalizado.")

if __name__ == "__main__":
    main()
    