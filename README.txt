# Liver Health Smart System

## Files
- `app.py` -> main Flask app
- `templates/index.html` -> HTML page
- `static/css/style.css` -> page styling and animations
- `static/js/app.js` -> dynamic frontend logic
- `requirements.txt` -> Python libraries
- `start_project.bat` -> easiest Windows auto-run file
- `auto_run.dart` -> Dart launcher version
- `uploads/` -> generated processed images

## What was improved
- Split the project into clean files instead of one inline file
- Added more image-processing filters:
  - Grayscale
  - Bilateral Filter
  - CLAHE
  - Median blur
  - Morphological opening
  - Black-Hat
  - Gaussian enhancement
  - Otsu threshold
  - Adaptive threshold
  - Combined mask
  - Edge detection
  - Heatmap overlay
  - Final suspicious-region detection
- Added contour validation rules for better accuracy:
  - area filtering
  - aspect ratio filtering
  - solidity filtering
  - circularity filtering
- Advanced dynamic and animated web page
- Drag & drop upload with preview
- Better enzyme interpretation and AST/ALT ratio report

## Important note
This project is an educational/demo computer-vision system only.
It is **not** a medical diagnostic device.

## How to run
### Easiest way on Windows
Double-click:
`start_project.bat`

It will:
1. Create `venv`
2. Install libraries
3. Start the Flask project
4. Open the browser

### Run with Dart launcher
If Dart SDK is installed:
`dart run auto_run.dart`
