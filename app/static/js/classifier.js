// AI Medical Waste Classifier Interactive Controller
document.addEventListener('DOMContentLoaded', function () {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('wasteImageInput');
  const previewContainer = document.getElementById('previewContainer');
  const previewImage = document.getElementById('previewImage');
  const scanBtn = document.getElementById('scanBtn');
  const scanningSpinner = document.getElementById('scanningSpinner');
  const resultCard = document.getElementById('resultCard');

  if (!dropzone || !fileInput) return;

  let currentFile = null;

  // Dropzone drag-over handlers
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  });

  dropzone.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFile(fileInput.files[0]);
    }
  });

  function handleFile(file) {
    if (!file.type.match('image.*')) {
      alert('Please select an image file (PNG, JPG, JPEG, WEBP).');
      return;
    }
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImage.src = e.target.result;
      previewContainer.classList.remove('d-none');
      scanBtn.disabled = false;
      resultCard.classList.add('d-none');
    };
    reader.readAsDataURL(file);
  }

  // Scan Action
  scanBtn.addEventListener('click', () => {
    if (!currentFile) return;

    scanBtn.disabled = true;
    scanningSpinner.classList.remove('d-none');
    resultCard.classList.add('d-none');

    const formData = new FormData();
    formData.append('image', currentFile);

    fetch('/ai/scan', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        scanningSpinner.classList.add('d-none');
        scanBtn.disabled = false;

        if (!data.success) {
          alert('Error during image classification: ' + (data.error || 'Unknown error'));
          return;
        }

        renderPrediction(data);
      })
      .catch(err => {
        scanningSpinner.classList.add('d-none');
        scanBtn.disabled = false;
        alert('Server connection error: ' + err.message);
      });
  });

  function renderPrediction(data) {
    resultCard.classList.remove('d-none');

    // UI elements
    const binBadge = document.getElementById('predBinBadge');
    const catName = document.getElementById('predCategoryName');
    const confText = document.getElementById('predConfidenceText');
    const confFill = document.getElementById('predConfidenceFill');
    const containerText = document.getElementById('predContainer');
    const treatmentText = document.getElementById('predTreatment');
    const itemsText = document.getElementById('predItems');
    const demoModeIndicator = document.getElementById('demoModeIndicator');
    const warningAlert = document.getElementById('reviewWarningAlert');

    // Populate data
    binBadge.textContent = data.bin_color + ' Bin';
    binBadge.style.backgroundColor = data.bin_color_hex;
    binBadge.style.color = (data.predicted_category === 'WHITE' || data.predicted_category === 'YELLOW') ? '#1e293b' : '#ffffff';

    catName.textContent = data.category_name;
    confText.textContent = data.confidence_percent + ' (' + data.confidence_tier + ' Certainty)';

    const confPct = Math.round(data.confidence * 100);
    confFill.style.width = confPct + '%';
    if (confPct >= 75) {
      confFill.className = 'confidence-fill bg-success';
    } else if (confPct >= 50) {
      confFill.className = 'confidence-fill bg-warning';
    } else {
      confFill.className = 'confidence-fill bg-danger';
    }

    containerText.textContent = data.container_type;
    treatmentText.textContent = data.treatment_method;
    itemsText.textContent = data.permitted_items;

    if (data.demo_mode) {
      demoModeIndicator.classList.remove('d-none');
    } else {
      demoModeIndicator.classList.add('d-none');
    }

    if (data.needs_review) {
      warningAlert.classList.remove('d-none');
    } else {
      warningAlert.classList.add('d-none');
    }

    // Populate Verification Form fields
    document.getElementById('hiddenImageFilename').value = data.image_filename;
    document.getElementById('hiddenAiCategory').value = data.predicted_category;
    document.getElementById('hiddenAiConfidence').value = data.confidence;
    
    // Auto-select predicted category in dropdown
    const catSelect = document.getElementById('verifyCategorySelect');
    if (data.category_id) {
      catSelect.value = data.category_id;
    }

    // Populate probability distribution list
    const probList = document.getElementById('probabilityDistributionList');
    if (probList && data.probabilities) {
      probList.innerHTML = '';
      for (const [code, prob] of Object.entries(data.probabilities)) {
        const pct = Math.round(prob * 100);
        const li = document.createElement('div');
        li.className = 'mb-2';
        li.innerHTML = `
          <div class="d-flex justify-content-between small mb-1">
            <span class="fw-semibold">${code}</span>
            <span>${pct}%</span>
          </div>
          <div class="progress" style="height: 6px;">
            <div class="progress-bar ${code === data.predicted_category ? 'bg-primary' : 'bg-secondary'}" style="width: ${pct}%"></div>
          </div>
        `;
        probList.appendChild(li);
      }
    }

    // Scroll smoothly to results
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Verification Form Submit Action
  const verifyForm = document.getElementById('verificationForm');
  if (verifyForm) {
    verifyForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('commitRecordBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving to Ledger...';

      const formData = new FormData(verifyForm);

      fetch('/ai/confirm-and-log', {
        method: 'POST',
        body: formData
      })
        .then(res => res.json())
        .then(res => {
          if (res.success) {
            window.location.href = res.redirect_url;
          } else {
            alert('Could not save record: ' + (res.error || 'Validation error'));
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Confirm & Log Waste Record';
          }
        })
        .catch(err => {
          alert('Submission failed: ' + err.message);
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Confirm & Log Waste Record';
        });
    });
  }
});
