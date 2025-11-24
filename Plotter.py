import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import TextBox, Button, Slider
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

        # --- Valores para los sliders de DoS ---
        self.dos_duracion_s = 6.0
        self.dos_frecuencia_hz = 8.0
        # ------------------------------------

        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4, self.ax5) = plt.subplots(
            5, 1, figsize=(12, 15), sharex=True
        )
        # Establecer el título solo en la barra de la ventana
        title = 'Análisis en Tiempo Real: Sistema de Auto-Escalado'
        self.fig.canvas.manager.set_window_title(title)

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

        # Ajustar layout para dejar espacio para los controles en la parte superior
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.82, bottom=0.05, hspace=0.5)

        # --- Controles interactivos (en la parte superior) ---

        # Etiqueta para tiempo de procesamiento promedio (arriba)
        proc_time_text = f"T. Procesamiento Base: {self.cliente.base_processing_ms} ms (±20%)"
        self.fig.text(0.05, 0.95, proc_time_text, fontsize=10, transform=self.fig.transFigure)

        # Etiqueta para frecuencia de peticiones base
        freq_base_text = f"Freq. Peticiones Base: {self.cliente.frecuencia_promedio_hz:.2f} Hz (Estable)"
        self.fig.text(0.05, 0.92, freq_base_text, fontsize=10, transform=self.fig.transFigure)


        # TextBox para setpoint en segundos
        self.fig.text(0.25, 0.95, "Latencia Objetivo:", fontsize=10)
        textbox_ax = self.fig.add_axes([0.38, 0.945, 0.06, 0.03])
        self.text_box = TextBox(textbox_ax, "", initial=f"{self.latencia_deseada_s:.2f}")
        self.text_box.on_submit(self._on_setpoint_change)

        # TextBox para cantidad máxima de instancias
        self.fig.text(0.25, 0.91, "Max Instancias:", fontsize=10)
        max_inst_ax = self.fig.add_axes([0.38, 0.905, 0.06, 0.03])
        self.max_inst_textbox = TextBox(max_inst_ax, "", initial=f"{self.medidor.manager.max_servers}")
        self.max_inst_textbox.on_submit(self._on_max_instancias_change)

        # --- Etiquetas informativas para ganancias Kp y Kd ---
        controlador = self.medidor.controlador
        kp_text = f"Ganancia Kp: {controlador.Kp:.2f}"
        kd_text = f"Ganancia Kd: {controlador.Kd:.2f}"
        self.fig.text(0.05, 0.88, kp_text, fontsize=10, transform=self.fig.transFigure)
        self.fig.text(0.05, 0.85, kd_text, fontsize=10, transform=self.fig.transFigure)

        # Etiqueta para el cumplimiento de SLO
        self.error_band_s = 0.4 # Banda para medir el SLO
        umbral_max_slo = self.latencia_deseada_s + self.error_band_s
        self.slo_band_text_obj = self.fig.text(0.25, 0.88, f"SLO Lat. Máx: {umbral_max_slo:.1f}s", fontsize=10, transform=self.fig.transFigure)

        self.slo_text = self.fig.text(0.25, 0.85, "SLO (1 min): --%", fontsize=10, transform=self.fig.transFigure)
        self.fig.text(0.05, 0.82, f"Banda Muerta Ctr: ±{controlador.deadband_s}s", fontsize=10, transform=self.fig.transFigure)


        # Slider para frecuencia de muestreo (Hz)
        slider_muestreo_ax = self.fig.add_axes([0.55, 0.95, 0.40, 0.02])
        self.muestreo_slider = Slider(
            ax=slider_muestreo_ax,
            label='Frecuencia Muestreo (Hz)',
            valmin=1,  # 1 Hz (1000 ms)
            valmax=100, # 100 Hz (10 ms)
            valinit=1 / self.medidor.intervalo_medicion_s,
            valstep=1,
        )
        self.muestreo_slider.on_changed(self._on_muestreo_change)

        # --- Controles de Ataque DoS en una línea ---

        # 1. Botón para ataque DoS
        button_ax = self.fig.add_axes([0.55, 0.89, 0.15, 0.04])
        self.dos_button = Button(button_ax, "⚡ Iniciar Ataque DoS")
        self.dos_button.on_clicked(self._on_dos_click)

        # 2. Recuadro para duración de ataque DoS
        self.fig.text(0.73, 0.90, "Duración (s):", fontsize=10)
        dos_duracion_ax = self.fig.add_axes([0.81, 0.895, 0.08, 0.03])
        self.dos_duracion_textbox = TextBox(
            dos_duracion_ax, "", initial=f"{self.dos_duracion_s:.1f}"
        )
        self.dos_duracion_textbox.on_submit(self._on_dos_duracion_change)

        # 3. Slider para frecuencia de ataque DoS
        slider_dos_freq_ax = self.fig.add_axes([0.55, 0.85, 0.40, 0.02])
        self.dos_freq_slider = Slider(
            ax=slider_dos_freq_ax,
            label='Frecuencia Ataque (Hz)',
            valmin=1, valmax=1000, valinit=self.dos_frecuencia_hz, valstep=1,
        )
        self.dos_freq_slider.on_changed(lambda val: setattr(self, 'dos_frecuencia_hz', val))

    # ---------- Callbacks de interfaz ----------

    def _on_setpoint_change(self, text: str):
        try:
            nuevo_sp_s = float(text)
            if nuevo_sp_s <= 0:
                logging.warning("Setpoint debe ser mayor que 0.")
                self.text_box.set_val(f"{self.latencia_deseada_s:.2f}") # Revertir
                return
        except ValueError:
            logging.warning("Valor de setpoint invalido. Use, por ejemplo, 1 o 0.5.")
            self.text_box.set_val(f"{self.latencia_deseada_s:.2f}") # Revertir
            return

        self.latencia_deseada_s = nuevo_sp_s
        self.medidor.latencia_deseada_s = nuevo_sp_s

        # --- SOLUCIÓN: Sincronizar el cliente con el nuevo setpoint ---
        self.cliente.base_processing_ms = int(nuevo_sp_s * 1000)

        self.setpoint_line.set_ydata([nuevo_sp_s, nuevo_sp_s])
        self.setpoint_line.set_label(f'Latencia Deseada ({nuevo_sp_s:.2f}s)')
        self.ax1.legend(loc="upper right")

        # Actualizar la etiqueta del umbral de SLO
        umbral_max_slo = self.latencia_deseada_s + self.error_band_s
        self.slo_band_text_obj.set_text(f"SLO Lat. Máx: {umbral_max_slo:.1f}s")

        logging.info("Nuevo setpoint establecido: %.3f s.", nuevo_sp_s)

    def _on_dos_click(self, event):
        logging.info("Disparando ataque DoS con Duracion=%.1fs y Frecuencia=%.1f RPS",
                     self.dos_duracion_s, self.dos_frecuencia_hz)
        self.cliente.ejecutar_dos(duracion_s=self.dos_duracion_s, frecuencia_promedio_hz=self.dos_frecuencia_hz)

    def _on_dos_duracion_change(self, text: str):
        try:
            nueva_duracion = float(text)
            if nueva_duracion <= 0:
                logging.warning("La duracion del ataque debe ser mayor a 0.")
                self.dos_duracion_textbox.set_val(f"{self.dos_duracion_s:.1f}")
                return
            self.dos_duracion_s = nueva_duracion
            logging.info("Nueva duracion de ataque DoS establecida: %.1f s", nueva_duracion)
        except ValueError:
            logging.warning("Valor de duracion de ataque invalido.")
            self.dos_duracion_textbox.set_val(f"{self.dos_duracion_s:.1f}")

    def _on_muestreo_change(self, freq_hz):
        if freq_hz == 0: return
        nuevo_intervalo_s = 1.0 / freq_hz
        self.medidor.intervalo_medicion_s = nuevo_intervalo_s
        logging.info("Nueva frecuencia de muestreo: %.1f Hz (intervalo: %.3f s)", freq_hz, nuevo_intervalo_s)

    def _on_max_instancias_change(self, text: str):
        try:
            nuevo_max = int(text)
            manager = self.medidor.manager
            num_actual = len(manager.instancias)

            if nuevo_max < manager.MIN_SERVERS or nuevo_max < num_actual:
                raise ValueError(f"Debe ser >= {max(manager.MIN_SERVERS, num_actual)}")

            manager.max_servers = nuevo_max
            logging.info("Nuevo maximo de instancias establecido: %d", nuevo_max)

        except ValueError as e:
            logging.warning("Valor de max_instancias invalido: %s", e)
            # Revertir al valor actual en la caja de texto
            self.max_inst_textbox.set_val(f"{self.medidor.manager.max_servers}")


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
                "Plotter: Actualizando con %d puntos. Ultimo: t=%.2f, lat=%.3f s, inst=%d, pet=%d",
                len(timestamps),
                timestamps[-1],
                lat_s[-1] if lat_s else -1,
                instancias[-1] if instancias else -1,
                peticiones[-1] if peticiones else -1,
            )
        else:
            logging.debug("Plotter: No hay datos para graficar todavia.")

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

        # Actualizar texto de SLO
        slo_compliance = self.data_collector.get_slo_compliance(
            window_seconds=60,
            setpoint_s=self.latencia_deseada_s,
            error_band_s=self.error_band_s
        )
        self.slo_text.set_text(f"SLO (1 min): {slo_compliance:.1f}%")

        return self.line1, self.line2, self.line3, self.line4, self.line5

    def _setup_axes(self):
        """Configura las propiedades iniciales de los ejes."""
        # Este método puede ser expandido si se necesita más configuración
        pass

    def run_animation(self):
        ani = FuncAnimation(self.fig, self._update_plot, blit=False, interval=200)
        # plt.tight_layout() # No usar tight_layout con subplots_adjust y add_axes manuales
        plt.show()
