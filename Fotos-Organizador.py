import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
from datetime import datetime
import threading
import platform
import subprocess
import json

# Configuración visual global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OrganizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Organizador de Archivos")
        
        # LÓGICA PARA CENTRAR VENTANA
        ancho_ventana = 1100
        alto_ventana = 900
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla // 2) - (ancho_ventana // 2)
        y = (alto_pantalla // 2) - (alto_ventana // 2)
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        
        # Paleta de Colores
        self.color_bg = "#1a1c1e"
        self.color_card = "#2d3238"
        self.color_primary = "#4b7a99"
        self.color_success = "#4e9a06"
        self.color_danger = "#a40000"
        self.color_folder_highlight = "#3e4a56"

        self.archivo_config = "config_ruta.txt"
        self.archivo_historial = "historial_lotes.json"
        self.ruta_destino_base = self.cargar_configuracion()
        self.historial = self.cargar_historial()
        self.path_origen = ""

        # Interfaz
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, segmented_button_fg_color="#212529", 
                                      segmented_button_selected_color=self.color_primary,
                                      segmented_button_unselected_hover_color="#343a40")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_procesar = self.tabview.add(" 📁 PROCESAR ")
        self.tab_historial = self.tabview.add(" 📜 HISTORIAL ")
        self.tab_buscador = self.tabview.add(" 🔍 BUSCADOR ")
        
        self._crear_tab_procesamiento()
        self._crear_tab_historial()
        self._crear_tab_buscador()

    # --- FUNCIÓN PARA QUITAR BARRA MANTENIENDO SCROLL ---
    def _quitar_barra(self, widget):
        """Oculta la barra de scroll de un CTkScrollableFrame o CTkTextbox"""
        if hasattr(widget, "_scrollbar"):
            widget._scrollbar.grid_forget() # Quita el espacio de la barra
            widget._scrollbar.configure(width=0) # Anula su tamaño

    def buscar_archivos(self, event=None):
        termino = self.entry_busqueda.get().lower().strip()
        if len(termino) < 2:
            for widget in self.scroll_resultados.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.scroll_resultados, text="✍️ Escribe al menos 2 letras...", text_color="#6c757d").pack(pady=40)
            return 
        threading.Thread(target=self._ejecutar_busqueda_recursiva, args=(termino,), daemon=True).start()

    def _ejecutar_busqueda_recursiva(self, termino):
        self.after(0, lambda: [w.destroy() for w in self.scroll_resultados.winfo_children()])
        encontrados = 0
        vistos = set()
        for lote in self.historial:
            ruta_lote = lote.get("ruta_destino", "")
            if os.path.exists(ruta_lote):
                if termino in lote.get("nombre_caso", "").lower():
                    self.after(0, self._agregar_resultado_carpeta, lote.get("nombre_caso", "S/N"), ruta_lote)
                    vistos.add(ruta_lote)
                    encontrados += 1

        if os.path.exists(self.ruta_destino_base) and self.ruta_destino_base != "No configurada":
            for root, dirs, files in os.walk(self.ruta_destino_base):
                dirs[:] = [d for d in dirs if d.lower() not in ['system volume information', '$recycle.bin']]
                for d in dirs:
                    ruta_completa = os.path.join(root, d)
                    if termino in d.lower() and ruta_completa not in vistos:
                        self.after(0, self._agregar_resultado_carpeta, d, ruta_completa)
                        encontrados += 1
                for f in files:
                    if termino in f.lower():
                        ruta_archivo = os.path.join(root, f)
                        self.after(0, self._agregar_resultado_archivo, f, ruta_archivo)
                        encontrados += 1
                if encontrados > 100: break

        if encontrados == 0:
            self.after(0, lambda: ctk.CTkLabel(self.scroll_resultados, 
                text="⚠️ No se encontraron coincidencias.", text_color="#e74c3c").pack(pady=50))

    def _agregar_resultado_carpeta(self, nombre, ruta):
        item = ctk.CTkFrame(self.scroll_resultados, fg_color=self.color_folder_highlight, corner_radius=10)
        item.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(item, text=f"📁 CARPETA: {nombre.upper()}", font=("Segoe UI", 12, "bold")).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(item, text="ABRIR", width=100, command=lambda: self._abrir_carpeta(ruta)).pack(side="right", padx=15)

    def _agregar_resultado_archivo(self, nombre, ruta_completa):
        item = ctk.CTkFrame(self.scroll_resultados, fg_color="#2d3238", corner_radius=8)
        item.pack(fill="x", pady=3, padx=10)
        ctk.CTkLabel(item, text=f"📄 ARCHIVO: {nombre}", font=("Segoe UI", 11)).pack(side="left", padx=20, pady=8)
        ctk.CTkButton(item, text="VER ARCHIVO", width=100, height=28, fg_color="transparent", border_width=1, 
                     command=lambda: self._abrir_carpeta(ruta_completa)).pack(side="right", padx=15)

    def _mover_con_seguridad(self, origen, destino_carpeta, nombre_archivo):
        destino_final = os.path.join(destino_carpeta, nombre_archivo)
        if os.path.exists(destino_final):
            base, ext = os.path.splitext(nombre_archivo)
            timestamp = datetime.now().strftime("%H%M%S")
            nuevo_nombre = f"{base}_{timestamp}{ext}"
            destino_final = os.path.join(destino_carpeta, nuevo_nombre)
        shutil.move(origen, destino_final)

    def guardar_historial_json(self):
        with open(self.archivo_historial, "w", encoding="utf-8") as f:
            json.dump(self.historial, f, indent=2)

    def _crear_tab_procesamiento(self):
        container = ctk.CTkScrollableFrame(self.tab_procesar, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20)
        self._quitar_barra(container) # <--- OCULTAR BARRA
        
        header_rutas = ctk.CTkLabel(container, text="CONFIGURACIÓN DE RUTAS", font=("Segoe UI", 14, "bold"), text_color=self.color_primary)
        header_rutas.pack(anchor="w", pady=(0, 10))
        
        f_dest = ctk.CTkFrame(container, fg_color=self.color_card, corner_radius=15, border_width=1, border_color="#3f444b")
        f_dest.pack(fill="x", pady=(0, 15))
        
        lbl_dest_title = ctk.CTkLabel(f_dest, text="📍 Carpeta Destino Principal", font=("Segoe UI", 13, "bold"))
        lbl_dest_title.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.lbl_destino = ctk.CTkLabel(f_dest, text=self.ruta_destino_base, font=("Consolas", 12), text_color="#adb5bd", wraplength=800)
        self.lbl_destino.pack(pady=10, padx=20, anchor="w")
        
        f_btns_dest = ctk.CTkFrame(f_dest, fg_color="transparent")
        f_btns_dest.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(f_btns_dest, text="📂 ABRIR CARPETA RAÍZ", fg_color="#343a40", hover_color="#495057", 
                     command=lambda: self._abrir_carpeta(self.ruta_destino_base), height=32).pack(side="left", padx=(0, 10))

        ctk.CTkButton(f_btns_dest, text="CAMBIAR RUTA", fg_color="transparent", border_width=1, 
                     hover_color="#343a40", command=self.configurar_destino, height=32).pack(side="left")
        
        f_orig = ctk.CTkFrame(container, fg_color=self.color_card, corner_radius=15, border_width=1, border_color="#3f444b")
        f_orig.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(f_orig, text="📸 Carpeta de Origen", font=("Segoe UI", 13, "bold")).pack(pady=(10, 0), padx=20, anchor="w")
        self.lbl_origen = ctk.CTkLabel(f_orig, text="Seleccione el origen...", font=("Segoe UI", 12), text_color="orange")
        self.lbl_origen.pack(pady=10, padx=20, anchor="w")
        ctk.CTkButton(f_orig, text="SELECCIONAR CARPETA", fg_color=self.color_primary, font=("Segoe UI", 12, "bold"), 
                     command=self.seleccionar_origen, height=40).pack(pady=(0, 15), padx=20, fill="x")
        
        header_datos = ctk.CTkLabel(container, text="DETALLES DEL PROCESAMIENTO", font=("Segoe UI", 14, "bold"), text_color=self.color_primary)
        header_datos.pack(anchor="w", pady=(10, 10))
        
        self.entry_caso = ctk.CTkEntry(container, placeholder_text="👤 Nombre del Paciente o Caso...", height=50, font=("Segoe UI", 15))
        self.entry_caso.pack(fill="x", pady=10)
        
        self.combobox_cat = ctk.CTkComboBox(container, values=["Casos", "Laboratorio - Equipo", "Cursos", "Otros"], height=45, font=("Segoe UI", 14))
        self.combobox_cat.set("Casos")
        self.combobox_cat.pack(fill="x", pady=10)
        
        self.btn_procesar = ctk.CTkButton(container, text="ORGANIZAR AHORA", height=60, font=("Segoe UI", 18, "bold"), 
                                        fg_color=self.color_success, hover_color="#3d7a05", command=self.procesar_lote_thread)
        self.btn_procesar.pack(fill="x", pady=40)
        
        self.progress_bar = ctk.CTkProgressBar(container, height=12, progress_color=self.color_primary)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def _crear_tab_historial(self):
        top_f = ctk.CTkFrame(self.tab_historial, fg_color="transparent")
        top_f.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(top_f, text="ÚLTIMOS MOVIMIENTOS", font=("Segoe UI", 20, "bold")).pack(side="left")
        ctk.CTkButton(top_f, text="🗑️ BORRAR HISTORIAL", fg_color="#441111", width=150, height=35, command=self.limpiar_historial).pack(side="right")
        ctk.CTkButton(top_f, text="🔄 ACTUALIZAR", fg_color=self.color_card, width=120, height=35, command=self._actualizar_historial).pack(side="right", padx=10)
        
        self.textbox_historial = ctk.CTkTextbox(self.tab_historial, font=("Segoe UI", 16), border_width=2, border_color="#3f444b", corner_radius=15)
        self.textbox_historial.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        self._quitar_barra(self.textbox_historial) # <--- OCULTAR BARRA
        self._actualizar_historial()

    def _crear_tab_buscador(self):
        main_f = ctk.CTkFrame(self.tab_buscador, fg_color="transparent")
        main_f.pack(fill="both", expand=True, padx=40, pady=20)
        ctk.CTkLabel(main_f, text="ENCUENTRA ARCHIVOS O CARPETAS", font=("Segoe UI", 22, "bold")).pack(pady=(10, 20))
        
        self.entry_busqueda = ctk.CTkEntry(main_f, placeholder_text="Escriba nombre de paciente o archivo...", height=50, font=("Segoe UI", 16))
        self.entry_busqueda.pack(fill="x", pady=10)
        self.entry_busqueda.bind("<KeyRelease>", self.buscar_archivos) 
        
        self.scroll_resultados = ctk.CTkScrollableFrame(main_f, label_text=" RESULTADOS DE BÚSQUEDA REAL ", fg_color="#1e2227", corner_radius=15)
        self.scroll_resultados.pack(fill="both", expand=True, pady=20)
        self._quitar_barra(self.scroll_resultados) # <--- OCULTAR BARRA

    def _actualizar_historial(self):
        self.textbox_historial.configure(state="normal")
        self.textbox_historial.delete("0.0", "end")
        if not self.historial:
            self.textbox_historial.insert("end", "\n   No hay registros en el historial.")
        else:
            for reg in reversed(self.historial):
                self.textbox_historial.insert("end", f" ➜ {reg['nombre_caso'].upper()}\n   📍 {reg['ruta_destino']}\n {'—'*60}\n\n")
        self.textbox_historial.configure(state="disabled")

    def cargar_configuracion(self):
        if os.path.exists(self.archivo_config):
            with open(self.archivo_config, "r", encoding="utf-8") as f: return f.read().strip()
        return "No configurada"

    def cargar_historial(self):
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, "r", encoding="utf-8") as f: return json.load(f)
            except: return []
        return []

    def configurar_destino(self):
        ruta = filedialog.askdirectory()
        if ruta:
            with open(self.archivo_config, "w", encoding="utf-8") as f: f.write(ruta)
            self.ruta_destino_base = ruta
            self.lbl_destino.configure(text=ruta)

    def seleccionar_origen(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.path_origen = ruta
            archivos = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
            self.lbl_origen.configure(text=f"✅ {len(archivos)} archivos encontrados", text_color="#2ecc71")

    def procesar_lote_thread(self):
        if not self.path_origen or not self.entry_caso.get() or self.ruta_destino_base == "No configurada":
            messagebox.showerror("Error", "Faltan datos o configurar la ruta de destino."); return
        threading.Thread(target=self.procesar_lote, daemon=True).start()

    def procesar_lote(self):
        self.btn_procesar.configure(state="disabled", text="PROCESANDO...")
        try:
            caso = "".join([c if c not in '<>:"/\\|?*' else "_" for c in self.entry_caso.get().strip()])
            cat_limpia = self.combobox_cat.get().replace("/", "-")
            fecha = datetime.now().strftime("%d-%m-%Y")
            ruta_final = os.path.join(self.ruta_destino_base, cat_limpia, f"{fecha}_{caso}")
            os.makedirs(ruta_final, exist_ok=True)
            todos_archivos = [f for f in os.listdir(self.path_origen) if os.path.isfile(os.path.join(self.path_origen, f))]
            for i, nombre in enumerate(todos_archivos):
                self._mover_con_seguridad(os.path.join(self.path_origen, nombre), ruta_final, nombre)
                self.progress_bar.set((i+1)/len(todos_archivos))
            self.historial.append({"fecha_caso": fecha, "nombre_caso": caso, "categoria": cat_limpia, "ruta_destino": ruta_final})
            self.guardar_historial_json()
            messagebox.showinfo("Éxito", f"Organizado en: {cat_limpia}")
            self.after(0, self._actualizar_historial)
            self.entry_caso.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_procesar.configure(state="normal", text="ORGANIZAR AHORA")
            self.progress_bar.set(0)

    def _abrir_carpeta(self, ruta):
        if not ruta or not os.path.exists(ruta):
            messagebox.showwarning("Aviso", "La ruta no existe."); return
        try:
            if platform.system() == "Windows":
                if os.path.isfile(ruta):
                    subprocess.run(['explorer', '/select,', os.path.normpath(ruta)])
                else:
                    os.startfile(ruta)
            elif platform.system() == "Darwin": subprocess.Popen(["open", ruta])
            else: subprocess.Popen(["xdg-open", ruta])
        except: pass

    def limpiar_historial(self):
        if messagebox.askyesno("Confirmar", "¿Deseas borrar el historial visual?"):
            self.historial = []
            if os.path.exists(self.archivo_historial): os.remove(self.archivo_historial)
            self._actualizar_historial()

if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()