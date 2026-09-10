/**
 * Video Inspection Frontend Controller.
 */

const videoInspection = {
  currentFile: null,
  currentResult: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const dropZone = document.getElementById('vid-drop-zone');
    const fileInput = document.getElementById('vid-file-input');

    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(name => {
      dropZone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      dropZone.addEventListener(name, (e) => {
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
    const validExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
      app.showToast('Please select a valid video format (MP4, AVI, MOV, MKV, WEBM)', 'error');
      return;
    }

    this.currentFile = file;
    this.currentResult = null;

    const dropZone = document.getElementById('vid-drop-zone');
    const workspace = document.getElementById('vid-workspace');
    const player = document.getElementById('vid-player-element');
    const title = document.getElementById('vid-filename-title');

    if (dropZone) dropZone.style.display = 'none';
    if (workspace) workspace.style.display = 'grid';
    if (title) title.textContent = file.name;

    if (player) {
      player.src = URL.createObjectURL(file);
      player.load();
    }

    this.resetResultPanel();
  },

  resetResultPanel() {
    const statusCard = document.getElementById('vid-status-card');
    const statusPill = document.getElementById('vid-status-pill');
    const heading = document.getElementById('vid-status-heading');
    const label = document.getElementById('vid-defect-label');
    const framesVal = document.getElementById('vid-frames-val');
    const defectFramesVal = document.getElementById('vid-defect-frames-val');
    const timeVal = document.getElementById('vid-time-val');
    const confVal = document.getElementById('vid-conf-val');
    const summaryList = document.getElementById('vid-defect-summary-list');
    const btnDownload = document.getElementById('btn-download-video-result');

    if (statusCard) statusCard.className = 'status-summary-card';
    if (statusPill) { statusPill.className = 'status-pill unknown'; statusPill.textContent = 'READY TO PROCESS'; }
    if (heading) { heading.className = 'status-heading'; heading.textContent = 'Ready to Analyze Video'; }
    if (label) label.textContent = 'Awaiting frame extraction and YOLO detection';
    if (framesVal) framesVal.textContent = '-- / --';
    if (defectFramesVal) defectFramesVal.textContent = '0';
    if (timeVal) timeVal.textContent = '-- s';
    if (confVal) confVal.textContent = '--%';
    if (btnDownload) btnDownload.style.display = 'none';
    if (summaryList) {
      summaryList.innerHTML = `
        <div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 1rem;">
          Click "Process Video" to begin frame-by-frame analysis.
        </div>
      `;
    }
  },

  async analyze() {
    if (!this.currentFile) {
      app.showToast('Please select a video file first.', 'error');
      return;
    }

    const overlay = document.getElementById('vid-loading-overlay');
    const btnAnalyze = document.getElementById('btn-analyze-video');
    const progressFill = document.getElementById('vid-progress-fill');
    const skipSelect = document.getElementById('vid-frame-skip');

    if (overlay) overlay.classList.add('active');
    if (btnAnalyze) btnAnalyze.disabled = true;
    if (progressFill) progressFill.style.width = '20%';

    try {
      const formData = new FormData();
      formData.append('file', this.currentFile);
      if (skipSelect) {
        formData.append('frame_skip', skipSelect.value);
      }

      if (progressFill) progressFill.style.width = '60%';

      const response = await fetch('/api/video/predict', {
        method: 'POST',
        body: formData,
      });

      if (progressFill) progressFill.style.width = '90%';

      const res = await response.json();

      if (!response.ok || !res.success) {
        const errorMsg = res.message || res.error || 'Video processing failed';
        app.showToast(errorMsg, 'error');
        if (res.model_available === false) {
          app.showMissingModelBanner();
          this.renderMissingModel(errorMsg);
        }
        return;
      }

      this.currentResult = res.data;
      this.renderResults(res.data);
      app.showToast(`YOLO Video Inspection: ${res.data.status}`, res.data.status === 'GOOD' ? 'success' : 'error');

    } catch (err) {
      console.error('Video inspection network error:', err);
      app.showToast('Network error during video upload and processing.', 'error');
    } finally {
      if (progressFill) progressFill.style.width = '100%';
      if (overlay) overlay.classList.remove('active');
      if (btnAnalyze) btnAnalyze.disabled = false;
    }
  },

  renderMissingModel(message) {
    const statusCard = document.getElementById('vid-status-card');
    const statusPill = document.getElementById('vid-status-pill');
    const heading = document.getElementById('vid-status-heading');
    const label = document.getElementById('vid-defect-label');
    const confVal = document.getElementById('vid-conf-val');
    const summaryList = document.getElementById('vid-defect-summary-list');

    if (statusCard) statusCard.className = 'status-summary-card';
    if (statusPill) { statusPill.className = 'status-pill unknown'; statusPill.textContent = 'REAL AI MODEL NOT AVAILABLE'; }
    if (heading) { heading.className = 'status-heading'; heading.textContent = 'AI Detection Unavailable'; }
    if (label) label.textContent = message || 'Please place best.pt in models/trained/best.pt.';
    if (confVal) confVal.textContent = 'N/A';
    if (summaryList) {
      summaryList.innerHTML = `
        <div style="padding: 1rem; border-radius: var(--radius-md); background: rgba(239,68,68,0.1); border: 1px solid var(--status-defect); color: var(--text-primary); font-size: 0.85rem;">
          <strong style="color: var(--status-defect);">REAL AI MODEL NOT AVAILABLE</strong><br>
          ${message || 'Trained YOLO model weights (best.pt) were not found on the server. Place trained weights in models/trained/best.pt to enable real defect detection.'}
        </div>
      `;
    }
  },

  renderResults(data) {
    const isDefect = data.status === 'DEFECT';
    const statusCard = document.getElementById('vid-status-card');
    const statusPill = document.getElementById('vid-status-pill');
    const heading = document.getElementById('vid-status-heading');
    const label = document.getElementById('vid-defect-label');
    const framesVal = document.getElementById('vid-frames-val');
    const defectFramesVal = document.getElementById('vid-defect-frames-val');
    const timeVal = document.getElementById('vid-time-val');
    const confVal = document.getElementById('vid-conf-val');
    const summaryList = document.getElementById('vid-defect-summary-list');
    const player = document.getElementById('vid-player-element');
    const btnDownload = document.getElementById('btn-download-video-result');

    // Update video player to annotated result video
    if (player && data.result_video_url) {
      player.src = data.result_video_url + '?t=' + new Date().getTime();
      player.load();
    }

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

    if (label) {
      label.textContent = isDefect
        ? `Defects flagged across ${data.defect_frames} frame(s) by YOLO`
        : 'All examined video frames verified defect-free by YOLO model';
    }

    if (framesVal) framesVal.textContent = `${data.total_frames} frames`;
    if (defectFramesVal) defectFramesVal.textContent = `${data.defect_frames} frames`;
    if (timeVal) timeVal.textContent = `${data.processing_time_seconds} s`;
    if (confVal) {
      confVal.textContent = data.max_confidence > 0 ? `${(data.max_confidence * 100).toFixed(1)}%` : 'N/A';
    }

    if (btnDownload && data.result_video_url) {
      btnDownload.style.display = 'inline-flex';
      btnDownload.href = data.result_video_url;
      btnDownload.setAttribute('download', data.result_filename || 'annotated_video.mp4');
    }

    // Render defect summary
    if (summaryList) {
      const summary = data.defect_summary || {};
      const keys = Object.keys(summary);

      if (keys.length === 0) {
        summaryList.innerHTML = `
          <div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 1.25rem;">
            No defect anomalies detected across video frames.
          </div>
        `;
      } else {
        summaryList.innerHTML = keys.map(k => `
          <div class="detection-item">
            <div class="detection-info">
              <span class="detection-title">${k}</span>
              <span class="detection-coords">Detected across timeline</span>
            </div>
            <span class="detection-conf" style="color: var(--status-defect);">
              ${summary[k]} frame(s)
            </span>
          </div>
        `).join('');
      }
    }
  },

  reset() {
    this.currentFile = null;
    this.currentResult = null;
    const dropZone = document.getElementById('vid-drop-zone');
    const workspace = document.getElementById('vid-workspace');
    const fileInput = document.getElementById('vid-file-input');
    const player = document.getElementById('vid-player-element');

    if (fileInput) fileInput.value = '';
    if (player) player.src = '';
    if (dropZone) dropZone.style.display = 'block';
    if (workspace) workspace.style.display = 'none';
  }
};
