/**
 * Live Camera Stream and Real-time Telemetry Controller.
 */

const liveCamera = {
  isStreaming: false,
  statusPollInterval: null,
  recentSnapshots: [],
  devices: [],

  init() {
    this.loadCameraDevices();
    this.checkInitialStatus();
  },

  async loadCameraDevices() {
    const select = document.getElementById('camera-select');
    if (!select) return;

    try {
      const response = await fetch('/api/camera/devices');
      const res = await response.json();
      if (res.success && res.data && Array.isArray(res.data.devices)) {
        this.devices = res.data.devices;
        const currentIdx = res.data.current_index ?? 0;

        select.innerHTML = '';
        this.devices.forEach(dev => {
          const opt = document.createElement('option');
          opt.value = dev.index;
          opt.textContent = dev.label || `Camera ${dev.index}: ${dev.name}`;
          if (dev.index === currentIdx) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });

        if (this.devices.length === 0) {
          select.innerHTML = '<option value="0">Default Camera (Cam 0)</option>';
        }
      }
    } catch (e) {
      console.warn('Failed to load camera devices:', e);
      if (select && select.options.length === 0) {
        select.innerHTML = '<option value="0">Cam 0 (Default)</option><option value="1">Cam 1 (External USB)</option>';
      }
    }
  },

  async checkInitialStatus() {
    try {
      const response = await fetch('/api/camera/status');
      const res = await response.json();
      if (res.success && res.data && res.data.is_running) {
        this.setStreamingUI(true);
        this.startStatusPolling();
      }
    } catch (e) {
      console.warn('Initial camera check failed:', e);
    }
  },

  dismissError() {
    const errorBanner = document.getElementById('live-camera-error-banner');
    if (errorBanner) errorBanner.style.display = 'none';
  },

  async start() {
    this.dismissError();

    const select = document.getElementById('camera-select');
    const selectedIndex = select ? parseInt(select.value, 10) : 0;

    try {
      const response = await fetch('/api/camera/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_index: selectedIndex }),
      });
      const res = await response.json();

      if (!response.ok || !res.success) {
        const errorMsg = res.error || res.message || 'Camera not accessible.';
        this.showCameraError(errorMsg);
        app.showToast(errorMsg, 'error');
        return;
      }

      this.setStreamingUI(true);
      this.startStatusPolling();
      app.showToast(`Camera ${selectedIndex} streaming started.`, 'success');

    } catch (err) {
      console.error('Camera start error:', err);
      this.showCameraError('Camera not accessible. Please check Windows Camera Privacy settings and verify the USB cable is plugged in.');
      app.showToast('Failed to connect to webcam.', 'error');
    }
  },

  async stop() {
    this.stopStatusPolling();

    try {
      await fetch('/api/camera/stop', { method: 'POST' });
    } catch (err) {
      console.error('Camera stop network error:', err);
    } finally {
      this.setStreamingUI(false);
      app.showToast('Webcam stopped.', 'info');
    }
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

    if (running) {
      if (streamImg) {
        const select = document.getElementById('camera-select');
        const camIdx = select ? parseInt(select.value, 10) : 0;
        streamImg.src = `/api/camera/stream?camera_index=${camIdx}&t=${new Date().getTime()}`;
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
    if (!this.isStreaming) return;

    try {
      const response = await fetch('/api/camera/status');
      const res = await response.json();
      if (res.success && res.data) {
        const d = res.data;
        this.updateTelemetry(d);
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
    const fpsVal = document.getElementById('live-fps-val');
    const fpsMetricVal = document.getElementById('live-fps-metric-val');
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
    if (countVal) countVal.textContent = data.detection_count;
    if (fpsVal) fpsVal.textContent = data.fps;
    if (fpsMetricVal) fpsMetricVal.textContent = data.fps;
    if (devIdxVal && data.camera_index !== undefined) devIdxVal.textContent = `Cam ${data.camera_index}`;
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
    if (devIdxVal) {
      const select = document.getElementById('camera-select');
      devIdxVal.textContent = select ? `Cam ${select.value}` : 'Cam 0';
    }
  },

  async saveSnapshot() {
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
