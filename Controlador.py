import logging

class Controlador:
    """
    Controlador PD (proporcional-derivativo) con umbrales.
    La señal de control resultante indica cuánto variar la cantidad de instancias.
    """

    def __init__(self, system_manager, Kp=1.0, Kd=0.2, deadband_s=0.2):
        """
        :param system_manager: gestor del sistema al que se le enviará la señal de control.
        :param Kp: Ganancia proporcional (queda implícita en los umbrales).
        :param Kd: Ganancia derivativa (afecta la suavidad de la respuesta).
        """
        self.manager = system_manager
        self.Kp = Kp
        self.Kd = Kd
        self.deadband_s = deadband_s
        self.error_previo = 0.0
        self.step = 0  # contador discreto de tiempo (para logs)

    # --- Lógica de umbrales sobre el error de latencia (en segundos) ---

    @staticmethod
    def _umbrales(error_s: float) -> int:
        """ (DEPRECATED - Use la versión de instancia) """
        # Esta función estática ya no se usa, pero se mantiene por si acaso.
        # La lógica ahora está en la versión de instancia que usa self.deadband_s
        abs_error = abs(error_s)
        if abs_error < 0.2: return 0
        elif abs_error < 1.0: return -1 if error_s > 0 else 1
        else: return -2 if error_s > 0 else 2

    def _umbrales_con_banda_muerta(self, error_s: float) -> int:
        """
        Devuelve cuántas instancias se deberían agregar (valor positivo)
        o quitar (valor negativo) en función del error de latencia.
        """
        abs_error = abs(error_s)
        if abs_error < self.deadband_s:
            return 0
        elif abs_error < self.deadband_s + 0.6: # Umbral intermedio
            return -1 if error_s > 0 else 1
        else:
            return -2 if error_s > 0 else 2

    # --- Entrada desde el Medidor ---

    def recibir_error(self,
                      error_s: float,
                      latencia_promedio_s: float,
                      total_peticiones: int,
                      num_servers_actual: int,
                      setpoint_s: float) -> None:
        """
        Recibe el error de latencia y métricas del sistema, calcula la señal de
        control PD y llama al actuador (SystemManager.scale).
        """
        self.step += 1

        # Parte "P": lógica por umbrales (entrega un entero discreto)
        accion_por_umbrales = self._umbrales_con_banda_muerta(error_s)

        # Parte "D": derivada discreta (Δerror) escalada por Kd
        derivada = error_s - self.error_previo
        accion_derivativa = self.Kd * derivada

        control_signal = accion_por_umbrales + accion_derivativa

        # Aplicamos la señal al actuador
        self.manager.scale(control_signal)
        num_servers_nuevo = len(self.manager.instancias)

        # Logging estilo ejemplo, pero con tiempo medio de respuesta
        logging.info(
            "Tiempo: %d - Cantidad de servidores activos: %d - Tiempo medio de respuesta: %.3fs",
            self.step,
            num_servers_actual,
            latencia_promedio_s,
        )
        logging.info(
            "Cantidad de requests: %d - Senal de control (PD): %.3f - Nuevo numero de servidores: %d",
            total_peticiones,
            control_signal,
            num_servers_nuevo,
        )
        logging.info("-----------------------------------------------------------------")

        # Actualizamos estado previo
        self.error_previo = error_s