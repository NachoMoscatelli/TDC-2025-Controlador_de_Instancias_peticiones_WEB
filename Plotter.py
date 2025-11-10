import matplotlib.pyplot as plt

class Plotter:
    """
    Genera gráficos a partir de los datos recolectados en la simulación.
    """
    @staticmethod
    def plot_simulation_data(data_collector, latencia_deseada_ms):
        """
        Crea y guarda un gráfico con 3 subplots: Latencia, Instancias y Peticiones.
        """
        if not data_collector.timestamps:
            print("No hay datos para graficar.")
            return

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        fig.suptitle('Análisis de Simulación del Sistema de Auto-Escalado', fontsize=16)

        # Subplot 1: Latencia Promedio
        ax1.plot(data_collector.timestamps, data_collector.latencias_promedio, label='Latencia Promedio', color='b')
        ax1.axhline(y=latencia_deseada_ms, color='r', linestyle='--', label=f'Latencia Deseada ({latencia_deseada_ms}ms)')
        ax1.set_ylabel('Latencia (ms)')
        ax1.legend()
        ax1.grid(True)

        # Subplot 2: Cantidad de Instancias
        ax2.plot(data_collector.timestamps, data_collector.cantidad_instancias, label='Instancias Activas', color='g', drawstyle='steps-post')
        ax2.set_ylabel('Nº de Instancias')
        ax2.legend()
        ax2.grid(True)

        # Subplot 3: Peticiones Activas
        ax3.plot(data_collector.timestamps, data_collector.peticiones_activas, label='Peticiones en el Sistema', color='orange')
        ax3.set_xlabel('Tiempo (s)')
        ax3.set_ylabel('Nº de Peticiones')
        ax3.legend()
        ax3.grid(True)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig('simulacion_plot.png')
        print("\nGráfico de la simulación guardado en 'simulacion_plot.png'")