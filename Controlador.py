import logging

class Controlador:
    """
    Implementa un controlador PID para generar una señal de control.
    """
    def __init__(self, system_manager, Kp=1.0, Ki=0.0, Kd=0.0):
        """
        Inicializa el controlador PID.

        :param system_manager: El gestor del sistema al que se enviará la señal de control.
        :param Kp: Ganancia Proporcional.
        :param Ki: Ganancia Integral.
        :param Kd: Ganancia Derivativa.
        """
        self.manager = system_manager
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.error_previo = 0
        self.integral = 0

    def recibir_error(self, error):
        """
        Recibe la señal de error del medidor, calcula la señal de control y la envía.
        """
        # --- Lógica del Controlador PID ---
        # Componente Proporcional
        P = self.Kp * error
        
        # Por ahora, solo usamos el componente Proporcional
        pid_signal = P
        
        logging.info(f"Controlador: Recibido error={error*1000:.2f}ms. Generando señal PID={pid_signal:.3f}")
        self.manager.scale(pid_signal)