import time
import logging
from Cliente import Cliente
from SystemManager import SystemManager
from Controlador import Controlador
from Medidor import Medidor
from DataCollector import DataCollector
from Plotter import Plotter

def main():
    """
    Punto de entrada principal de la simulación.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

    sim_start_time = time.time()
    latencia_deseada = 200 # en ms

    manager = SystemManager()
    data_collector = DataCollector(sim_start_time)
    controlador = Controlador(manager, Kp=0.1) # Aumentamos Kp para una reacción más fuerte
    medidor = Medidor(manager, controlador, data_collector, latencia_deseada_ms=latencia_deseada)

    # Creamos una instancia inicial para procesar las peticiones
    manager.create_instance()

    cliente = Cliente(manager)

    logging.info("Iniciando simulación...")
    medidor.iniciar()
    cliente.iniciar(sim_start_time)
    
    # Esperamos a que el cliente termine de enviar peticiones
    cliente.esperar_finalizacion()
    
    # Detenemos todos los componentes en orden
    # Una vez que el cliente ha enviado todo, esperamos a que el manager procese
    # todas las peticiones pendientes antes de detener al medidor.
    # Esto asegura que medimos durante todo el ciclo de procesamiento.
    manager.detener_instancias()
    medidor.detener()
    logging.info("Simulación finalizada.")

    # Graficamos los resultados
    Plotter.plot_simulation_data(data_collector, latencia_deseada)

if __name__ == "__main__":
    main()
    