import time
import logging
import threading
import tkinter as tk
from Cliente import Cliente
from SystemManager import SystemManager
from Controlador import Controlador
from Medidor import Medidor
from DataCollector import DataCollector
from Plotter import Plotter

def run_simulation(cliente, medidor, manager, start_time):
    """
    Función que contiene la lógica de la simulación para ser ejecutada en un hilo.
    """
    logging.info("Iniciando simulación...")
    medidor.iniciar()
    cliente.iniciar(start_time) # Usamos el tiempo de inicio unificado
    # La función del hilo de simulación ahora termina, pero los hilos del cliente
    # y del medidor (que son daemon) seguirán corriendo en segundo plano.

def on_closing(root, cliente, medidor, manager):
    """Maneja el cierre de la ventana de la GUI."""
    logging.info("Cerrando la aplicación...")
    
    # 1. Detener al cliente para que no genere más peticiones.
    cliente.detener()
    # 2. Detener el medidor para que no envíe más señales de control.
    medidor.detener()
    # 3. Detener el manager y sus instancias.
    manager.detener_instancias()
    # 4. Destruir la ventana de la GUI.
    root.destroy()

def main():
    """
    Punto de entrada principal: configura los componentes y lanza la UI y la simulación.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        datefmt='%H:%M:%S',
        filename='simulacion.log',
        filemode='w' 
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console_handler)

    sim_start_time = time.time()
    latencia_deseada = 200 # en ms
    frecuencia_normal_hz = 10 # Hz
    frecuencia_pico_hz = 50 # Hz

    # --- Configuración de Componentes ---
    manager = SystemManager()
    data_collector = DataCollector(sim_start_time)
    controlador = Controlador(manager, Kp=0.7,Ki=0.8,Kd=0.9) # Kp=1.6 para una reacción sensible
    medidor = Medidor(manager, controlador, data_collector, sim_start_time, latencia_deseada_ms=latencia_deseada)
    cliente = Cliente(manager, frecuencia_normal_hz, frecuencia_pico_hz) # Ya no necesita numero_peticiones

    manager.create_instance()

    # --- Configuración de la GUI ---
    root = tk.Tk()
    root.title("Panel de Control de Simulación")

    plotter = Plotter(root, data_collector, latencia_deseada)

    # Botón para generar un pico de tráfico
    pico_button = tk.Button(root, text="Generar Pico de Tráfico (10s)", 
                            command=lambda: cliente.aumentar_frecuencia(10))
    pico_button.pack(pady=10)

    # --- Ejecución ---
    sim_thread = threading.Thread(target=run_simulation, args=(cliente, medidor, manager, sim_start_time), name="SimThread")
    sim_thread.start()

    plotter.run_animation()

    # Manejar el cierre de la ventana
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, cliente, medidor, manager))
    root.mainloop()

if __name__ == "__main__":
    main()
    