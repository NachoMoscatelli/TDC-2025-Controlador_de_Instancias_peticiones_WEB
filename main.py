import time
import logging
from Cliente import Cliente
from SystemManager import SystemManager

def main():
    """
    Punto de entrada principal de la simulación.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

    manager = SystemManager()
    # Creamos una instancia inicial para procesar las peticiones
    manager.create_instance()

    cliente = Cliente(manager)

    logging.info("Iniciando simulación...")
    cliente.iniciar(time.time())
    cliente.esperar_finalizacion()
    manager.detener_instancias()
    logging.info("Simulación finalizada.")

if __name__ == "__main__":
    main()
    