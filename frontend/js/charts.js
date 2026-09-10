/**
 * Chart.js Visualization Wrappers and Rendering Utilities.
 */

const AppCharts = {
  distributionChart: null,
  goodVsDefectChart: null,
  timelineChart: null,

  // Color tokens aligned with design system
  colors: {
    defectColors: [
      '#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#3b82f6'
    ],
    good: '#10b981',
    defect: '#ef4444',
    bgDark: '#1e293b',
    border: '#334155',
    text: '#94a3b8',
    grid: 'rgba(51, 65, 85, 0.4)'
  },

  renderDefectDistribution(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.distributionChart) {
      this.distributionChart.destroy();
    }

    if (!labels || labels.length === 0 || data.every(v => v === 0)) {
      labels = ['No Defects Recorded'];
      data = [1];
    }

    this.distributionChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: this.colors.defectColors,
          borderWidth: 2,
          borderColor: '#182234'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
          }
        },
        cutout: '65%'
      }
    });
  },

  renderGoodVsDefect(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.goodVsDefectChart) {
      this.goodVsDefectChart.destroy();
    }

    this.goodVsDefectChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: [this.colors.good, this.colors.defect],
          borderWidth: 2,
          borderColor: '#182234'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
          }
        }
      }
    });
  },

  renderActivityTimeline(canvasId, labels, goodData, defectData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.timelineChart) {
      this.timelineChart.destroy();
    }

    this.timelineChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Good Prints',
            data: goodData,
            backgroundColor: this.colors.good,
            borderRadius: 4
          },
          {
            label: 'Defects Detected',
            data: defectData,
            backgroundColor: this.colors.defect,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            grid: { color: this.colors.grid },
            ticks: { color: this.colors.text }
          },
          y: {
            stacked: true,
            beginAtZero: true,
            grid: { color: this.colors.grid },
            ticks: { color: this.colors.text, stepSize: 1 }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
          }
        }
      }
    });
  }
};
