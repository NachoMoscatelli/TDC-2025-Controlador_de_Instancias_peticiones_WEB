import time
import time
import logging
import threading
import queue

class Instancia:
    """
    Representa una instancia de servidor que puede procesar una petición a la vez.
    """
    def __init__(self, id_instancia, semaforo):
        """
        Inicializa la instancia.

        :param id_instancia: Un identificador único para la instancia.
        :param semaforo: El objeto threading.Semaphore compartido para notificar disponibilidad.
        """
        self.id = id_instancia
        self.peticiones = queue.Queue(maxsize=1)
        self._thread = threading.Thread(target=self._bucle_procesamiento, daemon=True)
        self.semaforo = semaforo
        self._lock = threading.Lock()
        self.arrival_time_actual = None
        self._ocupado = False
        self._activo = threading.Event()

    def iniciar(self):
        """Inicia el hilo de procesamiento de la instancia."""
        if not self._thread.is_alive():
            self._activo.set()
            self._thread.start()
            logging.info(f"Instancia {self.id}: Iniciada.")

    def detener(self):
        """Detiene el hilo de procesamiento de la instancia."""
        if self._thread.is_alive():
            self._activo.clear()
            try:
                # Desbloquea la cola en caso de que el hilo esté esperando
                self.peticiones.put_nowait(None)
            except queue.Full:
                pass # La cola ya estaba llena, el hilo no está esperando
            self._thread.join()
            logging.info(f"Instancia {self.id}: Detenida.")

    def recibir_peticion(self, arrival_time, processing_time):
        """
        Envía una nueva petición a la cola de la instancia para ser procesada.
        """
        with self._lock:
            self.arrival_time_actual = arrival_time
        self.peticiones.put((arrival_time, processing_time))

    def esta_libre(self):
        """Devuelve True si la instancia no está procesando una petición."""
        with self._lock:
            return not self._ocupado

    def get_datos_peticion_actual(self):
        """
        Devuelve el estado de ocupación y el tiempo de llegada de la petición actual.
        """
        with self._lock:
            return self._ocupado, self.arrival_time_actual

    def _bucle_procesamiento(self):
        """
        Espera una petición, simula su procesamiento y espera la siguiente.
        """
        while self._activo.is_set():
            peticion = self.peticiones.get()
            if peticion is None: # Señal para terminar
                break
            
            _, tiempo_procesamiento = peticion
            
            with self._lock:
                self._ocupado = True
            logging.info(f"Instancia {self.id}: Comienza a procesar petición que tardará {tiempo_procesamiento:.3f}s.")
            time.sleep(tiempo_procesamiento)
            with self._lock:
                self._ocupado = False
                self.arrival_time_actual = None
            
            # Libera el semáforo, indicando que una instancia ha quedado libre.
            self.semaforo.release()

            logging.info(f"Instancia {self.id}: Petición finalizada. Esperando nueva petición.")
            self.peticiones.task_done()