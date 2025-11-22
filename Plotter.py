import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import TextBox, Button
import logging

class Plotter:
    """
    Genera gráficos a partir de los datos recolectados en la simulación.
    Además provee controles interactivos:
      - TextBox para cambiar la latencia deseada (setpoint) en segundos.
      - Botón para iniciar un ataque DoS.
    """
    def __init__(self, data_collector, latencia_deseada_s, medidor, cliente,
                 window_size_seconds=60):
        self.data_collector = data_collector
        self.latencia_deseada_s = latencia_deseada_s
        self.medidor = medidor
        self.cliente = cliente
        self.window_size_seconds = window_size_seconds

        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4, self.ax5) = plt.subplots(
            5, 1, figsize=(12, 15), sharex=True
        )
        self.fig.suptitle('Análisis en Tiempo Real del Sistema de Auto-Escalado', fontsize=16)

        # Subplot 1: Latencia Promedio (s)
        self.line1, = self.ax1.plot([], [], label='Latencia Promedio', color='b')
        self.setpoint_line = self.ax1.axhline(
            y=self.latencia_deseada_s,
            color='r',
            linestyle='--',
            label=f'Latencia Deseada ({self.latencia_deseada_s:.2f}s)',
        )
        self.ax1.set_ylabel('Latencia (s)')
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

        # Subplot 4: Error (s)
        self.line4, = self.ax4.plot([], [], label='Error (Deseada - Medida)', color='purple')
        self.ax4.axhline(y=0, color='k', linestyle='--', linewidth=0.8)
        self.ax4.set_ylabel('Error (s)')
        self.ax4.legend()
        self.ax4.grid(True)

        # Subplot 5: Tasa de Peticiones
        self.line5, = self.ax5.plot([], [], label='Peticiones Nuevas / Intervalo', color='c', drawstyle='steps-post')
        self.ax5.set_ylabel('Nº Peticiones Nuevas')
        self.ax5.legend()
        self.ax5.grid(True)
        self.ax5.yaxis.set_major_locator(MaxNLocator(integer=True))

        # --- Controles interactivos (arriba de todo) ---

        # TextBox para setpoint en segundos
        textbox_ax = self.fig.add_axes([0.60, 0.96, 0.30, 0.03])
        self.text_box = TextBox(textbox_ax, "Setpoint [s]: ", initial=f"{self.latencia_deseada_s:.2f}")
        self.text_box.on_submit(self._on_setpoint_change)

        # Botón para ataque DoS
        button_ax = self.fig.add_axes([0.30, 0.96, 0.20, 0.03])
        self.dos_button = Button(button_ax, "⚡ Iniciar Ataque DoS")
        self.dos_button.on_clicked(self._on_dos_click)

    # ---------- Callbacks de interfaz ----------

    def _on_setpoint_change(self, text: str):
        try:
            nuevo_sp_s = float(text)
            if nuevo_sp_s <= 0:
                logging.warning("Setpoint debe ser mayor que 0.")
                return
        except ValueError:
            logging.warning("Valor de setpoint inválido. Use, por ejemplo, 1 o 0.5.")
            return

        self.latencia_deseada_s = nuevo_sp_s
        self.medidor.latencia_deseada_s = nuevo_sp_s

        self.setpoint_line.set_ydata([nuevo_sp_s, nuevo_sp_s])
        self.setpoint_line.set_label(f'Latencia Deseada ({nuevo_sp_s:.2f}s)')
        self.ax1.legend(loc="upper right")

        logging.info("Nuevo setpoint establecido: %.3f s.", nuevo_sp_s)

    def _on_dos_click(self, event):
        self.cliente.ejecutar_dos()

    # ---------- Actualización de gráficos ----------

    def _update_plot(self, frame):
        with self.data_collector.lock:
            timestamps = list(self.data_collector.timestamps)
            lat_s = list(self.data_collector.latencias_promedio)
            instancias = list(self.data_collector.cantidad_instancias)
            peticiones = list(self.data_collector.peticiones_activas)
            err_s = list(self.data_collector.errores)
            peticiones_nuevas = list(self.data_collector.peticiones_nuevas)

        if timestamps:
            logging.debug(
                "Plotter: Actualizando con %d puntos. Último: t=%.2f, lat=%.3f s, inst=%d, pet=%d",
                len(timestamps),
                timestamps[-1],
                lat_s[-1] if lat_s else -1,
                instancias[-1] if instancias else -1,
                peticiones[-1] if peticiones else -1,
            )
        else:
            logging.debug("Plotter: No hay datos para graficar todavía.")

        self.line1.set_data(timestamps, lat_s)
        self.line2.set_data(timestamps, instancias)
        self.line3.set_data(timestamps, peticiones)
        self.line4.set_data(timestamps, err_s)
        self.line5.set_data(timestamps, peticiones_nuevas)

        if timestamps:
            current_time = timestamps[-1]
            xmin = max(0, current_time - self.window_size_seconds)
            xmax = xmin + self.window_size_seconds
            self.ax1.set_xlim(xmin, xmax)

            visible_indices = [i for i, t in enumerate(timestamps) if xmin <= t <= xmax]

            if visible_indices:
                start_idx, end_idx = visible_indices[0], visible_indices[-1] + 1

                def set_y_limits(ax, data_slice):
                    if not data_slice:
                        return
                    min_val, max_val = min(data_slice), max(data_slice)
                    if min_val == max_val:
                        min_val -= 0.01
                        max_val += 0.01
                    padding = (max_val - min_val) * 0.10
                    ax.set_ylim(min_val - padding, max_val + padding)

                set_y_limits(self.ax1, lat_s[start_idx:end_idx])
                set_y_limits(self.ax2, instancias[start_idx:end_idx])
                set_y_limits(self.ax3, peticiones[start_idx:end_idx])
                set_y_limits(self.ax4, err_s[start_idx:end_idx])
                set_y_limits(self.ax5, peticiones_nuevas[start_idx:end_idx])
            else:
                for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5]:
                    ax.relim()
                    ax.autoscale_y()

        return self.line1, self.line2, self.line3, self.line4, self.line5

    def run_animation(self):
        ani = FuncAnimation(self.fig, self._update_plot, blit=False, interval=200)
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()