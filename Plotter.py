import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import tkinter as tk
import logging

class Plotter:
    """
    Genera gráficos a partir de los datos recolectados en la simulación.
    """
    def __init__(self, root, data_collector, latencia_deseada_ms, window_size_seconds=60):
        """
        Inicializa el plotter para visualización en tiempo real.
        """
        self.root = root
        self.data_collector = data_collector
        self.latencia_deseada_ms = latencia_deseada_ms
        self.window_size_seconds = window_size_seconds

        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4, self.ax5) = plt.subplots(5, 1, figsize=(12, 15), sharex=True)
        self.fig.suptitle('Análisis en Tiempo Real del Sistema de Auto-Escalado', fontsize=16)

        self._setup_axes()

        # Subplot 1: Latencia Promedio
        self.line1, = self.ax1.plot([], [], label='Latencia Promedio', color='b')
        self.ax1.axhline(y=self.latencia_deseada_ms, color='r', linestyle='--', label=f'Latencia Deseada ({self.latencia_deseada_ms}ms)')
        self.ax1.set_ylabel('Latencia (ms)')
        self.ax1.legend()
        self.ax1.grid(True)

        # Subplot 2: Cantidad de Instancias
        self.line2, = self.ax2.plot([], [], label='Instancias Activas', color='g', drawstyle='steps-post')
        self.ax2.set_ylabel('Nº de Instancias')
        self.ax2.legend()
        self.ax2.grid(True)
        self.ax2.yaxis.set_major_locator(MaxNLocator(integer=True))

        # Subplot 3: Peticiones Activas
        self.line3, = self.ax3.plot([], [], label='Peticiones en el Sistema', color='orange')
        self.ax3.set_xlabel('Tiempo (s)')
        self.ax3.set_ylabel('Nº de Peticiones')
        self.ax3.legend()
        self.ax3.grid(True)
        self.ax3.yaxis.set_major_locator(MaxNLocator(integer=True))

        # Subplot 4: Error
        self.line4, = self.ax4.plot([], [], label='Error (Deseada - Medida)', color='purple')
        self.ax4.axhline(y=0, color='k', linestyle='--', linewidth=0.8)
        self.ax4.set_ylabel('Error (ms)')
        self.ax4.legend()
        self.ax4.grid(True)

        # Subplot 5: Tasa de Peticiones
        self.line5, = self.ax5.plot([], [], label='Peticiones Nuevas / Intervalo', color='c', drawstyle='steps-post')
        self.ax5.set_ylabel('Nº Peticiones Nuevas')
        self.ax5.legend()
        self.ax5.grid(True)
        self.ax5.yaxis.set_major_locator(MaxNLocator(integer=True))

    def _update_plot(self, frame):
        """Función que se llama en cada frame de la animación para actualizar los datos."""
        # Usamos el lock para obtener una copia consistente de todos los datos
        with self.data_collector.lock:
            timestamps = list(self.data_collector.timestamps)
            latencias = list(self.data_collector.latencias_promedio)
            instancias = list(self.data_collector.cantidad_instancias)
            peticiones = list(self.data_collector.peticiones_activas)
            errores = list(self.data_collector.errores)
            peticiones_nuevas = list(self.data_collector.peticiones_nuevas)

        if timestamps:
            logging.debug(f"Plotter: Actualizando con {len(timestamps)} puntos. Último: t={timestamps[-1]:.2f}, lat={latencias[-1]:.2f}, inst={instancias[-1]}, pet={peticiones[-1]}")
        else:
            logging.debug("Plotter: No hay datos para graficar todavía.")

        self.line1.set_data(timestamps, latencias)
        self.line2.set_data(timestamps, instancias)
        self.line3.set_data(timestamps, peticiones)
        self.line4.set_data(timestamps, errores)
        self.line5.set_data(timestamps, peticiones_nuevas)

        # Re-ajustar los límites de los ejes dinámicamente
        if timestamps:
            # --- Lógica de la ventana deslizante ---
            current_time = timestamps[-1]
            xmin = max(0, current_time - self.window_size_seconds)
            xmax = xmin + self.window_size_seconds
            self.ax1.set_xlim(xmin, xmax)

            # --- Lógica de re-escalado manual del eje Y ---
            visible_indices = [i for i, t in enumerate(timestamps) if xmin <= t <= xmax]
            
            if visible_indices:
                start_idx, end_idx = visible_indices[0], visible_indices[-1] + 1

                # Función auxiliar para establecer los límites del eje Y con un margen
                def set_y_limits(ax, data_slice):
                    if not data_slice: return
                    min_val, max_val = min(data_slice), max(data_slice)
                    if min_val == max_val:
                        min_val -= 1
                        max_val += 1
                    
                    padding = (max_val - min_val) * 0.10 # 10% de margen
                    ax.set_ylim(min_val - padding, max_val + padding)

                # Aplicar a cada subplot
                set_y_limits(self.ax1, latencias[start_idx:end_idx])
                set_y_limits(self.ax2, instancias[start_idx:end_idx])
                set_y_limits(self.ax3, peticiones[start_idx:end_idx])
                set_y_limits(self.ax4, errores[start_idx:end_idx])
                set_y_limits(self.ax5, peticiones_nuevas[start_idx:end_idx])
            else:
                for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5]:
                    ax.relim(); ax.autoscale_y()

        return self.line1, self.line2, self.line3, self.line4, self.line5

    def _setup_axes(self):
        """Configura las propiedades iniciales de los ejes."""
        # Este método puede ser expandido si se necesita más configuración
        pass

    def run_animation(self):
        """Inicia la animación y muestra el gráfico."""
        canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ani = FuncAnimation(self.fig, self._update_plot, blit=False, interval=200)
        plt.tight_layout(rect=[0, 0, 1, 0.96])