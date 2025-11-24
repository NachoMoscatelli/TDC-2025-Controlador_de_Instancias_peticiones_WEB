import time
import logging
from Cliente import Cliente
from SystemManager import SystemManager
from Controlador import Controlador
from Medidor import Medidor
from DataCollector import DataCollector
from Plotter import Plotter

def main():
    # Logging a archivo + consola
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        datefmt='%H:%M:%S',
        filename='simulacion.log',
        filemode='w' 
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console_handler)

    sim_start_time = time.time()

    # --- Setpoint inicial: 1 segundo ---
    latencia_deseada_s = 1.0
    latencia_deseada_ms = int(latencia_deseada_s * 1000)

    data_collector = DataCollector(sim_start_time)
    manager = SystemManager(data_collector, max_servers=50)
    controlador = Controlador(manager, Kp=0.8, Kd=7.0, deadband_s=0)
    medidor = Medidor(
        manager,
        controlador,
        data_collector,
        sim_start_time,
        latencia_deseada_ms=latencia_deseada_ms,
        intervalo_medicion_ms=1000/50,  # Frecuencia de muestreo de 50 Hz
    )

    # Cliente: base_processing_ms ≈ setpoint para que la latencia estable
    # con una instancia oscile alrededor de 1 s.
    cliente = Cliente(
        manager,
        frecuencia_promedio_hz=1,      # Carga base conservadora (1 petición cada 2 segundos)
        base_processing_ms=latencia_deseada_ms,
    )

    plotter = Plotter(data_collector, latencia_deseada_s, medidor, cliente)

    # Empezamos con una instancia
    manager.create_instance()

    # Iniciamos medidor y cliente
    medidor.iniciar()
    cliente.iniciar(sim_start_time)

    # UI (bloqueante)
    plotter.run_animation()

    # Cuando se cierra la ventana, apagamos todo ordenadamente
    cliente.detener()
    manager.clear_pending_requests() # Limpiamos la cola de peticiones
    manager.detener_instancias()
    medidor.detener()
    logging.info("Programa finalizado.")

if __name__ == "__main__":
    main()