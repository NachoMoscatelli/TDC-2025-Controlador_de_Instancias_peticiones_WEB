import time
import logging
import threading

class Medidor:
    """
    Mide la latencia promedio del sistema y genera una señal de error.
    """
    def __init__(self, system_manager, controlador, latencia_deseada_ms=200, intervalo_medicion_ms=20):
        """
        Inicializa el Medidor.

        :param system_manager: El gestor del sistema que contiene las instancias.
        :param controlador: El controlador al que se le enviará la señal de error.
        :param latencia_deseada_ms: El valor de referencia para la latencia.
        :param intervalo_medicion_ms: Cada cuántos milisegundos se debe medir la latencia.
        """
        self.manager = system_manager
        self.controlador = controlador
        self.latencia_deseada_s = latencia_deseada_ms / 1000.0
        self.intervalo_medicion_ms = intervalo_medicion_ms / 1000.0
        self._thread = threading.Thread(target=self._bucle_medicion, daemon=True)
        self._activo = threading.Event()

    def iniciar(self):
        """Inicia el hilo de medición."""
        self._activo.set()
        self._thread.start()

    def detener(self):
        """Detiene el hilo de medición."""
        self._activo.clear()
        self._thread.join()

    def _bucle_medicion(self):
        """Bucle principal que mide periódicamente la latencia."""
        logging.info("Medidor: Iniciado.")
        while self._activo.is_set():
            time.sleep(self.intervalo_medicion_ms)
            
            latencia_promedio = self.get_average_latency()
            if latencia_promedio is not None:
                error = self.latencia_deseada_s - latencia_promedio
                logging.info(f"Medidor: Latencia Promedio: {latencia_promedio*1000:.2f}ms. Error: {error*1000:.2f}ms.")
                self.controlador.recibir_error(error)

    def get_average_latency(self):
        """
        Calcula la latencia promedio de todas las instancias.
        Las instancias inactivas aportan una latencia de 0.
        """
        instancias = self.manager.instancias
        if not instancias:
            return None

        tiempo_referencia = time.time()
        latencia_total = 0

        for instancia in instancias:
            ocupado, arrival_time = instancia.get_datos_peticion_actual()
            if ocupado and arrival_time:
                latencia_total += (tiempo_referencia - arrival_time)
        
        return latencia_total / len(instancias)