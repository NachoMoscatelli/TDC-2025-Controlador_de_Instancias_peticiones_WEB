import time
import logging
import threading
import queue

class Instancia:
    """
    Representa una instancia de servidor que puede procesar una petición a la vez.
    """
    def __init__(self, id_instancia, semaforo):
        self.id = id_instancia
        self.peticiones = queue.Queue(maxsize=1)
        self._thread = threading.Thread(target=self._bucle_procesamiento, daemon=True)
        self.semaforo = semaforo
        self._lock = threading.Lock()
        self.arrival_time_actual = None
        self._ocupado = False
        self._activo = threading.Event()

    def iniciar(self):
        if not self._thread.is_alive():
            self._activo.set()
            self._thread.start()
            logging.info(f"Instancia {self.id}: Iniciada.")

    def detener(self):
        if self._thread.is_alive():
            self._activo.clear()
            try:
                self.peticiones.put_nowait(None)
            except queue.Full:
                pass
            self._thread.join()
            logging.info(f"Instancia {self.id}: Detenida.")

    def recibir_peticion(self, arrival_time, processing_time):
        with self._lock:
            self.arrival_time_actual = arrival_time
        self.peticiones.put((arrival_time, processing_time))

    def esta_libre(self):
        with self._lock:
            return not self._ocupado

    def get_datos_peticion_actual(self):
        with self._lock:
            return self._ocupado, self.arrival_time_actual

    def _bucle_procesamiento(self):
        while self._activo.is_set():
            peticion = self.peticiones.get()
            if peticion is None:
                break
            _, tiempo_procesamiento = peticion
            with self._lock:
                self._ocupado = True
            logging.info(
                "Instancia %s: Comienza a procesar petición que tardará %.3fs.",
                self.id,
                tiempo_procesamiento,
            )
            time.sleep(tiempo_procesamiento)
            with self._lock:
                self._ocupado = False
                self.arrival_time_actual = None
            self.semaforo.release()
            logging.info("Instancia %s: Petición finalizada. Esperando nueva petición.", self.id)
            self.peticiones.task_done()