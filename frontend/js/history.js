/**
 * Inspection History & Audit Trail Controller.
 */

const historyManager = {
  currentPage: 1,
  totalPages: 1,
  totalItems: 0,
  searchDebounceTimer: null,

  init() {
    this.bindEvents();
    this.fetchHistory();
  },

  bindEvents() {
    const searchInput = document.getElementById('history-search-input');
    const filterType = document.getElementById('history-filter-type');
    const filterStatus = document.getElementById('history-filter-status');
    const filterDefect = document.getElementById('history-filter-defect');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
          this.currentPage = 1;
          this.fetchHistory();
        }, 300);
      });
    }

    if (filterType) filterType.addEventListener('change', () => { this.currentPage = 1; this.fetchHistory(); });
    if (filterStatus) filterStatus.addEventListener('change', () => { this.currentPage = 1; this.fetchHistory(); });
    if (filterDefect) filterDefect.addEventListener('change', () => { this.currentPage = 1; this.fetchHistory(); });
  },

  async fetchHistory() {
    const search = document.getElementById('history-search-input')?.value || '';
    const type = document.getElementById('history-filter-type')?.value || 'all';
    const status = document.getElementById('history-filter-status')?.value || 'ALL';
    const defect = document.getElementById('history-filter-defect')?.value || 'all';

    const params = new URLSearchParams({
      page: this.currentPage,
      per_page: 10,
    });
    if (search) params.append('search', search);
    if (type !== 'all') params.append('type', type);
    if (status !== 'ALL') params.append('status', status);
    if (defect !== 'all') params.append('defect', defect);

    const tbody = document.getElementById('history-table-body');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            <div class="spinner" style="margin: 0 auto 0.75rem auto;"></div>
            Fetching inspection records...
          </td>
        </tr>
      `;
    }

    try {
      const response = await fetch(`/api/history?${params.toString()}`);
      const res = await response.json();

      if (res.success && res.data) {
        this.currentPage = res.data.pagination.page;
        this.totalPages = res.data.pagination.total_pages;
        this.totalItems = res.data.pagination.total_items;
        this.renderTable(res.data.items);
        this.updatePagination();
      }
    } catch (err) {
      console.error('History fetch error:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" style="text-align: center; padding: 2rem; color: var(--status-defect);">
              Failed to load records.
            </td>
          </tr>
        `;
      }
    }
  },

  renderTable(items) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    if (!items || items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
            No inspection records found matching criteria.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = items.map(item => {
      const isDefect = item.status === 'DEFECT';
      const typeBadgeClass = item.inspection_type === 'image' ? 'badge-model-ok' : (item.inspection_type === 'video' ? 'badge' : 'badge-model-missing');
      const formattedDate = item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A';
      const fileName = item.original_filename || item.result_filename || 'Record';
      const confDisplay = item.confidence ? `${Math.round(item.confidence * 100)}%` : '--';
      const timeDisplay = item.inspection_type === 'video' ? `${item.processing_time}s` : `${item.processing_time}ms`;

      return `
        <tr>
          <td class="font-mono" style="color: var(--accent-primary); font-weight: 600;">#${item.id}</td>
          <td>
            <span class="badge" style="background: var(--bg-tertiary); color: var(--text-primary); text-transform: uppercase;">
              ${item.inspection_type}
            </span>
          </td>
          <td style="color: var(--text-secondary); font-size: 0.85rem;">${formattedDate}</td>
          <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${fileName}">
            ${fileName}
          </td>
          <td>
            <span class="status-pill ${isDefect ? 'defect' : 'good'}" style="font-size: 0.75rem; padding: 0.2rem 0.6rem;">
              ${isDefect ? 'DEFECT' : 'GOOD'}
            </span>
          </td>
          <td style="font-weight: 500;">${item.defect_type || 'Normal / Good'}</td>
          <td style="font-weight: 600; color: ${isDefect ? 'var(--status-defect)' : 'var(--status-good)'};">${confDisplay}</td>
          <td style="color: var(--text-muted); font-size: 0.85rem;">${timeDisplay}</td>
          <td style="text-align: right;">
            <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
              <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="historyManager.viewRecord(${item.id})">
                View 🔍
              </button>
              <button class="btn btn-danger" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="historyManager.deleteRecord(${item.id})">
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  updatePagination() {
    const pageInfo = document.getElementById('history-page-info');
    const btnPrev = document.getElementById('btn-prev-page');
    const btnNext = document.getElementById('btn-next-page');

    if (pageInfo) {
      pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages} (${this.totalItems} total inspections)`;
    }
    if (btnPrev) btnPrev.disabled = this.currentPage <= 1;
    if (btnNext) btnNext.disabled = this.currentPage >= this.totalPages;
  },

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.fetchHistory();
    }
  },

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.fetchHistory();
    }
  },

  resetFilters() {
    const s = document.getElementById('history-search-input');
    const t = document.getElementById('history-filter-type');
    const st = document.getElementById('history-filter-status');
    const d = document.getElementById('history-filter-defect');
    if (s) s.value = '';
    if (t) t.value = 'all';
    if (st) st.value = 'ALL';
    if (d) d.value = 'all';
    this.currentPage = 1;
    this.fetchHistory();
  },

  async viewRecord(id) {
    try {
      const response = await fetch(`/api/history/${id}`);
      const res = await response.json();

      if (!res.success || !res.data) {
        app.showToast('Failed to load inspection details.', 'error');
        return;
      }

      const rec = res.data;
      const isDefect = rec.status === 'DEFECT';
      let mediaHtml = '';

      if (rec.inspection_type === 'video') {
        mediaHtml = `
          <video controls style="width: 100%; max-height: 360px; border-radius: var(--radius-md); background: #000; margin-bottom: 1rem;">
            <source src="/results/videos/${rec.result_filename}">
          </video>
        `;
      } else if (rec.inspection_type === 'live') {
        mediaHtml = `
          <img src="/results/live_frames/${rec.result_filename}" alt="Snapshot" style="width: 100%; max-height: 360px; object-fit: contain; border-radius: var(--radius-md); background: #000; margin-bottom: 1rem;">
        `;
      } else {
        mediaHtml = `
          <img src="/results/images/${rec.result_filename}" alt="Annotated Result" style="width: 100%; max-height: 360px; object-fit: contain; border-radius: var(--radius-md); background: #000; margin-bottom: 1rem;">
        `;
      }

      const detectionsHtml = rec.detections && rec.detections.length > 0
        ? rec.detections.map(d => `
          <div class="detection-item">
            <div class="detection-info">
              <span class="detection-title">${d.class_name}</span>
              <span class="detection-coords">BBox: [${d.bbox.x1}, ${d.bbox.y1}] → [${d.bbox.x2}, ${d.bbox.y2}]</span>
            </div>
            <span class="detection-conf">${Math.round(d.confidence * 100)}%</span>
          </div>
        `).join('')
        : '<p style="color: var(--text-muted); font-size: 0.85rem;">No localized defect instances recorded.</p>';

      const content = `
        <div class="modal-header">
          <h2 style="font-size: 1.25rem; font-weight: 700;">Inspection Record #${rec.id}</h2>
          <button class="modal-close" onclick="app.closeModal()">✕</button>
        </div>
        <div>
          ${mediaHtml}
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
            <div class="metric-box">
              <div class="metric-box-label">Status</div>
              <div class="status-pill ${isDefect ? 'defect' : 'good'}">${rec.status}</div>
            </div>
            <div class="metric-box">
              <div class="metric-box-label">Dominant Defect</div>
              <div class="metric-box-value" style="font-size: 1rem;">${rec.defect_type || 'Normal'}</div>
            </div>
            <div class="metric-box">
              <div class="metric-box-label">Confidence</div>
              <div class="metric-box-value">${Math.round((rec.confidence || 0) * 100)}%</div>
            </div>
            <div class="metric-box">
              <div class="metric-box-label">Source</div>
              <div class="metric-box-value" style="font-size: 0.9rem;">${rec.source || 'System'}</div>
            </div>
          </div>

          <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem;">Detection Coordinates</h3>
          <div class="detections-list-container" style="max-height: 180px;">
            ${detectionsHtml}
          </div>
        </div>
      `;

      app.openModal(content);
    } catch (e) {
      console.error('Error fetching record details:', e);
      app.showToast('Network error opening record.', 'error');
    }
  },

  async deleteRecord(id) {
    if (!confirm(`Are you sure you want to delete inspection record #${id}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/history/${id}`, { method: 'DELETE' });
      const res = await response.json();
      if (res.success) {
        app.showToast(`Record #${id} deleted.`, 'success');
        this.fetchHistory();
      } else {
        app.showToast(res.error || 'Failed to delete record.', 'error');
      }
    } catch (e) {
      console.error('Delete error:', e);
      app.showToast('Network error deleting record.', 'error');
    }
  }
};
