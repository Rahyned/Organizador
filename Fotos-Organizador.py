import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
from datetime import datetime
import threading
from pathlib import Path
import logging
import platform
import subprocess

# Configuración de logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OrganizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("Organizador de Archivos")
        self.geometry("900x800")
        self.resizable(True, True)
        self.minsize(700, 600)
        
        # Colores personalizados (mate)
        self.color_primary = "#4b7a99"
        self.color_secondary = "#2d3f4e"
        self.color_accent = "#6b7280"
        self.color_success = "#5a8a6f"
        self.color_warning = "#a68a5a"

        # Archivo donde se guardará la ruta
        self.archivo_config = "config_ruta.txt"
        self.ruta_destino_base = self.cargar_configuracion()
        
        # Estado del procesamiento
        self.procesando = False

        # --- INTERFAZ ---
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=self.color_secondary, corner_radius=0)
        header_frame.pack(fill="x", pady=0)
        
        ctk.CTkLabel(
            header_frame, 
            text="Organizador de Archivos", 
            font=("Segoe UI", 32, "bold"),
            text_color=self.color_primary
        ).pack(pady=20)

        # Contenido principal - ScrollableFrame
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Configurar peso de la columna para centrado
        main_frame._parent_frame.grid_columnconfigure(0, weight=1)

        # --- SECCIÓN 1: DESTINO ---
        dest_frame = ctk.CTkFrame(main_frame, fg_color=self.color_secondary, corner_radius=12)
        dest_frame.pack(fill="x", pady=(0, 25), padx=20)
        
        ctk.CTkLabel(
            dest_frame,
            text="Carpeta de Destino",
            font=("Segoe UI", 16, "bold"),
            text_color=self.color_primary
        ).pack(anchor="w", pady=(15, 12), padx=15)
        
        btn_frame_dest = ctk.CTkFrame(dest_frame, fg_color="transparent")
        btn_frame_dest.pack(fill="x", pady=(0, 12), padx=15)
        
        self.btn_config = ctk.CTkButton(
            btn_frame_dest, text="Seleccionar Destino", 
            command=self.configurar_destino,
            font=("Segoe UI", 13, "bold"),
            height=40,
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=8
        )
        self.btn_config.pack(side="left", padx=(0, 12))
        
        self.btn_abrir_destino = ctk.CTkButton(
            btn_frame_dest, text="Abrir", 
            command=self.abrir_carpeta_destino,
            font=("Segoe UI", 13, "bold"),
            height=40,
            width=90,
            fg_color=self.color_success,
            hover_color="#4a7359",
            corner_radius=8
        )
        self.btn_abrir_destino.pack(side="left")
        
        self.lbl_destino = ctk.CTkLabel(
            dest_frame,
            text=f"{self._truncar_ruta(self.ruta_destino_base, 80)}", 
            font=("Segoe UI", 12, "bold"),
            text_color="#ffffff",
            wraplength=600,
            justify="left"
        )
        self.lbl_destino.pack(fill="x", pady=(0, 15), padx=15)

        # --- SEPARADOR ---
        ctk.CTkLabel(main_frame, text="─" * 80, text_color="#444444").pack(pady=15)
        origen_frame = ctk.CTkFrame(main_frame, fg_color=self.color_secondary, corner_radius=12)
        origen_frame.pack(fill="x", pady=(0, 25), padx=20)
        
        ctk.CTkLabel(
            origen_frame,
            text="Carpeta de Origen",
            font=("Segoe UI", 16, "bold"),
            text_color=self.color_primary
        ).pack(anchor="w", pady=(15, 12), padx=15)
        
        btn_frame_origen = ctk.CTkFrame(origen_frame, fg_color="transparent")
        btn_frame_origen.pack(fill="x", pady=(0, 12), padx=15)
        
        self.btn_origen = ctk.CTkButton(
            btn_frame_origen, text="Seleccionar Origen", 
            command=self.seleccionar_origen,
            font=("Segoe UI", 13, "bold"),
            height=40,
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=8
        )
        self.btn_origen.pack(side="left", padx=(0, 12))
        
        self.btn_abrir_origen = ctk.CTkButton(
            btn_frame_origen, text="Abrir", 
            command=self.abrir_carpeta_origen,
            font=("Segoe UI", 13, "bold"),
            height=40,
            width=90,
            fg_color=self.color_success,
            hover_color="#4a7359",
            corner_radius=8
        )
        self.btn_abrir_origen.pack(side="left")
        
        self.path_origen = ""
        self.lbl_origen = ctk.CTkLabel(
            origen_frame, 
            text="No seleccionada", 
            text_color=self.color_warning,
            font=("Segoe UI", 12, "bold")
        )
        self.lbl_origen.pack(fill="x", pady=(0, 8), padx=15)
        
        self.lbl_contador = ctk.CTkLabel(
            origen_frame, text="", 
            text_color=self.color_accent, 
            font=("Segoe UI", 12, "bold")
        )
        self.lbl_contador.pack(fill="x", padx=15, pady=(0, 15))

        # --- SEPARADOR ---
        ctk.CTkLabel(main_frame, text="─" * 80, text_color="#444444").pack(pady=15)

        # --- SECCIÓN 3: CLASIFICACIÓN ---
        clasificacion_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        clasificacion_frame.pack(fill="x", pady=(0, 25), padx=20)
        
        ctk.CTkLabel(
            clasificacion_frame,
            text="Clasificación y Datos",
            font=("Segoe UI", 16, "bold"),
            text_color=self.color_primary
        ).pack(anchor="w", pady=(0, 15))
        
        # Fecha
        ctk.CTkLabel(
            clasificacion_frame, text="Fecha:", 
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(0, 6))
        
        self.entry_fecha = ctk.CTkEntry(
            clasificacion_frame, placeholder_text="DD-MM-AAAA",
            font=("Segoe UI", 12),
            height=40,
            border_width=2,
            border_color=self.color_primary,
            fg_color=self.color_secondary,
            corner_radius=8
        )
        self.entry_fecha.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.entry_fecha.pack(fill="x", pady=(0, 15))

        # Caso
        ctk.CTkLabel(
            clasificacion_frame, text="Nombre del Caso / Paciente / Curso:", 
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(0, 6))
        
        self.entry_caso = ctk.CTkEntry(
            clasificacion_frame, placeholder_text="Ej: Paciente_Juan_García",
            font=("Segoe UI", 12),
            height=40,
            border_width=2,
            border_color=self.color_primary,
            fg_color=self.color_secondary,
            corner_radius=8
        )
        self.entry_caso.pack(fill="x", pady=(0, 15))

        # Categoría
        ctk.CTkLabel(
            clasificacion_frame, text="Categoría:", 
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(0, 6))
        
        self.combobox_cat = ctk.CTkComboBox(
            clasificacion_frame, 
            values=["Casos", "Laboratorio/Equipo", "Cursos", "Otras"],
            font=("Segoe UI", 12),
            height=40,
            border_width=2,
            border_color=self.color_primary,
            fg_color=self.color_secondary,
            corner_radius=8,
            dropdown_font=("Segoe UI", 12)
        )
        self.combobox_cat.set("Casos")
        self.combobox_cat.pack(fill="x")

        # --- SEPARADOR ---
        ctk.CTkLabel(main_frame, text="─" * 80, text_color="#444444").pack(pady=15)

        # --- BOTÓN DE PROCESAMIENTO ---
        self.btn_procesar = ctk.CTkButton(
            main_frame, text="ORGANIZAR Y MOVER ARCHIVOS", 
            height=50,
            font=("Segoe UI", 14, "bold"),
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=10,
            command=self.procesar_lote_thread
        )
        self.btn_procesar.pack(fill="x", padx=20, pady=(0, 15))
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(main_frame, corner_radius=8)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 12))
        self.progress_bar.set(0)
        
        self.lbl_estado = ctk.CTkLabel(
            main_frame, text="", 
            text_color=self.color_accent, 
            font=("Segoe UI", 11)
        )
        self.lbl_estado.pack(fill="x", padx=20, pady=(0, 20))

    # --- FUNCIONES DE UTILIDAD ---

    def _truncar_ruta(self, ruta, max_chars=70):
        """Trunca la ruta si es muy larga"""
        if len(ruta) > max_chars:
            return "..." + ruta[-(max_chars-3):]
        return ruta

    def _validar_fecha(self, fecha):
        """Valida que la fecha tenga el formato correcto"""
        try:
            datetime.strptime(fecha, "%d-%m-%Y")
            return True
        except ValueError:
            return False

    def _obtener_archivos(self, ruta):
        """Retorna todos los archivos (excepto carpetas) de una ruta"""
        try:
            archivos = os.listdir(ruta)
            archivos_validos = [
                f for f in archivos 
                if os.path.isfile(os.path.join(ruta, f))
            ]
            return archivos_validos
        except Exception as e:
            logging.error(f"Error al leer archivos: {e}")
            return []

    def _abrir_carpeta(self, ruta):
        """Abre una carpeta en el explorador de archivos según el SO"""
        if not os.path.exists(ruta):
            messagebox.showerror("Error", "La carpeta no existe.")
            return
        
        try:
            if platform.system() == "Windows":
                os.startfile(ruta)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", ruta])
            else:  # Linux
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
            logging.error(f"Error al abrir carpeta: {e}")

    # --- FUNCIONES DE LÓGICA ---

    def cargar_configuracion(self):
        """Lee el archivo txt para saber dónde guardar los archivos"""
        try:
            if os.path.exists(self.archivo_config):
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    ruta = f.read().strip()
                    if os.path.exists(ruta):
                        return ruta
        except Exception as e:
            logging.error(f"Error al cargar configuración: {e}")
        return "No configurada"

    def configurar_destino(self):
        """Permite elegir la carpeta de red y guarda la ruta en el txt"""
        ruta = filedialog.askdirectory(
            title="Selecciona la Carpeta Raíz de Destino (Servidor/Red)"
        )
        if ruta:
            try:
                with open(self.archivo_config, "w", encoding="utf-8") as f:
                    f.write(ruta)
                self.ruta_destino_base = ruta
                self.lbl_destino.configure(
                    text=f"{self._truncar_ruta(ruta)}"
                )
                messagebox.showinfo("Éxito", "Carpeta de destino configurada correctamente.")
                logging.info(f"Configuración guardada: {ruta}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")
                logging.error(f"Error al guardar configuración: {e}")

    def abrir_carpeta_destino(self):
        """Abre la carpeta de destino en el explorador"""
        if self.ruta_destino_base != "No configurada":
            self._abrir_carpeta(self.ruta_destino_base)
        else:
            messagebox.showwarning("Atención", "Primero debes configurar la carpeta de destino.")

    def seleccionar_origen(self):
        """Selecciona la carpeta donde están los archivos"""
        ruta = filedialog.askdirectory(
            title="Selecciona la carpeta con los archivos"
        )
        if ruta:
            self.path_origen = ruta
            nombre_carpeta = os.path.basename(ruta)
            archivos = self._obtener_archivos(ruta)
            
            self.lbl_origen.configure(
                text=f"✓ {nombre_carpeta}", 
                text_color=self.color_success
            )
            self.lbl_contador.configure(
                text=f"{len(archivos)} archivo(s) encontrado(s)"
            )

    def abrir_carpeta_origen(self):
        """Abre la carpeta de origen en el explorador"""
        if self.path_origen:
            self._abrir_carpeta(self.path_origen)
        else:
            messagebox.showwarning("Atención", "Primero debes seleccionar una carpeta de origen.")

    def procesar_lote_thread(self):
        """Inicia el procesamiento en un hilo separado para no bloquear la UI"""
        if not self.procesando:
            thread = threading.Thread(target=self.procesar_lote)
            thread.start()

    def procesar_lote(self):
        """Mueve los archivos y crea la estructura automática"""
        self.procesando = True
        self.btn_procesar.configure(state="disabled")
        
        try:
            # Verificación de configuración
            if self.ruta_destino_base == "No configurada":
                messagebox.showwarning("Atención", 
                    "Primero debes configurar la Carpeta de Destino.")
                return

            # Obtener datos de la interfaz
            fecha = self.entry_fecha.get().strip()
            caso = self.entry_caso.get().strip()
            categoria = self.combobox_cat.get()

            # Validación de campos
            if not self.path_origen:
                messagebox.showerror("Error", "No has seleccionado la carpeta de origen.")
                return
            
            if not caso:
                messagebox.showerror("Error", "Debes escribir un nombre para el caso.")
                return
            
            if not self._validar_fecha(fecha):
                messagebox.showerror("Error", "Formato de fecha inválido. Usa: DD-MM-AAAA")
                return

            # Obtener todos los archivos
            archivos = self._obtener_archivos(self.path_origen)
            
            if not archivos:
                messagebox.showwarning("Advertencia", 
                    "No se encontraron archivos en la carpeta seleccionada.")
                return

            nombre_carpeta_final = f"{fecha}_{caso}"
            ruta_final = os.path.join(self.ruta_destino_base, categoria, nombre_carpeta_final)

            # Crear estructura de carpetas
            if not os.path.exists(ruta_final):
                os.makedirs(ruta_final)

            # Mover archivos con barra de progreso
            for idx, archivo in enumerate(archivos):
                try:
                    ruta_origen = os.path.join(self.path_origen, archivo)
                    ruta_destino = os.path.join(ruta_final, archivo)
                    shutil.move(ruta_origen, ruta_destino)
                    
                    # Actualizar barra de progreso
                    progreso = (idx + 1) / len(archivos)
                    self.progress_bar.set(progreso)
                    self.lbl_estado.configure(
                        text=f"Moviendo: {archivo} ({idx + 1}/{len(archivos)})"
                    )
                    self.update()
                except Exception as e:
                    logging.error(f"Error al mover {archivo}: {e}")
                    messagebox.showwarning("Advertencia", 
                        f"No se pudo mover {archivo}: {e}")

            # Éxito
            messagebox.showinfo("Éxito", 
                f"Proceso completado!\n\nSe movieron {len(archivos)} archivos a:\n{categoria}/{nombre_carpeta_final}")
            logging.info(f"Proceso completado: {len(archivos)} archivos movidos a {ruta_final}")
            
            # Resetear interfaz
            self.entry_caso.delete(0, 'end')
            self.lbl_origen.configure(text="No seleccionada", text_color=self.color_warning)
            self.lbl_contador.configure(text="")
            self.path_origen = ""
            self.progress_bar.set(0)
            self.lbl_estado.configure(text="")

        except Exception as e:
            messagebox.showerror("Error de Sistema", 
                f"No se pudieron mover los archivos: {e}")
            logging.error(f"Error en procesar_lote: {e}")
        
        finally:
            self.procesando = False
            self.btn_procesar.configure(state="normal")


if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()