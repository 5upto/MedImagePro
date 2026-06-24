import ctypes
import os

from PIL import Image, ImageTk
from ultralytics import YOLO
from torchvision.models.segmentation import deeplabv3_resnet50

from src.core.annotation_ops import AnnotationOpsMixin
from src.core.export_ops import ExportOpsMixin
from src.core.image_ops import ImageOpsMixin
from src.core.state_ops import StateOpsMixin
from src.ui.dialogs import DialogsMixin
from src.ui.layout import LayoutMixin
from src.ui.widgets import WidgetsMixin


class Dicomet(LayoutMixin, WidgetsMixin, DialogsMixin, ImageOpsMixin, AnnotationOpsMixin, ExportOpsMixin, StateOpsMixin):
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

        self.res_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Resources'))

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

        self.build_layout()
        self._init_state()

    def _init_state(self):
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

    def set_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()
