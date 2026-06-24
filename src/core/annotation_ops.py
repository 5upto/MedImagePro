import tkinter as tk
from tkinter import simpledialog

class AnnotationOpsMixin:
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
