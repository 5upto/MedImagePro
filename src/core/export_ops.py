import os
import pickle
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from PIL import Image, ImageDraw
from fpdf import FPDF
import pydicom

class ExportOpsMixin:
    def export_as_pdf(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No processed image to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=10)
            
            logo_viml = os.path.join(self.res_dir, "VIML.png")
            logo_iitmandi = os.path.join(self.res_dir, "IITMANDI.png")
            logo_width = 20
            logo_height = 20

            def add_header():
                pdf.image(logo_viml, x=10, y=8, w=logo_width)
                pdf.image(logo_iitmandi, x=pdf.w - logo_width - 10, y=8, w=logo_width)
                pdf.ln(20)

            pdf.add_page()
            add_header()
        
            pdf.set_font("Arial", size=16, style='B')
            pdf.cell(200, 10, txt="Dicomet Report", ln=True, align="C")
            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            file_name = os.path.basename(file_path)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(0, 10, txt=f"File Name: {file_name}", ln=True)
            pdf.cell(0, 10, txt=f"Date and Time: {current_datetime}", ln=True)
            pdf.ln(5)

            pdf.set_font("Arial", size=10, style='B')
            pdf.cell(90, 10, txt="Original Image", border=0, ln=0, align="C")
            pdf.cell(90, 10, txt="Processed Image", border=0, ln=1, align="C")
            pdf.ln(5)

            original_image_path = "original_image_temp.png"
            self.original_image.save(original_image_path)
            pdf.image(original_image_path, x=10, y=pdf.get_y(), w=90)
            os.remove(original_image_path)

            processed_image_path = "processed_image_temp.png"
            self.processed_image.save(processed_image_path)
            pdf.image(processed_image_path, x=110, y=pdf.get_y(), w=90)
            os.remove(processed_image_path)

            pdf.ln(95)

            case_count = 0
            for idx, detection in enumerate(self.detections):
                if detection['comment']:
                    case_number = case_count + 1
                    if case_count == 1 or case_count % 3 == 1:
                        pdf.add_page()
                        add_header()
                        pdf.ln(5)

                    pdf.set_font("Arial", size=10, style='B')
                    pdf.cell(0, 10, txt=f"Case No : {case_number}", ln=True)
                
                    pdf.set_font("Arial", size=10)
                    pdf.cell(0, 10, txt=f"ID {detection['id']} : {detection['comment']}", ln=True)
                    pdf.ln(5)

                    pdf.cell(90, 10, txt="Original Portion", border=0, ln=0, align="C")
                    pdf.cell(90, 10, txt="Original Portion with Bbox", border=0, ln=1, align="C")
                    pdf.ln(5)

                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox
                    temp_img_original_path = f"bbox_{case_number}_original_temp.png"
                    temp_img_original = self.original_image.crop((x1, y1, x2, y2))
                    temp_img_original.save(temp_img_original_path)
                    pdf.image(temp_img_original_path, x=30, y=pdf.get_y(), w=45)
                    os.remove(temp_img_original_path)

                    extra_x = int((x2 - x1) * 0.05)
                    extra_y = int((y2 - y1) * 0.05)
                    x1_exp = max(0, x1 - extra_x)
                    y1_exp = max(0, y1 - extra_y)
                    x2_exp = min(self.processed_image.width, x2 + extra_x)
                    y2_exp = min(self.processed_image.height, y2 + extra_y)

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
                    pdf.image(temp_img_processed_path, x=120, y=pdf.get_y(), w=45)
                    os.remove(temp_img_processed_path)

                    pdf.ln(95)
                    case_count += 1

            pdf.output(file_path)
            messagebox.showinfo("Export Successful", f"PDF saved to {file_path}")
            self.log_history('PDF Exported')

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
            for element in list(self.dicom_image.iterall()):
                if (element.tag.group, element.tag.element) >= (0x0019, 0x1000) and (element.tag.group, element.tag.element) <= (0x0019, 0x10FF):
                    del self.dicom_image[element.tag]

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

            pydicom.dcmwrite(file_path, self.dicom_image)
            messagebox.showinfo("Success", f"Modified DICOM saved to {file_path}")
