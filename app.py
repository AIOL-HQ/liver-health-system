import os
import cv2
import numpy as np
import time
import base64
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.routing import Route, Mount as StarletteMount
from starlette.responses import Response

# ── PIL is used as a robust fallback decoder (fixes WebP + some JPEG variants)
from PIL import Image
import io

try:
    import tensorflow.lite as tflite
    HAS_TFLITE = True
except ImportError:
    HAS_TFLITE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_PATH = os.path.join(BASE_DIR, "liver_model.tflite")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}

# Accepted MIME types — used as a secondary guard alongside extension check
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",          # covers both .jpg and .jpeg
    "image/bmp",
    "image/webp",
    "image/x-bmp",
    "application/octet-stream",  # some clients send generic binary
}

app = FastAPI(title="Liver Cancer AI")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

if os.path.exists(os.path.join(BASE_DIR, "static")):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(BASE_DIR, "static")),
        name="static",
    )

# ─────────────────────────────────────────────────────────────────────────────
# BUG FIX 1 – allowed_file now guards against None / empty filename
# ─────────────────────────────────────────────────────────────────────────────
def allowed_file(filename: str | None) -> bool:
    if not filename:          # catches None and ""
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────────────────────────────────────
# BUG FIX 2 – robust image decoder that falls back to PIL for WebP / JPEG
#             variants that OpenCV cannot handle without a compiled codec
# ─────────────────────────────────────────────────────────────────────────────
def decode_image(raw_bytes: bytes) -> np.ndarray | None:
    """
    Try OpenCV first; fall back to PIL so WebP and exotic JPEG sub-types
    (e.g. JPEG 2000, progressive JPEG) are handled correctly.
    Returns a BGR numpy array or None on failure.
    """
    # ── Attempt 1: OpenCV (fastest path, works for PNG / standard JPEG / BMP)
    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is not None:
        return img

    # ── Attempt 2: PIL / Pillow (handles WebP, JPEG 2000, etc.)
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        # PIL gives RGB; OpenCV expects BGR
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class LiverCancerAI:
    def __init__(self, model_path):
        self.use_real_ai = HAS_TFLITE and os.path.exists(model_path)
        if self.use_real_ai:
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
        else:
            print(
                "⚠️ تنبيه: لم يتم العثور على ملف liver_model.tflite. سيتم استخدام محاكاة مؤقتة."
            )

    def preprocess(self, image_bgr):
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        input_shape = (224, 224)
        if self.use_real_ai:
            input_shape = (
                self.input_details[0]["shape"][1],
                self.input_details[0]["shape"][2],
            )

        resized = cv2.resize(enhanced_bgr, input_shape)
        normalized = np.expand_dims(resized, axis=0).astype(np.float32) / 255.0
        return normalized, enhanced_bgr

    # ─────────────────────────────────────────────────────────────────────────
    # BUG FIX 3 – x_center was wrong: box[2] is full width, so divide by 2
    # ─────────────────────────────────────────────────────────────────────────
    def analyze_anatomical_region(self, box, img_width):
        # box = [x, y, w, h]  →  center_x = x + w/2
        x_center = box[0] + (box[2] / 2)           # was: box[0] + box[2]  ← BUG
        if x_center > (img_width / 2):
            return "الفص الأيمن (Right Lobe) - منطقة عالية الخطورة"
        else:
            return "الفص الأيسر (Left Lobe)"

    def predict(self, image_bgr):
        img_height, img_width = image_bgr.shape[:2]
        input_data, enhanced_img = self.preprocess(image_bgr)

        detections = []
        is_cancerous = False
        confidence = 0.0

        if self.use_real_ai:
            self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]["index"])

            # ─────────────────────────────────────────────────────────────────
            # BUG FIX 4 – output_data.shape is always truthy (it's a tuple);
            #             use ndim or compare shape explicitly
            # ─────────────────────────────────────────────────────────────────
            if output_data.ndim > 1 and output_data.shape[1] >= 1:
                confidence = float(output_data[0][0])
            else:
                confidence = float(output_data[0])

            is_cancerous = confidence > 0.5

            # Placeholder bounding box for classification-only models
            x = int(img_width * 0.4)
            y = int(img_height * 0.4)
            w = int(img_width * 0.2)
            h = int(img_height * 0.2)
        else:
            # Fallback simulation
            confidence = 0.88
            is_cancerous = confidence > 0.5
            w = int(img_width * 0.1)
            h = int(img_height * 0.1)
            x = int(img_width * 0.6)
            y = int(img_height * 0.4)

        if is_cancerous:
            region_info = self.analyze_anatomical_region([x, y, w, h], img_width)
            detections.append(
                {
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    # ─────────────────────────────────────────────────────────
                    # BUG FIX 5 – confidence was a formatted string ("88.00%"),
                    #             making numeric comparisons impossible downstream.
                    #             Return a float; let the frontend format it.
                    # ─────────────────────────────────────────────────────────
                    "confidence": round(confidence, 4),       # e.g. 0.8800
                    "confidence_pct": f"{confidence * 100:.2f}%",  # display string
                    "anatomical_region": region_info,
                    "note": "اشتباه بكتلة غير طبيعية تحتاج لمراجعة.",
                }
            )

            cv2.rectangle(image_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(
                image_bgr,
                f"Tumor {confidence * 100:.1f}%",
                (x, max(y - 10, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        return {
            "diagnosis_status": "High Risk" if is_cancerous else "Clear",
            "has_cancer": is_cancerous,
            "regions": detections,
            "processed_image": image_bgr,
        }


ai_system = LiverCancerAI(MODEL_PATH)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# ─────────────────────────────────────────────────────────────────────────────
# BUG FIX 6 – enzyme endpoint: reject negative / physiologically impossible values
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/analyze_enzymes")
async def analyze_enzymes(alt: float = Form(...), ast: float = Form(...)):
    try:
        if alt < 0 or ast < 0:
            return JSONResponse(
                {"ok": False, "message": "قيم الإنزيمات لا يمكن أن تكون سالبة"},
                status_code=422,
            )

        flags = []
        severity = 0
        if alt > 56:
            flags.append("ALT high")
            severity += 2
        if ast > 40:
            flags.append("AST high")
            severity += 2

        status = (
            "Normal"
            if not flags
            else ("High concern" if severity > 4 else "Mild concern")
        )
        return JSONResponse({"ok": True, "data": {"flags": flags, "status": status}})
    except Exception as exc:
        return JSONResponse({"ok": False, "message": str(exc)}, status_code=400)


@app.post("/analyze_cancer")
async def analyze_cancer(file: UploadFile = File(...)):
    # ─────────────────────────────────────────────────────────────────────────
    # BUG FIX 7 – `not file` is always False for FastAPI UploadFile objects.
    #             Check filename (None/empty) and MIME type explicitly.
    # ─────────────────────────────────────────────────────────────────────────
    if not allowed_file(file.filename):
        return JSONResponse(
            {
                "ok": False,
                "message": (
                    f"نوع الملف غير مدعوم. الأنواع المسموح بها: "
                    f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            },
            status_code=400,
        )

    # Secondary MIME-type guard (content_type may be None for some clients)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return JSONResponse(
            {"ok": False, "message": f"نوع MIME غير مدعوم: {file.content_type}"},
            status_code=415,
        )

    raw_data = await file.read()

    if not raw_data:
        return JSONResponse(
            {"ok": False, "message": "الملف فارغ"}, status_code=400
        )

    # ─────────────────────────────────────────────────────────────────────────
    # BUG FIX 2 (applied) – use the robust decoder (PIL fallback for WebP / JPEG)
    # ─────────────────────────────────────────────────────────────────────────
    image = decode_image(raw_data)
    if image is None:
        return JSONResponse(
            {"ok": False, "message": "الملف تالف أو ليس صورة صالحة"},
            status_code=400,
        )

    result = ai_system.predict(image)

    ts = int(time.time())
    output_filename = f"ai_final_{ts}.jpg"
    cv2.imwrite(os.path.join(UPLOAD_FOLDER, output_filename), result["processed_image"])

    return JSONResponse(
        {
            "ok": True,
            "has_cancer": result["has_cancer"],
            "message": result["diagnosis_status"],
            "metrics": {
                "regions_count": len(result["regions"]),
                "regions": result["regions"],
            },
            "images": [
                {
                    "key": "final",
                    "title": "AI Diagnosis Overlay",
                    "description": "نتائج فحص الذكاء الاصطناعي",
                    "url": f"/uploads/{output_filename}",
                }
            ],
        }
    )


@app.get("/uploads/{path:path}")
async def uploaded_file(path: str):
    return FileResponse(os.path.join(UPLOAD_FOLDER, path))


# ─────────────────────────────────────────────────────────────────────────────
# FASTMCP ROUTES
# ─────────────────────────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette

mcp = FastMCP("LiverCancerAI")


@mcp.tool()
def analyze_cancer_image(image_data: str) -> dict:
    """Analyze liver CT/MRI image for tumor detection."""
    try:
        img_bytes = base64.b64decode(image_data)
        # ── BUG FIX 2 (applied to MCP tool as well) ──────────────────────────
        image = decode_image(img_bytes)
        if image is None:
            return {"ok": False, "error": "Invalid or unsupported image data"}

        result = ai_system.predict(image)
        return {
            "ok": True,
            "has_cancer": result["has_cancer"],
            "status": result["diagnosis_status"],
            "regions": result["regions"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def analyze_liver_enzymes(alt: float, ast: float) -> dict:
    """Analyze ALT/AST enzyme levels for liver health."""
    try:
        # ── BUG FIX 6 (applied to MCP tool as well) ──────────────────────────
        if alt < 0 or ast < 0:
            return {"ok": False, "error": "Enzyme values cannot be negative"}

        flags = []
        severity = 0
        if alt > 56:
            flags.append("ALT high")
            severity += 2
        if ast > 40:
            flags.append("AST high")
            severity += 2

        status = (
            "Normal"
            if not flags
            else ("High concern" if severity > 4 else "Mild concern")
        )
        return {"ok": True, "flags": flags, "status": status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


sse_transport = SseServerTransport("/mcp/messages/")


async def handle_sse(request: Request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (in_stream, out_stream):
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )


sse_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        StarletteMount("/messages/", app=sse_transport.handle_post_message),
    ]
)

app.mount("/mcp", sse_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)