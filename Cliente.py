import time
import logging
import threading
import random

class Cliente:
    """
    Genera una carga de trabajo de fondo y permite disparar ataques DoS.
    En estado estable, con una sola instancia, la latencia promedio tenderá
    a oscilar alrededor del setpoint inicial (base_processing_ms ≈ latencia deseada).
    """
    def __init__(self, manager, frecuencia_promedio_hz=0.25, base_processing_ms=1000):
        """
        :param manager: instancia de SystemManager que recibe las peticiones.
        :param frecuencia_promedio_hz: frecuencia promedio de llegada de peticiones (Hz).
        :param base_processing_ms: tiempo de procesamiento base (ms), típicamente igual
                                   a la latencia deseada inicial.
        """
        self.manager = manager
        self.frecuencia_promedio_hz = frecuencia_promedio_hz
        self.base_processing_ms = base_processing_ms
        self._thread = None
        self._running = threading.Event()
        self.sim_start_time = None

        # Calcula el tiempo de espera promedio en ms y define un rango aleatorio
        tiempo_espera_promedio_ms = (1 / frecuencia_promedio_hz) * 1000 if frecuencia_promedio_hz > 0 else 1000
        self.espera_min_ms = int(tiempo_espera_promedio_ms * 0.5)
        self.tiempo_espera_promedio_ms = tiempo_espera_promedio_ms
        self.espera_max_ms = int(tiempo_espera_promedio_ms * 1.5)
        logging.info(
            "Cliente configurado para ~%.2f Hz. Intervalo de espera: [%d ms - %d ms]",
            frecuencia_promedio_hz,
            self.espera_min_ms,
            self.espera_max_ms,
        )

        # Estado de ataque DoS
        self._dos_lock = threading.Lock()
        self._dos_activo = False

    def iniciar(self, sim_start_time):
        """Inicia el hilo del cliente para que comience a generar peticiones de fondo."""
        self.sim_start_time = sim_start_time
        self._running.set()
        self._thread = threading.Thread(target=self._generar_carga_base, name="Cliente", daemon=True)
        self._thread.start()
        logging.info("Cliente: hilo de carga base iniciado.")

    def detener(self):
        """Detiene el hilo de generación de carga."""
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        logging.info("Cliente: detenido.")

    def _generar_carga_base(self):
        """
        Genera peticiones a baja frecuencia para representar el estado estable.
        El tiempo de procesamiento está centrado en base_processing_ms (≈ setpoint).
        """
        while self._running.is_set(): # Usar el tiempo de espera promedio directamente
            espera_ms = self.tiempo_espera_promedio_ms
            time.sleep(espera_ms / 1000.0)

            # Procesamiento alrededor del setpoint (±20%)
            # procesamiento_ms = random.randint(
            #     int(self.base_processing_ms * 0.8),
            #     int(self.base_processing_ms * 1.2),
            # )
            # procesamiento_sec = procesamiento_ms / 1000.0
            procesamiento_sec = 1
            arrival_time = time.time() - self.sim_start_time
            self.manager.receive_request(arrival_time, procesamiento_sec)

    def ejecutar_dos(self, duracion_s=6.0, frecuencia_promedio_hz=8.0):
        """
        Dispara un ataque DoS durante `duracion_s` segundos,
        generando muchas más peticiones por segundo.
        """
        with self._dos_lock:
            if self._dos_activo:
                logging.info("Cliente: ya hay un ataque DoS en curso.")
                return
            self._dos_activo = True

        logging.warning(
            "⚠️ Cliente: ATAQUE DoS INICIADO (%.1f RPS durante %.1f s)",
            frecuencia_promedio_hz,
            duracion_s,
        )

        def _hilo_dos():
            fin = time.time() + duracion_s
            while time.time() < fin and self._running.is_set():
                if frecuencia_promedio_hz > 0: # Usar un tiempo de inter-llegada fijo para DoS
                    dt = 1 / frecuencia_promedio_hz
                else:
                    dt = 0.01
                time.sleep(dt)

                # En DoS usamos rangos similares pero suficientes para saturar la cola
                # procesamiento_ms = random.randint(
                #     int(self.base_processing_ms * 0.8),
                #     int(self.base_processing_ms * 1.2),
                # )
                # procesamiento_sec = procesamiento_ms / 1000.0
                procesamiento_sec = 1
                arrival_time = time.time() - self.sim_start_time
                self.manager.receive_request(arrival_time, procesamiento_sec)

            logging.info("Cliente: ataque DoS finalizado.")
            with self._dos_lock:
                self._dos_activo = False

        threading.Thread(target=_hilo_dos, name="Cliente-DoS", daemon=True).start()