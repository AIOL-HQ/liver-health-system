
const enzymeForm = document.getElementById('enzymeForm');
const enzymeResult = document.getElementById('enzymeResult');
const imageForm = document.getElementById('imageForm');
const imageInput = document.getElementById('imageInput');
const previewBox = document.getElementById('previewBox');
const previewImage = document.getElementById('previewImage');
const analysisResult = document.getElementById('analysisResult');
const stagesGrid = document.getElementById('stagesGrid');
const dropzone = document.getElementById('dropzone');
const loader = document.getElementById('loader');
const themeToggle = document.getElementById('themeToggle');

themeToggle?.addEventListener('click', () => {
    document.body.classList.toggle('light');
    localStorage.setItem('liverTheme', document.body.classList.contains('light') ? 'light' : 'dark');
});

window.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('liverTheme') === 'light') {
        document.body.classList.add('light');
    }
});

enzymeForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(enzymeForm);

    enzymeResult.className = 'result-area';
    enzymeResult.innerHTML = '<div class="badge info">Analyzing enzymes...</div>';
    enzymeResult.classList.remove('hidden');

    try {
        const response = await fetch('/analyze_enzymes', { method: 'POST', body: formData });
        const result = await response.json();

        if (!result.ok) {
            throw new Error(result.message || 'Analysis failed');
        }

        const data = result.data;
        const isNormal = data.status === 'Normal';

        enzymeResult.className = `result-area ${isNormal ? 'success' : 'danger'}`;
        enzymeResult.innerHTML = `
            <div class="result-header">
                <div>
                    <h3>${escapeHtml(data.name)} - Enzyme Report</h3>
                    <p>Age: ${escapeHtml(data.age)}</p>
                </div>
                <span class="badge ${isNormal ? 'success' : 'danger'}">${escapeHtml(data.status)}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric">
                    <strong>${data.flags.length}</strong>
                    <span>Abnormal Flags</span>
                </div>
                <div class="metric">
                    <strong>${data.severity_score}</strong>
                    <span>Severity Score</span>
                </div>
                <div class="metric">
                    <strong>${data.report.length}</strong>
                    <span>Clinical Notes</span>
                </div>
            </div>
            <ul class="result-list">
                ${data.report.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
            <div class="notice">
                This enzyme review is supportive information only and does not replace medical consultation.
            </div>
        `;
    } catch (error) {
        enzymeResult.className = 'result-area danger';
        enzymeResult.innerHTML = `<div class="badge danger">${escapeHtml(error.message)}</div>`;
    }
});

imageInput?.addEventListener('change', handleSelectedImage);

dropzone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});
dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files?.[0];
    if (file) {
        imageInput.files = e.dataTransfer.files;
        handleSelectedImage();
    }
});

function handleSelectedImage() {
    const file = imageInput.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        previewImage.src = reader.result;
        previewBox.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

imageForm?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = imageInput.files?.[0];
    if (!file) {
        alert('Please select an image first.');
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    analysisResult.classList.add('hidden');
    stagesGrid.innerHTML = '';
    loader.classList.remove('hidden');

    try {
        const response = await fetch('/analyze_cancer', { method: 'POST', body: formData });
        const result = await response.json();
        loader.classList.add('hidden');

        if (!result.ok) {
            throw new Error(result.message || 'Image analysis failed');
        }

        analysisResult.className = `result-area ${result.has_cancer ? 'danger' : 'success'}`;
        analysisResult.classList.remove('hidden');
        analysisResult.innerHTML = `
            <div class="result-header">
                <div>
                    <h3>${result.has_cancer ? 'Suspicious Result' : 'No Suspicious Regions'}</h3>
                    <p>${escapeHtml(result.message)}</p>
                </div>
                <span class="badge ${result.has_cancer ? 'danger' : 'success'}">
                    ${result.has_cancer ? 'Check Needed' : 'Stable Result'}
                </span>
            </div>
            <div class="metrics-grid">
                <div class="metric">
                    <strong>${result.metrics.regions_count}</strong>
                    <span>Detected Regions</span>
                </div>
                <div class="metric">
                    <strong>${result.metrics.largest_area}</strong>
                    <span>Largest Area</span>
                </div>
                <div class="metric">
                    <strong>${result.metrics.otsu_threshold}</strong>
                    <span>Otsu Threshold</span>
                </div>
                <div class="metric">
                    <strong>${escapeHtml(result.metrics.image_size)}</strong>
                    <span>Image Size</span>
                </div>
            </div>
            <div class="notice">${escapeHtml(result.medical_notice)}</div>
        `;

        stagesGrid.innerHTML = result.images.map((img, index) => `
            <article class="stage-card reveal" style="animation-delay:${index * 50}ms">
                <img src="${img.url}" alt="${escapeHtml(img.title)}" />
                <div class="stage-info">
                    <h4>${escapeHtml(img.title)}</h4>
                    <p>Stage ${index + 1} of the enhanced pipeline</p>
                </div>
            </article>
        `).join('');
    } catch (error) {
        loader.classList.add('hidden');
        analysisResult.className = 'result-area danger';
        analysisResult.classList.remove('hidden');
        analysisResult.innerHTML = `<div class="badge danger">${escapeHtml(error.message)}</div>`;
    }
});

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
