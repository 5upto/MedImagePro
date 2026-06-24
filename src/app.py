import os
import ctypes
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import StringVar
from PIL import Image, ImageTk, ImageSequence
from ultralytics import YOLO
from torchvision.models.segmentation import deeplabv3_resnet50

from src.ui.widgets import WidgetsMixin
from src.ui.dialogs import DialogsMixin
from src.core.image_ops import ImageOpsMixin
from src.core.annotation_ops import AnnotationOpsMixin
from src.core.export_ops import ExportOpsMixin
from src.core.state_ops import StateOpsMixin

class Dicomet(WidgetsMixin, DialogsMixin, ImageOpsMixin, AnnotationOpsMixin, ExportOpsMixin, StateOpsMixin):
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

    def __init__(self, root):
        self.root = root
        self.root.title("Dicomet")
        self.root.configure(bg=self.C['bg'])
        self.root.minsize(1100, 700)

        # Resources directory is one level above the src folder
        self.res_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Resources'))

        if os.name == 'nt':
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

        try:
            icon_img = Image.open(os.path.join(self.res_dir, 'app.png'))
            bbox = icon_img.getbbox()
            if bbox:
                icon_img = icon_img.crop(bbox)
            self.win_icon = ImageTk.PhotoImage(icon_img)
            self.root.iconphoto(True, self.win_icon)
        except Exception as e:
            print("Window icon load error:", e)

        self.setup_styles()
        self.load_icons()

        self.model = YOLO(os.path.join(self.res_dir, 'yolov8l.pt'))
        self.deeplab_model = deeplabv3_resnet50(weights='DEFAULT').eval()

        # ── HEADER ───────────────────────────────────────
        hdr = tk.Frame(root, bg=self.C['panel'], highlightthickness=0)
        hdr.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(hdr, height=1, bg=self.C['border']).pack(side=tk.BOTTOM, fill=tk.X)

        left = tk.Frame(hdr, bg=self.C['panel'])
        left.pack(side=tk.LEFT, padx=14, pady=6)
        
        # Load and place app.png in the brand area
        try:
            img = Image.open(os.path.join(self.res_dir, 'app.png'))
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            img = img.resize((32, 32), Image.LANCZOS)
            self.logo_app_png = ImageTk.PhotoImage(img)
            tk.Label(left, image=self.logo_app_png, bg=self.C['panel']).pack(side=tk.LEFT, padx=(0, 10))
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

        # Load and place IITMANDI and VIML logos in the footer
        try:
            for f, s in [('VIML.png', 18), ('IITMANDI.png', 20)]:
                img = Image.open(os.path.join(self.res_dir, f)).resize((s, s), Image.LANCZOS)
                attr_name = f"logo_{f.replace('.', '_')}"
                setattr(self, attr_name, ImageTk.PhotoImage(img))
            tk.Label(sb, image=self.logo_VIML_png, bg=self.C['panel']).pack(side=tk.RIGHT, padx=(4, 0))
            tk.Label(sb, image=self.logo_IITMANDI_png, bg=self.C['panel']).pack(side=tk.RIGHT, padx=(4, 0))
        except Exception as e:
            print("Footer logos load error:", e)

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
        loading_image = Image.open(os.path.join(self.res_dir, 'loading.gif'))
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
