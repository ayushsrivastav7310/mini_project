// Chart.js Dashboard Visualizations
document.addEventListener('DOMContentLoaded', function () {
  const categoryChartCanvas = document.getElementById('categoryDoughnutChart');
  const trendChartCanvas = document.getElementById('trendLineChart');
  const deptChartCanvas = document.getElementById('departmentBarChart');

  if (!categoryChartCanvas || !trendChartCanvas || !deptChartCanvas) return;

  fetch('/api/dashboard/stats')
    .then(response => response.json())
    .then(data => {
      renderCategoryChart(categoryChartCanvas, data.category_stats);
      renderTrendChart(trendChartCanvas, data.trend_labels, data.trend_data);
      renderDeptChart(deptChartCanvas, data.department_stats);
    })
    .catch(err => console.error('Error fetching dashboard statistics:', err));

  function renderCategoryChart(canvas, categoryStats) {
    const labels = categoryStats.map(c => c.name);
    const values = categoryStats.map(c => c.total_kg);
    const colors = categoryStats.map(c => c.color_hex);

    new Chart(canvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const val = ctx.raw || 0;
                return ` ${ctx.label}: ${val.toFixed(2)} kg`;
              }
            }
          }
        },
        cutout: '65%'
      }
    });
  }

  function renderTrendChart(canvas, labels, dataPoints) {
    new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Waste Generated (kg)',
          data: dataPoints,
          borderColor: '#0284c7',
          backgroundColor: 'rgba(2, 132, 199, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: '#0284c7',
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function (val) { return val + ' kg'; }
            },
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  function renderDeptChart(canvas, deptStats) {
    const labels = deptStats.map(d => d.code);
    const values = deptStats.map(d => d.total_kg);

    new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Waste Logged (kg)',
          data: values,
          backgroundColor: '#0f766e',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function (val) { return val + ' kg'; }
            },
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }
});
