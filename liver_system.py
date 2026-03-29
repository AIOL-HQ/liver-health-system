import cv2
import numpy as np
import base64
from flask import Flask, request, render_template_string
import webbrowser
from threading import Timer

app = Flask(__name__)

# ==========================================
# دالة مساعدة لتحويل الصور وعرضها بالمتصفح
# ==========================================
def get_base64(img_array):
    # إذا كانت الصورة رمادية، نحولها لـ BGR عشان العرض في المتصفح
    if len(img_array.shape) == 2:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    _, buffer = cv2.imencode('.jpg', img_array)
    return base64.b64encode(buffer).decode('utf-8')

# ==========================================
# تصميم الواجهات (HTML & CSS) - فخم ويعرض كل المراحل
# ==========================================
TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Liver Health System</title>
    <link href="/static/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar { background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
        .navbar-brand { font-weight: bold; color: #2c3e50 !important; }
        .card { border: none; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.08); padding: 20px; background-color: #ffffff; margin-bottom: 30px;}
        .card-header-custom { background-color: #ffffff; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
        .btn-custom { background-color: #3498db; color: white; border-radius: 8px; font-weight: bold; padding: 10px 20px; transition: 0.3s;}
        .btn-custom:hover { background-color: #2980b9; color: white; }
        .result-box { background-color: #e8f6f3; border-right: 5px solid #1abc9c; padding: 15px; border-radius: 5px; margin-top: 20px;}
        .result-danger { background-color: #fdedec; border-right: 5px solid #e74c3c; padding: 15px; border-radius: 5px; margin-top: 20px;}
        h2, h3, h4 { color: #2c3e50; }
        .english-title { font-family: 'Arial', sans-serif; color: #7f8c8d; font-size: 1.2rem; text-align: left; direction: ltr; margin-bottom: 20px;}
        .filter-card { border: 1px solid #ddd; border-radius: 10px; overflow: hidden; height: 100%; background: #fff;}
        .filter-title { background-color: #2c3e50; color: white; padding: 10px; font-size: 1rem; font-weight: bold; }
        .filter-img { width: 100%; height: 250px; object-fit: contain; background: #000; padding: 5px;}
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-light">
    <div class="container">
        <a class="navbar-brand" href="/">🏥 نظام فحص الكبد الذكي</a>
        <div>
            <a href="/" class="btn btn-outline-primary me-2">فحص الإنزيمات</a>
            <a href="/cancer" class="btn btn-outline-danger">فحص الكانسر بالصور</a>
        </div>
    </div>
</nav>

<div class="container">
    {% if page == 'enzymes' %}
    <div class="card">
        <div class="english-title">A complete system for testing liver enzymes</div>
        <div class="card-header-custom">
            <h3>إدخال بيانات المريض وفحص الإنزيمات</h3>
        </div>
        
        <form action="/analyze_enzymes" method="POST">
            <div class="row mb-3">
                <div class="col-md-6">
                    <label class="form-label fw-bold">اسم المريض:</label>
                    <input type="text" name="name" class="form-control" required placeholder="مثال: أحمد">
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold">العمر:</label>
                    <input type="number" name="age" class="form-control" required placeholder="مثال: 25">
                </div>
            </div>
            
            <h5 class="mt-4 mb-3" style="color:#34495e; font-weight:bold;">قيم الإنزيمات (وحدة/لتر):</h5>
            <div class="row mb-3">
                <div class="col-md-4 mb-3">
                    <label class="form-label">ALT (الطبيعي: 7 - 56):</label>
                    <input type="number" step="0.1" name="alt" class="form-control" required>
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">AST (الطبيعي: 10 - 40):</label>
                    <input type="number" step="0.1" name="ast" class="form-control" required>
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">ALP (الطبيعي: 44 - 147):</label>
                    <input type="number" step="0.1" name="alp" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">GGT (الطبيعي: 9 - 48):</label>
                    <input type="number" step="0.1" name="ggt" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Bilirubin (الطبيعي: 0.1 - 1.2 mg/dL):</label>
                    <input type="number" step="0.01" name="bilirubin" class="form-control" required>
                </div>
            </div>
            <button type="submit" class="btn btn-custom w-100 mt-2 fs-5">تشخيص حالة الإنزيمات</button>
        </form>

        {% if report %}
        <div class="{% if has_issue %}result-danger{% else %}result-box{% endif %}">
            <h4 class="mb-3">نتيجة الفحص للمريض: {{ name }} (العمر: {{ age }})</h4>
            <ul style="font-size: 1.15rem; line-height: 1.8; font-weight: 500;">
                {% for line in report %}
                    <li>{{ line }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    {% elif page == 'cancer' %}
    <div class="card">
        <div class="english-title">A system for diagnosing liver cancer</div>
        <div class="card-header-custom">
            <h3>رفع صورة الكبد للتشخيص الآلي (X-Ray / MRI)</h3>
            <p class="text-muted">يتم تمرير الصورة عبر 4 فلاتر طبية قوية، ثم الفلتر الخامس لاكتشاف وتحديد الورم.</p>
        </div>
        
        <form action="/analyze_cancer" method="POST" enctype="multipart/form-data">
            <div class="mb-4">
                <label class="form-label fw-bold fs-5">اختر صورة الكبد من جهازك:</label>
                <input class="form-control form-control-lg" type="file" name="image" accept="image/*" required>
            </div>
            <button type="submit" class="btn btn-danger w-100 fs-5" style="border-radius: 8px; font-weight: bold; padding: 12px;">بدء الفحص الدقيق بالذكاء الاصطناعي</button>
        </form>

        {% if images_data %}
        <div class="mt-5">
            {% if has_cancer %}
                <div class="alert alert-danger text-center shadow-sm" style="font-size:1.3rem; font-weight:bold; border: 2px solid #e74c3c;">
                    <span dir="ltr" style="display:block; font-size:1.6rem; margin-bottom:10px; color:#c0392b;">There are suspicious places</span>
                    تم فحص الكبد وتم تشخيص الكبد وكشف وجود اماكن مشبوها بالكبد يرجى مراجعة الطبيب باقرب وقت.
                </div>
            {% else %}
                <div class="alert alert-success text-center shadow-sm" style="font-size:1.3rem; font-weight:bold; border: 2px solid #27ae60;">
                    <span dir="ltr" style="display:block; font-size:1.6rem; margin-bottom:10px; color:#16a085;">There is nothing suspicious</span>
                    تم فحص الكبد، ولا يوجد أي مشاكل، الكبد سليم.
                </div>
            {% endif %}
            
            <hr class="my-5">
            <h3 class="mb-4 text-center fw-bold" style="color: #2c3e50;">مراحل المعالجة الطبية للصورة</h3>
            
            <div class="row g-4 text-center">
                {% for img in images_data %}
                <div class="col-md-4">
                    <div class="filter-card shadow-sm">
                        <div class="filter-title">{{ img.title }}</div>
                        <img src="data:image/jpeg;base64,{{ img.data }}" class="filter-img">
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}
</div>

</body>
</html>
"""

# ==========================================
# مسارات السيرفر (Routes)
# ==========================================

@app.route('/')
def home():
    return render_template_string(TEMPLATE, page='enzymes')

@app.route('/analyze_enzymes', methods=['POST'])
def analyze_enzymes():
    name = request.form['name']
    age = request.form['age']
    alt = float(request.form['alt'])
    ast = float(request.form['ast'])
    alp = float(request.form['alp'])
    ggt = float(request.form['ggt'])
    bili = float(request.form['bilirubin'])
    
    report = []
    has_issue = False
    
    # تحليل ALT
    if alt > 56:
        report.append("ALT : مرتفع ➜ يدل على التهاب كبد / تلف خلايا")
        has_issue = True
    elif alt < 7:
        report.append("ALT : منخفض ➜ غالباً ليس له أهمية كبيرة")
        
    # تحليل AST
    if ast > 40:
        report.append("AST : مرتفع ➜ التهاب كبد / تليف / ممكن إصابة عضلية")
        has_issue = True
        if ast > alt:
            report.append("⚠️ AST أعلى من ALT ➜ ممكن يدل على مشاكل مزمنة")
            
    # تحليل ALP
    if alp > 147:
        report.append("ALP : مرتفع ➜ انسداد صفراوي / مشاكل في المرارة")
        has_issue = True
    elif alp < 44:
        report.append("ALP : منخفض ➜ نادر، ممكن نقص تغذية")
        
    # تحليل GGT (كما طلبته حرفياً)
    if ggt > 48:
        report.append("GGT : مرتفع ➜ يدل على مشاكل في الكبد أو انسداد صفراوي")
        has_issue = True
        
    # تحليل Bilirubin
    if bili > 1.2:
        report.append("Bilirubin : مرتفع ➜ ضعف الكبد / انسداد / يسبب اصفرار (يرقان)")
        has_issue = True
        
    if not has_issue:
        report.append("✅ جميع الإنزيمات ضمن المعدلات الطبيعية، ولا توجد مشاكل.")
        
    return render_template_string(TEMPLATE, page='enzymes', name=name, age=age, report=report, has_issue=has_issue)

@app.route('/cancer')
def cancer_page():
    return render_template_string(TEMPLATE, page='cancer')

@app.route('/analyze_cancer', methods=['POST'])
def analyze_cancer():
    file = request.files['image']
    if not file:
        return "لم يتم رفع صورة", 400

    npimg = np.frombuffer(file.read(), np.uint8)
    original_img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    # 1. المرحلة الأولى: Grayscale
    gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    
    # 2. المرحلة الثانية: Bilateral Filter (تنقية المستشفيات)
    filter1_bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # 3. المرحلة الثالثة: CLAHE (تحسين التباين لصور الأشعة)
    clahe_obj = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    filter2_clahe = clahe_obj.apply(filter1_bilateral)
    
    # 4. المرحلة الرابعة: Morphological Black-Hat (استخراج المناطق الداكنة جداً)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    filter3_blackhat = cv2.morphologyEx(filter2_clahe, cv2.MORPH_BLACKHAT, kernel)
    
    # تحسين إضافي بعد استخراج المناطق الداكنة لتنعيمها
    filter4_blur = cv2.GaussianBlur(filter3_blackhat, (5, 5), 0)

    # 5. المرحلة الخامسة (التشخيص): Threshold + Contours
    # الأماكن الداكنة في الصورة الأصلية أصبحت الآن بيضاء مضيئة بسبب الـ Black-Hat
    _, thresh = cv2.threshold(filter4_blur, 40, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    has_cancer = False
    final_output = original_img.copy()
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 200: # تجاهل النقاط الصغيرة العشوائية
            x, y, w, h = cv2.boundingRect(cnt)
            # رسم المربع الأحمر
            cv2.rectangle(final_output, (x, y), (x+w, y+h), (0, 0, 255), 3)
            # وضع نص توضيحي
            cv2.putText(final_output, "Tumor", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            has_cancer = True

    # تجميع الصور لعرضها بالواجهة
    images_data = [
        {"title": "1. الصورة الأصلية (Grayscale)", "data": get_base64(gray)},
        {"title": "2. فلتر Bilateral (تنقية التشويش)", "data": get_base64(filter1_bilateral)},
        {"title": "3. فلتر CLAHE (رفع تباين الأشعة)", "data": get_base64(filter2_clahe)},
        {"title": "4. فلتر Black-Hat (عزل الأماكن الداكنة)", "data": get_base64(filter3_blackhat)},
        {"title": "الفلتر الخامس: التحديد (Threshold)", "data": get_base64(thresh)},
        {"title": "النتيجة النهائية (التشخيص)", "data": get_base64(final_output)}
    ]
    
    return render_template_string(TEMPLATE, page='cancer', images_data=images_data, has_cancer=has_cancer)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True, use_reloader=False)
