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
        # Para el cálculo de SLO: (timestamp, latencia_individual_s)
        self.peticiones_resueltas = []


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

    def collect_peticion_resuelta(self, latencia_s: float):
        """Registra la latencia de una petición individual cuando se completa."""
        with self.lock:
            current_time = time.time() - self.start_time
            self.peticiones_resueltas.append((current_time, latencia_s))

    def get_slo_compliance(self, window_seconds: int, setpoint_s: float, error_band_s: float) -> float:
        """
        Calcula el porcentaje de peticiones resueltas en la última ventana de tiempo
        que cayeron dentro de la banda de error (setpoint ± error_band).
        """
        with self.lock:
            if not self.peticiones_resueltas:
                return 100.0

            now = time.time() - self.start_time
            limite_inferior_tiempo = now - window_seconds

            peticiones_recientes = [p for p in self.peticiones_resueltas if p[0] >= limite_inferior_tiempo]
            if not peticiones_recientes:
                return 100.0

            # Nueva lógica: una petición cumple si su latencia es MENOR O IGUAL al umbral máximo tolerable.
            # No penalizamos las peticiones que son más rápidas que el setpoint.
            umbral_maximo_tolerable = setpoint_s + error_band_s
            dentro_de_banda = sum(1 for _, lat in peticiones_recientes if lat <= umbral_maximo_tolerable)
            return (dentro_de_banda / len(peticiones_recientes)) * 100.0