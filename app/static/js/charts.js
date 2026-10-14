// Real-Time Live Operations Center & Chart.js Controller
document.addEventListener('DOMContentLoaded', function () {
  const categoryCanvas = document.getElementById('categoryDoughnutChart');
  const trendCanvas = document.getElementById('trendLineChart');
  const deptCanvas = document.getElementById('departmentBarChart');

  if (!categoryCanvas || !trendCanvas || !deptCanvas) return;

  const deptFilter = document.getElementById('liveDepartmentFilter');
  const intervalSelect = document.getElementById('liveRefreshInterval');
  const manualSyncBtn = document.getElementById('manualSyncBtn');
  const syncIcon = document.getElementById('syncIcon');
  const syncTimestampEl = document.getElementById('liveSyncTimestamp');

  let categoryChart = null;
  let trendChart = null;
  let deptChart = null;
  let pollingTimer = null;

  // Initialize
  fetchAndUpdateLiveStats();
  setupPolling();

  // Event Listeners
  deptFilter?.addEventListener('change', () => {
    fetchAndUpdateLiveStats();
  });

  intervalSelect?.addEventListener('change', () => {
    setupPolling();
  });

  manualSyncBtn?.addEventListener('click', () => {
    if (syncIcon) syncIcon.classList.add('spin-animation');
    fetchAndUpdateLiveStats().finally(() => {
      setTimeout(() => {
        if (syncIcon) syncIcon.classList.remove('spin-animation');
      }, 500);
    });
  });

  function setupPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    const intervalMs = parseInt(intervalSelect?.value || '15000', 10);
    if (intervalMs > 0) {
      pollingTimer = setInterval(() => {
        fetchAndUpdateLiveStats();
      }, intervalMs);
    }
  }

  function fetchAndUpdateLiveStats() {
    const deptId = deptFilter?.value || '';
    const url = `/api/dashboard/live${deptId ? `?department_id=${deptId}` : ''}`;

    return fetch(url)
      .then(res => res.json())
      .then(data => {
        updateDOMMetrics(data);
        updateCharts(data);
        if (syncTimestampEl && data.sync_time) {
          syncTimestampEl.textContent = data.sync_time;
        }
      })
      .catch(err => console.error('Error fetching real-time live telemetry:', err));
  }

  function updateDOMMetrics(data) {
    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined && val !== null) el.textContent = val;
    };

    setTxt('kpiTotalKg', data.total_kg);
    setTxt('kpiTotalRecords', data.total_records);
    setTxt('kpiTodayKg', data.today_kg);
    setTxt('kpiTodayRecords', data.today_records);
    setTxt('kpiPendingVerif', data.pending_verifications);
    setTxt('kpiDispatchedKg', data.dispatched_kg);
    setTxt('kpiStoredKg', data.stored_kg);

    if (data.compliance) {
      setTxt('kpiComplianceScore', data.compliance.score + '%');
      setTxt('kpiComplianceGrade', data.compliance.grade);
      const scoreEl = document.getElementById('kpiComplianceScore');
      if (scoreEl && data.compliance.class) {
        scoreEl.className = 'fw-bold my-1 ' + data.compliance.class;
      }
    }

    if (data.forecast) {
      setTxt('kpiForecastKg', data.forecast.tomorrow_kg);
      setTxt('kpiForecastTrend', data.forecast.trend_direction);
    }

    // Update anomalies container
    const anomalyContainer = document.getElementById('liveAnomalyContainer');
    if (anomalyContainer) {
      if (!data.anomalies || data.anomalies.length === 0) {
        anomalyContainer.classList.add('d-none');
        anomalyContainer.innerHTML = '';
      } else {
        anomalyContainer.classList.remove('d-none');
        let html = '';
        data.anomalies.forEach(a => {
          const alertClass = a.level === 'CRITICAL' ? 'alert-danger border-danger' : (a.level === 'WARNING' ? 'alert-warning border-warning' : 'alert-info border-info');
          const iconClass = a.level === 'CRITICAL' ? 'bi-shield-x fs-3 text-danger' : (a.level === 'WARNING' ? 'bi-exclamation-triangle-fill fs-3 text-warning' : 'bi-info-circle-fill fs-3 text-info');
          html += `
            <div class="alert ${alertClass} shadow-sm d-flex align-items-center justify-content-between mb-2" role="alert">
              <div class="d-flex align-items-center">
                <i class="bi ${iconClass} me-3"></i>
                <div>
                  <div class="fw-bold">${a.title}</div>
                  <div class="small">${a.message}</div>
                </div>
              </div>
            </div>`;
        });
        anomalyContainer.innerHTML = html;
      }
    }
  }

  function updateCharts(data) {
    // 1. Doughnut Chart
    if (data.category_stats) {
      const catLabels = data.category_stats.map(c => c.name);
      const catValues = data.category_stats.map(c => c.total_kg);
      const catColors = data.category_stats.map(c => c.color_hex);

      if (!categoryChart) {
        categoryChart = new Chart(categoryCanvas.getContext('2d'), {
          type: 'doughnut',
          data: {
            labels: catLabels,
            datasets: [{
              data: catValues,
              backgroundColor: catColors,
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
                  label: ctx => ` ${ctx.label}: ${(ctx.raw || 0).toFixed(2)} kg`
                }
              }
            },
            cutout: '65%'
          }
        });
      } else {
        categoryChart.data.labels = catLabels;
        categoryChart.data.datasets[0].data = catValues;
        categoryChart.data.datasets[0].backgroundColor = catColors;
        categoryChart.update();
      }
    }

    // 2. Trend Line Chart
    if (data.trend_labels && data.trend_data) {
      if (!trendChart) {
        trendChart = new Chart(trendCanvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: data.trend_labels,
            datasets: [{
              label: 'Daily Generation (kg)',
              data: data.trend_data,
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
            plugins: { legend: { display: false } },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { callback: val => val + ' kg' },
                grid: { color: '#f1f5f9' }
              },
              x: { grid: { display: false } }
            }
          }
        });
      } else {
        trendChart.data.labels = data.trend_labels;
        trendChart.data.datasets[0].data = data.trend_data;
        trendChart.update();
      }
    }

    // 3. Department Bar Chart
    if (data.department_stats) {
      const deptLabels = data.department_stats.map(d => d.code);
      const deptValues = data.department_stats.map(d => d.total_kg);

      if (!deptChart) {
        deptChart = new Chart(deptCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels: deptLabels,
            datasets: [{
              label: 'Ward Generation (kg)',
              data: deptValues,
              backgroundColor: '#0f766e',
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { callback: val => val + ' kg' },
                grid: { color: '#f1f5f9' }
              },
              x: { grid: { display: false } }
            }
          }
        });
      } else {
        deptChart.data.labels = deptLabels;
        deptChart.data.datasets[0].data = deptValues;
        deptChart.update();
      }
    }
  }
});
