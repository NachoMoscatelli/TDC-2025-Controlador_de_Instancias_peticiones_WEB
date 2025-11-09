import time
import logging
import threading

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
        # Lista de tuplas: (tiempo_desde_ultima_peticion_ms, tiempo_procesamiento_ms)
        # Cada tupla es UNA petición.
        self.peticiones_programadas = [
            (100, 150),  # Espera 100ms, llega petición que tarda 150ms en procesarse
            (50, 200),   # 50ms después, llega otra que tarda 200ms
            (50, 180),
            (20, 300),   # 20ms después, llega una pesada de 300ms
            (20, 250),
            (20, 280),   # Ráfaga de peticiones pesadas
            (500, 50),   # Pausa de 500ms, llega una petición ligera
            (400, 60),
            (10, 400),   # Ráfaga final con una petición muy pesada
            (10, 350),
            (10, 380),
        ]
        self.manager = manager
        self.thread = None

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