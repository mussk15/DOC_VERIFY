// DocuVerify AI - Frontend Application Logic

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
  }

  // --- State ---
  let selectedFile = null;
  let verificationData = null;
  let currentViewMode = 'side-by-side'; // 'side-by-side' | 'original' | 'ela'

  // --- DOM References ---
  const apiStatusPill = document.getElementById('api-status-pill');
  const apiStatusText = document.getElementById('api-status-text');

  const dropzone = document.getElementById('dropzone');
  const dropzonePrompt = document.getElementById('dropzone-prompt');
  const fileInput = document.getElementById('file-input');
  const filePreviewCard = document.getElementById('file-preview-card');
  const previewThumbnail = document.getElementById('preview-thumbnail');
  const previewFilename = document.getElementById('preview-filename');
  const previewFilesize = document.getElementById('preview-filesize');
  const btnClearFile = document.getElementById('btn-clear-file');

  const btnVerify = document.getElementById('btn-verify');
  const btnIconContainer = document.getElementById('btn-icon-container');
  const btnLabel = document.getElementById('btn-label');
  const processingBanner = document.getElementById('processing-banner');
  const processingStageText = document.getElementById('processing-stage-text');

  const resultsSection = document.getElementById('results-section');
  const resultTimestamp = document.getElementById('result-timestamp');

  // Forensic View Controls
  const tabSideBySide = document.getElementById('tab-side-by-side');
  const tabOriginal = document.getElementById('tab-original');
  const tabEla = document.getElementById('tab-ela');
  const dualViewGrid = document.getElementById('dual-view-grid');
  const singleViewContainer = document.getElementById('single-view-container');
  const viewOriginalImg = document.getElementById('view-original-img');
  const viewElaImg = document.getElementById('view-ela-img');
  const viewSingleImg = document.getElementById('view-single-img');
  const singleViewBadge = document.getElementById('single-view-badge');

  // Forensic Telemetry
  const metricMeanError = document.getElementById('metric-mean-error');
  const metricMaxError = document.getElementById('metric-max-error');
  const metricAnomalousBlocks = document.getElementById('metric-anomalous-blocks');
  const metricAnomalyRatio = document.getElementById('metric-anomaly-ratio');
  const forensicSummaryText = document.getElementById('forensic-summary-text');

  // Verification Report Controls
  const auditIdBadge = document.getElementById('audit-id-badge');
  const verdictBanner = document.getElementById('verdict-banner');
  const verdictIconContainer = document.getElementById('verdict-icon-container');
  const verdictIcon = document.getElementById('verdict-icon');
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictSummary = document.getElementById('verdict-summary');

  const gaugeLevelBadge = document.getElementById('gauge-level-badge');
  const gaugeScoreValue = document.getElementById('gauge-score-value');
  const gaugeBar = document.getElementById('gauge-bar');

  // Extracted Data Controls
  const ocrConfidenceBadge = document.getElementById('ocr-confidence-badge');
  const extractedName = document.getElementById('extracted-name');
  const extractedId = document.getElementById('extracted-id');
  const extractedMarks = document.getElementById('extracted-marks');
  const extractedCourse = document.getElementById('extracted-course');

  // Registry Match Controls
  const registryMatchPill = document.getElementById('registry-match-pill');
  const registryMatchedContent = document.getElementById('registry-matched-content');
  const registryNotFoundContent = document.getElementById('registry-not-found-content');
  const regOfficialName = document.getElementById('reg-official-name');
  const regOfficialId = document.getElementById('reg-official-id');
  const regOfficialMarks = document.getElementById('reg-official-marks');
  const regOfficialYear = document.getElementById('reg-official-year');

  // Discrepancy & Hash Controls
  const discrepanciesBox = document.getElementById('discrepancies-box');
  const discrepanciesList = document.getElementById('discrepancies-list');
  const docHashText = document.getElementById('doc-hash-text');
  const btnCopyHash = document.getElementById('btn-copy-hash');

  // Audit Table & Modals
  const auditTableBody = document.getElementById('audit-table-body');
  const btnRefreshAudit = document.getElementById('btn-refresh-audit');
  const refreshIcon = document.getElementById('refresh-icon');

  const btnViewRegistry = document.getElementById('btn-view-registry');
  const registryModal = document.getElementById('registry-modal');
  const btnCloseRegistryModal = document.getElementById('btn-close-registry-modal');
  const registryTableBody = document.getElementById('registry-table-body');

  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');
  const btnCloseLightbox = document.getElementById('btn-close-lightbox');

  const toast = document.getElementById('toast');

  // --- Initial System Health Check ---
  checkSystemHealth();
  fetchAuditLogs();

  async function checkSystemHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        apiStatusPill.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium';
        apiStatusText.textContent = 'API Connected (FastAPI)';
      } else {
        throw new Error('Health check non-200');
      }
    } catch (e) {
      apiStatusPill.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium';
      apiStatusText.textContent = 'Connecting to Engine...';
    }
  }

  // --- Drag & Drop Handlers ---
  dropzone.addEventListener('click', (e) => {
    // Prevent triggering if clicked on clear button
    if (e.target.closest('#btn-clear-file')) return;
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dropzone-active');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dropzone-active');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files[0]) {
      handleFileSelected(dt.files[0]);
    }
  });

  btnClearFile.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  function clearSelectedFile() {
    selectedFile = null;
    fileInput.value = '';
    filePreviewCard.classList.add('hidden');
    dropzonePrompt.classList.remove('hidden');
    btnVerify.disabled = true;
  }

  function handleFileSelected(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Please select a valid image file (JPEG, PNG, WebP).', 'error');
      return;
    }

    selectedFile = file;
    previewFilename.textContent = file.name;
    previewFilesize.textContent = formatBytes(file.size);

    const reader = new FileReader();
    reader.onload = (e) => {
      previewThumbnail.src = e.target.result;
      dropzonePrompt.classList.add('hidden');
      filePreviewCard.classList.remove('hidden');
      filePreviewCard.classList.add('flex');
      btnVerify.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  // --- Quick Test Samples Loading ---
  document.querySelectorAll('.btn-sample').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const sampleName = btn.getAttribute('data-sample');
      await loadSampleDocument(sampleName);
    });
  });

  async function loadSampleDocument(sampleFilename) {
    try {
      showToast(`Loading test sample: ${sampleFilename}...`, 'info');
      const res = await fetch(`/samples/${sampleFilename}`);
      if (!res.ok) throw new Error('Sample not found');

      const blob = await res.blob();
      const file = new File([blob], sampleFilename, { type: 'image/jpeg' });
      handleFileSelected(file);
      showToast(`Loaded ${sampleFilename}. Ready to verify!`, 'success');
    } catch (err) {
      showToast(`Could not load test sample. Make sure server is running.`, 'error');
    }
  }

  function setButtonLoading(isLoading) {
    if (isLoading) {
      btnVerify.disabled = true;
      btnLabel.textContent = 'Processing Forensics & OCR...';
      if (btnIconContainer) {
        btnIconContainer.innerHTML = `<svg class="w-4 h-4 animate-spin text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
      }
      processingBanner.classList.remove('hidden');
    } else {
      btnVerify.disabled = !selectedFile;
      btnLabel.textContent = 'Run Verification & Forensic Analysis';
      if (btnIconContainer) {
        btnIconContainer.innerHTML = `<i data-lucide="scan" class="w-4 h-4"></i>`;
        if (window.lucide) lucide.createIcons();
      }
      processingBanner.classList.add('hidden');
    }
  }

  // --- Run Verification & Forensic Analysis ---
  btnVerify.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Set UI Loading State
    setButtonLoading(true);

    // Stage updates simulation
    const stageInterval = simulateProgressStages();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/verify', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Verification failed' }));
        throw new Error(errData.detail || `Server returned ${response.status}`);
      }

      const result = await response.json();
      verificationData = result;

      // Render Verification & Forensic Results
      renderVerificationResults(result);

      // Smooth scroll to results
      resultsSection.classList.remove('hidden');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Refresh Audit Trail Table
      fetchAuditLogs();

      showToast('Forensic & Registry analysis complete!', 'success');

    } catch (err) {
      showToast(`Verification error: ${err.message}`, 'error');
    } finally {
      clearInterval(stageInterval);
      setButtonLoading(false);
    }
  });

  function simulateProgressStages() {
    const stages = [
      '1. Cryptographic Document SHA-256 Hashing...',
      '2. OpenCV Error Level Analysis (ELA) & DCT block variance...',
      '3. EasyOCR text extraction and deep regex parsing...',
      '4. Cross-verifying against institutional SHA-256 registry...',
    ];
    let index = 0;
    processingStageText.textContent = stages[0];
    return setInterval(() => {
      index = (index + 1) % stages.length;
      processingStageText.textContent = stages[index];
    }, 700);
  }

  // --- Render Results ---
  function renderVerificationResults(data) {
    const v = data.verification_result;
    const f = data.forensic_analysis;
    const o = data.extracted_data;
    const r = data.registry_comparison;
    const meta = data.audit_meta;

    resultTimestamp.textContent = `Analyzed: ${new Date(meta.timestamp).toLocaleTimeString()}`;

    // 1. Render Images
    // Original Document preview
    if (selectedFile) {
      const reader = new FileReader();
      reader.onload = (e) => {
        viewOriginalImg.src = e.target.result;
        if (currentViewMode === 'original') viewSingleImg.src = e.target.result;
      };
      reader.readAsDataURL(selectedFile);
    }

    // ELA Tamper Heatmap preview
    viewElaImg.src = f.ela_image_base64;
    if (currentViewMode === 'ela') viewSingleImg.src = f.ela_image_base64;

    // 2. Forensic Telemetry
    metricMeanError.textContent = f.mean_error.toFixed(2);
    metricMaxError.textContent = f.max_error.toFixed(1);
    metricAnomalousBlocks.textContent = f.anomalous_blocks !== undefined ? f.anomalous_blocks : '0';
    metricAnomalyRatio.textContent = (f.anomaly_ratio * 100).toFixed(1) + '%';
    forensicSummaryText.textContent = f.analysis_summary;

    // 3. Verdict Banner
    auditIdBadge.textContent = `Audit #${meta.audit_id}`;
    verdictSummary.textContent = v.summary;

    // Verdict Styling & Color Mapping
    if (v.verdict === 'VERIFIED') {
      verdictBanner.className = 'p-4 rounded-xl border flex items-center space-x-3.5 bg-emerald-950/40 border-emerald-500/40 text-emerald-300';
      verdictIconContainer.className = 'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 bg-emerald-500/20 text-emerald-400 shadow-lg shadow-emerald-500/10';
      verdictIcon.setAttribute('data-lucide', 'shield-check');
      verdictBadge.className = 'text-xs font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
      verdictBadge.textContent = 'VERIFIED AUTHENTIC';
    } else if (v.verdict === 'TAMPERED_SUSPECT') {
      verdictBanner.className = 'p-4 rounded-xl border flex items-center space-x-3.5 bg-rose-950/40 border-rose-500/40 text-rose-300';
      verdictIconContainer.className = 'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 bg-rose-500/20 text-rose-400 shadow-lg shadow-rose-500/10';
      verdictIcon.setAttribute('data-lucide', 'shield-alert');
      verdictBadge.className = 'text-xs font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30';
      verdictBadge.textContent = 'TAMPERING DETECTED';
    } else if (v.verdict === 'MISMATCH') {
      verdictBanner.className = 'p-4 rounded-xl border flex items-center space-x-3.5 bg-amber-950/40 border-amber-500/40 text-amber-300';
      verdictIconContainer.className = 'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 bg-amber-500/20 text-amber-400 shadow-lg shadow-amber-500/10';
      verdictIcon.setAttribute('data-lucide', 'alert-triangle');
      verdictBadge.className = 'text-xs font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30';
      verdictBadge.textContent = 'RECORD MISMATCH';
    } else {
      // NOT_FOUND
      verdictBanner.className = 'p-4 rounded-xl border flex items-center space-x-3.5 bg-slate-900 border-slate-700 text-slate-300';
      verdictIconContainer.className = 'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 bg-slate-800 text-slate-400 shadow-lg';
      verdictIcon.setAttribute('data-lucide', 'help-circle');
      verdictBadge.className = 'text-xs font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700';
      verdictBadge.textContent = 'UNREGISTERED RECORD';
    }

    // 4. Tamper Risk Gauge
    const score = f.tamper_risk_score;
    gaugeScoreValue.textContent = `${score}%`;
    gaugeLevelBadge.textContent = f.tamper_level;

    if (f.tamper_level === 'LOW') {
      gaugeLevelBadge.className = 'font-bold text-[11px] px-2 py-0.5 rounded uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
      gaugeBar.className = 'risk-meter-fill h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400';
    } else if (f.tamper_level === 'MODERATE') {
      gaugeLevelBadge.className = 'font-bold text-[11px] px-2 py-0.5 rounded uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30';
      gaugeBar.className = 'risk-meter-fill h-full rounded-full bg-gradient-to-r from-amber-500 to-yellow-400';
    } else {
      gaugeLevelBadge.className = 'font-bold text-[11px] px-2 py-0.5 rounded uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30';
      gaugeBar.className = 'risk-meter-fill h-full rounded-full bg-gradient-to-r from-rose-500 to-red-600';
    }

    // Trigger bar animation
    setTimeout(() => {
      gaugeBar.style.width = `${Math.min(100, Math.max(4, score))}%`;
    }, 100);

    // 5. Extracted Data
    ocrConfidenceBadge.textContent = `Conf: ${Math.round(o.ocr_confidence * 100)}%`;
    extractedName.textContent = o.detected_name || 'Not detected';
    extractedId.textContent = o.detected_id || 'Not detected';
    extractedMarks.textContent = o.detected_marks || 'Not detected';
    extractedCourse.textContent = o.detected_course || 'Not specified';

    // 6. Registry Comparison
    if (r.matched && r.official_record) {
      registryMatchPill.className = 'text-[10px] font-black uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
      registryMatchPill.textContent = 'REGISTRY MATCH';
      registryMatchedContent.classList.remove('hidden');
      registryNotFoundContent.classList.add('hidden');

      regOfficialName.textContent = r.official_record.student_name;
      regOfficialId.textContent = r.official_record.student_id;
      regOfficialMarks.textContent = r.official_record.marks_or_grade;
      regOfficialYear.textContent = `${r.official_record.issue_year} (${r.official_record.institution})`;
    } else {
      registryMatchPill.className = 'text-[10px] font-black uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700';
      registryMatchPill.textContent = 'NO MATCH FOUND';
      registryMatchedContent.classList.add('hidden');
      registryNotFoundContent.classList.remove('hidden');
    }

    // 7. Discrepancies
    if (r.discrepancies && r.discrepancies.length > 0) {
      discrepanciesList.innerHTML = '';
      r.discrepancies.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        discrepanciesList.appendChild(li);
      });
      discrepanciesBox.classList.remove('hidden');
    } else {
      discrepanciesBox.classList.add('hidden');
    }

    // 8. Document Hash
    docHashText.textContent = meta.document_hash;

    // Refresh icons
    if (window.lucide) lucide.createIcons();
  }

  // --- View Mode Tabs Switcher ---
  tabSideBySide.addEventListener('click', () => setViewMode('side-by-side'));
  tabOriginal.addEventListener('click', () => setViewMode('original'));
  tabEla.addEventListener('click', () => setViewMode('ela'));

  function setViewMode(mode) {
    currentViewMode = mode;
    [tabSideBySide, tabOriginal, tabEla].forEach(t => {
      t.className = 'px-2.5 py-1 rounded-md hover:text-white transition';
    });

    if (mode === 'side-by-side') {
      tabSideBySide.className = 'px-2.5 py-1 rounded-md bg-brand-600 text-white shadow transition';
      dualViewGrid.classList.remove('hidden');
      singleViewContainer.classList.add('hidden');
    } else if (mode === 'original') {
      tabOriginal.className = 'px-2.5 py-1 rounded-md bg-brand-600 text-white shadow transition';
      dualViewGrid.classList.add('hidden');
      singleViewContainer.classList.remove('hidden');
      viewSingleImg.src = viewOriginalImg.src;
      singleViewBadge.textContent = 'Original Document View';
    } else if (mode === 'ela') {
      tabEla.className = 'px-2.5 py-1 rounded-md bg-brand-600 text-white shadow transition';
      dualViewGrid.classList.add('hidden');
      singleViewContainer.classList.remove('hidden');
      viewSingleImg.src = viewElaImg.src;
      singleViewBadge.textContent = 'ELA Tamper Heatmap (Error Level Analysis)';
    }
  }

  // --- Audit Trail Fetcher ---
  btnRefreshAudit.addEventListener('click', () => {
    refreshIcon.classList.add('animate-spin');
    fetchAuditLogs().finally(() => {
      setTimeout(() => refreshIcon.classList.remove('animate-spin'), 400);
    });
  });

  async function fetchAuditLogs() {
    try {
      const res = await fetch('/api/audit-logs');
      if (!res.ok) throw new Error('Failed to fetch audit logs');
      const logs = await res.json();
      renderAuditTable(logs);
    } catch (err) {
      auditTableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-4 text-center text-rose-400">Failed to load audit trail.</td></tr>`;
    }
  }

  function renderAuditTable(logs) {
    if (!logs || logs.length === 0) {
      auditTableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-8 text-center text-slate-400">No verification audit logs recorded yet.</td></tr>`;
      return;
    }

    auditTableBody.innerHTML = logs.map(log => {
      const dateStr = log.timestamp ? new Date(log.timestamp).toLocaleString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
      }) : '--';

      const shortHash = log.document_hash ? `${log.document_hash.substring(0, 8)}...${log.document_hash.substring(log.document_hash.length - 6)}` : '--';

      let verdictPill = '';
      if (log.match_status === 'VERIFIED') {
        verdictPill = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">VERIFIED</span>`;
      } else if (log.match_status === 'TAMPERED_SUSPECT') {
        verdictPill = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">TAMPERED</span>`;
      } else if (log.match_status === 'MISMATCH') {
        verdictPill = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">MISMATCH</span>`;
      } else {
        verdictPill = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">NOT FOUND</span>`;
      }

      const credentialStr = log.detected_name ? `${log.detected_name} <span class="text-slate-400 font-mono">(${log.detected_id || 'No ID'})</span>` : (log.detected_id || 'Unknown');

      return `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="px-4 py-3 font-mono text-[11px] text-slate-400">
            <span class="text-white font-bold">#${log.id}</span><br>
            <span class="text-[10px]">${dateStr}</span>
          </td>
          <td class="px-4 py-3 text-slate-200 font-medium truncate max-w-[140px]" title="${log.filename}">
            ${log.filename}
          </td>
          <td class="px-4 py-3 font-mono text-[11px] text-slate-400 cursor-pointer hover:text-white transition" onclick="copyToClipboard('${log.document_hash}')" title="Click to copy full SHA-256">
            ${shortHash}
          </td>
          <td class="px-4 py-3 text-slate-300 truncate max-w-[180px]">
            ${credentialStr}
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center space-x-1.5">
              <span class="font-mono font-bold ${log.tamper_risk_score > 50 ? 'text-rose-400' : (log.tamper_risk_score > 25 ? 'text-amber-400' : 'text-emerald-400')}">
                ${log.tamper_risk_score.toFixed(1)}%
              </span>
              <span class="text-[10px] text-slate-400 uppercase">(${log.tamper_level})</span>
            </div>
          </td>
          <td class="px-4 py-3 text-right">
            ${verdictPill}
          </td>
        </tr>
      `;
    }).join('');
  }

  // --- Registry Records Modal ---
  btnViewRegistry.addEventListener('click', async () => {
    try {
      registryModal.classList.remove('hidden');
      registryModal.classList.add('flex');
      registryTableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-6 text-center text-slate-400">Loading registry...</td></tr>`;

      const res = await fetch('/api/records');
      if (!res.ok) throw new Error('Could not fetch records');
      const records = await res.json();

      registryTableBody.innerHTML = records.map(r => `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="px-4 py-3 font-semibold text-white">${r.student_name}</td>
          <td class="px-4 py-3 font-mono text-brand-300 font-bold">${r.student_id}</td>
          <td class="px-4 py-3 font-mono text-[11px] text-slate-400 cursor-pointer hover:text-white" onclick="copyToClipboard('${r.student_id_hash}')" title="Click to copy SHA-256 hash">
            ${r.student_id_hash.substring(0, 12)}...
          </td>
          <td class="px-4 py-3 text-slate-300">${r.course}</td>
          <td class="px-4 py-3 font-semibold text-emerald-400">${r.marks_or_grade}</td>
          <td class="px-4 py-3 text-slate-400 font-mono">${r.issue_year}</td>
        </tr>
      `).join('');
    } catch (e) {
      registryTableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-4 text-center text-rose-400">Failed to load records.</td></tr>`;
    }
  });

  btnCloseRegistryModal.addEventListener('click', () => {
    registryModal.classList.add('hidden');
    registryModal.classList.remove('flex');
  });

  registryModal.addEventListener('click', (e) => {
    if (e.target === registryModal) {
      registryModal.classList.add('hidden');
      registryModal.classList.remove('flex');
    }
  });

  // --- Lightbox Viewer ---
  window.openLightbox = function(which) {
    if (which === 'original') {
      lightboxImg.src = viewOriginalImg.src;
      lightboxCaption.textContent = 'Original Input Document';
    } else if (which === 'ela') {
      lightboxImg.src = viewElaImg.src;
      lightboxCaption.textContent = 'Error Level Analysis (ELA) Forensic Heatmap (90% Quality Delta)';
    } else {
      lightboxImg.src = viewSingleImg.src;
      lightboxCaption.textContent = singleViewBadge.textContent;
    }
    lightboxModal.classList.remove('hidden');
    lightboxModal.classList.add('flex');
  };

  btnCloseLightbox.addEventListener('click', () => {
    lightboxModal.classList.add('hidden');
    lightboxModal.classList.remove('flex');
  });

  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) {
      lightboxModal.classList.add('hidden');
      lightboxModal.classList.remove('flex');
    }
  });

  // --- Utilities ---
  btnCopyHash.addEventListener('click', () => {
    if (docHashText.textContent && docHashText.textContent !== '--') {
      copyToClipboard(docHashText.textContent);
    }
  });

  window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('SHA-256 Hash copied to clipboard!', 'info');
    }).catch(() => {
      showToast('Failed to copy to clipboard', 'error');
    });
  };

  function showToast(message, type = 'info') {
    toast.textContent = message;
    if (type === 'success') {
      toast.className = 'fixed bottom-6 right-6 z-50 transform opacity-100 transition-all duration-300 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 border bg-emerald-950 border-emerald-500/50 text-emerald-200';
    } else if (type === 'error') {
      toast.className = 'fixed bottom-6 right-6 z-50 transform opacity-100 transition-all duration-300 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 border bg-rose-950 border-rose-500/50 text-rose-200';
    } else {
      toast.className = 'fixed bottom-6 right-6 z-50 transform opacity-100 transition-all duration-300 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 border bg-slate-900 border-slate-700 text-slate-200';
    }

    setTimeout(() => {
      toast.className = 'fixed bottom-6 right-6 z-50 transform translate-y-20 opacity-0 transition-all duration-300 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 border';
    }, 3200);
  }

  function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }
});
