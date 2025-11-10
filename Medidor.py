import time
import logging
import threading

class Medidor:
    """
    Mide la latencia promedio del sistema y genera una señal de error.
    """
    def __init__(self, system_manager, controlador, data_collector, latencia_deseada_ms=200, intervalo_medicion_ms=20):
        """
        Inicializa el Medidor.

        :param system_manager: El gestor del sistema que contiene las instancias.
        :param controlador: El controlador al que se le enviará la señal de error.
        :param data_collector: El objeto para registrar los datos de la simulación.
        :param latencia_deseada_ms: El valor de referencia para la latencia.
        :param intervalo_medicion_ms: Cada cuántos milisegundos se debe medir la latencia.
        """
        self.manager = system_manager
        self.controlador = controlador
        self.data_collector = data_collector
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
            
            latencia_promedio, peticiones_activas = self.get_system_metrics()
            if latencia_promedio is not None:
                error = self.latencia_deseada_s - latencia_promedio
                # Recolectamos los datos para la gráfica
                self.data_collector.collect(latencia_promedio, len(self.manager.instancias), peticiones_activas)
                logging.info(f"Medidor: Latencia Promedio: {latencia_promedio*1000:.2f}ms. Error: {error*1000:.2f}ms.")
                self.controlador.recibir_error(error)

    def get_system_metrics(self):
        """
        Calcula la latencia promedio de todas las instancias.
        Las instancias inactivas aportan una latencia de 0.
        """
        tiempo_referencia = time.time()
        latencia_total = 0

        # 1. Medir latencia de peticiones SIENDO PROCESADAS
        peticiones_en_proceso = 0
        for instancia in self.manager.instancias:
            ocupado, arrival_time = instancia.get_datos_peticion_actual()
            if ocupado and arrival_time:
                latencia_total += (tiempo_referencia - arrival_time)
                peticiones_en_proceso += 1
        
        # 2. Medir latencia de peticiones EN COLA
        peticiones_en_cola = self.manager.get_peticiones_pendientes_snapshot()
        for arrival_time, _ in peticiones_en_cola:
            if arrival_time: # Ignorar la "píldora venenosa" (None)
                latencia_total += (tiempo_referencia - arrival_time)
        
        # El número total de peticiones activas es la suma de las que están en cola y en proceso.
        num_peticiones_activas = len(peticiones_en_cola) + peticiones_en_proceso
        
        if num_peticiones_activas == 0:
            # Si no hay peticiones, la latencia es 0 y no hay peticiones activas.
            return 0.0, 0
        
        # Se divide por el total de peticiones activas para obtener la latencia promedio por petición.
        latencia_promedio = latencia_total / num_peticiones_activas
        return latencia_promedio, num_peticiones_activas