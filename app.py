import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, simpledialog, messagebox, Scrollbar, OptionMenu, StringVar
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageSequence
from fpdf import FPDF
import pydicom
import os
import pickle
import numpy as np
from ultralytics import YOLO
import torch
from torchvision import transforms
from torchvision.models.segmentation import deeplabv3_resnet50
from datetime import datetime
import threading
import ctypes

class Dicomet:
    C = {
        'bg': '#F5F7FA',
        'panel': '#FFFFFF',
        'border': '#DCE3EB',
        'accent': '#2563EB',
        'accent_light': '#DBEAFE',
        'accent_hover': '#1D4ED8',
        'text': '#1E293B',
        'text_secondary': '#64748B',
        'text_on_accent': '#FFFFFF',
        'success': '#16A34A',
        'success_bg': '#DCFCE7',
        'warning': '#D97706',
        'danger': '#DC2626',
        'danger_bg': '#FEE2E2',
        'canvas_bg': '#1E293B',
        'entry_bg': '#F8FAFC',
        'scroll_bg': '#E2E8F0',
        'selected_bbox': '#2563EB',
        'bbox_default': '#DC2626',
        'toolbar_label': '#94A3B8',
        'header_bg': '#FFFFFF',
        'status_bg': '#F8FAFC',
        'overlay_bg': '#000000',
        'original_accent': '#2563EB',
        'processed_accent': '#16A34A',
    }

    FS = {
        'title': 12,
        'subtitle': 9,
        'normal': 9,
        'small': 8,
        'tiny': 7,
        'status': 8,
        'button': 9,
        'label': 8,
        'group_label': 7,
        'header_large': 15,
    }

    def setup_styles(self):
        default = tkfont.nametofont("TkDefaultFont")
        default.configure(size=self.FS['normal'], family='Segoe UI')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.C['bg'], foreground=self.C['text'],
                        fieldbackground=self.C['entry_bg'])
        style.configure('Treeview', background=self.C['panel'], foreground=self.C['text'],
                        fieldbackground=self.C['panel'], borderwidth=0,
                        font=('Segoe UI', self.FS['small']))
        style.configure('Treeview.Heading', background=self.C['bg'], foreground=self.C['text'],
                        font=('Segoe UI', self.FS['small'], 'bold'), borderwidth=0,
                        relief=tk.FLAT)
        style.map('Treeview.Heading', background=[('active', self.C['accent_light'])])
        style.map('Treeview', background=[('selected', self.C['accent_light'])],
                  foreground=[('selected', self.C['text'])])
        style.configure('TSpinbox', arrowsize=12)

    def load_icons(self):
        self.icons = {}
        res_dir = os.path.join(os.path.dirname(__file__), 'Resources')
        icon_map = {
            'folder': 'folder.png', 'play': 'play.png', 'undo': 'undo.png',
            'restore': 'restore.png', 'pdf': 'pdf.png', 'dicom': 'dicom.png',
            'save': 'save.png', 'load': 'load.png', 'eye': 'eye.png',
            'eye_off': 'eye-off.png', 'info': 'info.png', 'history': 'history.png',
            'delete': 'delete.png', 'copy': 'copy.png', 'paste': 'paste.png',
            'zoom_in': 'zoom_in.png', 'zoom_out': 'zoom_out.png',
            'close': 'close.png', 'check': 'check.png', 'plus': 'plus.png',
            'menu': 'menu.png', 'cog': 'cog.png',
            'pan': 'pan.png', 'crop': 'crop.png', 'fit': 'fit-to-screen.png',
            'fullscreen': 'fullscreen.png', 'pencil': 'pencil.png',
        }
        for name, fname in icon_map.items():
            path = os.path.join(res_dir, fname)
            if os.path.exists(path):
                self.icons[name] = tk.PhotoImage(file=path)

    def make_btn(self, parent, icon_name, text, command, btn_bg=None, btn_fg=None,
                 hover_bg=None, padx=10, pady=5, font_size=None):
        icon = self.icons.get(icon_name)
        bg = btn_bg or self.C['panel']
        fg = btn_fg or self.C['text']
        hv = hover_bg or self.C['accent_light']
        btn = tk.Button(parent, image=icon, text=text, compound=tk.LEFT,
                        command=command, bg=bg, fg=fg,
                        activebackground=hv, activeforeground=self.C['text'],
                        relief=tk.FLAT, padx=padx, pady=pady, borderwidth=0,
                        font=('Segoe UI', font_size or self.FS['button']),
                        cursor='hand2', highlightthickness=1,
                        highlightbackground=self.C['border'],
                        highlightcolor=self.C['border'])
        btn.bind('<Enter>', lambda e, b=btn: b.config(bg=hv))
        btn.bind('<Leave>', lambda e, b=btn, c=bg: b.config(bg=c))
        return btn

    def make_sep(self, parent, height=28, width=1):
        s = tk.Frame(parent, width=width, bg=self.C['border'])
        s.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=5)
        return s

    def make_round_card(self, parent, padx=0, pady=0, side=tk.TOP, fill=tk.X, expand=False):
        c = tk.Frame(parent, bg=self.C['panel'],
                     highlightbackground=self.C['border'],
                     highlightthickness=1)
        c.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
        return c

    def _make_modern_slider(self, parent, command, from_=10, to=0.1, initial=1,
                            orient='vertical', length=110):
        pad = 14
        tr = 6
        if orient == 'vertical':
            ch = length
        else:
            ch = 24
        canvas = tk.Canvas(parent, height=ch, bg=self.C['panel'],
                           highlightthickness=0, relief=tk.FLAT)
        cur = [initial]

        def redraw(event=None):
            canvas.delete('all')
            cw = canvas.winfo_width()
            if cw < 10:
                return
            ratio = (cur[0] - to) / (from_ - to)
            if orient == 'vertical':
                x1 = cw // 2
                y1, y2 = pad, ch - pad
                yp = y2 - ratio * (y2 - y1)
                canvas.create_line(x1, y1, x1, y2, fill=self.C['border'],
                                   width=3, capstyle=tk.ROUND)
                canvas.create_line(x1, yp, x1, y2, fill=self.C['accent'],
                                   width=3, capstyle=tk.ROUND)
                canvas.create_oval(x1 - tr, yp - tr, x1 + tr, yp + tr,
                                   fill='white', outline=self.C['accent'], width=2)
            else:
                x1, x2 = pad, cw - pad
                y1 = ch // 2
                xp = x1 + ratio * (x2 - x1)
                canvas.create_line(x1, y1, x2, y1, fill=self.C['border'],
                                   width=3, capstyle=tk.ROUND)
                canvas.create_line(x1, y1, xp, y1, fill=self.C['accent'],
                                   width=3, capstyle=tk.ROUND)
                canvas.create_oval(xp - tr, y1 - tr, xp + tr, y1 + tr,
                                   fill='white', outline=self.C['accent'], width=2)

        def set_value(v):
            v = max(to, min(from_, float(v)))
            cur[0] = v
            redraw()

        def _on_drag(event):
            cw = canvas.winfo_width()
            if cw < 10:
                return
            if orient == 'vertical':
                y1, y2 = pad, ch - pad
                ratio = 1 - (event.y - y1) / (y2 - y1)
            else:
                x1, x2 = pad, cw - pad
                ratio = (event.x - x1) / (x2 - x1)
            ratio = max(0, min(1, ratio))
            v = to + ratio * (from_ - to)
            cur[0] = v
            redraw()
            command(v)

        canvas.bind('<Configure>', redraw)
        canvas.bind('<B1-Motion>', _on_drag)
        canvas.bind('<Button-1>', lambda e: (_on_drag(e), canvas.focus_set()))
        canvas.set_value = set_value
        redraw()
        return canvas

    def __init__(self, root):
        self.root = root
        self.root.title("Dicomet")
        self.root.configure(bg=self.C['bg'])
        self.root.minsize(1100, 700)

        if os.name == 'nt':
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
            self.root.iconbitmap(icon_path)

        self.setup_styles()
        self.load_icons()

        self.model = YOLO('yolov8l.pt')
        self.deeplab_model = deeplabv3_resnet50(pretrained=True).eval()

        # ── HEADER ───────────────────────────────────────
        hdr = tk.Frame(root, bg=self.C['panel'], highlightthickness=0)
        hdr.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(hdr, height=1, bg=self.C['border']).pack(side=tk.BOTTOM, fill=tk.X)

        left = tk.Frame(hdr, bg=self.C['panel'])
        left.pack(side=tk.LEFT, padx=14, pady=6)
        
        # Load and place IITMANDI and VIML logos in the brand area
        try:
            for f, s in [('VIML.png', 20), ('IITMANDI.png', 24)]:
                img = Image.open(f).resize((s, s), Image.LANCZOS)
                attr_name = f"logo_{f.replace('.', '_')}"
                setattr(self, attr_name, ImageTk.PhotoImage(img))
            tk.Label(left, image=self.logo_VIML_png, bg=self.C['panel']).pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(left, image=self.logo_IITMANDI_png, bg=self.C['panel']).pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            print("Logo load error:", e)

        t = tk.Frame(left, bg=self.C['panel'])
        t.pack(side=tk.LEFT)
        tk.Label(t, text="Dicomet", bg=self.C['panel'], fg=self.C['text'],
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        tk.Label(t, text="Intelligent DICOM Imaging", bg=self.C['panel'],
                 fg=self.C['text_secondary'],
                 font=('Segoe UI', 9)).pack(anchor='w')

        right = tk.Frame(hdr, bg=self.C['panel'])
        right.pack(side=tk.RIGHT, padx=12, pady=6)
        self.make_btn(right, 'info', '', self.show_help, padx=4, pady=2,
                      font_size=self.FS['tiny']).pack(side=tk.RIGHT, padx=1)
        self.make_btn(right, 'cog', '', self.show_settings, padx=4, pady=2,
                      font_size=self.FS['tiny']).pack(side=tk.RIGHT, padx=1)

        # ── TOOLBAR ─────────────────────────────────────
        tb_card = self.make_round_card(root, padx=14, pady=(6, 2), fill=tk.X)
        tb_row = tk.Frame(tb_card, bg=self.C['panel'])
        tb_row.pack(side=tk.TOP, fill=tk.X)

        grps = [
            [('folder', 'Open', self.load_image), ('save', 'Save', self.save_project), ('load', 'Load', self.load_project)],
            [('play', 'Apply', self.apply_filter)],
            [('undo', 'Undo', self.undo), ('restore', 'Restore', self.restore)],
            [('pdf', 'PDF', self.export_as_pdf), ('dicom', 'DICOM', self.export_modified_dicom)],
            [('info', 'Details', self.toggle_details_visibility), ('history', 'History', self.toggle_history_log)],
        ]
        for gi, grp in enumerate(grps):
            if gi:
                self.make_sep(tb_row)
            gc = tk.Frame(tb_row, bg=self.C['panel'],
                          highlightbackground=self.C['border'], highlightthickness=1)
            gc.pack(side=tk.LEFT, padx=2, pady=1)
            ginner = tk.Frame(gc, bg=self.C['panel'])
            ginner.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
            for ic, tx, cmd in grp:
                is_apply = tx == 'Apply'
                bg = self.C['accent'] if is_apply else self.C['panel']
                fg = self.C['text_on_accent'] if is_apply else self.C['text']
                hv = self.C['accent_hover'] if is_apply else self.C['accent_light']
                btn = self.make_btn(ginner, ic, tx, cmd, btn_bg=bg, btn_fg=fg,
                                    hover_bg=hv, padx=10, pady=5, font_size=self.FS['small'])
                btn.pack(side=tk.LEFT)
                if tx == 'Details':
                    self.details_toggle_button = btn
                elif tx == 'History':
                    self.history_button = btn

        self.model_var = StringVar(self.root)
        self.model_var.set("YOLOv8")
        self.model_menu = tk.OptionMenu(tb_row, self.model_var, "YOLOv8", "DeepLabV3")
        self.model_menu.config(bg=self.C['panel'], fg=self.C['text'],
                               relief=tk.FLAT, highlightthickness=1,
                               highlightbackground=self.C['border'],
                               highlightcolor=self.C['border'],
                               borderwidth=0, font=('Segoe UI', self.FS['button']),
                               cursor='hand2', padx=8, pady=4,
                               activebackground=self.C['accent_light'],
                               activeforeground=self.C['accent'])
        self.model_menu['menu'].configure(bg=self.C['panel'], fg=self.C['text'],
                                          activebackground=self.C['accent_light'],
                                          activeforeground=self.C['accent'],
                                          font=('Segoe UI', self.FS['normal']))
        self.model_menu.pack(side=tk.RIGHT, padx=2, pady=1)

        # ── MAIN CONTENT ────────────────────────────────
        self.main_frame = tk.Frame(root, bg=self.C['bg'])
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.details_window = None
        self.history_window = None
        self.history_listbox = None

        # ── IMAGES WORKSPACE ────────────────────────────
        ws = tk.Frame(self.main_frame, bg=self.C['bg'])
        ws.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=14, pady=8)

        img_row = tk.Frame(ws, bg=self.C['bg'])
        img_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def make_viewer(parent, label_text, accent_color, bbox_attr, toggle_fn):
            card = self.make_round_card(parent, side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
            tb = tk.Frame(card, bg=self.C['panel'])
            tb.pack(side=tk.TOP, fill=tk.X)
            lbl_bg = tk.Frame(tb, bg=self.C['panel'])
            lbl_bg.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(lbl_bg, text=label_text, bg=self.C['panel'], fg=accent_color,
                     font=('Segoe UI', 9, 'bold'), anchor='w',
                     padx=6, pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True)
            btn = self.make_btn(tb, 'eye_off', 'BBox', toggle_fn,
                                padx=6, pady=2, font_size=self.FS['tiny'])
            btn.pack(side=tk.RIGHT, padx=4, pady=3)
            setattr(self, bbox_attr, True)
            cv = tk.Canvas(card, bg=self.C['canvas_bg'], cursor='cross',
                           relief=tk.FLAT, borderwidth=0,
                           highlightthickness=0)
            cv.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
            return card, cv, btn

        self.original_panel, self.original_canvas, self.original_bbox_btn = make_viewer(
            img_row, 'ORIGINAL', self.C['original_accent'],
            'original_bboxes_visible', self.toggle_original_bboxes)



        self.processed_panel, self.processed_canvas, self.processed_bbox_btn = make_viewer(
            img_row, 'PROCESSED', self.C['processed_accent'],
            'processed_bboxes_visible', self.toggle_processed_bboxes)

        # Bottom controls card
        ctrl_card = self.make_round_card(ws, fill=tk.X, pady=(4, 2))
        ctrl = tk.Frame(ctrl_card, bg=self.C['panel'])
        ctrl.pack(side=tk.TOP, fill=tk.X)

        self.make_btn(ctrl, 'pan', 'Hand', self.toggle_pan, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_btn(ctrl, 'fit', 'Fit', self.fit_to_screen, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_btn(ctrl, 'fullscreen', 'Full', self.toggle_fullscreen, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_sep(ctrl)
        hz = tk.Frame(ctrl, bg=self.C['panel'])
        hz.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Label(hz, text="Zoom:", bg=self.C['panel'], fg=self.C['text_secondary'],
                 font=('Segoe UI', self.FS['tiny'])).pack(side=tk.LEFT, padx=(0, 6))
        self.make_btn(hz, 'zoom_out', '', None, padx=5, pady=2).pack(side=tk.LEFT)
        self.zoom_slider = self._make_modern_slider(
            hz, command=self.zoom_images,
            from_=10, to=0.1, initial=1,
            orient='horizontal', length=140)
        self.zoom_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.make_btn(hz, 'zoom_in', '', None, padx=5, pady=2).pack(side=tk.LEFT)
        self.zoom_pct = tk.Label(hz, text="1.00x", bg=self.C['panel'], fg=self.C['text'],
                                 font=('Segoe UI', 8, 'bold'))
        self.zoom_pct.pack(side=tk.LEFT, padx=(6, 0))

        # ── ANNOTATIONS PANEL ──────────────────────────
        ann_card = self.make_round_card(root, padx=14, pady=(2, 6), fill=tk.X)
        a_inner = tk.Frame(ann_card, bg=self.C['panel'])
        a_inner.pack(side=tk.TOP, fill=tk.X)

        ah = tk.Frame(a_inner, bg=self.C['panel'])
        ah.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(4, 2))
        tk.Label(ah, text="ANNOTATIONS", bg=self.C['panel'], fg=self.C['accent'],
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        af = tk.Frame(ah, bg=self.C['panel'])
        af.pack(side=tk.RIGHT)
        for ic, tx, cb in [('pencil', 'Edit', None), ('copy', 'Copy', None),
                           ('delete', 'Delete', None)]:
            self.make_btn(af, ic, tx, cb, padx=6, pady=2,
                          font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=1)

        tf = tk.Frame(a_inner, bg=self.C['panel'])
        tf.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 4))

        self.annotations_tree = ttk.Treeview(tf, columns=('id', 'class', 'confidence', 'comment'),
                                             show='headings', height=4, selectmode='browse')
        for col, w, hdr in [('id', 40, 'ID'), ('class', 100, 'CLASS'),
                            ('confidence', 80, 'CONFIDENCE'),
                            ('comment', 400, 'COMMENT')]:
            self.annotations_tree.column(col, width=w, anchor='w')
            self.annotations_tree.heading(col, text=hdr, anchor='w')
        self.annotations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vs = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self.annotations_tree.yview)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotations_tree.configure(yscrollcommand=vs.set)

        self.comment_text = tk.Text(root, height=1)

        # ── STATUS BAR ─────────────────────────────────
        sf = tk.Frame(root, bg=self.C['panel'])
        sf.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(sf, height=1, bg=self.C['border']).pack(side=tk.TOP, fill=tk.X)
        sb = tk.Frame(sf, bg=self.C['panel'])
        sb.pack(side=tk.TOP, fill=tk.X, padx=14, pady=3)

        dot = tk.Canvas(sb, width=6, height=6, bg=self.C['panel'], highlightthickness=0)
        dot.pack(side=tk.LEFT, padx=(0, 5))
        dot.create_oval(0, 0, 6, 6, fill=self.C['success'], outline='')
        self.status_label = tk.Label(sb, text="Ready", bg=self.C['panel'],
                                     fg=self.C['text_secondary'],
                                     font=('Segoe UI', self.FS['status']))
        self.status_label.pack(side=tk.LEFT)
        self.image_info_label = tk.Label(sb, text="", bg=self.C['panel'],
                                         fg=self.C['text_secondary'],
                                         font=('Segoe UI', self.FS['status']))
        self.image_info_label.pack(side=tk.LEFT, padx=(18, 0))

        # ── CANVAS BINDINGS ────────────────────────────
        self.processed_canvas.bind("<Button-1>", self.canvas_click)
        self.processed_canvas.bind("<Double-1>", self.canvas_double_click)
        self.processed_canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.processed_canvas.bind("<B1-Motion>", self.move_bounding_box)
        self.processed_canvas.bind("<Motion>", self.canvas_motion)
        self.processed_canvas.bind("<Delete>", self.delete_bbox_keypress)
        self.processed_canvas.bind("<d>", self.delete_bbox_keypress)
        self.processed_canvas.bind("<D>", self.delete_bbox_keypress)
        self.processed_canvas.bind("<Control-c>", self.copy_bbox)
        self.processed_canvas.bind("<Control-C>", self.copy_bbox)
        self.processed_canvas.bind("<Control-v>", self.paste_bbox)
        self.processed_canvas.bind("<Control-V>", self.paste_bbox)
        self.original_canvas.bind("<ButtonPress-1>", self.pan_start)
        self.original_canvas.bind("<B1-Motion>", self.pan_move)

        # ── STATE ──────────────────────────────────────
        self.detections = []
        self.bbox_handles = {}
        self.bbox_labels = {}
        self.detection_comments = {}
        self.selected_bbox = None
        self.clipboard_bbox = None
        self.move_start = None
        self.resizing = False
        self.resize_handle = None

        self.original_image = None
        self.processed_image = None
        self.dicom_image = None
        self.image_scale = 1
        self.original_zoom_factor = 1
        self.processed_zoom_factor = 1

        self.history = []
        self.initial_state = None
        self.loading_overlay = None
        self.loading_label = None
        self.loading_timer = None

        # ── LOADING GIF ────────────────────────────────
        loading_image = Image.open('loading.gif')
        self.loading_frames = []
        for frame in ImageSequence.Iterator(loading_image):
            frame = frame.convert("RGBA")
            data = frame.getdata()
            new_data = []
            for item in data:
                if item[0] == 255 and item[1] == 255 and item[2] == 255:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            frame.putdata(new_data)
            resized = frame.resize((48, 48), Image.LANCZOS)
            self.loading_frames.append(ImageTk.PhotoImage(resized))

    def set_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.set_status(f"Loading {os.path.basename(file_path)}...")
            if file_path.lower().endswith('.dcm'):
                self.dicom_image = pydicom.dcmread(file_path)
                pixel_array = self.dicom_image.pixel_array
                pixel_array = self.normalize_pixel_array(pixel_array)
                image = Image.fromarray(pixel_array).convert('L')
                self.dicom_text = str(self.dicom_image)
            else:
                image = Image.open(file_path)

            self.original_image = image
            self.processed_image = image.copy()
            self.root.update_idletasks()
            cw = self.original_canvas.winfo_width()
            ch = self.original_canvas.winfo_height()
            if cw > 1 and ch > 1:
                scale = min(cw / image.width, ch / image.height)
                self.image_scale = scale
                self.zoom_slider.set_value(scale)
            self.display_image(self.original_canvas, self.original_image)
            self.display_image(self.processed_canvas, self.processed_image)
            self.save_initial_state()
            self.history = []
            self.log_history('Image loaded')
            self.update_annotations_tree()
            w, h = image.size
            pct = f"{int(self.image_scale * 100)}%"
            self.image_info_label.config(text=f"Image: {os.path.basename(file_path)}  ·  Size: {w}×{h}  ·  Zoom: {pct}")
            self.zoom_pct.config(text=f"{self.image_scale:.2f}x")
            self.set_status(f"Loaded {os.path.basename(file_path)}")

    def normalize_pixel_array(self, pixel_array):
        if np.issubdtype(pixel_array.dtype, np.integer):
            max_val = np.max(pixel_array)
            if max_val > 0:
                pixel_array = (pixel_array / max_val) * 255.0
            pixel_array = pixel_array.astype(np.uint8)
        elif np.issubdtype(pixel_array.dtype, np.float):
            pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array))
            pixel_array = (pixel_array * 255).astype(np.uint8)
        return pixel_array
    
    def show_loading_animation(self):
        if self.loading_overlay:
            return
        
        # 1. Overlay window (light mist/fade, covering screen)
        self.loading_overlay = tk.Toplevel(self.root)
        if os.name == 'nt':
            self.loading_overlay.overrideredirect(True)
        else:
            try:
                self.loading_overlay.attributes("-type", "splash")
            except Exception:
                self.loading_overlay.overrideredirect(True)
        self.loading_overlay.configure(bg='#F5F7FA')
        self.loading_overlay.transient(self.root)
        self.loading_overlay.wait_visibility()
        self.loading_overlay.attributes("-alpha", 0.75) # Light shadow mist (75% opacity for sharp GIF)

        def sync_geometry(event=None):
            if self.loading_overlay and self.loading_overlay.winfo_exists():
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                self.loading_overlay.geometry(f"{w}x{h}+{x}+{y}")

        sync_geometry()
        self.configure_bind_id = self.root.bind("<Configure>", sync_geometry)

        # Loading spinner frame inside the overlay.
        # Background is set to '#F5F7FA' to match the overlay, making the GIF background transparent.
        self.loading_label = tk.Label(self.loading_overlay, image=self.loading_frames[0], bg='#F5F7FA', highlightthickness=0)
        self.loading_label.pack(expand=True)

        self.loading_frame_idx = [0]
        self.update_loading_frame()
        self.loading_overlay.grab_set()

    def update_loading_frame(self):
        if not self.loading_overlay or not self.loading_frames:
            return
        idx = self.loading_frame_idx[0]
        if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
            self.loading_label.configure(image=self.loading_frames[idx])
        self.loading_frame_idx[0] = (idx + 1) % len(self.loading_frames)
        self.loading_timer = self.root.after(100, self.update_loading_frame)

    def hide_loading_animation(self):
        if self.loading_timer:
            self.root.after_cancel(self.loading_timer)
            self.loading_timer = None
        if hasattr(self, 'configure_bind_id') and self.configure_bind_id:
            self.root.unbind("<Configure>", self.configure_bind_id)
            self.configure_bind_id = None
        if self.loading_overlay:
            self.loading_overlay.destroy()
            self.loading_overlay = None

    def apply_filter(self):
        if self.processed_image:
            self.show_loading_animation()
            threading.Thread(target=self.apply_filter_in_background).start()

    def apply_filter_in_background(self):
        # Simulating filter application with sleep
        import time
        time.sleep(3)  # Simulate long processing time
        
        self.log_history('Before filter')
        if not self.original_image:
            messagebox.showerror("Error", "Load an image first.")
            return

        model_name = self.model_var.get()
        if model_name == "YOLOv8":
            self.apply_yolo_filter()
        elif model_name == "DeepLabV3":
            self.apply_deeplab_filter()

        self.save_initial_state()
        # Here you would apply your actual filter logic
        self.hide_loading_animation()
        

    def apply_yolo_filter(self):
        if not self.original_image:
            messagebox.showerror("Error", "Load an image first.")
            return

        image_np = np.array(self.original_image.convert("RGB"))
        results = self.model(image_np)

        self.detections.clear()
        for i, result in enumerate(results):
            for j, bbox in enumerate(result.boxes):
                x1, y1, x2, y2 = bbox.xyxy[0].int().tolist()
                class_name = result.names[bbox.cls[0].item()]
                confidence = bbox.conf[0].item()
                detection_id = len(self.detections)
                self.detections.append({
                    'id': detection_id,
                    'bbox': (x1, y1, x2, y2),
                    'class': class_name,
                    'confidence': confidence,
                    'comment': ''
                })
        self.save_initial_state()
        self.display_image(self.original_canvas, self.original_image, self.detections)
        self.display_image(self.processed_canvas, self.processed_image, self.detections)
        self.log_history('YOLOV8 filter applied')
        self.set_status(f"YOLOv8: {len(self.detections)} detections")

    def apply_deeplab_filter(self):
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        input_tensor = preprocess(self.original_image.convert("RGB"))
        input_batch = input_tensor.unsqueeze(0)

        with torch.no_grad():
            output = self.deeplab_model(input_batch)['out'][0]
        output_predictions = output.argmax(0).byte().cpu().numpy()

        mask = Image.fromarray(output_predictions)
        mask = mask.resize(self.original_image.size, Image.NEAREST)
        mask = mask.convert("L")

        self.processed_image = Image.composite(self.original_image.convert("RGBA"), mask.convert("RGBA"), mask)
        self.display_image(self.original_canvas, self.original_image, self.detections)
        self.display_image(self.processed_canvas, self.processed_image, self.detections)
        self.log_history('DeepLabV3 filter applied')
        self.set_status("DeepLabV3 segmentation applied")

    def display_image(self, canvas, image, detections=[]):
        show_bboxes = (self.original_bboxes_visible and canvas == self.original_canvas) or \
                      (self.processed_bboxes_visible and canvas == self.processed_canvas)

        if show_bboxes and detections:
            image = self.draw_bounding_boxes(image.copy())

        image = image.resize((int(image.width * self.image_scale), int(image.height * self.image_scale)), Image.LANCZOS)
        canvas.image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor=tk.NW, image=canvas.image)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        canvas.delete("bbox")

    def draw_bounding_boxes(self, image=None):
        if image is not None:
            draw = ImageDraw.Draw(image)
            font_path = "arial.ttf"
            font = ImageFont.truetype(font_path, 15) if os.path.exists(font_path) else ImageFont.load_default()

            for detection in self.detections:
                x1, y1, x2, y2 = detection['bbox']
                class_name = detection['class']
                confidence = detection['confidence']
                detection_id = detection['id']

                bbox_color = self.C['bbox_default']
                if self.selected_bbox is not None and detection_id == self.selected_bbox:
                    bbox_color = self.C['selected_bbox']

                draw.rectangle([x1, y1, x2, y2], outline=bbox_color, width=2)
                label = f"{detection_id}: {class_name} {confidence:.2f}"

                text_bbox = draw.textbbox((0, 0), label, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_bg = Image.new("RGB", (text_width + 6, text_height + 6), bbox_color)
                text_bg_draw = ImageDraw.Draw(text_bg)
                text_bg_draw.text((3, 3), label, fill="white", font=font)
                image.paste(text_bg, (x1, y1 - text_height - 6))

        comments = '\n'.join([f"ID {d['id']}: {d['comment']}" for d in self.detections if d['comment']])
        self.comment_text.delete("1.0", tk.END)
        self.comment_text.insert(tk.END, comments)
        self.update_annotations_tree()
        return image


    def toggle_original_bboxes(self):
        self.original_bboxes_visible = not self.original_bboxes_visible
        self.display_image(self.original_canvas, self.original_image, self.detections)
        icon = 'eye' if self.original_bboxes_visible else 'eye_off'
        self.original_bbox_btn.config(image=self.icons.get(icon), text='BBox')

    def toggle_processed_bboxes(self):
        self.processed_bboxes_visible = not self.processed_bboxes_visible
        self.display_image(self.processed_canvas, self.processed_image, self.detections)
        icon = 'eye' if self.processed_bboxes_visible else 'eye_off'
        self.processed_bbox_btn.config(image=self.icons.get(icon), text='BBox')

    def zoom_images(self, value):
        self.image_scale = float(value)
        self.zoom_slider.set_value(self.image_scale)
        x_str = f"{self.image_scale:.2f}x"
        self.zoom_pct.config(text=x_str)
        self.display_image(self.original_canvas, self.original_image, self.detections)
        self.display_image(self.processed_canvas, self.processed_image, self.detections)
            
    def fit_to_screen(self):
        if not self.original_image:
            return
        cw = self.original_canvas.winfo_width()
        ch = self.original_canvas.winfo_height()
        if cw > 1 and ch > 1:
            scale = min(cw / self.original_image.width, ch / self.original_image.height)
            self.zoom_images(scale)

    def toggle_fullscreen(self):
        self.fullscreen = not getattr(self, 'fullscreen', False)
        self.root.attributes('-fullscreen', self.fullscreen)

    def toggle_pan(self):
        self.pan_mode = not getattr(self, 'pan_mode', False)
        cursor = 'fleur' if self.pan_mode else 'cross'
        self.processed_canvas.config(cursor=cursor)
        self.original_canvas.config(cursor=cursor)

    def pan_start(self, event):
        self.original_canvas.scan_mark(event.x, event.y)

    def pan_move(self, event):
        self.original_canvas.scan_dragto(event.x, event.y, gain=1)
        self.sync_canvases()

    def sync_canvases(self):
        # Get the scroll region of the original canvas
        x0, x1 = self.original_canvas.xview()
        y0, y1 = self.original_canvas.yview()
        
        # Set the processed canvas view to match the original canvas
        self.processed_canvas.xview_moveto(x0)
        self.processed_canvas.yview_moveto(y0)

    def save_initial_state(self):
        self.initial_state = {
            'original_image': self.original_image,
            'processed_image': self.processed_image,
            'detections': [d.copy() for d in self.detections]
        }

    def restore(self):
        if self.initial_state:
            self.original_image = self.initial_state['original_image']
            self.processed_image = self.initial_state['processed_image']
            self.detections = [d.copy() for d in self.initial_state['detections']]
            self.display_image(self.original_canvas, self.original_image, self.detections)
            self.display_image(self.processed_canvas, self.processed_image, self.detections)
            self.update_comment_section()

    def undo(self):
        if self.history:
            last_state = self.history.pop()
            self.original_image = last_state['original_image']
            self.processed_image = last_state['processed_image']
            self.detections = last_state['detections']
            self.display_image(self.original_canvas, self.original_image, self.detections)
            self.display_image(self.processed_canvas, self.processed_image, self.detections)
            self.update_comment_section()

    def save_project(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".dicomet", filetypes=[("Dicomet Projects", "*.dicomet")])
        if file_path:
            project_data = {
                'original_image': self.original_image,
                'processed_image': self.processed_image,
                'dicom_image': self.dicom_image,
                'detections': self.detections,
                'comments': self.detection_comments
            }
            with open(file_path, 'wb') as file:
                pickle.dump(project_data, file)

    def load_project(self):
        file_path = filedialog.askopenfilename(defaultextension=".dicomet", filetypes=[("Dicomet Projects", "*.dicomet")])
        if file_path:
            with open(file_path, 'rb') as file:
                project_data = pickle.load(file)
                self.original_image = project_data['original_image']
                self.processed_image = project_data['processed_image']
                self.dicom_image = project_data['dicom_image']
                self.detections = project_data['detections']
                self.detection_comments = project_data['comments']
                self.display_image(self.original_canvas, self.original_image, self.detections)
                self.display_image(self.processed_canvas, self.processed_image, self.detections)
    def canvas_motion(self, event):
        bbox_id = self.find_bbox(event.x, event.y)
        if bbox_id is not None and self.is_resize_handle(event.x, event.y):
            self.processed_canvas.config(cursor="bottom_right_corner")
        elif bbox_id is not None:
            self.processed_canvas.config(cursor="fleur")
        else:
            self.processed_canvas.config(cursor="cross")

    def canvas_click(self, event):
        self.processed_canvas.focus_set()
        self.selected_bbox = self.find_bbox(event.x, event.y)
        if self.selected_bbox is not None:
            self.move_start = (event.x, event.y)
            self.resizing = self.is_resize_handle(event.x, event.y)
            self.processed_canvas.config(cursor="bottom_right_corner" if self.resizing else "fleur")
        self.draw_bounding_boxes()
        self.display_image(self.processed_canvas, self.processed_image, self.detections)

    def canvas_double_click(self, event):
        bbox_id = self.find_bbox(event.x, event.y)
        if bbox_id is not None:
            comment = simpledialog.askstring("Add Comment", f"Enter your comment for bbox ID {bbox_id}:")
            if comment:
                self.detection_comments[bbox_id] = comment
                self.detections[bbox_id]['comment'] = comment
                self.draw_bounding_boxes()
                self.log_history('Comment added')
                self.display_image(self.processed_canvas, self.processed_image, self.detections)

    def canvas_release(self, event):
        self.move_start = None
        self.resizing = False
        self.resize_handle = None
        self.processed_canvas.config(cursor="cross")
        self.draw_bounding_boxes()
        self.log_history('BBox moved')
        self.display_image(self.processed_canvas, self.processed_image, self.detections)

    def move_bounding_box(self, event):
        if self.selected_bbox is not None:
            dx = event.x - self.move_start[0]
            dy = event.y - self.move_start[1]
            self.move_start = (event.x, event.y)
            img_w, img_h = self.processed_image.width, self.processed_image.height
            bbox = list(self.detections[self.selected_bbox]['bbox'])
            if self.resizing:
                self.resize_bbox(bbox, dx, dy)
                bbox[2] = max(bbox[0] + 2, min(bbox[2], img_w))
                bbox[3] = max(bbox[1] + 2, min(bbox[3], img_h))
            else:
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                bbox[0] = max(0, min(bbox[0] + dx, img_w - w))
                bbox[1] = max(0, min(bbox[1] + dy, img_h - h))
                bbox[2] = bbox[0] + w
                bbox[3] = bbox[1] + h
            self.detections[self.selected_bbox]['bbox'] = tuple(bbox)
            self.draw_bounding_boxes()
            self.display_image(self.processed_canvas, self.processed_image, self.detections)

    def is_resize_handle(self, x, y):
        if self.selected_bbox is None:
            return False
        scale = self.image_scale
        ix = x / scale if scale else x
        iy = y / scale if scale else y
        bbox = self.detections[self.selected_bbox]['bbox']
        handle_size = 10
        x1, y1, x2, y2 = bbox
        if abs(ix - x2) <= handle_size and abs(iy - y2) <= handle_size:
            self.resize_handle = 'bottom_right'
            return True
        return False

    def resize_bbox(self, bbox, dx, dy):
        if self.resize_handle == 'bottom_right':
            bbox[2] += dx
            bbox[3] += dy

    def delete_bbox_keypress(self, event):
        if self.selected_bbox is not None:
            del self.detections[self.selected_bbox]
            for i, d in enumerate(self.detections):
                d['id'] = i
            self.selected_bbox = None
            self.draw_bounding_boxes()
            self.display_image(self.processed_canvas, self.processed_image, self.detections)
            self.log_history('BBOX Deleted')
            self.set_status(f"Deleted bbox, {len(self.detections)} remaining")
        return "break"

    def copy_bbox(self, event):
        if self.selected_bbox is not None:
            det = self.detections[self.selected_bbox]
            self.clipboard_bbox = {
                'bbox': det['bbox'],
                'class': det['class'],
                'confidence': det['confidence'],
                'comment': det.get('comment', '')
            }
            self.set_status(f"Copied bbox ID {det['id']}")
        return "break"

    def paste_bbox(self, event):
        if self.clipboard_bbox is not None:
            bbox = self.clipboard_bbox['bbox']
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            offset = 20
            new_bbox = (bbox[0] + offset, bbox[1] + offset, bbox[2] + offset, bbox[3] + offset)
            new_id = len(self.detections)
            self.detections.append({
                'id': new_id,
                'bbox': new_bbox,
                'class': self.clipboard_bbox['class'],
                'confidence': self.clipboard_bbox['confidence'],
                'comment': self.clipboard_bbox['comment']
            })
            self.selected_bbox = new_id
            self.draw_bounding_boxes()
            self.display_image(self.processed_canvas, self.processed_image, self.detections)
            self.set_status(f"Pasted bbox ID {new_id}")
        return "break"

    def find_bbox(self, x, y):
        scale = self.image_scale
        ix = x / scale if scale else x
        iy = y / scale if scale else y
        for detection in self.detections:
            x1, y1, x2, y2 = detection['bbox']
            if x1 <= ix <= x2 and y1 <= iy <= y2:
                return detection['id']
        return None

    def update_annotations_tree(self):
        for item in self.annotations_tree.get_children():
            self.annotations_tree.delete(item)
        for d in self.detections:
            cid = d['id']
            cls = d['class']
            conf = f"{d['confidence']:.0%}" if d['confidence'] <= 1 else f"{d['confidence']:.2f}"
            cmt = d.get('comment', '')
            self.annotations_tree.insert('', tk.END, values=(cid, cls, conf, cmt))

    def toggle_details_visibility(self):
        if self.details_window is not None and self.details_window.winfo_exists():
            self.details_window.lift()
            return
        win = tk.Toplevel(self.root)
        win.title("DICOM Details")
        win.geometry("600x500")
        win.configure(bg=self.C['panel'])
        txt = tk.Text(win, bg=self.C['entry_bg'], fg=self.C['text'],
                      font=('Consolas', self.FS['small']),
                      relief=tk.FLAT, borderwidth=0, padx=12, pady=12)
        txt.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)
        txt.insert(tk.END, getattr(self, 'dicom_text', 'No DICOM data loaded.'))
        txt.config(state=tk.DISABLED)
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_details(win))
        self.details_window = win

    def close_details(self, win):
        win.destroy()
        self.details_window = None

    def export_as_pdf(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No processed image to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=10)
            
            # Define logo images and their dimensions
            logo_viml = "VIML.png"
            logo_iitmandi = "IITMANDI.png"
            logo_width = 20  # Adjust as per your requirement
            logo_height = 20  # Adjust as per your requirement

            # Header with logos
            def add_header():
                pdf.image(logo_viml, x=10, y=8, w=logo_width)
                pdf.image(logo_iitmandi, x=pdf.w - logo_width - 10, y=8, w=logo_width)
                pdf.ln(20)  # Add a vertical space below the logos

            # Add the first page with header and main title
            pdf.add_page()
            add_header()
        
            # Title
            pdf.set_font("Arial", size=16, style='B')
            pdf.cell(200, 10, txt="Dicomet Report", ln=True, align="C")
            pdf.ln(10)  # Add a larger vertical space

            # File name and date/time
            pdf.set_font("Arial", size=12)
            file_name = os.path.basename(file_path)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(0, 10, txt=f"File Name: {file_name}", ln=True)
            pdf.cell(0, 10, txt=f"Date and Time: {current_datetime}", ln=True)
            pdf.ln(5)

            # Original and Processed Images Side by Side with Titles
            pdf.set_font("Arial", size=10, style='B')
            pdf.cell(90, 10, txt="Original Image", border=0, ln=0, align="C")
            pdf.cell(90, 10, txt="Processed Image", border=0, ln=1, align="C")
            pdf.ln(5)

            # Save and insert original image
            original_image_path = "original_image_temp.png"
            self.original_image.save(original_image_path)
            pdf.image(original_image_path, x=10, y=pdf.get_y(), w=90)
            os.remove(original_image_path)

            # Save and insert processed image
            processed_image_path = "processed_image_temp.png"
            self.processed_image.save(processed_image_path)
            pdf.image(processed_image_path, x=110, y=pdf.get_y(), w=90)
            os.remove(processed_image_path)

            pdf.ln(95)  # Ensure enough space after images


            case_count = 0

            for idx, detection in enumerate(self.detections):
                if detection['comment']:
                    case_number = case_count + 1
                    if case_count == 1 or case_count % 3 == 1:
                        pdf.add_page()  # Start a new page for every 3 cases
                        add_header()
                        pdf.ln(5)

                    # Case title
                    pdf.set_font("Arial", size=10, style='B')
                    pdf.cell(0, 10, txt=f"Case No : {case_number}", ln=True)
                
                    # ID and comment
                    pdf.set_font("Arial", size=10)
                    pdf.cell(0, 10, txt=f"ID {detection['id']} : {detection['comment']}", ln=True)
                    pdf.ln(5)

                    # Titles for Bbox Images
                    pdf.cell(90, 10, txt="Original Portion", border=0, ln=0, align="C")
                    pdf.cell(90, 10, txt="Original Portion with Bbox", border=0, ln=1, align="C")
                    pdf.ln(5)

                    # Original portion of the bbox
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox
                    temp_img_original_path = f"bbox_{case_number}_original_temp.png"
                    temp_img_original = self.original_image.crop((x1, y1, x2, y2))
                    temp_img_original.save(temp_img_original_path)
                    pdf.image(temp_img_original_path, x=30, y=pdf.get_y(), w=45)
                    os.remove(temp_img_original_path)

                    # Processed portion with only the main bbox
                    extra_x = int((x2 - x1) * 0.05)
                    extra_y = int((y2 - y1) * 0.05)
                    x1_exp = max(0, x1 - extra_x)
                    y1_exp = max(0, y1 - extra_y)
                    x2_exp = min(self.processed_image.width, x2 + extra_x)
                    y2_exp = min(self.processed_image.height, y2 + extra_y)

                    # Create a copy of the original image and draw only the specific bbox with details
                    temp_img_with_bbox = self.original_image.copy()
                    draw = ImageDraw.Draw(temp_img_with_bbox)
                    draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
                    text = f"{detection['id']}:{detection['class']} {detection['confidence']:.2f}"
                    text_bbox = draw.textbbox((x1, y1), text)
                    draw.rectangle(text_bbox, fill="red")
                    draw.text((x1, y1), text, fill="white")
                    temp_img_with_bbox_cropped = temp_img_with_bbox.crop((x1_exp, y1_exp, x2_exp, y2_exp))
                    temp_img_processed_path = f"bbox_{case_number}_processed_temp.png"
                    temp_img_with_bbox_cropped.save(temp_img_processed_path)
                    pdf.image(temp_img_processed_path, x=120, y=pdf.get_y(), w=45)  # Reduced width
                    os.remove(temp_img_processed_path)

                    pdf.ln(95)  # Add vertical space after images

                    case_count += 1

            # Save and close the PDF
            pdf.output(file_path)
            messagebox.showinfo("Export Successful", f"PDF saved to {file_path}")
            self.log_history('PDF Exported')
    
    def update_bounding_boxes(self):
        for bbox in self.bbox_handles.values():
            self.processed_canvas.delete(bbox)
        self.bbox_handles.clear()
        self.bbox_labels.clear()
        for detection in self.detections:
            x1, y1, x2, y2 = detection['bbox']
            bbox = self.processed_canvas.create_rectangle(x1, y1, x2, y2, outline='red')
            label = self.processed_canvas.create_text(x1, y1 - 10, anchor=tk.SW, text=f"ID {detection['id']}")
            self.bbox_handles[detection['id']] = bbox
            self.bbox_labels[detection['id']] = label

    def update_comment_section(self):
        self.comment_text.delete(1.0, tk.END)
        for detection in self.detections:
            comment = self.detection_comments.get(detection['id'], "")
            if comment:
                self.comment_text.insert(tk.END, f"ID {detection['id']}: {comment}\n")

    def export_modified_dicom(self):
        if self.dicom_image is None:
            messagebox.showerror("Error", "No DICOM image to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".dcm", filetypes=[("DICOM files", "*.dcm")])
        if file_path:
        # Update the DICOM metadata with bounding box and comment information
        # We will use private tags for this purpose (0019,xx00 to 0019,xxFF are commonly used for private data)
        
        # Clear any existing private tags in the range we plan to use
            for element in self.dicom_image.iterall():
                if (element.tag.group, element.tag.element) >= (0x0019, 0x1000) and (element.tag.group, element.tag.element) <= (0x0019, 0x10FF):
                    del self.dicom_image[element.tag]

        # Add new private tags for bounding boxes and comments
            for detection in self.detections:
                bbox = detection['bbox']
                comment = detection['comment']
                detection_id = detection['id']
                class_name = detection['class']
                confidence = detection['confidence']

                bbox_tag = pydicom.tag.Tag(0x0019, 0x1000 + detection_id)
                comment_tag = pydicom.tag.Tag(0x0019, 0x1080 + detection_id)

                bbox_data = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{class_name},{confidence:.2f}"
                self.dicom_image.add_new(bbox_tag, 'LT', bbox_data)

                if comment:
                    self.dicom_image.add_new(comment_tag, 'LT', comment)

        # Save the updated DICOM
            pydicom.dcmwrite(file_path, self.dicom_image)
            messagebox.showinfo("Success", f"Modified DICOM saved to {file_path}")
    
    def toggle_history_log(self):
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            return
        win = tk.Toplevel(self.root)
        win.title("History")
        win.geometry("450x400")
        win.configure(bg=self.C['panel'])
        self.history_listbox = tk.Listbox(win, bg=self.C['entry_bg'], fg=self.C['text'],
                                          font=('Segoe UI', self.FS['small']),
                                          relief=tk.FLAT, borderwidth=0,
                                          highlightthickness=0,
                                          selectbackground=self.C['accent_light'],
                                          selectforeground=self.C['accent'])
        self.history_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.history_listbox.bind('<Double-1>', self.revert_to_history_item)
        self.update_history_listbox()
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_history(win))
        self.history_window = win

    def close_history(self, win):
        self.history_listbox = None
        win.destroy()
        self.history_window = None

    def show_help(self):
        w = tk.Toplevel(self.root)
        w.title("Help")
        w.configure(bg=self.C['bg'])
        w.geometry("580x480")
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()

        inner = self.make_round_card(w, padx=14, pady=14, fill=tk.BOTH, expand=True)
        tk.Label(inner, text="Help & Keyboard Shortcuts",
                 bg=self.C['panel'], fg=self.C['accent'],
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 10))

        sections = [
            ("Mouse Controls",
             "• Left-click + drag on PROCESSED canvas → draw bounding box\n"
             "• Double-click a bbox → edit comment\n"
             "• Click + drag existing bbox → move it\n"
             "• Motion over bbox edge → resize handle"),
            ("Keyboard Shortcuts",
             "• Delete / D → delete selected bounding box\n"
             "• Ctrl+C → copy selected bbox\n"
             "• Ctrl+V → paste bbox\n"
             "• Dbl‑click on bbox → edit comment"),
            ("Filter Workflow",
             "1. Open an image (Open or DICOM button)\n"
             "2. Select model (YOLOv8 / DeepLabV3)\n"
             "3. Click Apply to run inference\n"
             "4. Edit / copy / delete bboxes as needed\n"
             "5. Export as PDF or modified DICOM"),
            ("Notes",
             "• Annotations are saved in the project file.\n"
             "• Use Undo / Restore to revert changes.\n"
             "• Zoom via the floating panel or the controls bar."),
        ]
        for title, body in sections:
            tk.Label(inner, text=title, bg=self.C['panel'], fg=self.C['text'],
                     font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(10, 2))
            tk.Label(inner, text=body, bg=self.C['panel'], fg=self.C['text_secondary'],
                     font=('Segoe UI', 9), justify=tk.LEFT).pack(anchor='w')

        tk.Button(inner, text="Close", command=w.destroy,
                  bg=self.C['accent'], fg=self.C['text_on_accent'],
                  relief=tk.FLAT, padx=20, pady=4,
                  font=('Segoe UI', 10),
                  activebackground=self.C['accent_hover'],
                  cursor='hand2').pack(pady=(16, 4))

    def show_settings(self):
        w = tk.Toplevel(self.root)
        w.title("Settings")
        w.configure(bg=self.C['bg'])
        w.geometry("400x340")
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()

        inner = self.make_round_card(w, padx=14, pady=14, fill=tk.BOTH, expand=True)
        tk.Label(inner, text="Settings",
                 bg=self.C['panel'], fg=self.C['accent'],
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 10))

        self.settings_vars = {}
        toggles = [
            ('show_bboxes', 'Show Bounding Boxes', True),
            ('auto_fit', 'Auto-Fit on Load', True),
            ('dark_canvas', 'Dark Canvas Background', False),
            ('zoom_smooth', 'Smooth Zoom', True),
        ]
        for key, label, default in toggles:
            var = tk.BooleanVar(value=default)
            self.settings_vars[key] = var
            cb = tk.Checkbutton(inner, text=label, variable=var,
                                bg=self.C['panel'], fg=self.C['text'],
                                selectcolor=self.C['panel'],
                                activebackground=self.C['panel'],
                                activeforeground=self.C['text'],
                                font=('Segoe UI', 10),
                                anchor='w', cursor='hand2')
            cb.pack(fill=tk.X, pady=3)

        tk.Button(inner, text="Apply", command=w.destroy,
                  bg=self.C['accent'], fg=self.C['text_on_accent'],
                  relief=tk.FLAT, padx=20, pady=4,
                  font=('Segoe UI', 10),
                  activebackground=self.C['accent_hover'],
                  cursor='hand2').pack(pady=(16, 4))

    def log_history(self, description):
        state = {
            'original_image': self.original_image.copy() if self.original_image else None,
            'processed_image': self.processed_image.copy() if self.processed_image else None,
            'detections': [d.copy() for d in self.detections],
            'description': description,
            'timestamp': datetime.now()
        }
        self.history.append(state)
        self.update_history_listbox()

    def update_history_listbox(self):
        if self.history_listbox is None:
            return
        self.history_listbox.delete(0, tk.END)
        for state in self.history:
            description = state['description']
            timestamp = state['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            self.history_listbox.insert(tk.END, f"{timestamp} - {description}")

    def revert_to_history_item(self, event):
        if self.history_listbox is None:
            return
        selected_index = self.history_listbox.curselection()[0]
        selected_state = self.history[selected_index]
        self.processed_image = selected_state['image']
        self.display_image(self.processed_canvas, self.processed_image)

if __name__ == "__main__":
    root = tk.Tk()
    app = Dicomet(root)
    # root.wm_iconbitmap('MedImagePro.ico')
    root.mainloop()     