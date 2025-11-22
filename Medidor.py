import time
import logging
import threading

class Medidor:
    """
    Mide la latencia promedio del sistema y genera una señal de error.
    """

    def __init__(self, system_manager, controlador, data_collector,
                 sim_start_time, latencia_deseada_ms=200, intervalo_medicion_ms=20):
        """
        :param system_manager: El gestor del sistema que contiene las instancias.
        :param controlador: El controlador PD al que se le enviará la señal de error.
        :param data_collector: Objeto para registrar los datos de la simulación.
        :param sim_start_time: Tiempo de inicio de la simulación (time.time()).
        :param latencia_deseada_ms: Valor de referencia para la latencia (ms).
        :param intervalo_medicion_ms: Cada cuántos ms se mide la latencia.
        """
        self.manager = system_manager
        self.controlador = controlador
        self.data_collector = data_collector
        self.sim_start_time = sim_start_time
        self.latencia_deseada_s = latencia_deseada_ms / 1000.0
        self.intervalo_medicion_s = intervalo_medicion_ms / 1000.0
        self._thread = threading.Thread(target=self._bucle_medicion, daemon=True)
        self._activo = threading.Event()

    def iniciar(self):
        """Inicia el hilo de medición."""
        self._activo.set()
        self._thread.start()
        logging.info("Medidor: Iniciado.")

    def detener(self):
        """Detiene el hilo de medición."""
        self._activo.clear()
        self._thread.join()
        logging.info("Medidor: Detenido.")

    def _bucle_medicion(self):
        """Bucle principal que mide periódicamente la latencia."""
        while self._activo.is_set():
            time.sleep(self.intervalo_medicion_s)
            latencia_promedio, peticiones_activas = self.get_system_metrics()
            if latencia_promedio is None:
                continue

            error_s = self.latencia_deseada_s - latencia_promedio
            peticiones_nuevas = self.manager.get_and_reset_nuevas_peticiones()

            # Guardamos datos en el collector (ms)
            self.data_collector.collect(
                latencia_promedio,
                len(self.manager.instancias),
                peticiones_activas,
                error_s,
                peticiones_nuevas,
            )

            logging.info(
                "Medidor: Latencia Promedio: %.2f ms. Error: %.2f ms.",
                latencia_promedio * 1000,
                error_s * 1000,
                )

            # Enviamos todo al controlador PD
            self.controlador.recibir_error(
                error_s,
                latencia_promedio,
                peticiones_activas,
                len(self.manager.instancias),
                self.latencia_deseada_s,
            )

    def get_system_metrics(self):
        """
        Calcula la latencia promedio de todas las peticiones (en proceso + en cola).
        """
        tiempo_referencia = time.time() - self.sim_start_time
        latencia_total = 0.0
        peticiones_en_proceso = 0

        # 1. Medir latencia de peticiones en procesamiento
        for instancia in self.manager.instancias:
            ocupado, arrival_time = instancia.get_datos_peticion_actual()
            if ocupado and arrival_time is not None:
                latencia_total += (tiempo_referencia - arrival_time)
                peticiones_en_proceso += 1

        # 2. Medir latencia de peticiones en cola
        peticiones_en_cola = self.manager.get_peticiones_pendientes_snapshot()
        for arrival_time, _ in peticiones_en_cola:
            if arrival_time is not None:
                latencia_total += (tiempo_referencia - arrival_time)

        num_peticiones_activas = peticiones_en_proceso + len(peticiones_en_cola)

        if num_peticiones_activas == 0:
            return 0.0, 0

        latencia_promedio = latencia_total / num_peticiones_activas
        return latencia_promedio, num_peticiones_activas