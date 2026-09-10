/**
 * Main Application Framework, Client-side Router, and System Coordinator.
 */

const app = {
  currentPage: 'dashboard',
  systemHealthy: false,
  modelAvailable: false,

  pageTitles: {
    'dashboard': 'Dashboard & Analytics',
    'live-inspection': 'Live Camera Defect Inspection',
    'image-inspection': 'Image Defect Inspection',
    'video-inspection': 'Video & Timelapse Inspection',
    'history': 'Inspection Audit Trail & History',
    'model-performance': 'YOLO Model Performance & Architecture',
  },

  async init() {
    this.bindNavigation();
    await this.checkSystemHealth();

    // Listen to hash change for browser history navigation
    window.addEventListener('hashchange', () => {
      const page = window.location.hash.replace('#', '') || 'dashboard';
      this.navigateTo(page, false);
    });

    const initialPage = window.location.hash.replace('#', '') || 'dashboard';
    await this.navigateTo(initialPage, true);
  },

  bindNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.getAttribute('data-page');
        if (page) this.navigateTo(page);
      });
    });

    // Close modal on backdrop click
    const modal = document.getElementById('app-modal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeModal();
      });
    }
  },

  async checkSystemHealth() {
    try {
      const response = await fetch('/api/health');
      const res = await response.json();

      if (res.success && res.data) {
        const d = res.data;
        this.systemHealthy = d.status === 'healthy';
        this.modelAvailable = d.model_available;

        const badge = document.getElementById('model-status-badge');
        const badgeText = document.getElementById('model-status-text');
        const warningBanner = document.getElementById('model-warning-banner');

        if (this.modelAvailable) {
          if (badge) badge.className = 'badge badge-model-ok';
          if (badgeText) badgeText.textContent = 'Model: Active (YOLO)';
          if (warningBanner) warningBanner.classList.add('hidden');
        } else {
          if (badge) badge.className = 'badge badge-model-missing';
          if (badgeText) badgeText.textContent = 'Model: Missing (best.pt)';
          if (warningBanner) warningBanner.classList.remove('hidden');
        }
      }
    } catch (e) {
      console.warn('Health check request failed:', e);
    }
  },

  showMissingModelBanner() {
    const warningBanner = document.getElementById('model-warning-banner');
    if (warningBanner) warningBanner.classList.remove('hidden');
  },

  async navigateTo(pageName, updateHash = true) {
    if (!this.pageTitles[pageName]) pageName = 'dashboard';
    this.currentPage = pageName;

    if (updateHash) {
      window.location.hash = pageName;
    }

    // Update active navbar item
    document.querySelectorAll('.nav-link').forEach(link => {
      if (link.getAttribute('data-page') === pageName) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Update Title in Header
    const titleEl = document.getElementById('current-page-title');
    if (titleEl) titleEl.textContent = this.pageTitles[pageName];

    // Load page template into main container
    const container = document.getElementById('app-view-container');
    if (!container) return;

    try {
      const res = await fetch(`/pages/${pageName}.html`);
      if (!res.ok) throw new Error(`Failed to load ${pageName}.html`);
      const html = await res.text();
      container.innerHTML = html;

      // Initialize page-specific controllers
      this.initPageController(pageName);
    } catch (err) {
      console.error('Page load error:', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 3rem; color: var(--status-defect);">
          <h2>Failed to load view</h2>
          <p style="color: var(--text-muted); margin-top: 0.5rem;">${err.message}</p>
        </div>
      `;
    }
  },

  initPageController(pageName) {
    switch (pageName) {
      case 'dashboard':
        if (typeof dashboardController !== 'undefined') dashboardController.init();
        break;
      case 'image-inspection':
        if (typeof imageInspection !== 'undefined') imageInspection.init();
        break;
      case 'video-inspection':
        if (typeof videoInspection !== 'undefined') videoInspection.init();
        break;
      case 'live-inspection':
        if (typeof liveCamera !== 'undefined') liveCamera.init();
        break;
      case 'history':
        if (typeof historyManager !== 'undefined') historyManager.init();
        break;
      case 'model-performance':
        this.loadModelPerformance();
        break;
    }
  },

  async loadModelPerformance() {
    try {
      // 1. Load Model Information and registered classes
      const infoRes = await fetch('/api/model/info');
      const infoData = await infoRes.json();

      if (infoData.success && infoData.data) {
        const d = infoData.data;
        const confEl = document.getElementById('perf-conf-val');
        const iouEl = document.getElementById('perf-iou-val');
        const sizeEl = document.getElementById('perf-size-val');
        const pathEl = document.getElementById('perf-model-path-code');
        const badgeEl = document.getElementById('perf-model-status-badge');
        const countBadge = document.getElementById('perf-class-count-badge');
        const classesTable = document.getElementById('perf-classes-table-body');

        if (confEl) confEl.textContent = d.confidence_threshold;
        if (iouEl) iouEl.textContent = d.iou_threshold;
        if (sizeEl) sizeEl.textContent = `${d.image_size} x ${d.image_size}`;
        if (pathEl) pathEl.textContent = d.model_path;
        if (countBadge) countBadge.textContent = `${d.classes_count} Classes`;

        if (badgeEl) {
          if (d.model_loaded) {
            badgeEl.className = 'badge badge-model-ok';
            badgeEl.textContent = 'Model Loaded';
          } else {
            badgeEl.className = 'badge badge-model-missing';
            badgeEl.textContent = 'Weights Missing';
          }
        }

        if (classesTable && d.classes) {
          classesTable.innerHTML = d.classes.map(c => `
            <tr>
              <td class="font-mono">${c.id}</td>
              <td class="font-mono" style="color: var(--accent-primary);">${c.name}</td>
              <td style="font-weight: 500;">${c.label}</td>
              <td>
                <span class="status-pill ${c.is_defect ? 'defect' : 'good'}" style="font-size: 0.75rem; padding: 0.2rem 0.6rem;">
                  ${c.is_defect ? 'Defect' : 'Normal / Good'}
                </span>
              </td>
            </tr>
          `).join('');
        }
      }

      // 2. Load genuine training metrics
      const metricRes = await fetch('/api/model/metrics');
      const metricData = await metricRes.json();

      const metricsContainer = document.getElementById('perf-metrics-container');
      const noMetricsNotice = document.getElementById('perf-no-metrics-notice');

      if (metricData.success && metricData.data && metricData.data.metrics_available) {
        if (metricsContainer) metricsContainer.style.display = 'block';
        if (noMetricsNotice) noMetricsNotice.style.display = 'none';

        const kpiGrid = document.getElementById('perf-metrics-kpi-grid');
        const cmImg = document.getElementById('perf-cm-img');
        const plotImg = document.getElementById('perf-plot-img');

        if (kpiGrid && metricData.data.metrics) {
          const m = metricData.data.metrics;
          kpiGrid.innerHTML = Object.keys(m).map(k => `
            <div class="metric-box">
              <div class="metric-box-label">${k}</div>
              <div class="metric-box-value">${m[k]}</div>
            </div>
          `).join('');
        }

        if (cmImg && metricData.data.confusion_matrix_url) {
          cmImg.src = metricData.data.confusion_matrix_url;
        }
        if (plotImg && metricData.data.training_plot_url) {
          plotImg.src = metricData.data.training_plot_url;
        }
      } else {
        if (metricsContainer) metricsContainer.style.display = 'none';
        if (noMetricsNotice) noMetricsNotice.style.display = 'block';
      }

    } catch (e) {
      console.error('Error loading model performance data:', e);
    }
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  openModal(contentHtml) {
    const modal = document.getElementById('app-modal');
    const body = document.getElementById('modal-body-container');
    if (modal && body) {
      body.innerHTML = contentHtml;
      modal.classList.add('active');
    }
  },

  closeModal() {
    const modal = document.getElementById('app-modal');
    if (modal) {
      modal.classList.remove('active');
    }
  }
};

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
