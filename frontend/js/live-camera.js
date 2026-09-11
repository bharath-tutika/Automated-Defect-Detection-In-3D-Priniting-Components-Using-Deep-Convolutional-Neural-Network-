/**
 * Live Camera Stream and Real-time Telemetry Controller.
 * Supports both Client Browser Webcam (including external USB & built-in webcams)
 * and Server Hardware VideoCapture.
 */

const liveCamera = {
  isStreaming: false,
  streamMode: 'browser', // 'browser' or 'server'
  browserStream: null,
  frameLoopActive: false,
  isProcessingFrame: false,
  lastFrameTimestamp: 0,
  frameCount: 0,
  fps: 0,
  fpsInterval: null,
  statusPollInterval: null,
  recentSnapshots: [],
  saveNextSnapshot: false,
  availableDevices: [],

  init() {
    this.dismissError();
    this.refreshDeviceList();
    this.checkInitialStatus();
  },

  onSourceModeChange() {
    const modeSelect = document.getElementById('camera-mode-select');
    this.streamMode = modeSelect ? modeSelect.value : 'browser';
    this.refreshDeviceList();
  },

  async refreshDeviceList() {
    const select = document.getElementById('camera-device-select');
    if (!select) return;

    select.innerHTML = '<option value="default">Scanning cameras...</option>';

    const modeSelect = document.getElementById('camera-mode-select');
    const currentMode = modeSelect ? modeSelect.value : this.streamMode;

    if (currentMode === 'browser') {
      await this.loadBrowserCameras(select);
    } else {
      await this.loadServerCameras(select);
    }
  },

  async loadBrowserCameras(selectElement) {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        selectElement.innerHTML = '<option value="default">Default Camera</option>';
        return;
      }

      // Check if we need to request temporary permission to populate human-readable labels
      let devices = await navigator.mediaDevices.enumerateDevices();
      let videoDevices = devices.filter(d => d.kind === 'videoinput');

      // If labels are empty, prompt a fast stream to unlock camera device labels
      if (videoDevices.length > 0 && !videoDevices[0].label) {
        try {
          const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
          tempStream.getTracks().forEach(t => t.stop());
          devices = await navigator.mediaDevices.enumerateDevices();
          videoDevices = devices.filter(d => d.kind === 'videoinput');
        } catch (permErr) {
          console.debug('Temporary label request notice:', permErr);
        }
      }

      selectElement.innerHTML = '';
      if (videoDevices.length === 0) {
        selectElement.innerHTML = '<option value="default">Default Camera (Auto-detect)</option>';
        return;
      }

      videoDevices.forEach((dev, idx) => {
        const opt = document.createElement('option');
        opt.value = dev.deviceId || 'default';
        const label = dev.label || `Camera ${idx + 1} (USB / External)`;
        opt.textContent = `${idx + 1}. ${label}`;
        selectElement.appendChild(opt);
      });

    } catch (err) {
      console.warn('Error loading browser cameras:', err);
      selectElement.innerHTML = '<option value="default">Default System Camera</option><option value="external">External USB Camera</option>';
    }
  },

  async loadServerCameras(selectElement) {
    try {
      const response = await fetch('/api/camera/devices');
      const res = await response.json();
      selectElement.innerHTML = '';

      if (res.success && res.data && Array.isArray(res.data.devices) && res.data.devices.length > 0) {
        res.data.devices.forEach(dev => {
          const opt = document.createElement('option');
          opt.value = dev.index;
          opt.textContent = dev.label || `Server Cam ${dev.index}`;
          selectElement.appendChild(opt);
        });
      } else {
        selectElement.innerHTML = '<option value="0">Server Cam 0 (Default)</option><option value="1">Server Cam 1 (External USB)</option>';
      }
    } catch (err) {
      console.warn('Error loading server cameras:', err);
      selectElement.innerHTML = '<option value="0">Server Cam 0 (Default)</option><option value="1">Server Cam 1 (External USB)</option>';
    }
  },

  async checkInitialStatus() {
    try {
      const response = await fetch('/api/camera/status');
      const res = await response.json();
      if (res && res.success && res.data && res.data.is_running) {
        this.streamMode = 'server';
        const modeSelect = document.getElementById('camera-mode-select');
        if (modeSelect) modeSelect.value = 'server';
        this.setStreamingUI(true);
        this.startStatusPolling();
      }
    } catch (e) {
      console.debug('Initial camera check notice:', e);
    }
  },

  dismissError() {
    const errorBanner = document.getElementById('live-camera-error-banner');
    if (errorBanner) errorBanner.style.display = 'none';
  },

  async start() {
    this.dismissError();
    const modeSelect = document.getElementById('camera-mode-select');
    this.streamMode = modeSelect ? modeSelect.value : 'browser';

    if (this.streamMode === 'browser') {
      await this.startBrowserWebcam();
    } else {
      await this.startServerHardwareCamera();
    }
  },

  async startBrowserWebcam() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support webcam access or HTTPS is required.');
      }

      const deviceSelect = document.getElementById('camera-device-select');
      const selectedDeviceId = deviceSelect ? deviceSelect.value : 'default';

      const videoConstraints = {
        width: { ideal: 640 },
        height: { ideal: 480 },
      };

      if (selectedDeviceId && selectedDeviceId !== 'default') {
        videoConstraints.deviceId = { exact: selectedDeviceId };
      } else {
        videoConstraints.facingMode = 'environment';
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: videoConstraints,
        audio: false,
      });

      this.browserStream = stream;
      const videoEl = document.getElementById('live-browser-video');
      if (videoEl) {
        videoEl.srcObject = stream;
        await videoEl.play();
      }

      this.setStreamingUI(true);
      this.startBrowserFrameLoop();

      const selectedName = deviceSelect && deviceSelect.selectedOptions.length > 0 ? deviceSelect.selectedOptions[0].textContent : 'Camera';
      app.showToast(`Connected to ${selectedName}. Live AI detection active.`, 'success');

    } catch (err) {
      console.error('Browser webcam error:', err);
      let msg = 'Could not access webcam.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Camera permission was denied. Please click the lock/camera icon in your browser address bar and allow camera access.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = 'Selected external camera was not found. Please verify the USB cable is plugged in.';
      } else {
        msg = err.message || msg;
      }
      this.showCameraError(msg);
      app.showToast(msg, 'error');
    }
  },

  startBrowserFrameLoop() {
    this.frameLoopActive = true;
    this.frameCount = 0;
    this.lastFrameTimestamp = performance.now();

    this.fpsInterval = setInterval(() => {
      this.fps = this.frameCount;
      this.frameCount = 0;
      const fpsEl = document.getElementById('live-fps-val');
      const fpsMetric = document.getElementById('live-fps-metric-val');
      if (fpsEl) fpsEl.textContent = this.fps.toFixed(1);
      if (fpsMetric) fpsMetric.textContent = this.fps.toFixed(1);
    }, 1000);

    const captureFrame = async () => {
      if (!this.frameLoopActive) return;

      const videoEl = document.getElementById('live-browser-video');
      const canvasEl = document.getElementById('live-browser-canvas');
      const streamImg = document.getElementById('live-stream-feed');

      if (videoEl && canvasEl && videoEl.readyState >= 2 && !this.isProcessingFrame) {
        this.isProcessingFrame = true;
        try {
          canvasEl.width = videoEl.videoWidth || 640;
          canvasEl.height = videoEl.videoHeight || 480;
          const ctx = canvasEl.getContext('2d');
          ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

          const base64Data = canvasEl.toDataURL('image/jpeg', 0.75);

          const payload = {
            image: base64Data,
            fps: this.fps,
            save_snapshot: this.saveNextSnapshot,
          };
          this.saveNextSnapshot = false;

          const response = await fetch('/api/camera/process_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });

          const res = await response.json();
          if (res.success && res.data) {
            this.frameCount++;
            if (streamImg && res.data.annotated_image) {
              streamImg.src = res.data.annotated_image;
              streamImg.style.display = 'block';
            }
            this.updateTelemetry(res.data);

            if (res.data.saved_snapshot) {
              this.addSnapshotToGallery(res.data.saved_snapshot);
              app.showToast('Snapshot frame recorded.', 'success');
            }
          }
        } catch (e) {
          console.debug('Frame processing cycle:', e);
        } finally {
          this.isProcessingFrame = false;
        }
      }

      if (this.frameLoopActive) {
        setTimeout(captureFrame, 150); // ~6-8 FPS inference cycle
      }
    };

    captureFrame();
  },

  stopBrowserFrameLoop() {
    this.frameLoopActive = false;
    this.isProcessingFrame = false;
    if (this.fpsInterval) {
      clearInterval(this.fpsInterval);
      this.fpsInterval = null;
    }
    if (this.browserStream) {
      this.browserStream.getTracks().forEach(track => track.stop());
      this.browserStream = null;
    }
    const videoEl = document.getElementById('live-browser-video');
    if (videoEl) {
      videoEl.srcObject = null;
    }
  },

  async startServerHardwareCamera() {
    try {
      const deviceSelect = document.getElementById('camera-device-select');
      const camIdx = deviceSelect ? parseInt(deviceSelect.value, 10) || 0 : 0;

      const response = await fetch('/api/camera/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_index: camIdx }),
      });
      const res = await response.json();

      if (!response.ok || !res.success) {
        const errorMsg = res.error || res.message || 'Server hardware camera not accessible.';
        this.showCameraError(errorMsg);
        app.showToast(errorMsg, 'error');
        return;
      }

      this.setStreamingUI(true);
      this.startStatusPolling();
      app.showToast(`Server camera ${camIdx} streaming active.`, 'success');

    } catch (err) {
      console.error('Server camera start error:', err);
      this.showCameraError('Cloud servers do not have attached USB webcams. Please switch source to "Browser Webcam".');
      app.showToast('Failed to connect to server camera.', 'error');
    }
  },

  async stop() {
    if (this.streamMode === 'browser') {
      this.stopBrowserFrameLoop();
    } else {
      this.stopStatusPolling();
      try {
        await fetch('/api/camera/stop', { method: 'POST' });
      } catch (err) {
        console.error('Camera stop network error:', err);
      }
    }

    this.setStreamingUI(false);
    app.showToast('Camera stopped.', 'info');
  },

  setStreamingUI(running) {
    this.isStreaming = running;
    const streamImg = document.getElementById('live-stream-feed');
    const offlineHolder = document.getElementById('live-offline-placeholder');
    const fpsPill = document.getElementById('live-fps-pill');
    const camIndicator = document.getElementById('live-cam-indicator');
    const btnStart = document.getElementById('btn-start-cam');
    const btnStop = document.getElementById('btn-stop-cam');
    const btnSnap = document.getElementById('btn-snap-cam');
    const modeSelect = document.getElementById('camera-mode-select');
    const devSelect = document.getElementById('camera-device-select');

    if (running) {
      if (streamImg) {
        if (this.streamMode === 'server') {
          const deviceSelect = document.getElementById('camera-device-select');
          const camIdx = deviceSelect ? parseInt(deviceSelect.value, 10) || 0 : 0;
          streamImg.src = `/api/camera/stream?camera_index=${camIdx}&t=${new Date().getTime()}`;
        }
        streamImg.style.display = 'block';
      }
      if (offlineHolder) offlineHolder.style.display = 'none';
      if (fpsPill) fpsPill.style.display = 'block';
      if (camIndicator) {
        camIndicator.className = 'badge badge-model-ok';
        camIndicator.textContent = 'Live Streaming';
      }
      if (btnStart) btnStart.disabled = true;
      if (btnStop) btnStop.disabled = false;
      if (btnSnap) btnSnap.disabled = false;
      if (modeSelect) modeSelect.disabled = true;
      if (devSelect) devSelect.disabled = true;
    } else {
      if (streamImg) {
        streamImg.src = '';
        streamImg.style.display = 'none';
      }
      if (offlineHolder) offlineHolder.style.display = 'flex';
      if (fpsPill) fpsPill.style.display = 'none';
      if (camIndicator) {
        camIndicator.className = 'badge';
        camIndicator.style.background = 'var(--bg-tertiary)';
        camIndicator.style.color = 'var(--text-secondary)';
        camIndicator.textContent = 'Offline';
      }
      if (btnStart) btnStart.disabled = false;
      if (btnStop) btnStop.disabled = true;
      if (btnSnap) btnSnap.disabled = true;
      if (modeSelect) modeSelect.disabled = false;
      if (devSelect) devSelect.disabled = false;

      this.resetTelemetry();
    }
  },

  startStatusPolling() {
    this.stopStatusPolling();
    this.statusPollInterval = setInterval(() => this.pollTelemetry(), 600);
  },

  stopStatusPolling() {
    if (this.statusPollInterval) {
      clearInterval(this.statusPollInterval);
      this.statusPollInterval = null;
    }
  },

  async pollTelemetry() {
    if (!this.isStreaming || this.streamMode !== 'server') return;

    try {
      const response = await fetch('/api/camera/status');
      const res = await response.json();
      if (res.success && res.data) {
        this.updateTelemetry(res.data);
      }
    } catch (e) {
      console.debug('Telemetry poll tick error:', e);
    }
  },

  updateTelemetry(data) {
    const isDefect = data.status === 'DEFECT';
    const statusCard = document.getElementById('live-status-card');
    const statusPill = document.getElementById('live-status-pill');
    const heading = document.getElementById('live-status-heading');
    const label = document.getElementById('live-defect-label');
    const confVal = document.getElementById('live-conf-val');
    const countVal = document.getElementById('live-count-val');
    const devIdxVal = document.getElementById('live-device-idx-val');

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
        ? `Defect identified (${data.detection_count} bounding box active via YOLO)`
        : 'Live print nominal — no defects detected';
    }

    if (confVal) {
      confVal.textContent = data.confidence_percentage > 0 ? `${data.confidence_percentage}%` : 'N/A';
    }
    if (countVal) countVal.textContent = data.detection_count ?? (data.detections ? data.detections.length : 0);
    if (devIdxVal) {
      const devSelect = document.getElementById('camera-device-select');
      const selectedName = devSelect && devSelect.selectedOptions.length > 0 ? devSelect.selectedOptions[0].textContent : (this.streamMode === 'browser' ? 'Browser Cam' : 'Server Cam');
      devIdxVal.textContent = selectedName.split('(')[0].trim();
    }
  },

  resetTelemetry() {
    const statusCard = document.getElementById('live-status-card');
    const statusPill = document.getElementById('live-status-pill');
    const heading = document.getElementById('live-status-heading');
    const label = document.getElementById('live-defect-label');
    const confVal = document.getElementById('live-conf-val');
    const countVal = document.getElementById('live-count-val');
    const fpsVal = document.getElementById('live-fps-val');
    const fpsMetricVal = document.getElementById('live-fps-metric-val');
    const devIdxVal = document.getElementById('live-device-idx-val');

    if (statusCard) statusCard.className = 'status-summary-card';
    if (statusPill) { statusPill.className = 'status-pill unknown'; statusPill.textContent = 'OFFLINE'; }
    if (heading) { heading.className = 'status-heading'; heading.textContent = 'Awaiting Feed'; }
    if (label) label.textContent = 'No live detections active';
    if (confVal) confVal.textContent = '--%';
    if (countVal) countVal.textContent = '0';
    if (fpsVal) fpsVal.textContent = '0.0';
    if (fpsMetricVal) fpsMetricVal.textContent = '0.0';
    if (devIdxVal) devIdxVal.textContent = 'Webcam';
  },

  async saveSnapshot() {
    if (this.streamMode === 'browser') {
      this.saveNextSnapshot = true;
      app.showToast('Capturing live frame snapshot...', 'info');
      return;
    }

    try {
      const response = await fetch('/api/camera/snapshot', { method: 'POST' });
      const res = await response.json();

      if (!response.ok || !res.success) {
        app.showToast(res.error || 'Failed to capture frame.', 'error');
        return;
      }

      app.showToast('Defect snapshot saved to records.', 'success');
      this.addSnapshotToGallery(res.data);

    } catch (err) {
      console.error('Snapshot capture error:', err);
      app.showToast('Network error while saving frame.', 'error');
    }
  },

  addSnapshotToGallery(item) {
    this.recentSnapshots.unshift(item);
    if (this.recentSnapshots.length > 5) this.recentSnapshots.pop();

    const list = document.getElementById('live-snapshots-list');
    if (!list) return;

    list.innerHTML = this.recentSnapshots.map(snap => `
      <div class="detection-item ${snap.status === 'DEFECT' ? '' : 'good-item'}">
        <div class="detection-info">
          <span class="detection-title">${snap.defect_type || 'Snapshot'}</span>
          <span class="detection-coords">${snap.filename}</span>
        </div>
        <a href="${snap.image_url}" target="_blank" class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">
          View ↗
        </a>
      </div>
    `).join('');
  },

  showCameraError(message) {
    const errorBanner = document.getElementById('live-camera-error-banner');
    const errorText = document.getElementById('live-cam-error-text');
    if (errorBanner) errorBanner.style.display = 'flex';
    if (errorText && message) errorText.textContent = message;
    this.setStreamingUI(false);
  }
};
