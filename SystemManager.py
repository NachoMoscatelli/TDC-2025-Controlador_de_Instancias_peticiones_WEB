import logging
import threading
import queue
from Instancia import Instancia

class SystemManager:
    """
    Clase que gestiona las instancias de procesamiento y distribuye las peticiones.
    """
    def __init__(self):
        """
        Inicializa el SystemManager.
        """
        self.peticiones_pendientes = queue.Queue()
        self.instancias = []
        self.cola_lock = threading.Lock() # Lock para proteger el acceso a la cola
        self.peticiones_nuevas_sem = threading.Semaphore(0) # Semáforo para peticiones entrantes
        self.instancias_libres_sem = threading.Semaphore(0) # Semáforo que cuenta instancias libres
        self.next_instance_id = 0
        self._activo = threading.Event()
        self._peticiones_nuevas_contador = 0
        self._contador_lock = threading.Lock()
        self._dispatcher_thread = threading.Thread(target=self._bucle_despachador, daemon=True)
        self._activo.set()
        self._dispatcher_thread.start()

    def create_instance(self):
        """
        Crea una nueva instancia de procesamiento, la inicia y la añade a la lista.
        """
        instance_id = self.next_instance_id
        logging.info(f"Manager: Creando instancia {instance_id}...")
        nueva_instancia = Instancia(id_instancia=instance_id, semaforo=self.instancias_libres_sem)
        nueva_instancia.iniciar()
        self.instancias.append(nueva_instancia)
        self.instancias_libres_sem.release() # Incrementamos el contador: hay una nueva instancia libre
        self.next_instance_id += 1
        return nueva_instancia

    def destroy_instance(self):
        """
        Busca una instancia libre, la detiene y la elimina del sistema.
        """
        if len(self.instancias) <= 1:
            logging.warning("Manager: Intento de desescalado por debajo del mínimo (1 instancia). Acción cancelada.")
            return

        # Intentamos adquirir un "ticket" de instancia libre. Si no podemos, no hay ninguna libre para destruir.
        if self.instancias_libres_sem.acquire(blocking=False):
            # Si tuvimos éxito, ahora debemos encontrar cuál es la instancia libre.
            for instancia in self.instancias:
                if instancia.esta_libre():
                    logging.info(f"Manager: Destruyendo instancia {instancia.id} por baja carga...")
                    instancia.detener()
                    self.instancias.remove(instancia)
                    return # Instancia destruida, salimos.
            # Si llegamos aquí, es un estado inconsistente (el semáforo dijo que había una libre pero no la encontramos).
            # Devolvemos el ticket para no romper el sistema.
            self.instancias_libres_sem.release()

    def receive_request(self, arrival_time, processing_time):
        """
        Recibe una petición del cliente y la añade a la cola interna para ser procesada.
        Esta función ahora es no bloqueante.
        """
        logging.info(f"<-- Manager: Petición recibida a las {arrival_time:.2f} "
                     f"con un tiempo de procesamiento de {processing_time:.3f}s.")
        # Pone la petición en la cola y "avisa" al despachador incrementando el semáforo.
        with self.cola_lock:
            self.peticiones_pendientes.put((arrival_time, processing_time))
        with self._contador_lock:
            self._peticiones_nuevas_contador += 1
        self.peticiones_nuevas_sem.release()

    def get_peticiones_pendientes_snapshot(self):
        """Devuelve una copia segura de las peticiones en la cola."""
        with self.cola_lock:
            # .queue es el deque interno del objeto Queue
            return list(self.peticiones_pendientes.queue)

    def get_and_reset_nuevas_peticiones(self):
        """Devuelve el número de peticiones recibidas desde la última llamada y resetea el contador."""
        with self._contador_lock:
            count = self._peticiones_nuevas_contador
            self._peticiones_nuevas_contador = 0
            return count

    def _bucle_despachador(self):
        """
        Hilo que consume de la cola de peticiones pendientes y las asigna a instancias libres.
        """
        while True:
            # Espera a que llegue una nueva petición (con timeout para permitir el apagado).
            # Si acquire() devuelve False, es por timeout. Si es True, es por una señal.
            self.peticiones_nuevas_sem.acquire()
            # Hay una petición garantizada en la cola, la sacamos sin bloquear.
            with self.cola_lock:
                peticion = self.peticiones_pendientes.get()

            if peticion is None: # Píldora venenosa para terminar el hilo
                break

            # Adquiere el semáforo. Se bloqueará aquí si no hay instancias libres.
            self.instancias_libres_sem.acquire()

            # Al pasar de aquí, tenemos garantizado que hay un "ticket" para una instancia libre.
            for instancia in self.instancias:
                if instancia.esta_libre():
                    instancia.recibir_peticion(*peticion)
                    self.peticiones_pendientes.task_done()
                    break # Petición asignada

    def get_avg_latency(self):
        """Calcula y devuelve la latencia media de las peticiones (sin implementar)."""
        pass

    def scale(self, pid_signal):
        """Ajusta el número de instancias basado en la señal de un controlador PID."""
        # --- Umbrales de ESCALADO (cuando la latencia es ALTA, señal NEGATIVA) ---
        SCALE_UP_SEVERE_THRESHOLD = -0.16  # Corresponde a +100ms de latencia (300ms total)
        SCALE_UP_MODERATE_THRESHOLD = -0.112 # Corresponde a +70ms de latencia (270ms total)
        SCALE_UP_MILD_THRESHOLD = -0.048   # Corresponde a +30ms de latencia (230ms total)

        # --- Umbrales de DESESCALADO (cuando la latencia es BAJA, señal POSITIVA) ---
        SCALE_DOWN_SEVERE_THRESHOLD = 0.16   # Corresponde a -100ms de latencia (100ms total)
        SCALE_DOWN_MODERATE_THRESHOLD = 0.112  # Corresponde a -70ms de latencia (130ms total)
        SCALE_DOWN_MILD_THRESHOLD = 0.048    # Corresponde a -30ms de latencia (170ms total)

        # Lógica de Escalado (Scale-Up)
        if pid_signal < SCALE_UP_SEVERE_THRESHOLD:
            logging.info(f"Manager: Señal PID severa ({pid_signal:.2f}). Creando 4 instancias.")
            for _ in range(4): self.create_instance()
        elif pid_signal < SCALE_UP_MODERATE_THRESHOLD:
            logging.info(f"Manager: Señal PID moderada ({pid_signal:.2f}). Creando 2 instancias.")
            for _ in range(2): self.create_instance()
        elif pid_signal < SCALE_UP_MILD_THRESHOLD:
            logging.info(f"Manager: Señal PID leve ({pid_signal:.2f}). Creando 1 instancia.")
            self.create_instance()
        # Lógica de Desescalado (Scale-Down)
        elif pid_signal > SCALE_DOWN_SEVERE_THRESHOLD:
            logging.info(f"Manager: Señal PID de baja carga severa ({pid_signal:.2f}). Destruyendo 4 instancias.")
            for _ in range(4): self.destroy_instance()
        elif pid_signal > SCALE_DOWN_MODERATE_THRESHOLD:
            logging.info(f"Manager: Señal PID de baja carga moderada ({pid_signal:.2f}). Destruyendo 2 instancias.")
            for _ in range(2): self.destroy_instance()
        elif pid_signal > SCALE_DOWN_MILD_THRESHOLD:
            logging.info(f"Manager: Señal PID de baja carga leve ({pid_signal:.2f}). Destruyendo 1 instancia.")
            self.destroy_instance()

    def detener_instancias(self):
        """Detiene todas las instancias activas."""
        logging.info("Manager: Esperando a que se procesen todas las peticiones en cola...")
        self.peticiones_pendientes.join() # Espera a que se despachen todas las peticiones reales.
        
        # Enviamos la "píldora venenosa" para detener al despachador
        with self.cola_lock:
            self.peticiones_pendientes.put(None)
        self.peticiones_nuevas_sem.release() # Despertamos al despachador para que la vea
        
        self._dispatcher_thread.join() # Espera a que el hilo despachador termine.
        logging.info("Manager: Deteniendo instancias de procesamiento...")
        for instancia in self.instancias:
            instancia.detener()