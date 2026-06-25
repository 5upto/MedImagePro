import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import StringVar

from PIL import Image, ImageTk, ImageSequence


class LayoutMixin:
    def build_layout(self):
        self._build_header()
        self._build_toolbar()
        self._build_main_workspace()
        self._build_annotations_panel()
        self._build_status_bar()
        self._bind_canvas_events()
        self._load_loading_frames()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=self.C['panel'], highlightthickness=0)
        hdr.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(hdr, height=1, bg=self.C['border']).pack(side=tk.BOTTOM, fill=tk.X)

        left = tk.Frame(hdr, bg=self.C['panel'])
        left.pack(side=tk.LEFT, padx=14, pady=6)

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

        title = tk.Frame(left, bg=self.C['panel'])
        title.pack(side=tk.LEFT)
        tk.Label(title, text="Dicomet", bg=self.C['panel'], fg=self.C['text'],
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        tk.Label(title, text="Intelligent DICOM Imaging", bg=self.C['panel'],
                 fg=self.C['text_secondary'],
                 font=('Segoe UI', 9)).pack(anchor='w')

        right = tk.Frame(hdr, bg=self.C['panel'])
        right.pack(side=tk.RIGHT, padx=12, pady=6)
        self.make_btn(right, 'info', '', self.show_help, padx=4, pady=2,
                      font_size=self.FS['tiny']).pack(side=tk.RIGHT, padx=1)
        self.make_btn(right, 'cog', '', self.show_settings, padx=4, pady=2,
                      font_size=self.FS['tiny']).pack(side=tk.RIGHT, padx=1)

    def _build_toolbar(self):
        tb_card = self.make_round_card(self.root, padx=14, pady=(4, 1), fill=tk.X,
                                       content_inset=2)
        tb_row = tk.Frame(tb_card, bg=self.C['panel'])
        tb_row.pack(side=tk.TOP, fill=tk.X)

        groups = [
            [('folder', 'Open', self.load_image), ('save', 'Save', self.save_project), ('load', 'Load', self.load_project)],
            [('play', 'Apply', self.apply_filter)],
            [('undo', 'Undo', self.undo), ('restore', 'Restore', self.restore)],
            [('pdf', 'PDF', self.export_as_pdf), ('dicom', 'DICOM', self.export_modified_dicom)],
            [('info', 'Details', self.toggle_details_visibility), ('history', 'History', self.toggle_history_log)],
        ]
        for group_index, group in enumerate(groups):
            if group_index:
                self.make_sep(tb_row)
            group_container = self.make_round_card(tb_row, side=tk.LEFT, fill=tk.X,
                                                   padx=1, pady=0, corner_radius=10,
                                                   content_inset=1)
            group_inner = tk.Frame(group_container, bg=self.C['panel'])
            group_inner.pack(side=tk.TOP, fill=tk.X)
            for icon_name, text, command in group:
                is_apply = text == 'Apply'
                bg = self.C['accent'] if is_apply else self.C['panel']
                fg = self.C['text_on_accent'] if is_apply else self.C['text']
                hover = self.C['accent_hover'] if is_apply else self.C['accent_light']
                btn = self.make_btn(group_inner, icon_name, text, command,
                                    btn_bg=bg, btn_fg=fg, hover_bg=hover,
                                    padx=8, pady=3, font_size=self.FS['small'])
                btn.pack(side=tk.LEFT)
                if text == 'Details':
                    self.details_toggle_button = btn
                elif text == 'History':
                    self.history_button = btn

        self.model_var = StringVar(self.root)
        self.model_var.set("YOLOv8")
        model_menu_card = self.make_round_card(tb_row, side=tk.RIGHT, fill=tk.X,
                                               padx=1, pady=0, corner_radius=10,
                                               content_inset=1)
        self.model_menu = tk.OptionMenu(model_menu_card, self.model_var, "YOLOv8", "DeepLabV3")
        self.model_menu.config(bg=self.C['panel'], fg=self.C['text'],
                               relief=tk.FLAT, highlightthickness=0,
                               borderwidth=0, font=('Segoe UI', self.FS['button']),
                               cursor='hand2', padx=6, pady=2,
                               activebackground=self.C['accent_light'],
                               activeforeground=self.C['accent'])
        self.model_menu['menu'].configure(bg=self.C['panel'], fg=self.C['text'],
                                          activebackground=self.C['accent_light'],
                                          activeforeground=self.C['accent'],
                                          font=('Segoe UI', self.FS['normal']))
        self.model_menu.pack(side=tk.TOP, fill=tk.X)

    def _build_main_workspace(self):
        self.main_frame = tk.Frame(self.root, bg=self.C['bg'])
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.details_window = None
        self.history_window = None
        self.history_listbox = None

        workspace = tk.Frame(self.main_frame, bg=self.C['bg'])
        workspace.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=14, pady=6)

        image_row = tk.Frame(workspace, bg=self.C['bg'])
        image_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.original_panel, self.original_canvas, self.original_bbox_btn = self._make_viewer(
            image_row, 'ORIGINAL', self.C['original_accent'],
            'original_bboxes_visible', self.toggle_original_bboxes)

        self.processed_panel, self.processed_canvas, self.processed_bbox_btn = self._make_viewer(
            image_row, 'PROCESSED', self.C['processed_accent'],
            'processed_bboxes_visible', self.toggle_processed_bboxes)

        self._build_bottom_controls(workspace)

    def _make_viewer(self, parent, label_text, accent_color, bbox_attr, toggle_fn):
        card = self.make_round_card(parent, side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        toolbar = tk.Frame(card, bg=self.C['panel'])
        toolbar.pack(side=tk.TOP, fill=tk.X)
        label_bg = tk.Frame(toolbar, bg=self.C['panel'])
        label_bg.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(label_bg, text=label_text, bg=self.C['panel'], fg=accent_color,
                 font=('Segoe UI', 9, 'bold'), anchor='w',
                 padx=6, pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = self.make_btn(toolbar, 'eye_off', 'BBox', toggle_fn,
                            padx=6, pady=2, font_size=self.FS['tiny'])
        btn.pack(side=tk.RIGHT, padx=4, pady=3)
        setattr(self, bbox_attr, True)
        canvas = tk.Canvas(card, bg=self.C['canvas_bg'], cursor='cross',
                           relief=tk.FLAT, borderwidth=0,
                           highlightthickness=0)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        return card, canvas, btn

    def _build_bottom_controls(self, parent):
        ctrl_card = self.make_round_card(parent, fill=tk.X, pady=(2, 1),
                                         content_inset=2)
        ctrl = tk.Frame(ctrl_card, bg=self.C['panel'])
        ctrl.pack(side=tk.TOP, fill=tk.X)

        self.make_btn(ctrl, 'pan', 'Hand', self.toggle_pan, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_btn(ctrl, 'fit', 'Fit', self.fit_to_screen, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_btn(ctrl, 'fullscreen', 'Full', self.toggle_fullscreen, padx=8, pady=3,
                      font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=2)
        self.make_sep(ctrl)
        zoom_row = tk.Frame(ctrl, bg=self.C['panel'])
        zoom_row.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Label(zoom_row, text="Zoom:", bg=self.C['panel'], fg=self.C['text_secondary'],
                 font=('Segoe UI', self.FS['tiny'])).pack(side=tk.LEFT, padx=(0, 6))
        self.make_btn(zoom_row, 'zoom_out', '', None, padx=5, pady=2).pack(side=tk.LEFT)
        self.zoom_slider = self._make_modern_slider(
            zoom_row, command=self.zoom_images,
            from_=10, to=0.1, initial=1,
            orient='horizontal', length=140)
        self.zoom_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.make_btn(zoom_row, 'zoom_in', '', None, padx=5, pady=2).pack(side=tk.LEFT)
        self.zoom_pct = tk.Label(zoom_row, text="1.00x", bg=self.C['panel'], fg=self.C['text'],
                                 font=('Segoe UI', 8, 'bold'))
        self.zoom_pct.pack(side=tk.LEFT, padx=(6, 0))

    def _build_annotations_panel(self):
        ann_card = self.make_round_card(self.root, padx=14, pady=(2, 6), fill=tk.X)
        inner = tk.Frame(ann_card, bg=self.C['panel'])
        inner.pack(side=tk.TOP, fill=tk.X)

        header = tk.Frame(inner, bg=self.C['panel'])
        header.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(4, 2))
        tk.Label(header, text="ANNOTATIONS", bg=self.C['panel'], fg=self.C['accent'],
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        actions = tk.Frame(header, bg=self.C['panel'])
        actions.pack(side=tk.RIGHT)
        for icon_name, text, command in [('pencil', 'Edit', None), ('copy', 'Copy', None),
                                         ('delete', 'Delete', None)]:
            self.make_btn(actions, icon_name, text, command, padx=6, pady=2,
                          font_size=self.FS['tiny']).pack(side=tk.LEFT, padx=1)

        table_frame = self.make_round_card(inner, side=tk.TOP, fill=tk.X,
                                           padx=6, pady=(0, 4), corner_radius=10)

        self.annotations_tree = ttk.Treeview(table_frame, columns=('id', 'class', 'confidence', 'comment'),
                                             show='headings', height=4, selectmode='browse')
        for col, width, heading in [('id', 40, 'ID'), ('class', 100, 'CLASS'),
                                    ('confidence', 80, 'CONFIDENCE'),
                                    ('comment', 400, 'COMMENT')]:
            self.annotations_tree.column(col, width=width, anchor='w')
            self.annotations_tree.heading(col, text=heading, anchor='w')
        self.annotations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.annotations_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotations_tree.configure(yscrollcommand=scrollbar.set)

        self.comment_text = tk.Text(self.root, height=1)

    def _build_status_bar(self):
        status_frame = tk.Frame(self.root, bg=self.C['panel'])
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(status_frame, height=1, bg=self.C['border']).pack(side=tk.TOP, fill=tk.X)
        status_bar = tk.Frame(status_frame, bg=self.C['panel'])
        status_bar.pack(side=tk.TOP, fill=tk.X, padx=14, pady=3)

        dot = tk.Canvas(status_bar, width=6, height=6, bg=self.C['panel'], highlightthickness=0)
        dot.pack(side=tk.LEFT, padx=(0, 5))
        dot.create_oval(0, 0, 6, 6, fill=self.C['success'], outline='')
        self.status_label = tk.Label(status_bar, text="Ready", bg=self.C['panel'],
                                     fg=self.C['text_secondary'],
                                     font=('Segoe UI', self.FS['status']))
        self.status_label.pack(side=tk.LEFT)
        self.image_info_label = tk.Label(status_bar, text="", bg=self.C['panel'],
                                         fg=self.C['text_secondary'],
                                         font=('Segoe UI', self.FS['status']))
        self.image_info_label.pack(side=tk.LEFT, padx=(18, 0))

        try:
            for filename, size in [('VIML.png', 18), ('IITMANDI.png', 20)]:
                img = Image.open(os.path.join(self.res_dir, filename)).resize((size, size), Image.LANCZOS)
                attr_name = f"logo_{filename.replace('.', '_')}"
                setattr(self, attr_name, ImageTk.PhotoImage(img))
            tk.Label(status_bar, image=self.logo_VIML_png, bg=self.C['panel']).pack(side=tk.RIGHT, padx=(4, 0))
            tk.Label(status_bar, image=self.logo_IITMANDI_png, bg=self.C['panel']).pack(side=tk.RIGHT, padx=(4, 0))
        except Exception as e:
            print("Footer logos load error:", e)

    def _bind_canvas_events(self):
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

    def _load_loading_frames(self):
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
