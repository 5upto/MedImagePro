import os
import tkinter as tk
from PIL import Image, ImageTk

class DialogsMixin:
    def show_loading_animation(self):
        if self.loading_overlay:
            return
        
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
        self.loading_overlay.attributes("-alpha", 0.75)

        def sync_geometry(event=None):
            if self.loading_overlay and self.loading_overlay.winfo_exists():
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                self.loading_overlay.geometry(f"{w}x{h}+{x}+{y}")

        sync_geometry()
        self.configure_bind_id = self.root.bind("<Configure>", sync_geometry)

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
