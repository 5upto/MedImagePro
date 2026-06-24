import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font as tkfont
from PIL import Image, ImageTk

class WidgetsMixin:
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
        res_dir = self.res_dir
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
