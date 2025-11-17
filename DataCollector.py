import time
import threading

class DataCollector:
    """
    Almacena los datos de la simulación en cada punto de tiempo para su posterior graficación.
    """
    def __init__(self, sim_start_time):
        self.start_time = sim_start_time
        self.lock = threading.Lock()
        self.timestamps = []
        self.latencias_promedio = []
        self.cantidad_instancias = []
        self.peticiones_activas = []
        self.errores = []
        self.peticiones_nuevas = []

    def collect(self, latencia_promedio, num_instancias, peticiones_activas, error, peticiones_nuevas):
        """Registra una nueva entrada de datos."""
        with self.lock:
            current_time = time.time() - self.start_time
            self.timestamps.append(current_time)
            self.latencias_promedio.append(latencia_promedio * 1000) # Guardar en ms
            self.cantidad_instancias.append(num_instancias)
            self.peticiones_activas.append(peticiones_activas)
            self.errores.append(error * 1000) # Guardar en ms
            self.peticiones_nuevas.append(peticiones_nuevas)