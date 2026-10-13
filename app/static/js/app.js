// Global Utilities & Interactive Behaviors
document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss bootstrap alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert.alert-dismissible:not(.alert-permanent)');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
      } catch (e) {
        alert.remove();
      }
    }, 6000);
  });

  // Initialize tooltips if any
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
