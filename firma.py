import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter
import io

class AplicacionFirmaPDF:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmador de PDF Avanzado")
        self.root.geometry("1100x800")
        
        # Variables de estado
        self.pdf_doc = None
        self.pagina_actual = 0
        self.zoom = 1.0
        
        self.firma_img_original = None
        self.firma_img_procesada = None
        self.tk_firma = None
        
        self.firma_x = 100
        self.firma_y = 100
        self.arrastrando = False
        
        self.id_firma_canvas = None
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Panel izquierdo (Controles)
        panel_controles = tk.Frame(self.root, width=300, bg="#2b2b2b", padx=15, pady=15)
        panel_controles.pack(side=tk.LEFT, fill=tk.Y)
        
        # Estilos base
        estilo_btn = {"font": ("Arial", 11, "bold"), "fg": "white", "pady": 5}
        
        # 1. Cargar Archivos
        tk.Label(panel_controles, text="1. ARCHIVOS", bg="#2b2b2b", fg="white", font=("Arial", 12, "bold")).pack(pady=(0,5))
        tk.Button(panel_controles, text="Cargar PDF", command=self.cargar_pdf, bg="#d9534f", **estilo_btn).pack(fill=tk.X, pady=5)
        tk.Button(panel_controles, text="Cargar Firma (PNG)", command=self.cargar_firma, bg="#5bc0de", **estilo_btn).pack(fill=tk.X, pady=5)
        
        # Navegación PDF
        frame_nav = tk.Frame(panel_controles, bg="#2b2b2b")
        frame_nav.pack(fill=tk.X, pady=15)
        tk.Button(frame_nav, text="◀ Ant", command=self.pagina_anterior, font=("Arial", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.lbl_pagina = tk.Label(frame_nav, text="Pág: 0/0", bg="#2b2b2b", fg="white", font=("Arial", 10))
        self.lbl_pagina.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_nav, text="Sig ▶", command=self.pagina_siguiente, font=("Arial", 10)).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
        
        tk.Frame(panel_controles, height=2, bg="#555").pack(fill=tk.X, pady=15) # Separador
        
        # 2. Ajustes de Firma
        tk.Label(panel_controles, text="2. EDICIÓN DE FIRMA", bg="#2b2b2b", fg="white", font=("Arial", 12, "bold")).pack(pady=(0,5))
        
        tk.Label(panel_controles, text="Tamaño de la firma:", bg="#2b2b2b", fg="white").pack(anchor=tk.W)
        self.slider_tamano = tk.Scale(panel_controles, from_=10, to=400, orient=tk.HORIZONTAL, command=self.cambiar_tamano_firma, bg="#2b2b2b", fg="white", highlightthickness=0)
        self.slider_tamano.set(100)
        self.slider_tamano.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(panel_controles, text="➕ Engrosar Tinta", command=self.engrosar_firma, bg="#444", fg="white", pady=5).pack(fill=tk.X, pady=2)
        tk.Button(panel_controles, text="💧 Suavizar Bordes", command=self.suavizar_firma, bg="#444", fg="white", pady=5).pack(fill=tk.X, pady=2)
        tk.Button(panel_controles, text="🔄 Restaurar Original", command=self.restaurar_firma, bg="#666", fg="white", pady=5).pack(fill=tk.X, pady=(2, 15))
        
        tk.Frame(panel_controles, height=2, bg="#555").pack(fill=tk.X, pady=15) # Separador
        
        # 3. Guardar
        tk.Label(panel_controles, text="3. FINALIZAR", bg="#2b2b2b", fg="white", font=("Arial", 12, "bold")).pack(pady=(0,5))
        tk.Button(panel_controles, text="Guardar PDF Firmado", command=self.guardar_pdf, bg="#5cb85c", **estilo_btn).pack(fill=tk.X, pady=5)
        
        # Instrucciones breves
        tk.Label(panel_controles, text="* Arrastra la firma con el mouse\npara posicionarla.", bg="#2b2b2b", fg="#aaa", justify=tk.LEFT).pack(side=tk.BOTTOM, pady=20)
        
        # Panel derecho (Visualizador / Canvas)
        self.frame_canvas = tk.Frame(self.root, bg="#1e1e1e")
        self.frame_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.frame_canvas, bg="#525659", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Eventos del ratón para mover la firma
        self.canvas.bind("<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        
    def cargar_pdf(self):
        ruta_pdf = filedialog.askopenfilename(title="Selecciona el PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if not ruta_pdf: return
        
        self.pdf_doc = fitz.open(ruta_pdf)
        self.pagina_actual = 0
        self.mostrar_pagina()
        
    def mostrar_pagina(self):
        if not self.pdf_doc: return
        
        pagina = self.pdf_doc[self.pagina_actual]
        self.lbl_pagina.config(text=f"Pág: {self.pagina_actual + 1}/{len(self.pdf_doc)}")
        
        # Calcular zoom para que la página encaje verticalmente en la pantalla (max 750px)
        alto_pagina = pagina.rect.height
        self.zoom = 750.0 / alto_pagina
        matriz = fitz.Matrix(self.zoom, self.zoom)
        
        # Renderizar la página del PDF a imagen
        pix = pagina.get_pixmap(matrix=matriz)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_pdf = ImageTk.PhotoImage(img)
        
        # Dibujar PDF en el fondo del Canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_pdf)
        
        # Redibujar la firma encima si ya está cargada
        self.dibujar_firma()
        
    def cargar_firma(self):
        ruta_firma = filedialog.askopenfilename(title="Selecciona tu firma", filetypes=[("Imágenes PNG", "*.png")])
        if not ruta_firma: return
        
        # Cargar manteniendo el canal RGBA para soportar transparencias
        self.firma_img_original = Image.open(ruta_firma).convert("RGBA")
        self.firma_img_procesada = self.firma_img_original.copy()
        
        # Centrar la firma por defecto
        self.firma_x, self.firma_y = 100, 100 
        self.actualizar_imagen_firma()
        
    def actualizar_imagen_firma(self, redibujar=True):
        if not self.firma_img_procesada: return
        
        porcentaje = self.slider_tamano.get() / 100.0
        nuevo_ancho = int(self.firma_img_procesada.width * porcentaje)
        nuevo_alto = int(self.firma_img_procesada.height * porcentaje)
        
        if nuevo_ancho > 0 and nuevo_alto > 0:
            # Usar Lanczos para alta calidad al redimensionar
            img_redimensionada = self.firma_img_procesada.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            self.tk_firma = ImageTk.PhotoImage(img_redimensionada)
            if redibujar:
                self.dibujar_firma()
            return img_redimensionada
            
    def cambiar_tamano_firma(self, valor):
        self.actualizar_imagen_firma()
        
    def engrosar_firma(self):
        if not self.firma_img_procesada: return
        # Separar canales. Para engrosar una firma oscura sobre fondo transparente, 
        # aplicamos un filtro de máximo (dilatación) únicamente al canal de transparencia (Alpha)
        r, g, b, a = self.firma_img_procesada.split()
        a = a.filter(ImageFilter.MaxFilter(3))
        self.firma_img_procesada = Image.merge("RGBA", (r, g, b, a))
        self.actualizar_imagen_firma()
        
    def suavizar_firma(self):
        if not self.firma_img_procesada: return
        # Aplica un filtro de suavizado para eliminar píxeles dentados (antialiasing rústico)
        self.firma_img_procesada = self.firma_img_procesada.filter(ImageFilter.SMOOTH_MORE)
        self.actualizar_imagen_firma()
        
    def restaurar_firma(self):
        if not self.firma_img_original: return
        self.firma_img_procesada = self.firma_img_original.copy()
        self.slider_tamano.set(100)
        self.actualizar_imagen_firma()
        
    def dibujar_firma(self):
        if not self.tk_firma: return
        
        if self.id_firma_canvas:
            self.canvas.delete(self.id_firma_canvas)
            
        self.id_firma_canvas = self.canvas.create_image(self.firma_x, self.firma_y, anchor=tk.NW, image=self.tk_firma)
        
    def iniciar_arrastre(self, event):
        if not self.tk_firma: return
        
        # Comprobar si el clic ocurrió dentro de la zona de la firma actual
        ancho = self.tk_firma.width()
        alto = self.tk_firma.height()
        
        if (self.firma_x <= event.x <= self.firma_x + ancho) and (self.firma_y <= event.y <= self.firma_y + alto):
            self.arrastrando = True
            # Calcular la distancia desde el clic hasta la esquina de la imagen
            self.offset_x = event.x - self.firma_x
            self.offset_y = event.y - self.firma_y
        else:
            self.arrastrando = False
            
    def arrastrar(self, event):
        if not self.tk_firma or not self.arrastrando: return
        
        # Mover la imagen manteniendo el offset del ratón
        self.firma_x = event.x - self.offset_x
        self.firma_y = event.y - self.offset_y
        self.canvas.coords(self.id_firma_canvas, self.firma_x, self.firma_y)
        
    def pagina_anterior(self):
        if self.pdf_doc and self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.mostrar_pagina()
            
    def pagina_siguiente(self):
        if self.pdf_doc and self.pagina_actual < len(self.pdf_doc) - 1:
            self.pagina_actual += 1
            self.mostrar_pagina()
            
    def guardar_pdf(self):
        if not self.pdf_doc or not self.firma_img_procesada:
            messagebox.showwarning("Atención", "Carga un PDF y tu firma PNG primero.")
            return
            
        ruta_salida = filedialog.asksaveasfilename(title="Guardar PDF firmado como...", defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not ruta_salida: return
        
        pagina = self.pdf_doc[self.pagina_actual]
        
        # Obtener la imagen de la firma ya escalada tal cual se ve en la pantalla
        firma_final = self.actualizar_imagen_firma(redibujar=False)
        ancho_final = firma_final.width
        alto_final = firma_final.height
        
        # Convertir las coordenadas de la pantalla (canvas) a las coordenadas reales del documento PDF
        x_pdf = self.firma_x / self.zoom
        y_pdf = self.firma_y / self.zoom
        w_pdf = ancho_final / self.zoom
        h_pdf = alto_final / self.zoom
        
        rectangulo = fitz.Rect(x_pdf, y_pdf, x_pdf + w_pdf, y_pdf + h_pdf)
        
        # Convertir la imagen procesada a memoria (bytes) para que PyMuPDF la inserte directo
        img_bytes = io.BytesIO()
        firma_final.save(img_bytes, format="PNG")
        
        # Insertar firma sin perder calidad
        pagina.insert_image(rectangulo, stream=img_bytes.getvalue())
        
        self.pdf_doc.save(ruta_salida)
        messagebox.showinfo("Éxito", f"¡Documento firmado y guardado con éxito en:\n{ruta_salida}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionFirmaPDF(root)
    root.mainloop()