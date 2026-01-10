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
import json
from collections import defaultdict
import sys

def ruta_recurso(relativa):
    
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En modo desarrollo, usar la carpeta del script actual
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relativa)

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
        
        # Configurar ícono
        try:
            ruta_icono = ruta_recurso("camara.ico")
            if os.path.exists(ruta_icono):
                self.iconbitmap(ruta_icono)
                logging.info(f"Icono cargado desde: {ruta_icono}")
            else:
                logging.warning(f"Archivo de icono no encontrado en: {ruta_icono}")
        except Exception as e:
            logging.error(f"Error al cargar el icono: {e}")
        
        self.resizable(True, True) 
        self.minsize(700, 600)
        
        # Centrar ventana en pantalla
        self.update_idletasks()
        ancho_ventana = 900
        alto_ventana = 800
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla // 2) - (ancho_ventana // 2)
        y = (alto_pantalla // 2) - (alto_ventana // 2)
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
         
        
        # Colores personalizados (mate)
        self.color_primary = "#4b7a99"
        self.color_secondary = "#2d3f4e"
        self.color_accent = "#6b7280"
        self.color_success = "#5a8a6f"
        self.color_warning = "#a68a5a"
        self.color_danger = "#8b5a5a"

        # Archivos de configuración
        self.archivo_config = "config_ruta.txt"
        self.archivo_historial = "historial_lotes.json"
        self.ruta_destino_base = self.cargar_configuracion()
        
        # Estado del procesamiento
        self.procesando = False
        
        # Cargar historial
        self.historial = self.cargar_historial()
        
        # Variable para guardar ruta seleccionada en buscador
        self.ultima_ruta_buscada = None
        self.resultados_busqueda = []

        # --- INTERFAZ CON TABS ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)
        
        # Crear pestañas
        self.tab_procesar = self.tabview.add("Procesar")
        self.tab_historial = self.tabview.add("Historial")
        self.tab_buscador = self.tabview.add("Buscar Archivos")
        
        # Configurar pestañas
        self._crear_tab_procesamiento()
        self._crear_tab_historial()
        self._crear_tab_buscador()

    def _crear_tab_procesamiento(self):
        """Crea la pestaña de procesamiento"""
        # Header
        header_frame = ctk.CTkFrame(self.tab_procesar, fg_color=self.color_secondary, corner_radius=0)
        header_frame.pack(fill="x", pady=0)
        
        ctk.CTkLabel(
            header_frame, 
            text="Organizador de Archivos", 
            font=("Segoe UI", 32, "bold"),
            text_color=self.color_primary
        ).pack(pady=20)

        # Contenido principal
        main_frame = ctk.CTkScrollableFrame(self.tab_procesar, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

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

        # --- SECCIÓN 2: ORIGEN ---
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

        # --- SECCIÓN 3: CLASIFICACIÓN ---
        clasificacion_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        clasificacion_frame.pack(fill="x", pady=(0, 25), padx=20)
        
        ctk.CTkLabel(
            clasificacion_frame,
            text="Clasificación y Datos",
            font=("Segoe UI", 16, "bold"),
            text_color=self.color_primary
        ).pack(anchor="w", pady=(0, 15))
        
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

        ctk.CTkLabel(
            clasificacion_frame, text="Categoría:", 
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(0, 6))
        
        self.combobox_cat = ctk.CTkComboBox(
            clasificacion_frame, 
            values=["Casos", "Laboratorio - Equipo", "Cursos", "Otras"],
            font=("Segoe UI", 12),
            height=40,
            border_width=2,
            border_color=self.color_primary,
            fg_color=self.color_secondary,
            corner_radius=8,
            dropdown_font=("Segoe UI", 12)
        )
        self.combobox_cat.set("Casos")
        self.combobox_cat.pack(fill="x", pady=(0, 25))

        # --- BOTÓN DE PROCESAMIENTO ---
        self.btn_procesar = ctk.CTkButton(
            main_frame, text="ORGANIZAR Y MOVER ARCHIVOS", 
            height=50,
            font=("Segoe UI", 14, "bold"),
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=10,
            command=self.mostrar_confirmacion
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

    def _crear_tab_historial(self):
        """Crea la pestaña de historial"""
        header_frame = ctk.CTkFrame(self.tab_historial, fg_color=self.color_secondary, corner_radius=0)
        header_frame.pack(fill="x", pady=0)
        
        ctk.CTkLabel(
            header_frame, 
            text="Historial de Lotes", 
            font=("Segoe UI", 28, "bold"),
            text_color=self.color_primary
        ).pack(pady=20)

        # Botones de acción
        btn_frame = ctk.CTkFrame(self.tab_historial, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame, text="Actualizar", 
            command=self._actualizar_historial,
            font=("Segoe UI", 11, "bold"),
            height=35,
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame, text="Limpiar Historial", 
            command=self.limpiar_historial,
            font=("Segoe UI", 11, "bold"),
            height=35,
            fg_color=self.color_danger,
            hover_color="#6b4545",
            corner_radius=8
        ).pack(side="left")

        # Textbox con historial
        self.textbox_historial = ctk.CTkTextbox(
            self.tab_historial, 
            font=("Segoe UI", 12),
            fg_color=self.color_secondary,
            text_color="#ffffff",
            border_width=2,
            border_color=self.color_primary,
            corner_radius=8
        )
        self.textbox_historial.pack(fill="both", expand=True, padx=20, pady=20)
        self.textbox_historial.configure(state="disabled")
        
        self._actualizar_historial()

    def _crear_tab_buscador(self):
        """Crea la pestaña de buscador de archivos"""
        header_frame = ctk.CTkFrame(self.tab_buscador, fg_color=self.color_secondary, corner_radius=0)
        header_frame.pack(fill="x", pady=0)
        
        ctk.CTkLabel(
            header_frame, 
            text="Buscar Archivos", 
            font=("Segoe UI", 28, "bold"),
            text_color=self.color_primary
        ).pack(pady=20)

        # Marco de búsqueda
        search_frame = ctk.CTkFrame(self.tab_buscador, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            search_frame, text="Buscar por nombre de archivo:", 
            font=("Segoe UI", 13, "bold"),
            text_color="#d4c5b9"
        ).pack(anchor="w", pady=(0, 8))
        
        self.entry_buscar = ctk.CTkEntry(
            search_frame, placeholder_text="Escribe el nombre del archivo...",
            font=("Segoe UI", 12),
            height=40,
            border_width=2,
            border_color=self.color_primary,
            fg_color=self.color_secondary,
            corner_radius=8
        )
        self.entry_buscar.pack(fill="x", pady=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.buscar_archivos())
        
        btn_frame_buscar = ctk.CTkFrame(search_frame, fg_color="transparent")
        btn_frame_buscar.pack(fill="x", pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame_buscar, text="Buscar", 
            command=self.buscar_archivos,
            font=("Segoe UI", 12, "bold"),
            height=40,
            fg_color=self.color_primary,
            hover_color="#3d6375",
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame_buscar, text="Limpiar", 
            command=self.limpiar_busqueda,
            font=("Segoe UI", 12, "bold"),
            height=40,
            fg_color=self.color_warning,
            hover_color="#8a6f4a",
            corner_radius=8
        ).pack(side="left")

        # Frame para resultados con scroll
        results_container = ctk.CTkFrame(self.tab_buscador, fg_color="transparent")
        results_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            results_container, text="Resultados (Haz clic en un resultado para abrir):", 
            font=("Segoe UI", 12, "bold"),
            text_color=self.color_primary
        ).pack(anchor="w", pady=(0, 10))
        
        # Frame scrollable para resultados
        self.scroll_resultados = ctk.CTkScrollableFrame(
            results_container,
            fg_color=self.color_secondary,
            corner_radius=8,
            border_width=2,
            border_color=self.color_primary
        )
        self.scroll_resultados.pack(fill="both", expand=True)
        
        # Mensaje inicial
        self.lbl_resultado_vacio = ctk.CTkLabel(
            self.scroll_resultados,
            text="Escribe un nombre de archivo para buscar...",
            font=("Segoe UI", 11),
            text_color="#9d8b7e"
        )
        self.lbl_resultado_vacio.pack(pady=20)

    def actualizar_preview(self):
        """Función vacía - preview eliminada"""
        pass

    def mostrar_confirmacion(self):
        """Muestra un diálogo de confirmación con la ruta"""
        fecha = self.entry_fecha.get().strip()
        caso = self.entry_caso.get().strip()
        categoria = self.combobox_cat.get()
        
        if not self.path_origen:
            messagebox.showerror("Error", "No has seleccionado la carpeta de origen.")
            return
        
        if not caso or not fecha:
            messagebox.showerror("Error", "Completa todos los campos.")
            return
        
        if not self._validar_fecha(fecha):
            messagebox.showerror("Error", "Formato de fecha inválido. Usa: DD-MM-AAAA")
            return
        
        # Obtener archivos a mover
        if isinstance(self.path_origen, list):
            archivos = [os.path.basename(f) for f in self.path_origen]
        else:
            archivos = self._obtener_archivos(self.path_origen)
        
        if not archivos:
            messagebox.showwarning("Advertencia", "No hay archivos en la carpeta de origen.")
            return
        
        nombre_carpeta = f"{fecha}_{caso}"
        # Normalizar categoría para la carpeta
        cat_normalizada = categoria.lower().replace(" - ", "-")
        ruta_final = os.path.join(self.ruta_destino_base, cat_normalizada, nombre_carpeta)
        
        # Detectar conflictos
        conflictos = []
        if os.path.exists(ruta_final):
            archivos_existentes = os.listdir(ruta_final)
            for archivo in archivos:
                if archivo in archivos_existentes:
                    conflictos.append(archivo)
        
        msg = f"""CONFIRMACIÓN DE MOVIMIENTO

Destino Final:
{ruta_final}

Cantidad de archivos a mover: {len(archivos)}
"""
        
        if conflictos:
            msg += f"\nADVERTENCIA - Archivos que serán sobrescritos:\n"
            for i, conf in enumerate(conflictos[:5], 1):
                msg += f"  {i}. {conf}\n"
            if len(conflictos) > 5:
                msg += f"  ... y {len(conflictos) - 5} más\n"
        
        msg += "\n¿Deseas continuar?"
        
        if messagebox.askyesno("Confirmar Movimiento", msg):
            self.procesar_lote_thread()

    def procesar_lote_thread(self):
        """Inicia el procesamiento en un hilo separado"""
        if not self.procesando:
            thread = threading.Thread(target=self.procesar_lote)
            thread.daemon = True
            thread.start()

    def procesar_lote(self):
        """Mueve los archivos y registra el historial"""
        self.procesando = True
        self.btn_procesar.configure(state="disabled")
        
        archivos_movidos = []
        
        try:
            if self.ruta_destino_base == "No configurada":
                messagebox.showwarning("Atención", "Configura la Carpeta de Destino.")
                return

            fecha = self.entry_fecha.get().strip()
            caso = self.entry_caso.get().strip()
            categoria = self.combobox_cat.get()
            
            if not self._validar_fecha(fecha):
                messagebox.showerror("Error", "Formato de fecha inválido.")
                return

            archivos = self._obtener_archivos(self.path_origen)
            
            if not archivos:
                messagebox.showwarning("Advertencia", "No hay archivos para mover.")
                return

            nombre_carpeta = f"{fecha}_{caso}"
            # Normalizar categoría para la carpeta
            cat_normalizada = categoria.lower().replace(" - ", "-")
            ruta_final = os.path.join(self.ruta_destino_base, cat_normalizada, nombre_carpeta)

            if not os.path.exists(ruta_final):
                os.makedirs(ruta_final)

            # Mover archivos - maneja tanto carpetas como archivos individuales
            if isinstance(self.path_origen, list):
                # Archivos individuales seleccionados
                archivos_a_mover = self.path_origen
            else:
                # Carpeta completa
                archivos_a_mover = [os.path.join(self.path_origen, f) for f in archivos]
            
            for idx, archivo_ruta in enumerate(archivos_a_mover):
                try:
                    nombre_archivo = os.path.basename(archivo_ruta)
                    
                    # Si viene de una lista, ya tiene la ruta completa
                    if isinstance(self.path_origen, list):
                        ruta_origen = archivo_ruta
                    else:
                        ruta_origen = archivo_ruta
                    
                    ruta_destino = os.path.join(ruta_final, nombre_archivo)
                    shutil.move(ruta_origen, ruta_destino)
                    archivos_movidos.append({
                        "nombre": nombre_archivo,
                        "ruta_destino": ruta_destino
                    })
                    
                    progreso = (idx + 1) / len(archivos_a_mover)
                    self.progress_bar.set(progreso)
                    self.lbl_estado.configure(
                        text=f"Moviendo: {nombre_archivo} ({idx + 1}/{len(archivos_a_mover)})"
                    )
                    self.update()
                except Exception as e:
                    logging.error(f"Error al mover {nombre_archivo}: {e}")

            # Guardar en historial
            self.guardar_en_historial(
                fecha=fecha,
                caso=caso,
                categoria=categoria,
                cantidad=len(archivos_movidos),
                ruta_destino=ruta_final,
                archivos=archivos_movidos
            )

            # Mensaje de éxito detallado
            msg_exito = f"""PROCESO COMPLETADO EXITOSAMENTE

Información del Lote:
• Caso: {caso}
• Fecha: {fecha}
• Categoría: {categoria}
• Archivos movidos: {len(archivos_movidos)}
• Destino: {ruta_final}

El lote ha sido registrado en el historial."""
            
            messagebox.showinfo("Éxito", msg_exito)
            logging.info(f"Lote completado: {len(archivos_movidos)} archivos en {ruta_final}")
            
            # Resetear
            self.entry_caso.delete(0, 'end')
            self.lbl_origen.configure(text="No seleccionada", text_color=self.color_warning)
            self.lbl_contador.configure(text="")
            self.path_origen = ""
            self.progress_bar.set(0)
            self.lbl_estado.configure(text="")
            self.actualizar_preview()

        except Exception as e:
            messagebox.showerror("Error de Sistema", f"Error: {e}")
            logging.error(f"Error en procesar_lote: {e}")
        
        finally:
            self.procesando = False
            self.btn_procesar.configure(state="normal")

    def cargar_historial(self):
        """Carga el historial desde JSON"""
        try:
            if os.path.exists(self.archivo_historial):
                with open(self.archivo_historial, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error cargando historial: {e}")
        return []

    def guardar_en_historial(self, fecha, caso, categoria, cantidad, ruta_destino, archivos):
        """Guarda un lote en el historial"""
        try:
            registro = {
                "timestamp": datetime.now().isoformat(),
                "fecha_caso": fecha,
                "nombre_caso": caso,
                "categoria": categoria,
                "cantidad_archivos": cantidad,
                "ruta_destino": ruta_destino,
                "archivos_movidos": archivos
            }
            
            self.historial.append(registro)
            
            with open(self.archivo_historial, "w", encoding="utf-8") as f:
                json.dump(self.historial, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Registro guardado en historial: {caso}")
            self._actualizar_historial()
            
        except Exception as e:
            logging.error(f"Error guardando historial: {e}")
            messagebox.showerror("Error", f"No se pudo guardar el historial: {e}")

    def _actualizar_historial(self):
        """Actualiza la visualización del historial"""
        try:
            self.textbox_historial.configure(state="normal")
            self.textbox_historial.delete("0.0", "end")
            
            if not self.historial:
                self.textbox_historial.insert("0.0", "No hay registros en el historial.")
            else:
                texto = "HISTORIAL DE LOTES PROCESADOS\n" + "="*100 + "\n\n"
                
                for i, registro in enumerate(reversed(self.historial), 1):
                    # Manejo de timestamps antiguos sin este campo
                    if "timestamp" in registro:
                        timestamp = datetime.fromisoformat(registro["timestamp"])
                        fecha_proc = timestamp.strftime('%d de %B de %Y a las %H:%M:%S')
                    else:
                        fecha_proc = "Fecha no disponible"
                    
                    texto += f"LOTE #{len(self.historial) - i + 1}\n"
                    texto += f"─" * 100 + "\n"
                    texto += f"Fecha de Procesamiento:  {fecha_proc}\n"
                    texto += f"Nombre del Caso:  {registro.get('nombre_caso', 'S/N').upper()}\n"
                    texto += f"Categoría:  {registro.get('categoria', 'S/N').upper()}\n"
                    texto += f"Cantidad de Archivos:  {registro.get('cantidad_archivos', '?')}\n"
                    texto += f"Ubicación Final:  {registro.get('ruta_destino', 'No disponible')}\n"
                    texto += "\n"
                
                self.textbox_historial.insert("0.0", texto)
            
            self.textbox_historial.configure(state="disabled")
        except Exception as e:
            logging.error(f"Error actualizando historial: {e}")

    def limpiar_historial(self):
        """Limpia el historial"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres limpiar el historial?"):
            try:
                self.historial = []
                with open(self.archivo_historial, "w", encoding="utf-8") as f:
                    json.dump([], f)
                self._actualizar_historial()
                messagebox.showinfo("Éxito", "Historial limpio")
            except Exception as e:
                messagebox.showerror("Error", f"Error limpiando historial: {e}")

    def buscar_archivos(self):
        """Busca archivos en todas las carpetas del destino"""
        termino_busqueda = self.entry_buscar.get().strip().lower()
        
        # Limpiar resultados anteriores
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
        
        self.resultados_busqueda = []
        
        if not termino_busqueda:
            self.lbl_resultado_vacio = ctk.CTkLabel(
                self.scroll_resultados,
                text="Escribe un nombre de archivo para buscar...",
                font=("Segoe UI", 11),
                text_color="#9d8b7e"
            )
            self.lbl_resultado_vacio.pack(pady=20)
            return
        
        if self.ruta_destino_base == "No configurada":
            lbl_error = ctk.CTkLabel(
                self.scroll_resultados,
                text="Primero debes configurar la carpeta de destino.",
                font=("Segoe UI", 11),
                text_color="#e74c3c"
            )
            lbl_error.pack(pady=20)
            return
        
        try:
            for raiz, directorios, archivos in os.walk(self.ruta_destino_base):
                for archivo in archivos:
                    if termino_busqueda in archivo.lower():
                        ruta_completa = os.path.join(raiz, archivo)
                        self.resultados_busqueda.append(ruta_completa)
            
            if not self.resultados_busqueda:
                lbl_no_encontrado = ctk.CTkLabel(
                    self.scroll_resultados,
                    text=f"No se encontraron archivos con '{termino_busqueda}'",
                    font=("Segoe UI", 11),
                    text_color="#e74c3c"
                )
                lbl_no_encontrado.pack(pady=20)
            else:
                # Mostrar cada resultado como botón clickeable
                for i, ruta in enumerate(self.resultados_busqueda, 1):
                    nombre_archivo = os.path.basename(ruta)
                    carpeta_padre = os.path.dirname(ruta)
                    
                    # Frame para cada resultado
                    resultado_frame = ctk.CTkFrame(
                        self.scroll_resultados,
                        fg_color="#3a4655",
                        corner_radius=8,
                        border_width=1,
                        border_color=self.color_primary
                    )
                    resultado_frame.pack(fill="x", padx=10, pady=8)
                    
                    # Info del archivo
                    info_frame = ctk.CTkFrame(resultado_frame, fg_color="transparent")
                    info_frame.pack(fill="x", padx=15, pady=10, side="left", expand=True)
                    
                    ctk.CTkLabel(
                        info_frame,
                        text=f"#{i} {nombre_archivo}",
                        font=("Segoe UI", 11, "bold"),
                        text_color="#d4c5b9"
                    ).pack(anchor="w")
                    
                    ctk.CTkLabel(
                        info_frame,
                        text=f"{carpeta_padre}",
                        font=("Segoe UI", 9),
                        text_color="#9d8b7e"
                    ).pack(anchor="w", pady=(2, 0))
                    
                    # Botón para abrir
                    ctk.CTkButton(
                        resultado_frame,
                        text="Abrir",
                        font=("Segoe UI", 10, "bold"),
                        height=32,
                        width=80,
                        fg_color=self.color_success,
                        hover_color="#4a7359",
                        corner_radius=6,
                        command=lambda r=ruta: self._abrir_carpeta(os.path.dirname(r))
                    ).pack(side="right", padx=15, pady=10)
        
        except Exception as e:
            lbl_error = ctk.CTkLabel(
                self.scroll_resultados,
                text=f"Error en la búsqueda: {e}",
                font=("Segoe UI", 11),
                text_color="#e74c3c"
            )
            lbl_error.pack(pady=20)
            logging.error(f"Error buscando archivos: {e}")

    def abrir_ultima_ruta_buscada(self):
        """Abre la ubicación del último resultado de búsqueda"""
        if self.ultima_ruta_buscada and os.path.exists(self.ultima_ruta_buscada):
            self._abrir_carpeta(self.ultima_ruta_buscada)
        else:
            messagebox.showwarning("Advertencia", "No hay resultados para abrir.")

    def limpiar_busqueda(self):
        """Limpia los resultados de búsqueda"""
        self.entry_buscar.delete(0, "end")
        self.resultados_busqueda = []
        self.ultima_ruta_buscada = None
        
        # Limpiar widgets
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
        
        self.lbl_resultado_vacio = ctk.CTkLabel(
            self.scroll_resultados,
            text="Escribe un nombre de archivo para buscar...",
            font=("Segoe UI", 11),
            text_color="#9d8b7e"
        )
        self.lbl_resultado_vacio.pack(pady=20)

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

    def _obtener_archivos(self, ruta=None):
        """Retorna todos los archivos (excepto carpetas) de una ruta o lista de archivos"""
        try:
            # Si path_origen es una lista de archivos individuales
            if isinstance(self.path_origen, list):
                return [os.path.basename(f) for f in self.path_origen]
            
            # Si es una carpeta
            if ruta is None:
                ruta = self.path_origen
            
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
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
            logging.error(f"Error al abrir carpeta: {e}")

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
                self.actualizar_preview()
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
        """Selecciona la carpeta o archivos individuales"""
        from tkinter import Toplevel
        
        ventana_seleccion = Toplevel(self)
        ventana_seleccion.title("Seleccionar Origen")
        ventana_seleccion.geometry("400x200")
        ventana_seleccion.resizable(False, False)
        ventana_seleccion.attributes('-topmost', True)
        
        try:
            ruta_icono = ruta_recurso("camara.ico")
            if os.path.exists(ruta_icono):
                ventana_seleccion.iconbitmap(default=ruta_icono)
        except Exception as e:
            logging.error(f"Error al cargar icono en ventana emergente: {e}")
        
        ventana_seleccion.update_idletasks()
        x = (ventana_seleccion.winfo_screenwidth() // 2) - (400 // 2)
        y = (ventana_seleccion.winfo_screenheight() // 2) - (200 // 2)
        ventana_seleccion.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            ventana_seleccion,
            text="¿Qué deseas seleccionar?",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)
        
        def seleccionar_carpeta():
            ventana_seleccion.destroy()
            ruta = filedialog.askdirectory(title="Selecciona la carpeta con los archivos")
            if ruta:
                self.path_origen = ruta
                nombre_carpeta = os.path.basename(ruta)
                archivos = self._obtener_archivos(ruta)
                self.lbl_origen.configure(text=f"✓ Carpeta: {nombre_carpeta}", text_color=self.color_success)
                self.lbl_contador.configure(text=f"{len(archivos)} archivo(s) encontrado(s)")
        
        def seleccionar_archivos():
            ventana_seleccion.destroy()
            archivos = filedialog.askopenfilenames(title="Selecciona los archivos que deseas mover")
            if archivos:
                self.path_origen = list(archivos)
                cantidad = len(archivos)
                self.lbl_origen.configure(text=f"✓ {cantidad} archivo(s) seleccionado(s)", text_color=self.color_success)
                self.lbl_contador.configure(text=f"{cantidad} archivo(s) seleccionado(s)")
        
        ctk.CTkButton(
            ventana_seleccion,
            text="Seleccionar Carpeta Completa",
            command=seleccionar_carpeta,
            font=("Segoe UI", 12, "bold"),
            height=40,
            fg_color=self.color_primary,
            hover_color="#3d6375"
        ).pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            ventana_seleccion,
            text="Seleccionar Archivos Individuales",
            command=seleccionar_archivos,
            font=("Segoe UI", 12, "bold"),
            height=40,
            fg_color=self.color_success,
            hover_color="#4a7359"
        ).pack(fill="x", padx=20, pady=10)

    def abrir_carpeta_origen(self):
        """Abre la carpeta de origen en el explorador"""
        if self.path_origen:
            self._abrir_carpeta(self.path_origen)
        else:
            messagebox.showwarning("Atención", "Primero debes seleccionar una carpeta de origen.")


if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()