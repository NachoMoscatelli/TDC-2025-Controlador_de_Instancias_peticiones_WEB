import time
import logging
import threading
import csv

class Cliente:
    """
    Encapsula la lógica de un cliente que genera una carga de trabajo
    programada en un hilo separado.
    """
    def __init__(self, manager):
        """
        Inicializa el cliente.

        :param manager: La instancia de SystemManager a la que se enviarán las peticiones.
        """
        self.manager = manager
        self.thread = None
        self.peticiones_programadas = self._cargar_peticiones_desde_archivo("peticiones.csv")

    def _cargar_peticiones_desde_archivo(self, nombre_archivo):
        """Lee un archivo CSV para cargar la lista de peticiones programadas."""
        peticiones = []
        try:
            with open(nombre_archivo, mode='r', newline='') as archivo_csv:
                lector_csv = csv.reader(archivo_csv)
                for i, fila in enumerate(lector_csv):
                    if len(fila) == 2:
                        try:
                            espera_ms = int(fila[0])
                            procesamiento_ms = int(fila[1])
                            peticiones.append((espera_ms, procesamiento_ms))
                        except ValueError:
                            logging.warning(f"Cliente: Ignorando línea {i+1} en {nombre_archivo} por formato de número inválido.")
                    else:
                        logging.warning(f"Cliente: Ignorando línea {i+1} en {nombre_archivo} por no tener 2 columnas.")
            logging.info(f"Cliente: Se cargaron {len(peticiones)} peticiones desde {nombre_archivo}.")
        except FileNotFoundError:
            logging.error(f"Cliente: ¡Error! No se encontró el archivo de peticiones '{nombre_archivo}'. La simulación no tendrá carga.")
        return peticiones
        
    def iniciar(self, sim_start_time):
        """Inicia el hilo del cliente para que comience a generar peticiones."""
        self.thread = threading.Thread(target=self._generar_peticiones, args=(sim_start_time,))
        self.thread.start()

    def _generar_peticiones(self, sim_start_time):
        """Lógica interna del hilo: espera y envía peticiones según lo programado."""
        logging.info("--> Hilo Cliente: Iniciado y generando peticiones programadas.")
        for espera_ms, procesamiento_ms in self.peticiones_programadas:
            # Esperamos el tiempo relativo desde la última petición
            time.sleep(espera_ms / 1000.0)
            
            # Enviamos una única petición con su duración de procesamiento específica
            procesamiento_sec = procesamiento_ms / 1000.0
            self.manager.receive_request(time.time(), procesamiento_sec)
        
        logging.info("--> Hilo Cliente: Todas las peticiones programadas han sido enviadas.")

    def esperar_finalizacion(self):
        """Espera a que el hilo del cliente termine su ejecución."""
        if self.thread:
            self.thread.join()