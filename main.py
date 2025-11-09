import time
import logging
from Cliente import Cliente
from SystemManager import SystemManager
from Controlador import Controlador
from Medidor import Medidor

def main():
    """
    Punto de entrada principal de la simulación.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

    manager = SystemManager()
    controlador = Controlador(manager)
    medidor = Medidor(manager, controlador)

    # Creamos una instancia inicial para procesar las peticiones
    manager.create_instance()

    cliente = Cliente(manager)

    logging.info("Iniciando simulación...")
    medidor.iniciar()
    cliente.iniciar(time.time())
    
    # Esperamos a que el cliente termine de enviar peticiones
    cliente.esperar_finalizacion()
    
    # Detenemos todos los componentes en orden
    medidor.detener()
    manager.detener_instancias()
    logging.info("Simulación finalizada.")

if __name__ == "__main__":
    main()
    