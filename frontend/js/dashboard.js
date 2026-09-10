/**
 * Dashboard & Analytics Data Controller.
 */

const dashboardController = {
  async init() {
    await this.loadStats();
    await this.loadCharts();
  },

  async loadStats() {
    try {
      const response = await fetch('/api/dashboard/stats');
      const res = await response.json();
      if (res.success && res.data) {
        const d = res.data;
        const elTotal = document.getElementById('stat-total-val');
        const elGood = document.getElementById('stat-good-val');
        const elDefect = document.getElementById('stat-defect-val');
        const elRate = document.getElementById('stat-rate-val');
        const elSubtitle = document.getElementById('stat-by-type-subtitle');

        if (elTotal) elTotal.textContent = d.total_inspections;
        if (elGood) elGood.textContent = d.good_prints;
        if (elDefect) elDefect.textContent = d.defects_detected;
        if (elRate) elRate.textContent = `${d.defect_rate}%`;
        if (elSubtitle && d.by_type) {
          elSubtitle.textContent = `${d.by_type.image || 0} Images | ${d.by_type.video || 0} Videos | ${d.by_type.live || 0} Live`;
        }
      }
    } catch (e) {
      console.error('Failed to load dashboard stats:', e);
    }
  },

  async loadCharts() {
    try {
      const response = await fetch('/api/dashboard/charts');
      const res = await response.json();
      if (res.success && res.data) {
        const c = res.data;
        // 1. Defect distribution
        if (c.defect_distribution) {
          AppCharts.renderDefectDistribution(
            'chart-defect-distribution',
            c.defect_distribution.labels,
            c.defect_distribution.data
          );
        }

        // 2. Good vs Defective
        if (c.good_vs_defect) {
          AppCharts.renderGoodVsDefect(
            'chart-good-vs-defect',
            c.good_vs_defect.labels,
            c.good_vs_defect.data
          );
        }

        // 3. Activity Timeline
        if (c.timeline) {
          AppCharts.renderActivityTimeline(
            'chart-activity-timeline',
            c.timeline.labels,
            c.timeline.good_data,
            c.timeline.defect_data
          );
        }
      }
    } catch (e) {
      console.error('Failed to load dashboard charts:', e);
    }
  }
};
