# Liver Health System

A Flask web application for analyzing liver health through enzyme levels and medical image processing. The system provides a bilingual (Arabic/English) interface for clinicians and patients.

## Features

### Enzyme Analysis
- Input patient details and liver enzyme values (ALT, AST, ALP, GGT, Bilirubin)
- Automatic interpretation against normal ranges
- Detailed diagnostic report with recommendations

### Cancer Detection
- Upload liver X‑Ray/MRI images
- 5‑stage image processing pipeline:
  1. Grayscale conversion
  2. Bilateral filter (noise reduction)
  3. CLAHE (contrast enhancement)
  4. Morphological Black‑Hat (dark region extraction)
  5. Thresholding and contour detection for tumor localization
- Visual output of each processing step
- Clear indication of suspicious areas

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AIOL-HQ/liver-health-system
   cd liver-health-system
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python liver_system.py
```
The server will start at `http://127.0.0.1:5000/` and open automatically in your default browser.

### Enzyme Analysis
- Navigate to the home page (`/`)
- Fill in patient name, age, and enzyme values
- Click the diagnosis button to see the report

### Cancer Detection
- Click “فحص الكانسر بالصور” (Cancer Scan) in the navigation bar
- Upload a liver image (X‑Ray, MRI, etc.)
- Click the analysis button to view the step‑by‑step processing and final diagnosis

## Project Structure

```
Ahmad-website/
├── liver_system.py.py   # Main Flask application with routes and image processing
├── requirements.txt     # Python dependencies
├── static/
│   └── bootstrap.min.css # Bootstrap CSS for styling
├── .gitignore           # Git ignore rules
└── readme.md            # This file
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
