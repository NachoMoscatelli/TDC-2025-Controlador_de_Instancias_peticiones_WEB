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
    def __init__(self, manager, frecuencia_normal_hz=5, frecuencia_pico_hz=25):
        """
        Inicializa el cliente.

        :param manager: La instancia de SystemManager a la que se enviarán las peticiones.
        :param frecuencia_normal_hz: La frecuencia promedio de llegada de peticiones (en Hz).
        :param frecuencia_pico_hz: La frecuencia durante un pico de tráfico.
        """
        self.manager = manager
        self.thread = None
        self.frecuencia_normal_hz = frecuencia_normal_hz
        self.frecuencia_pico_hz = frecuencia_pico_hz
        self._lock_frecuencia = threading.Lock()
        self._pico_activo = False
        self._activo = threading.Event()
        
        logging.info(f"Cliente configurado para frecuencia normal de ~{frecuencia_normal_hz}Hz y pico de ~{frecuencia_pico_hz}Hz.")

    def aumentar_frecuencia(self, duracion_s):
        """Activa la frecuencia de pico durante un tiempo determinado."""
        with self._lock_frecuencia:
            if self._pico_activo:
                logging.warning("Cliente: Ya hay un pico de tráfico activo.")
                return
            logging.info(f"Cliente: ¡PICO DE TRÁFICO ACTIVADO! Duración: {duracion_s}s.")
            self._pico_activo = True
        
        # Usamos un temporizador para desactivar el pico después de la duración especificada
        timer = threading.Timer(duracion_s, self._desactivar_pico)
        timer.start()

    def _desactivar_pico(self):
        with self._lock_frecuencia:
            self._pico_activo = False
            logging.info("Cliente: Pico de tráfico finalizado. Volviendo a frecuencia normal.")

    def iniciar(self, sim_start_time):
        """Inicia el hilo del cliente para que comience a generar peticiones."""
        self._activo.set()
        self.thread = threading.Thread(target=self._generar_peticiones, args=(sim_start_time,), name="ClienteThread")
        self.thread.start()

    def detener(self):
        """Detiene el hilo del cliente."""
        self._activo.clear()
        if self.thread:
            self.thread.join()

    def _generar_peticiones(self, sim_start_time):
        """Lógica interna del hilo: genera y envía peticiones de forma aleatoria."""
        logging.info("--> Hilo Cliente: Iniciado. Generando peticiones de forma continua.")
        while self._activo.is_set():
            with self._lock_frecuencia:
                frecuencia_actual = self.frecuencia_pico_hz if self._pico_activo else self.frecuencia_normal_hz
            
            tiempo_espera_promedio_ms = (1 / frecuencia_actual) * 1000
            espera_min_ms = int(tiempo_espera_promedio_ms * 0.5)
            espera_max_ms = int(tiempo_espera_promedio_ms * 1.5)

            espera_ms = random.randint(espera_min_ms, espera_max_ms)
            procesamiento_ms = 100 # Tiempo de procesamiento constante

            # Esperamos el tiempo aleatorio
            time.sleep(espera_ms / 1000.0)
            
            procesamiento_sec = procesamiento_ms / 1000.0
            # Usamos el tiempo relativo al inicio de la simulación para la consistencia
            self.manager.receive_request(time.time() - sim_start_time, procesamiento_sec)