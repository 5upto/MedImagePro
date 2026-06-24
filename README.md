# Dicomet

**Intelligent DICOM Imaging Platform**

Dicomet is a desktop application for medical image visualization, AI-assisted analysis, annotation, and reporting. It enables medical professionals, researchers, and imaging specialists to work with DICOM studies and standard image formats while leveraging state-of-the-art deep learning models for detection and segmentation.

---

## Features

### Medical Image Visualization

* Load DICOM (`.dcm`) files
* Load standard image formats (`PNG`, `JPG`, `JPEG`)
* Automatic image normalization and rendering
* DICOM metadata extraction and inspection
* Side-by-side original and processed image viewing
* Synchronized zoom and pan navigation

### AI-Powered Analysis

#### YOLOv8 Object Detection

* Automatic object detection
* Bounding box generation
* Confidence scoring
* Class labeling
* Interactive post-processing

#### DeepLabV3 Semantic Segmentation

* Semantic segmentation of medical images
* Overlay visualization
* Processed image comparison

### Annotation Tools

* Select annotations
* Move annotations
* Resize annotations
* Delete annotations
* Copy and paste annotations
* Add comments to findings
* Toggle annotation visibility
* Real-time annotation updates

### Project Management

* Save complete analysis sessions
* Load previously saved projects
* Preserve annotations and comments
* Restore workspace state

### History & Recovery

* Action history tracking
* Undo operations
* Restore original image state
* Snapshot-based recovery

### Export & Reporting

#### PDF Report Export

Generate professional reports containing:

* Original images
* Processed images
* Findings
* Annotation summaries
* User comments
* Timestamped reports

#### DICOM Export

* Export annotated DICOM studies
* Preserve annotation metadata
* Store findings using DICOM private tags

### DICOM Metadata Support

* Read DICOM headers
* View patient and study metadata
* Inspect acquisition information
* Browse complete metadata records

---

## Supported File Formats

### Input

* DICOM (`.dcm`)
* PNG
* JPG
* JPEG

### Output

* PDF Reports
* Annotated DICOM Files
* Dicomet Project Files (`.mip`)

---

## Supported AI Models

| Model              | Purpose               |
| ------------------ | --------------------- |
| YOLOv8             | Object Detection      |
| DeepLabV3-ResNet50 | Semantic Segmentation |

---

## Technology Stack

### Core

* Python
* Tkinter
* Pillow (PIL)
* NumPy

### Medical Imaging

* PyDICOM

### Deep Learning

* PyTorch
* TorchVision
* Ultralytics YOLOv8

### Utilities

* Threading
* Pickle
* JSON

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/dicomet.git
cd dicomet
```

### Create a Virtual Environment

```bash
python -m venv venv
```

### Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running Dicomet

```bash
python app.py
```

---

## Project Structure

```text
MedImagePro/
│
├── Resources/
├── venv/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Typical Workflow

1. Load a DICOM study or image.
2. Review metadata and image details.
3. Apply an AI model:

   * YOLOv8 for object detection
   * DeepLabV3 for segmentation
4. Review generated results.
5. Edit annotations if necessary.
6. Add comments and findings.
7. Save the project.
8. Export a PDF report or annotated DICOM study.

---

## Future Roadmap

* Multi-slice DICOM series support
* 3D volume visualization
* Advanced measurement tools
* Additional AI models
* PACS integration
* Multi-user collaboration
* Clinical workflow enhancements

---

## Disclaimer

Dicomet is intended for research, educational, and workflow-assistance purposes. AI-generated detections, segmentations, and annotations should always be reviewed and validated by qualified medical professionals before clinical use.

