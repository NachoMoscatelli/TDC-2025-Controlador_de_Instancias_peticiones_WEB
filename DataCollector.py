import time
import threading

class DataCollector:
    """
    Almacena los datos de la simulación en cada punto de tiempo.
    """
    def __init__(self, sim_start_time):
        self.start_time = sim_start_time
        self.lock = threading.Lock()
        self.timestamps = []          # segundos desde inicio
        self.latencias_promedio = []  # en segundos
        self.cantidad_instancias = []
        self.peticiones_activas = []
        self.errores = []             # en segundos
        self.peticiones_nuevas = []

    def collect(self, latencia_promedio_s, num_instancias, peticiones_activas,
                error_s, peticiones_nuevas):
        """Registra una nueva entrada de datos."""
        with self.lock:
            current_time = time.time() - self.start_time
            self.timestamps.append(current_time)
            self.latencias_promedio.append(latencia_promedio_s)
            self.cantidad_instancias.append(num_instancias)
            self.peticiones_activas.append(peticiones_activas)
            self.errores.append(error_s)
            self.peticiones_nuevas.append(peticiones_nuevas)