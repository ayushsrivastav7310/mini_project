// Advanced AI Medical Waste Classifier & Live Camera Controller
document.addEventListener('DOMContentLoaded', function () {
  // Elements
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('wasteImageInput');
  const previewContainer = document.getElementById('previewContainer');
  const previewImage = document.getElementById('previewImage');
  const clearImageBtn = document.getElementById('clearImageBtn');
  const scanBtn = document.getElementById('scanBtn');
  const scanningSpinner = document.getElementById('scanningSpinner');
  const resultCard = document.getElementById('resultCard');
  const emptyPromptCard = document.getElementById('emptyPromptCard');

  // Tabs & Camera
  const tabUpload = document.getElementById('tabUpload');
  const tabCamera = document.getElementById('tabCamera');
  const uploadModeContainer = document.getElementById('uploadModeContainer');
  const cameraModeContainer = document.getElementById('cameraModeContainer');
  const startCameraBtn = document.getElementById('startCameraBtn');
  const snapPhotoBtn = document.getElementById('snapPhotoBtn');
  const cameraVideo = document.getElementById('cameraVideo');
  const cameraCanvas = document.getElementById('cameraCanvas');
  const cameraStartOverlay = document.getElementById('cameraStartOverlay');

  // Result Elements
  const predBinBadge = document.getElementById('predBinBadge');
  const predCategoryName = document.getElementById('predCategoryName');
  const activeEngineBadge = document.getElementById('activeEngineBadge');
  const predConfidenceText = document.getElementById('predConfidenceText');
  const predConfidenceFill = document.getElementById('predConfidenceFill');
  const reviewWarningAlert = document.getElementById('reviewWarningAlert');
  const predContainer = document.getElementById('predContainer');
  const predTreatment = document.getElementById('predTreatment');
  const predItems = document.getElementById('predItems');
  const probList = document.getElementById('probabilityDistributionList');

  // Telemetry Elements
  const telDominantHue = document.getElementById('telDominantHue');
  const telInferredMaterial = document.getElementById('telInferredMaterial');
  const telTextureComplexity = document.getElementById('telTextureComplexity');
  const telOpticalProfile = document.getElementById('telOpticalProfile');
  const telemetryEngineLabel = document.getElementById('telemetryEngineLabel');

  // Verification Form
  const commitForm = document.getElementById('verificationCommitForm');
  const formImageFilename = document.getElementById('formImageFilename');
  const formAiSuggestedCategory = document.getElementById('formAiSuggestedCategory');
  const formAiConfidence = document.getElementById('formAiConfidence');
  const formAssignedCategory = document.getElementById('formAssignedCategory');
  const formDescription = document.getElementById('formDescription');
  const formDepartmentId = document.getElementById('formDepartmentId');
  const commitRecordBtn = document.getElementById('commitRecordBtn');
  const resetScanBtn = document.getElementById('resetScanBtn');

  let currentFile = null;
  let videoStream = null;

  // 1. Tab Switching
  tabUpload?.addEventListener('click', () => {
    tabUpload.classList.add('active');
    tabCamera?.classList.remove('active');
    uploadModeContainer?.classList.remove('d-none');
    cameraModeContainer?.classList.add('d-none');
    stopCamera();
  });

  tabCamera?.addEventListener('click', () => {
    tabCamera.classList.add('active');
    tabUpload?.classList.remove('active');
    uploadModeContainer?.classList.add('d-none');
    cameraModeContainer?.classList.remove('d-none');
  });

  // 2. Camera Activation & Frame Snapping
  startCameraBtn?.addEventListener('click', () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(stream => {
          videoStream = stream;
          cameraVideo.srcObject = stream;
          cameraStartOverlay.classList.add('d-none');
          snapPhotoBtn.classList.remove('d-none');
        })
        .catch(err => {
          alert('Unable to access workstation camera: ' + err.message + '\nPlease use file upload instead.');
        });
    } else {
      alert('Camera access is not supported on this browser. Please use file upload.');
    }
  });

  snapPhotoBtn?.addEventListener('click', () => {
    if (!videoStream) return;
    const context = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth || 640;
    cameraCanvas.height = cameraVideo.videoHeight || 480;
    context.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

    cameraCanvas.toBlob(blob => {
      const file = new File([blob], 'camera_waste_capture.jpg', { type: 'image/jpeg' });
      handleFile(file);
      stopCamera();
      cameraStartOverlay.classList.remove('d-none');
      snapPhotoBtn.classList.add('d-none');
      // Switch back to preview
      uploadModeContainer?.classList.remove('d-none');
      cameraModeContainer?.classList.add('d-none');
      tabUpload?.classList.add('active');
      tabCamera?.classList.remove('active');
    }, 'image/jpeg', 0.92);
  });

  function stopCamera() {
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop());
      videoStream = null;
    }
  }

  // 3. File Dropzone
  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(name => {
      dropzone.addEventListener(name, e => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      dropzone.addEventListener(name, e => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', e => {
      if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
      }
    });

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleFile(fileInput.files[0]);
      }
    });
  }

  clearImageBtn?.addEventListener('click', () => {
    currentFile = null;
    previewContainer.classList.add('d-none');
    uploadModeContainer.classList.remove('d-none');
    scanBtn.disabled = true;
    resultCard.classList.add('d-none');
    emptyPromptCard.classList.remove('d-none');
  });

  function handleFile(file) {
    if (!file.type.match('image.*')) {
      alert('Please select a valid image file (PNG, JPG, JPEG, WEBP).');
      return;
    }
    currentFile = file;
    const reader = new FileReader();
    reader.onload = e => {
      previewImage.src = e.target.result;
      previewContainer.classList.remove('d-none');
      scanBtn.disabled = false;
      resultCard.classList.add('d-none');
      emptyPromptCard.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
  }

  // 4. Run AI Scan
  scanBtn?.addEventListener('click', () => {
    if (!currentFile) return;

    scanBtn.disabled = true;
    scanningSpinner.classList.remove('d-none');
    resultCard.classList.add('d-none');
    emptyPromptCard.classList.add('d-none');

    const formData = new FormData();
    formData.append('image', currentFile);

    fetch('/ai/scan', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        scanningSpinner.classList.add('d-none');
        scanBtn.disabled = false;

        if (!data.success) {
          alert('Error during visual classification: ' + (data.error || 'Unknown error'));
          emptyPromptCard.classList.remove('d-none');
          return;
        }

        renderPrediction(data);
      })
      .catch(err => {
        scanningSpinner.classList.add('d-none');
        scanBtn.disabled = false;
        alert('Server communication error: ' + err.message);
        emptyPromptCard.classList.remove('d-none');
      });
  });

  function renderPrediction(data) {
    resultCard.classList.remove('d-none');
    emptyPromptCard.classList.add('d-none');

    // Header badge
    predBinBadge.textContent = data.bin_color + ' Bin';
    predBinBadge.style.backgroundColor = data.bin_color_hex;
    predBinBadge.style.color = (data.predicted_category === 'WHITE' || data.predicted_category === 'YELLOW') ? '#1e293b' : '#ffffff';
    predCategoryName.textContent = data.category_name;

    if (activeEngineBadge && data.engine_name) {
      activeEngineBadge.textContent = data.engine_name;
    }

    // Confidence
    const pct = Math.round(data.confidence * 100);
    predConfidenceText.textContent = pct + '% (' + data.confidence_tier + ' CERTAINTY)';
    predConfidenceFill.style.width = pct + '%';
    predConfidenceFill.className = 'confidence-fill ' + (pct >= 75 ? 'bg-success' : (pct >= 50 ? 'bg-warning' : 'bg-danger'));

    // Warning alert
    if (data.needs_review) {
      reviewWarningAlert.classList.remove('d-none');
    } else {
      reviewWarningAlert.classList.add('d-none');
    }

    // BMW Guidance
    predContainer.textContent = data.container_type;
    predTreatment.textContent = data.treatment_method;
    predItems.textContent = data.permitted_items;

    // Feature Telemetry
    if (data.feature_telemetry) {
      const tel = data.feature_telemetry;
      if (telDominantHue) telDominantHue.textContent = tel.dominant_hue_name || 'N/A';
      if (telInferredMaterial) telInferredMaterial.textContent = tel.inferred_material || 'N/A';
      if (telTextureComplexity) telTextureComplexity.textContent = tel.texture_complexity || 'N/A';
      if (telOpticalProfile) telOpticalProfile.textContent = tel.optical_profile || 'N/A';
      if (telemetryEngineLabel) telemetryEngineLabel.textContent = tel.engine || data.engine_name;
    }

    // Multi-category probabilities list
    if (probList && data.probabilities) {
      let listHtml = '';
      for (const [cat, p] of Object.entries(data.probabilities)) {
        const probPct = Math.round(p * 100);
        listHtml += `
          <div class="mb-2">
            <div class="d-flex justify-content-between small mb-1">
              <span class="fw-semibold">${cat}</span>
              <span class="text-muted">${probPct}%</span>
            </div>
            <div class="progress" style="height: 6px;">
              <div class="progress-bar ${cat === data.predicted_category ? 'bg-primary' : 'bg-secondary'}" style="width: ${probPct}%;"></div>
            </div>
          </div>`;
      }
      probList.innerHTML = listHtml;
    }

    // Pre-populate verification form
    if (formImageFilename) formImageFilename.value = data.image_filename;
    if (formAiSuggestedCategory) formAiSuggestedCategory.value = data.predicted_category;
    if (formAiConfidence) formAiConfidence.value = data.confidence;
    if (formDescription && !formDescription.value) {
      formDescription.value = (data.feature_telemetry?.inferred_material || data.category_name);
    }

    // Auto-select category in dropdown
    if (formAssignedCategory) {
      for (let i = 0; i < formAssignedCategory.options.length; i++) {
        if (formAssignedCategory.options[i].getAttribute('data-code') === data.predicted_category) {
          formAssignedCategory.selectedIndex = i;
          break;
        }
      }
    }
  }

  // 5. Verification Form Submission
  commitForm?.addEventListener('submit', function (e) {
    e.preventDefault();

    if (!formDepartmentId.value) {
      alert('Please select the originating hospital department.');
      formDepartmentId.focus();
      return;
    }

    commitRecordBtn.disabled = true;
    commitRecordBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Committing to Waste Ledger...';

    const formData = new FormData(commitForm);

    fetch('/ai/confirm-and-log', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          alert('Error committing record: ' + (data.error || 'Unknown error'));
          commitRecordBtn.disabled = false;
          commitRecordBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Confirm, Print Slip & Commit to Ledger';
          return;
        }

        // Successfully committed -> Redirect to printable slip
        window.location.href = data.redirect_url;
      })
      .catch(err => {
        commitRecordBtn.disabled = false;
        commitRecordBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Confirm, Print Slip & Commit to Ledger';
        alert('Server error while saving record: ' + err.message);
      });
  });

  resetScanBtn?.addEventListener('click', () => {
    currentFile = null;
    previewContainer.classList.add('d-none');
    scanBtn.disabled = true;
    resultCard.classList.add('d-none');
    emptyPromptCard.classList.remove('d-none');
    commitForm.reset();
  });
});
