import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import numpy as np
import pydicom
import threading
from torchvision import transforms
import torch

class ImageOpsMixin:
    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.set_status(f"Loading {os.path.basename(file_path)}...")
            if file_path.lower().endswith('.dcm'):
                self.dicom_image = pydicom.dcmread(file_path)
                pixel_array = self.dicom_image.pixel_array
                
                # Squeeze singleton dimensions (e.g., (1, H, W) -> (H, W))
                if pixel_array.ndim > 2:
                    for axis in reversed(range(pixel_array.ndim)):
                        if pixel_array.shape[axis] == 1 and pixel_array.ndim > 2:
                            pixel_array = np.squeeze(pixel_array, axis=axis)
                
                # Handle multi-dimensional arrays (multi-frame / volumes)
                if pixel_array.ndim == 4:
                    pixel_array = pixel_array[0]
                
                if pixel_array.ndim == 3:
                    if pixel_array.shape[-1] not in (3, 4):
                        mid_idx = pixel_array.shape[0] // 2
                        pixel_array = pixel_array[mid_idx]
                
                pixel_array = self.normalize_pixel_array(pixel_array)
                
                if pixel_array.ndim == 3 and pixel_array.shape[-1] in (3, 4):
                    image = Image.fromarray(pixel_array)
                else:
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
        elif np.issubdtype(pixel_array.dtype, np.floating):
            pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array))
            pixel_array = (pixel_array * 255).astype(np.uint8)
        return pixel_array

    def apply_filter(self):
        if self.processed_image:
            self.show_loading_animation()
            threading.Thread(target=self.apply_filter_in_background).start()

    def apply_filter_in_background(self):
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
        x0, x1 = self.original_canvas.xview()
        y0, y1 = self.original_canvas.yview()
        self.processed_canvas.xview_moveto(x0)
        self.processed_canvas.yview_moveto(y0)
