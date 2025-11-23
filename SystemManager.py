import logging
import threading
import queue
import math
from Instancia import Instancia

class SystemManager:
    """
    Gestiona instancias de procesamiento y distribuye las peticiones.
    """
    MIN_SERVERS = 1

    def __init__(self, data_collector):
        self.peticiones_pendientes = queue.Queue()
        self.instancias = []
        self.data_collector = data_collector
        self.max_servers = 50  # Límite superior de instancias, ahora configurable
        self.cola_lock = threading.Lock()
        self.peticiones_nuevas_sem = threading.Semaphore(0)
        self.instancias_libres_sem = threading.Semaphore(0)
        self.next_instance_id = 0
        self._activo = threading.Event()
        self._activo.set()
        self._peticiones_nuevas_contador = 0
        self._contador_lock = threading.Lock()
        self._dispatcher_thread = threading.Thread(target=self._bucle_despachador, daemon=True)
        self._dispatcher_thread.start()

    def create_instance(self):
        instance_id = self.next_instance_id
        logging.info("Manager: Creando instancia %s...", instance_id)
        nueva_instancia = Instancia(id_instancia=instance_id, semaforo=self.instancias_libres_sem, data_collector=self.data_collector)
        nueva_instancia.iniciar()
        self.instancias.append(nueva_instancia)
        # nueva instancia libre:
        self.instancias_libres_sem.release()
        self.next_instance_id += 1
        return nueva_instancia

    def destroy_instance(self):
        if len(self.instancias) <= self.MIN_SERVERS:
            logging.warning(
                "Manager: intento de desescalado por debajo del mínimo (%d instancias). Acción cancelada.",
                self.MIN_SERVERS,
            )
            return

        if not self.instancias_libres_sem.acquire(blocking=False):
            # No hay instancias libres para destruir
            logging.debug("Manager: no hay instancias libres para destruir en este momento.")
            return

        for instancia in self.instancias:
            if instancia.esta_libre():
                logging.info("Manager: Destruyendo instancia %s por baja carga...", instancia.id)
                instancia.detener()
                self.instancias.remove(instancia)
                return

        # Estado inconsistente: devolvemos el ticket del semáforo
        self.instancias_libres_sem.release()

    def receive_request(self, arrival_time, processing_time):
        logging.info(
            "<-- Manager: Petición recibida t=%.2f con tiempo de procesamiento=%.3fs.",
            arrival_time,
            processing_time,
        )
        with self.cola_lock:
            self.peticiones_pendientes.put((arrival_time, processing_time))
        with self._contador_lock:
            self._peticiones_nuevas_contador += 1
        self.peticiones_nuevas_sem.release()

    def get_peticiones_pendientes_snapshot(self):
        with self.cola_lock:
            return list(self.peticiones_pendientes.queue)

    def get_and_reset_nuevas_peticiones(self):
        with self._contador_lock:
            count = self._peticiones_nuevas_contador
            self._peticiones_nuevas_contador = 0
            return count

    def _bucle_despachador(self):
        while self._activo.is_set():
            self.peticiones_nuevas_sem.acquire()
            with self.cola_lock:
                peticion = self.peticiones_pendientes.get()

            if peticion is None:
                break

            self.instancias_libres_sem.acquire()
            for instancia in self.instancias:
                if instancia.esta_libre():
                    instancia.recibir_peticion(*peticion)
                    self.peticiones_pendientes.task_done()
                    break

        logging.info("Dispatcher: detenido.")

    def scale(self, control_signal: float):
        """
        Ajusta el número de instancias basado en la señal de control PD.

        control_signal > 0  -> tiende a reducir instancias
        control_signal < 0  -> tiende a aumentar instancias
        """
        actual = len(self.instancias)
        deseado = math.ceil(actual + control_signal)
        deseado = max(self.MIN_SERVERS, min(self.max_servers, deseado))

        if deseado == actual:
            return

        if deseado > actual:
            delta = deseado - actual
            logging.info(
                "Manager.scale: señal=%.3f -> escalando hacia ARRIBA (+%d instancias, de %d a %d).",
                control_signal,
                delta,
                actual,
                deseado,
            )
            for _ in range(delta):
                self.create_instance()
        else:
            delta = actual - deseado
            logging.info(
                "Manager.scale: señal=%.3f -> escalando hacia ABAJO (-%d instancias, de %d a %d).",
                control_signal,
                delta,
                actual,
                deseado,
            )
            for _ in range(delta):
                self.destroy_instance()

    def detener_instancias(self):
        logging.info("Manager: Esperando a que se procesen todas las peticiones en cola...")
        self.peticiones_pendientes.join()
        with self.cola_lock:
            self.peticiones_pendientes.put(None)
        self.peticiones_nuevas_sem.release()
        self._activo.clear()
        self._dispatcher_thread.join()
        logging.info("Manager: Deteniendo instancias de procesamiento...")
        for instancia in list(self.instancias):
            instancia.detener()
        logging.info("Manager: todas las instancias detenidas.")