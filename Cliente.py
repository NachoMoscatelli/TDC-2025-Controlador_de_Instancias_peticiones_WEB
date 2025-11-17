import time
import logging
import threading
import csv
import random

class Cliente:
    """
    Encapsula la lógica de un cliente que genera una carga de trabajo
    programada en un hilo separado.
    """
    def __init__(self, manager, frecuencia_promedio_hz=5, numero_peticiones=500):
        """
        Inicializa el cliente.

        :param manager: La instancia de SystemManager a la que se enviarán las peticiones.
        :param frecuencia_promedio_hz: La frecuencia promedio de llegada de peticiones (en Hz).
        :param numero_peticiones: El número total de peticiones a generar.
        """
        self.manager = manager
        self.thread = None
        self.numero_peticiones = numero_peticiones

        # Calcula el tiempo de espera promedio en milisegundos a partir de la frecuencia
        tiempo_espera_promedio_ms = (1 / frecuencia_promedio_hz) * 1000

        # Crea un intervalo de tiempo aleatorio (ej. 50% a 150% del promedio)
        self.espera_min_ms = int(tiempo_espera_promedio_ms * 0.5)
        self.espera_max_ms = int(tiempo_espera_promedio_ms * 1.5)
        logging.info(f"Cliente configurado para ~{frecuencia_promedio_hz}Hz. Intervalo de espera: [{self.espera_min_ms}ms - {self.espera_max_ms}ms]")
        
    def iniciar(self, sim_start_time):
        """Inicia el hilo del cliente para que comience a generar peticiones."""
        self.thread = threading.Thread(target=self._generar_peticiones, args=(sim_start_time,))
        self.thread.start()

    def _generar_peticiones(self, sim_start_time):
        """Lógica interna del hilo: genera y envía peticiones de forma aleatoria."""
        logging.info(f"--> Hilo Cliente: Iniciado. Generando {self.numero_peticiones} peticiones aleatorias.")
        for _ in range(self.numero_peticiones):
            # Generamos tiempos aleatorios para la espera y el procesamiento
            espera_ms = random.randint(self.espera_min_ms, self.espera_max_ms)
            procesamiento_ms = 100 # Tiempo de procesamiento constante

            # Esperamos el tiempo aleatorio
            time.sleep(espera_ms / 1000.0)
            
            procesamiento_sec = procesamiento_ms / 1000.0
            # Usamos el tiempo relativo al inicio de la simulación para la consistencia
            self.manager.receive_request(time.time() - sim_start_time, procesamiento_sec)
        
        logging.info(f"--> Hilo Cliente: Se han enviado las {self.numero_peticiones} peticiones.")

    def esperar_finalizacion(self):
        """Espera a que el hilo del cliente termine su ejecución."""
        if self.thread:
            self.thread.join()