/**
 * Image Inspection Frontend Controller.
 */

const imageInspection = {
  currentFile: null,
  currentResult: null,
  currentView: 'annotated', // 'annotated' | 'original'

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const dropZone = document.getElementById('img-drop-zone');
    const fileInput = document.getElementById('img-file-input');

    if (!dropZone || !fileInput) return;

    // Drag & Drop events
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files.length > 0) {
        this.handleFile(dt.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        this.handleFile(e.target.files[0]);
      }
    });
  },

  handleFile(file) {
    const validExtensions = ['jpg', 'jpeg', 'png', 'webp', 'bmp'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
      app.showToast('Please select a valid image format (JPG, PNG, WEBP, BMP)', 'error');
      return;
    }

    this.currentFile = file;
    this.currentResult = null;

    const reader = new FileReader();
    reader.onload = (e) => {
      const dropZone = document.getElementById('img-drop-zone');
      const workspace = document.getElementById('img-workspace');
      const previewImg = document.getElementById('img-preview-element');
      const title = document.getElementById('img-filename-title');

      if (dropZone) dropZone.style.display = 'none';
      if (workspace) workspace.style.display = 'grid';
      if (previewImg) previewImg.src = e.target.result;
      if (title) title.textContent = file.name;

      this.resetResultPanel();
    };
    reader.readAsDataURL(file);
  },

  resetResultPanel() {
    const statusCard = document.getElementById('img-status-card');
    const statusPill = document.getElementById('img-status-pill');
    const heading = document.getElementById('img-status-heading');
    const defectLabel = document.getElementById('img-defect-label');
    const confVal = document.getElementById('img-conf-val');
    const timeVal = document.getElementById('img-time-val');
    const countVal = document.getElementById('img-defect-count-val');
    const idVal = document.getElementById('img-inspection-id-val');
    const list = document.getElementById('img-detections-list');
    const toggleGroup = document.getElementById('img-toggle-view-group');
    const btnDownload = document.getElementById('btn-download-result');

    if (statusCard) statusCard.className = 'status-summary-card';
    if (statusPill) { statusPill.className = 'status-pill unknown'; statusPill.textContent = 'READY TO INSPECT'; }
    if (heading) { heading.className = 'status-heading'; heading.textContent = 'Click Analyze to Inspect'; }
    if (defectLabel) defectLabel.textContent = 'YOLO inference pending';
    if (confVal) confVal.textContent = '--%';
    if (timeVal) timeVal.textContent = '-- ms';
    if (countVal) countVal.textContent = '0';
    if (idVal) idVal.textContent = '#--';
    if (toggleGroup) toggleGroup.style.display = 'none';
    if (btnDownload) btnDownload.style.display = 'none';
    if (list) {
      list.innerHTML = `
        <div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 1rem;">
          Click "Analyze Image" to run YOLO object detection.
        </div>
      `;
    }
  },

  async analyze() {
    if (!this.currentFile) {
      app.showToast('Please select an image first.', 'error');
      return;
    }

    const overlay = document.getElementById('img-loading-overlay');
    const btnAnalyze = document.getElementById('btn-analyze-image');

    if (overlay) overlay.classList.add('active');
    if (btnAnalyze) btnAnalyze.disabled = true;

    try {
      const formData = new FormData();
      formData.append('file', this.currentFile);

      const response = await fetch('/api/image/predict', {
        method: 'POST',
        body: formData,
      });

      const res = await response.json();

      if (!response.ok || !res.success) {
        const errorMsg = res.message || res.error || 'Inspection failed';
        app.showToast(errorMsg, 'error');
        if (res.model_available === false) {
          app.showMissingModelBanner();
          this.renderMissingModel(errorMsg);
        }
        return;
      }

      this.currentResult = res.data;
      this.renderResults(res.data);
      app.showToast(`YOLO Inspection: ${res.data.status}`, res.data.status === 'GOOD' ? 'success' : 'error');

    } catch (err) {
      console.error('Image inspection network error:', err);
      app.showToast('Failed to connect to backend server.', 'error');
    } finally {
      if (overlay) overlay.classList.remove('active');
      if (btnAnalyze) btnAnalyze.disabled = false;
    }
  },

  renderMissingModel(message) {
    const statusCard = document.getElementById('img-status-card');
    const statusPill = document.getElementById('img-status-pill');
    const heading = document.getElementById('img-status-heading');
    const defectLabel = document.getElementById('img-defect-label');
    const confVal = document.getElementById('img-conf-val');
    const list = document.getElementById('img-detections-list');

    if (statusCard) statusCard.className = 'status-summary-card';
    if (statusPill) { statusPill.className = 'status-pill unknown'; statusPill.textContent = 'REAL AI MODEL NOT AVAILABLE'; }
    if (heading) { heading.className = 'status-heading'; heading.textContent = 'AI Detection Unavailable'; }
    if (defectLabel) defectLabel.textContent = message || 'Please place best.pt in models/trained/best.pt.';
    if (confVal) confVal.textContent = 'N/A';
    if (list) {
      list.innerHTML = `
        <div style="padding: 1rem; border-radius: var(--radius-md); background: rgba(239,68,68,0.1); border: 1px solid var(--status-defect); color: var(--text-primary); font-size: 0.85rem;">
          <strong style="color: var(--status-defect);">REAL AI MODEL NOT AVAILABLE</strong><br>
          ${message || 'Trained YOLO model weights (best.pt) were not found on the server. Place trained weights in models/trained/best.pt to enable real defect detection.'}
        </div>
      `;
    }
  },

  renderResults(data) {
    const isDefect = data.status === 'DEFECT';
    const statusCard = document.getElementById('img-status-card');
    const statusPill = document.getElementById('img-status-pill');
    const heading = document.getElementById('img-status-heading');
    const defectLabel = document.getElementById('img-defect-label');
    const confVal = document.getElementById('img-conf-val');
    const timeVal = document.getElementById('img-time-val');
    const countVal = document.getElementById('img-defect-count-val');
    const idVal = document.getElementById('img-inspection-id-val');
    const list = document.getElementById('img-detections-list');
    const previewImg = document.getElementById('img-preview-element');
    const toggleGroup = document.getElementById('img-toggle-view-group');
    const btnDownload = document.getElementById('btn-download-result');

    // Update image to annotated version
    if (previewImg && data.result_image_url) {
      previewImg.src = data.result_image_url + '?t=' + new Date().getTime();
      this.currentView = 'annotated';
    }

    if (toggleGroup) toggleGroup.style.display = 'flex';

    if (statusCard) {
      statusCard.className = `status-summary-card ${isDefect ? 'defect' : 'good'}`;
    }

    if (statusPill) {
      statusPill.className = `status-pill ${isDefect ? 'defect' : 'good'}`;
      statusPill.textContent = isDefect ? 'DEFECT DETECTED' : 'GOOD PRINT';
    }

    if (heading) {
      heading.className = `status-heading ${isDefect ? 'defect' : 'good'}`;
      heading.textContent = isDefect ? data.dominant_defect : (data.dominant_defect || 'No Defect Detected');
    }

    if (defectLabel) {
      defectLabel.textContent = isDefect
        ? `Found ${data.defect_count} defect instance(s) via YOLO`
        : 'Zero defect anomalies detected in model inference';
    }

    if (confVal) {
      confVal.textContent = data.confidence_percentage > 0 ? `${data.confidence_percentage}%` : 'N/A';
    }
    if (timeVal) timeVal.textContent = `${data.processing_time_ms} ms`;
    if (countVal) countVal.textContent = data.defect_count || 0;
    if (idVal) idVal.textContent = `#${data.inspection_id || '--'}`;

    if (btnDownload && data.result_image_url) {
      btnDownload.style.display = 'inline-flex';
      btnDownload.href = data.result_image_url;
      btnDownload.setAttribute('download', data.result_filename || 'defect_inspection.jpg');
    }

    // Render detections items
    if (list) {
      if (!data.detections || data.detections.length === 0) {
        list.innerHTML = `
          <div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 1.25rem;">
            No localized defect bounding boxes detected. Print is nominal.
          </div>
        `;
      } else {
        list.innerHTML = data.detections.map(det => `
          <div class="detection-item ${det.is_defect ? '' : 'good-item'}">
            <div class="detection-info">
              <span class="detection-title">${det.class_name}</span>
              <span class="detection-coords">Box: [${det.bbox.x1}, ${det.bbox.y1}] → [${det.bbox.x2}, ${det.bbox.y2}]</span>
            </div>
            <span class="detection-conf" style="color: ${det.is_defect ? 'var(--status-defect)' : 'var(--status-good)'};">
              ${(det.confidence * 100).toFixed(1)}%
            </span>
          </div>
        `).join('');
      }
    }
  },

  switchView(type) {
    if (!this.currentResult) return;
    const previewImg = document.getElementById('img-preview-element');
    const btnAnnotated = document.getElementById('btn-show-annotated');
    const btnOriginal = document.getElementById('btn-show-original');

    if (type === 'annotated') {
      previewImg.src = this.currentResult.result_image_url + '?t=' + new Date().getTime();
      this.currentView = 'annotated';
      if (btnAnnotated) btnAnnotated.className = 'btn btn-primary';
      if (btnOriginal) btnOriginal.className = 'btn btn-secondary';
    } else {
      previewImg.src = this.currentResult.original_image_url;
      this.currentView = 'original';
      if (btnAnnotated) btnAnnotated.className = 'btn btn-secondary';
      if (btnOriginal) btnOriginal.className = 'btn btn-primary';
    }
  },

  reset() {
    this.currentFile = null;
    this.currentResult = null;
    const dropZone = document.getElementById('img-drop-zone');
    const workspace = document.getElementById('img-workspace');
    const fileInput = document.getElementById('img-file-input');

    if (fileInput) fileInput.value = '';
    if (dropZone) dropZone.style.display = 'block';
    if (workspace) workspace.style.display = 'none';
  }
};
