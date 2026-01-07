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

        self.title("Organizador de Archivos Pro - V2.0")
        self.geometry("1100x900")
        
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

        # Contenedor Principal
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

    # --- DISEÑO: TAB PROCESAMIENTO ---
    def _crear_tab_procesamiento(self):
        container = ctk.CTkScrollableFrame(self.tab_procesar, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20)

        # Sección de Rutas
        header_rutas = ctk.CTkLabel(container, text="CONFIGURACIÓN DE RUTAS", font=("Segoe UI", 14, "bold"), text_color=self.color_primary)
        header_rutas.pack(anchor="w", pady=(0, 10))

        # Tarjeta Destino
        f_dest = ctk.CTkFrame(container, fg_color=self.color_card, corner_radius=15, border_width=1, border_color="#3f444b")
        f_dest.pack(fill="x", pady=(0, 15))
        
        lbl_dest_title = ctk.CTkLabel(f_dest, text="📍 Carpeta Destino", font=("Segoe UI", 13, "bold"))
        lbl_dest_title.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.lbl_destino = ctk.CTkLabel(f_dest, text=self.ruta_destino_base, font=("Consolas", 12), text_color="#adb5bd", wraplength=800)
        self.lbl_destino.pack(pady=10, padx=20, anchor="w")
        
        btn_dest = ctk.CTkButton(f_dest, text="CAMBIAR RUTA", fg_color="transparent", border_width=1, hover_color="#343a40", 
                                 command=self.configurar_destino, height=32)
        btn_dest.pack(pady=(0, 15), padx=20, anchor="e")

        # Tarjeta Origen
        f_orig = ctk.CTkFrame(container, fg_color=self.color_card, corner_radius=15, border_width=1, border_color="#3f444b")
        f_orig.pack(fill="x", pady=(0, 30))
        
        lbl_orig_title = ctk.CTkLabel(f_orig, text="📸 Carpeta de Origen", font=("Segoe UI", 13, "bold"))
        lbl_orig_title.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.lbl_origen = ctk.CTkLabel(f_orig, text="Seleccione la carpeta donde están los archivos actuales", font=("Segoe UI", 12), text_color="orange")
        self.lbl_origen.pack(pady=10, padx=20, anchor="w")
        
        btn_orig = ctk.CTkButton(f_orig, text="SELECCIONAR CARPETA", fg_color=self.color_primary, font=("Segoe UI", 12, "bold"),
                                 command=self.seleccionar_origen, height=40)
        btn_orig.pack(pady=(0, 15), padx=20, fill="x")

        # Sección de Datos
        header_datos = ctk.CTkLabel(container, text="DETALLES DEL PROCESAMIENTO", font=("Segoe UI", 14, "bold"), text_color=self.color_primary)
        header_datos.pack(anchor="w", pady=(10, 10))

        f_inputs = ctk.CTkFrame(container, fg_color="transparent")
        f_inputs.pack(fill="x")

        self.entry_caso = ctk.CTkEntry(f_inputs, placeholder_text="👤 Nombre del Paciente o Caso...", height=50, font=("Segoe UI", 15))
        self.entry_caso.pack(fill="x", pady=10)

        self.combobox_cat = ctk.CTkComboBox(f_inputs, values=["Casos", "Laboratorio/Equipo", "Cursos", "Otros"], height=45, font=("Segoe UI", 14))
        self.combobox_cat.set("Casos")
        self.combobox_cat.pack(fill="x", pady=10)

        self.btn_procesar = ctk.CTkButton(container, text="ORGANIZAR AHORA", height=60, font=("Segoe UI", 18, "bold"), 
                                         fg_color=self.color_success, hover_color="#3d7a05", command=self.procesar_lote_thread)
        self.btn_procesar.pack(fill="x", pady=40)
        
        self.progress_bar = ctk.CTkProgressBar(container, height=12, progress_color=self.color_primary)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    # --- DISEÑO: TAB HISTORIAL ---
    def _crear_tab_historial(self):
        top_f = ctk.CTkFrame(self.tab_historial, fg_color="transparent")
        top_f.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(top_f, text="ÚLTIMOS MOVIMIENTOS", font=("Segoe UI", 20, "bold")).pack(side="left")
        ctk.CTkButton(top_f, text="🗑️ BORRAR HISTORIAL", fg_color="#441111", width=150, height=35, command=self.limpiar_historial).pack(side="right")
        ctk.CTkButton(top_f, text="🔄 ACTUALIZAR", fg_color=self.color_card, width=120, height=35, command=self._actualizar_historial).pack(side="right", padx=10)

        self.textbox_historial = ctk.CTkTextbox(self.tab_historial, font=("Segoe UI", 18), border_width=2, border_color="#3f444b", corner_radius=15)
        self.textbox_historial.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        self._actualizar_historial()

    # --- DISEÑO: TAB BUSCADOR ---
    def _crear_tab_buscador(self):
        main_f = ctk.CTkFrame(self.tab_buscador, fg_color="transparent")
        main_f.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(main_f, text="ENCUENTRA ARCHIVOS O CARPETAS", font=("Segoe UI", 22, "bold")).pack(pady=(10, 20))
        
        search_f = ctk.CTkFrame(main_f, fg_color="transparent")
        search_f.pack(fill="x", pady=10)
        
        self.entry_busqueda = ctk.CTkEntry(search_f, placeholder_text="Escriba el nombre del archivo o del paciente...", height=50, font=("Segoe UI", 16))
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.buscar_archivos()) 
        
        btn_search = ctk.CTkButton(search_f, text="🔍 BUSCAR", width=150, height=50, font=("Segoe UI", 14, "bold"), command=self.buscar_archivos)
        btn_search.pack(side="right")

        self.scroll_resultados = ctk.CTkScrollableFrame(main_f, label_text=" RESULTADOS DE BÚSQUEDA ", label_font=("Segoe UI", 13, "bold"), 
                                                        fg_color="#1e2227", corner_radius=15, border_width=1, border_color="#3f444b")
        self.scroll_resultados.pack(fill="both", expand=True, pady=20)

    # --- LÓGICA DE BÚSQUEDA ---
    def buscar_archivos(self):
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
            
        termino = self.entry_busqueda.get().lower().strip()
        if len(termino) < 2: return 

        encontrados = 0
        for lote in self.historial:
            # Carpetas de Casos
            if termino in lote.get("nombre_caso", "").lower():
                encontrados += 1
                item = ctk.CTkFrame(self.scroll_resultados, fg_color=self.color_folder_highlight, corner_radius=10)
                item.pack(fill="x", pady=5, padx=10)
                
                info = f"📁 CARPETA DE CASO: {lote['nombre_caso'].upper()}\n📅 {lote['fecha_caso']} | Categoría: {lote['categoria']}"
                ctk.CTkLabel(item, text=info, justify="left", font=("Segoe UI", 13, "bold")).pack(side="left", padx=20, pady=10)
                
                ctk.CTkButton(item, text="ABRIR", width=100, fg_color=self.color_primary, command=lambda r=lote['ruta_destino']: self._abrir_carpeta(r)).pack(side="right", padx=15)

            # Archivos individuales
            for archivo in lote.get("archivos_movidos", []):
                if termino in archivo.get("nombre", "").lower():
                    encontrados += 1
                    item_arc = ctk.CTkFrame(self.scroll_resultados, fg_color="#2d3238", corner_radius=8)
                    item_arc.pack(fill="x", pady=3, padx=10)
                    
                    info_arc = f"📄 ARCHIVO: {archivo['nombre']}\n📍 Caso: {lote['nombre_caso']}"
                    ctk.CTkLabel(item_arc, text=info_arc, justify="left", font=("Segoe UI", 12)).pack(side="left", padx=20, pady=8)
                    
                    ruta_btn = os.path.dirname(archivo.get("ruta_destino", ""))
                    ctk.CTkButton(item_arc, text="IR A FOTO", width=90, height=28, fg_color="transparent", border_width=1,
                                 command=lambda r=ruta_btn: self._abrir_carpeta(r)).pack(side="right", padx=15)

        if encontrados == 0:
            ctk.CTkLabel(self.scroll_resultados, text="No se encontraron coincidencias.", text_color="#6c757d").pack(pady=40)

    # --- LÓGICA GENERAL ---
    def _actualizar_historial(self):
        self.textbox_historial.configure(state="normal")
        self.textbox_historial.delete("0.0", "end")
        if not self.historial:
            self.textbox_historial.insert("end", "\n   No hay registros de movimientos aún.")
        else:
            for reg in reversed(self.historial):
                self.textbox_historial.insert("end", f" ➜ {reg['nombre_caso'].upper()}\n", "bold")
                self.textbox_historial.insert("end", f"   📅 {reg['fecha_caso']}  |  📂 {reg['categoria']}  |  📦 {reg['cantidad_archivos']} archivos\n")
                self.textbox_historial.insert("end", f"   📍 {reg['ruta_destino']}\n")
                self.textbox_historial.insert("end", " " + "—" * 60 + "\n\n")
        self.textbox_historial.configure(state="disabled")

    def cargar_configuracion(self):
        if os.path.exists(self.archivo_config):
            with open(self.archivo_config, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "No configurada"

    def cargar_historial(self):
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return []
        return []

    def configurar_destino(self):
        ruta = filedialog.askdirectory()
        if ruta:
            with open(self.archivo_config, "w", encoding="utf-8") as f:
                f.write(ruta)
            self.ruta_destino_base = ruta
            self.lbl_destino.configure(text=ruta)

    def seleccionar_origen(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.path_origen = ruta
            archivos = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
            self.lbl_origen.configure(text=f"✅ Carpeta lista: {len(archivos)} archivos encontrados", text_color="#2ecc71")

    def procesar_lote_thread(self):
        if not self.path_origen or not self.entry_caso.get():
            messagebox.showerror("Atención", "Por favor completa el nombre del caso y selecciona el origen."); return
        threading.Thread(target=self.procesar_lote, daemon=True).start()

    def procesar_lote(self):
        self.btn_procesar.configure(state="disabled", text="PROCESANDO...")
        try:
            caso = self.entry_caso.get().strip()
            cat = self.combobox_cat.get()
            fecha = datetime.now().strftime("%d-%m-%Y")
            
            todos_archivos = [f for f in os.listdir(self.path_origen) if os.path.isfile(os.path.join(self.path_origen, f))]
            ruta_final = os.path.join(self.ruta_destino_base, cat, f"{fecha}_{caso}")
            
            if not os.path.exists(ruta_final): os.makedirs(ruta_final)

            detalles_archivos = []
            for i, nombre in enumerate(todos_archivos):
                orig = os.path.join(self.path_origen, nombre)
                dest = os.path.join(ruta_final, nombre)
                shutil.move(orig, dest)
                detalles_archivos.append({"nombre": nombre, "ruta_destino": dest})
                self.progress_bar.set((i+1)/len(todos_archivos))
            
            lote_data = {
                "fecha_caso": fecha, "nombre_caso": caso, "categoria": cat,
                "cantidad_archivos": len(detalles_archivos), "ruta_destino": ruta_final,
                "archivos_movidos": detalles_archivos
            }
            self.historial.append(lote_data)
            with open(self.archivo_historial, "w", encoding="utf-8") as f:
                json.dump(self.historial, f, indent=2)

            messagebox.showinfo("Completado", f"El caso '{caso}' ha sido organizado correctamente.")
            self._actualizar_historial()
            self.entry_caso.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
        finally:
            self.btn_procesar.configure(state="normal", text="🚀 ORGANIZAR AHORA")
            self.progress_bar.set(0)

    def _abrir_carpeta(self, ruta):
        try:
            if platform.system() == "Windows": os.startfile(ruta)
            elif platform.system() == "Darwin": subprocess.Popen(["open", ruta])
            else: subprocess.Popen(["xdg-open", ruta])
        except: messagebox.showerror("Error", "No se pudo abrir la ubicación.")

    def limpiar_historial(self):
        if messagebox.askyesno("Borrar Historial", "¿Estás seguro? Esta acción no borra tus archivos, solo el registro del buscador."):
            self.historial = []; self._actualizar_historial()
            if os.path.exists(self.archivo_historial): os.remove(self.archivo_historial)

if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()