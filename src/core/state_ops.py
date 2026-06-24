import tkinter as tk
from datetime import datetime

class StateOpsMixin:
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
        self.processed_image = selected_state['processed_image']
        self.display_image(self.processed_canvas, self.processed_image)
