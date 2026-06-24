import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font as tkfont


def _draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    radius = max(0, min(radius, int((x2 - x1) / 2), int((y2 - y1) / 2)))
    if radius == 0:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, image=None, text="", command=None, bg="#FFFFFF",
                 fg="#1E293B", hover_bg="#DBEAFE", border="#DCE3EB",
                 active_fg=None, padx=10, pady=5, font=None, corner_radius=8):
        self._font = tkfont.Font(font=font)
        self._image = image
        self._text = text
        self._command = command
        self._normal_bg = bg
        self._hover_bg = hover_bg
        self._fg = fg
        self._active_fg = active_fg or fg
        self._border = border
        self._padx = padx
        self._pady = pady
        self._corner_radius = corner_radius
        width, height = self._measure()
        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'),
                         highlightthickness=0, relief=tk.FLAT, cursor='hand2')
        self._current_bg = bg
        self._current_fg = fg
        self._draw()
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

    def _measure(self):
        icon_width = self._image.width() if self._image else 0
        icon_height = self._image.height() if self._image else 0
        text_width = self._font.measure(self._text) if self._text else 0
        text_height = self._font.metrics('linespace')
        gap = 6 if icon_width and text_width else 0
        width = max(28, icon_width + gap + text_width + self._padx * 2)
        height = max(24, max(icon_height, text_height) + self._pady * 2)
        return width, height

    def _draw(self):
        self.delete('all')
        width, height = self._measure()
        self.configure(width=width, height=height)
        _draw_rounded_rect(self, 1, 1, width - 1, height - 1, self._corner_radius,
                           fill=self._current_bg, outline=self._border, width=1)

        icon_width = self._image.width() if self._image else 0
        text_width = self._font.measure(self._text) if self._text else 0
        gap = 6 if icon_width and text_width else 0
        content_width = icon_width + gap + text_width
        x = (width - content_width) / 2

        if self._image:
            self.create_image(x, height / 2, image=self._image, anchor=tk.W)
            x += icon_width + gap

        if self._text:
            self.create_text(x, height / 2, text=self._text, fill=self._current_fg,
                             font=self._font, anchor=tk.W)

    def _on_enter(self, event):
        self._current_bg = self._hover_bg
        self._current_fg = self._active_fg
        self._draw()

    def _on_leave(self, event):
        self._current_bg = self._normal_bg
        self._current_fg = self._fg
        self._draw()

    def _on_click(self, event):
        if self._command:
            self._command()

    def configure(self, cnf=None, **kwargs):
        custom_keys = {
            'image', 'text', 'command', 'bg', 'fg', 'activebackground',
            'activeforeground', 'highlightbackground', 'corner_radius'
        }
        needs_redraw = False
        for key in list(kwargs):
            if key not in custom_keys:
                continue
            value = kwargs.pop(key)
            if key == 'image':
                self._image = value
            elif key == 'text':
                self._text = value
            elif key == 'command':
                self._command = value
            elif key == 'bg':
                self._normal_bg = value
                self._current_bg = value
            elif key == 'fg':
                self._fg = value
                self._current_fg = value
            elif key == 'activebackground':
                self._hover_bg = value
            elif key == 'activeforeground':
                self._active_fg = value
            elif key == 'highlightbackground':
                self._border = value
            elif key == 'corner_radius':
                self._corner_radius = value
            needs_redraw = True
        result = super().configure(cnf, **kwargs)
        if needs_redraw:
            self._draw()
        return result

    config = configure


class RoundedCard:
    def __init__(self, parent, bg, border, corner_radius, parent_bg):
        self.outer = tk.Canvas(parent, bg=parent_bg, highlightthickness=0,
                               relief=tk.FLAT, borderwidth=0)
        self.inner = tk.Frame(self.outer, bg=bg)
        self._bg = bg
        self._border = border
        self._corner_radius = corner_radius
        self._inset = max(4, corner_radius // 2)
        self._window_id = self.outer.create_window(self._inset, self._inset,
                                                   anchor=tk.NW, window=self.inner)
        self.inner._rounded_outer = self.outer
        self.inner._rounded_card = self
        self.outer.bind('<Configure>', self._redraw)
        self.inner.bind('<Configure>', self._sync_size)

    def pack(self, **kwargs):
        self.outer.pack(**kwargs)
        return self.inner

    def _sync_size(self, event=None):
        req_width = self.inner.winfo_reqwidth() + self._inset * 2
        req_height = self.inner.winfo_reqheight() + self._inset * 2
        self.outer.configure(width=req_width, height=req_height)
        self._redraw()

    def _redraw(self, event=None):
        width = max(self.outer.winfo_width(), self.inner.winfo_reqwidth() + self._inset * 2)
        height = max(self.outer.winfo_height(), self.inner.winfo_reqheight() + self._inset * 2)
        self.outer.delete('card')
        _draw_rounded_rect(self.outer, 0, 0, width - 1, height - 1,
                           self._corner_radius, fill=self._bg,
                           outline=self._border, width=1, tags='card')
        self.outer.tag_lower('card')
        inner_width = max(1, width - self._inset * 2)
        inner_height = max(1, height - self._inset * 2)
        self.outer.coords(self._window_id, self._inset, self._inset)
        self.outer.itemconfigure(self._window_id, width=inner_width, height=inner_height)

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
                 hover_bg=None, padx=10, pady=5, font_size=None, corner_radius=8):
        icon = self.icons.get(icon_name)
        bg = btn_bg or self.C['panel']
        fg = btn_fg or self.C['text']
        hover = hover_bg or self.C['accent_light']
        btn = RoundedButton(parent, image=icon, text=text, command=command,
                            bg=bg, fg=fg, hover_bg=hover,
                            border=self.C['border'], active_fg=self.C['text'],
                            padx=padx, pady=pady,
                            font=('Segoe UI', font_size or self.FS['button']),
                            corner_radius=corner_radius)
        return btn

    def make_sep(self, parent, height=28, width=1):
        s = tk.Frame(parent, width=width, bg=self.C['border'])
        s.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=5)
        return s

    def make_round_card(self, parent, padx=0, pady=0, side=tk.TOP, fill=tk.X,
                        expand=False, corner_radius=10):
        try:
            parent_bg = parent.cget('bg')
        except tk.TclError:
            parent_bg = self.C['bg']
        card = RoundedCard(parent, self.C['panel'], self.C['border'],
                           corner_radius, parent_bg)
        return card.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)

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
