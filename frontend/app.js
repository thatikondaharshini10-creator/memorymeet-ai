// MemoryMeet — Complete Frontend Client Application
// Connects to FastAPI backend, Gemini AI reasoning, and Hindsight Cloud memory layer

const API_BASE = window.location.origin.includes('http') && !window.location.origin.startsWith('file:')
  ? window.location.origin
  : 'http://localhost:8000';

// API Endpoints
const ENDPOINTS = {
  HEALTH: `${API_BASE}/api/health`,
  PROCESS_TRANSCRIPT: `${API_BASE}/api/meetings/process-transcript`,
  UPLOAD_RECORDING: `${API_BASE}/api/meetings/upload-recording`,
  PREPARE: `${API_BASE}/api/meetings/prepare`,
  MEETINGS: `${API_BASE}/api/meetings`,
  BANK_INFO: `${API_BASE}/api/memories/bank`
};

// Demo Sample Transcripts
const SAMPLES = {
  SAMPLE_1: {
    title: "Q4 Product Architecture Alignment",
    transcript: `Sarah: The iOS and Android mobile launch is locked in for November 15th. We cannot push this date because marketing has booked campaigns.
Alice: Agreed. For all PR reviews, I strongly prefer async GitHub reviews instead of synchronous meetings due to timezone differences.
David: Understood. I will migrate our backend database from MySQL to PostgreSQL before October 25th to handle the new indexing.
Sarah: Note that we require dark mode support enabled by default on mobile.
David: I'll have the schema migration scripts ready by next Friday for Alice to review.`
  },
  SAMPLE_2: {
    title: "Security Review & Budget Allocation",
    transcript: `Marcus: All public API endpoints must mandate OAuth2 Bearer tokens with strict rate limiting of 100 requests per minute.
Elena: I've allocated $15,000 for cloud infrastructure scaling for Q4. Any expenditure exceeding this cap requires executive VP sign-off.
Marcus: Marcus prefers daily 5-minute async Slack updates instead of morning video calls.
Elena: Elena will audit all cloud provider invoices on the first Monday of each month.`
  }
};

// DOM Elements
const connectionPill = document.getElementById('connection-status-pill');
const connectionText = document.getElementById('connection-status-text');
const hindsightPill = document.getElementById('hindsight-bank-pill');
const hindsightText = document.getElementById('hindsight-bank-text');

// Navigation Tabs
const navTabs = document.querySelectorAll('.nav-tab');
const tabPanels = {
  'tab-ingest': document.getElementById('panel-ingest'),
  'tab-prepare': document.getElementById('panel-prepare'),
  'tab-history': document.getElementById('panel-history')
};

// Sub Tabs (Ingest View)
const subtabTranscript = document.getElementById('subtab-transcript');
const subtabUpload = document.getElementById('subtab-upload');
const formTranscriptView = document.getElementById('form-transcript-view');
const formUploadView = document.getElementById('form-upload-view');

// Ingest Controls
const inputTitle = document.getElementById('input-transcript-title');
const inputTranscript = document.getElementById('input-transcript-text');
const btnProcessTranscript = document.getElementById('btn-process-transcript');
const ingestSpinner = document.getElementById('ingest-spinner');
const ingestStatus = document.getElementById('ingest-status-msg');

const btnSample1 = document.getElementById('btn-sample-1');
const btnSample2 = document.getElementById('btn-sample-2');

// Audio Upload Controls
const fileDropArea = document.getElementById('file-drop-area');
const inputRecordingFile = document.getElementById('input-recording-file');
const selectedFileDisplay = document.getElementById('selected-file-display');
const inputAudioTitle = document.getElementById('input-audio-title');
const btnUploadRecording = document.getElementById('btn-upload-recording');
const uploadSpinner = document.getElementById('upload-spinner');
const uploadStatus = document.getElementById('upload-status-msg');

// Ingest Results Elements
const ingestResultsCard = document.getElementById('ingest-results-card');
const resultTitle = document.getElementById('result-meeting-title');
const resultRetainedCount = document.getElementById('result-retained-count');
const resultSummary = document.getElementById('result-summary-text');
const resultDecisions = document.getElementById('result-decisions-list');
const resultPreferences = document.getElementById('result-preferences-list');
const resultActions = document.getElementById('result-actions-list');
const resultStatements = document.getElementById('result-statements-list');

// Prep Controls
const inputPrepAgenda = document.getElementById('input-prep-agenda');
const btnGeneratePrep = document.getElementById('btn-generate-prep');
const prepSpinner = document.getElementById('prep-spinner');
const prepStatus = document.getElementById('prep-status-msg');

const btnPrepScen1 = document.getElementById('btn-prep-scenario-1');
const btnPrepScen2 = document.getElementById('btn-prep-scenario-2');
const btnPrepScen3 = document.getElementById('btn-prep-scenario-3');

// Prep Results Elements
const prepResultsCard = document.getElementById('prep-results-card');
const prepAgendaDisplay = document.getElementById('prep-agenda-display');
const prepRecalledCount = document.getElementById('prep-recalled-count');
const prepStrategicRec = document.getElementById('prep-strategic-rec');
const prepExecSummary = document.getElementById('prep-exec-summary');
const prepTalkingPoints = document.getElementById('prep-talking-points');
const prepParticipantInsights = document.getElementById('prep-participant-insights');
const prepRisksList = document.getElementById('prep-risks-list');
const prepRecalledItems = document.getElementById('prep-recalled-items');

// History
const btnRefreshHistory = document.getElementById('btn-refresh-history');
const historyTableBody = document.getElementById('history-table-body');

// -------------------------------------------------------------
// TAB SWITCHING
// -------------------------------------------------------------
navTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    navTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    Object.keys(tabPanels).forEach(key => {
      if (key === target) {
        tabPanels[key].classList.remove('hidden');
      } else {
        tabPanels[key].classList.add('hidden');
      }
    });

    if (target === 'tab-history') {
      loadHistory();
    }
  });
});

subtabTranscript.addEventListener('click', () => {
  subtabTranscript.classList.add('active');
  subtabUpload.classList.remove('active');
  formTranscriptView.classList.remove('hidden');
  formUploadView.classList.add('hidden');
});

subtabUpload.addEventListener('click', () => {
  subtabUpload.classList.add('active');
  subtabTranscript.classList.remove('active');
  formUploadView.classList.remove('hidden');
  formTranscriptView.classList.add('hidden');
});

// -------------------------------------------------------------
// SAMPLE QUICK-FILLS
// -------------------------------------------------------------
btnSample1.addEventListener('click', () => {
  inputTitle.value = SAMPLES.SAMPLE_1.title;
  inputTranscript.value = SAMPLES.SAMPLE_1.transcript;
});

btnSample2.addEventListener('click', () => {
  inputTitle.value = SAMPLES.SAMPLE_2.title;
  inputTranscript.value = SAMPLES.SAMPLE_2.transcript;
});

btnPrepScen1.addEventListener('click', () => {
  inputPrepAgenda.value = "Reviewing mobile launch timeline and architecture blockers with Sarah and David.";
});

btnPrepScen2.addEventListener('click', () => {
  inputPrepAgenda.value = "Sprint planning, PR review scheduling, and Postgres database migration with Alice and David.";
});

btnPrepScen3.addEventListener('click', () => {
  inputPrepAgenda.value = "Security architecture review, API rate limiting, and Q4 infrastructure budget with Marcus and Elena.";
});

// -------------------------------------------------------------
// HEALTH & BANK STATUS
// -------------------------------------------------------------
async function checkHealth() {
  try {
    const res = await fetch(ENDPOINTS.HEALTH);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    connectionPill.className = 'status-pill status-healthy';
    connectionText.textContent = 'Backend Online';

    // Also check Hindsight Bank Info
    fetchBankInfo();
  } catch (err) {
    connectionPill.className = 'status-pill status-error';
    connectionText.textContent = 'Backend Offline';
  }
}

async function fetchBankInfo() {
  try {
    const res = await fetch(ENDPOINTS.BANK_INFO);
    if (res.ok) {
      const data = await res.json();
      if (data.bank && data.bank.status === 'ready') {
        hindsightText.textContent = `Hindsight: ${data.bank.bank_id} (${data.bank.fact_count} facts)`;
      }
    }
  } catch (e) {
    // Ignore minor network blip
  }
}

// -------------------------------------------------------------
// PROCESS TRANSCRIPT (INGESTION)
// -------------------------------------------------------------
btnProcessTranscript.addEventListener('click', async () => {
  const title = inputTitle.value.trim();
  const transcript = inputTranscript.value.trim();

  if (!transcript) {
    alert("Please enter or paste a meeting transcript first.");
    return;
  }

  btnProcessTranscript.disabled = true;
  ingestSpinner.classList.remove('hidden');
  ingestStatus.textContent = "Gemini extracting memories & retaining to Hindsight Cloud...";

  try {
    const response = await fetch(ENDPOINTS.PROCESS_TRANSCRIPT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, transcript })
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.detail || result.error || "Failed to process transcript");
    }

    renderIngestResults(result.data);
    ingestStatus.textContent = "Memory retained successfully!";
    setTimeout(() => { ingestStatus.textContent = ""; }, 4000);
    fetchBankInfo();
  } catch (error) {
    alert(`Error processing meeting: ${error.message}`);
    ingestStatus.textContent = "Failed to process meeting.";
  } finally {
    btnProcessTranscript.disabled = false;
    ingestSpinner.classList.add('hidden');
  }
});

function renderIngestResults(data) {
  ingestResultsCard.classList.remove('hidden');
  resultTitle.textContent = data.title;
  resultRetainedCount.textContent = `${data.retained_count || 0} facts`;
  resultSummary.textContent = data.summary || "No summary generated.";

  const extracted = data.extracted_data || {};

  // Decisions
  resultDecisions.innerHTML = '';
  (extracted.decisions || []).forEach(d => {
    const li = document.createElement('li');
    li.textContent = d;
    resultDecisions.appendChild(li);
  });
  if (!extracted.decisions || extracted.decisions.length === 0) {
    resultDecisions.innerHTML = '<li>No explicit decisions detected.</li>';
  }

  // Preferences
  resultPreferences.innerHTML = '';
  (extracted.preferences || []).forEach(p => {
    const li = document.createElement('li');
    li.textContent = p;
    resultPreferences.appendChild(li);
  });
  if (!extracted.preferences || extracted.preferences.length === 0) {
    resultPreferences.innerHTML = '<li>No personal preferences detected.</li>';
  }

  // Action Items
  resultActions.innerHTML = '';
  (extracted.action_items || []).forEach(item => {
    const card = document.createElement('div');
    card.className = 'action-item-card';
    card.innerHTML = `
      <span class="action-task">${item.task}</span>
      <div class="action-meta">
        ${item.owner ? `<span class="action-owner">${item.owner}</span>` : ''}
        ${item.deadline ? `<span>Due: ${item.deadline}</span>` : ''}
      </div>
    `;
    resultActions.appendChild(card);
  });
  if (!extracted.action_items || extracted.action_items.length === 0) {
    resultActions.innerHTML = '<div class="action-item-card"><span>No action items noted.</span></div>';
  }

  // Retain statements (stored in Hindsight)
  resultStatements.innerHTML = '';
  (extracted.retain_statements || []).forEach(stmt => {
    const li = document.createElement('li');
    li.textContent = stmt;
    resultStatements.appendChild(li);
  });

  ingestResultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// -------------------------------------------------------------
// AUDIO FILE UPLOAD
// -------------------------------------------------------------
fileDropArea.addEventListener('click', () => inputRecordingFile.click());

fileDropArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  fileDropArea.classList.add('dragover');
});

fileDropArea.addEventListener('dragleave', () => fileDropArea.classList.remove('dragover'));

fileDropArea.addEventListener('drop', (e) => {
  e.preventDefault();
  fileDropArea.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) {
    inputRecordingFile.files = e.dataTransfer.files;
    handleFileSelected();
  }
});

inputRecordingFile.addEventListener('change', handleFileSelected);

function handleFileSelected() {
  const file = inputRecordingFile.files[0];
  if (file) {
    selectedFileDisplay.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
    btnUploadRecording.disabled = false;
  }
}

btnUploadRecording.addEventListener('click', async () => {
  const file = inputRecordingFile.files[0];
  if (!file) return;

  const title = inputAudioTitle.value.trim() || file.name;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);

  btnUploadRecording.disabled = true;
  uploadSpinner.classList.remove('hidden');
  uploadStatus.textContent = "Transcribing with Gemini multimodal & extracting memories...";

  try {
    const response = await fetch(ENDPOINTS.UPLOAD_RECORDING, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.detail || result.error || "Failed to transcribe recording");
    }

    renderIngestResults(result.data);
    uploadStatus.textContent = "Recording transcribed and retained!";
    setTimeout(() => { uploadStatus.textContent = ""; }, 4000);
    fetchBankInfo();
  } catch (error) {
    alert(`Error transcribing file: ${error.message}`);
    uploadStatus.textContent = "Upload failed.";
  } finally {
    btnUploadRecording.disabled = false;
    uploadSpinner.classList.add('hidden');
  }
});

// -------------------------------------------------------------
// MEETING PREPARATION (RECALL + BRIEF)
// -------------------------------------------------------------
btnGeneratePrep.addEventListener('click', async () => {
  const agenda = inputPrepAgenda.value.trim();
  if (!agenda) {
    alert("Please enter an upcoming meeting agenda or topic.");
    return;
  }

  btnGeneratePrep.disabled = true;
  prepSpinner.classList.remove('hidden');
  prepStatus.textContent = "Recalling historical memories from Hindsight & synthesizing brief...";

  try {
    const response = await fetch(ENDPOINTS.PREPARE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agenda })
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.detail || result.error || "Failed to generate meeting brief");
    }

    renderPrepResults(result.data);
    prepStatus.textContent = "Brief prepared!";
    setTimeout(() => { prepStatus.textContent = ""; }, 3000);
  } catch (error) {
    alert(`Error generating brief: ${error.message}`);
    prepStatus.textContent = "Failed to generate brief.";
  } finally {
    btnGeneratePrep.disabled = false;
    prepSpinner.classList.add('hidden');
  }
});

function renderPrepResults(data) {
  prepResultsCard.classList.remove('hidden');
  prepAgendaDisplay.textContent = `Agenda: ${data.agenda}`;
  prepRecalledCount.textContent = `${data.recalled_memories_count || 0} recalled`;

  const brief = data.brief || {};

  prepStrategicRec.textContent = brief.strategic_recommendation || "Maintain proactive alignment and clarify pending ownership.";
  prepExecSummary.textContent = brief.executive_summary || "No executive summary available.";

  // Talking points
  prepTalkingPoints.innerHTML = '';
  (brief.recommended_talking_points || []).forEach(pt => {
    const li = document.createElement('li');
    li.textContent = pt;
    prepTalkingPoints.appendChild(li);
  });

  // Participant insights
  prepParticipantInsights.innerHTML = '';
  (brief.participant_insights || []).forEach(pi => {
    const li = document.createElement('li');
    li.textContent = pi;
    prepParticipantInsights.appendChild(li);
  });

  // Risks
  prepRisksList.innerHTML = '';
  (brief.risks_and_unresolved_questions || []).forEach(risk => {
    const li = document.createElement('li');
    li.textContent = risk;
    prepRisksList.appendChild(li);
  });

  // Recalled Hindsight Memories List
  prepRecalledItems.innerHTML = '';
  const memories = data.recalled_memories || [];
  if (memories.length === 0) {
    prepRecalledItems.innerHTML = '<p class="memories-sub">No previous memories matched this agenda closely.</p>';
  } else {
    memories.forEach(m => {
      const card = document.createElement('div');
      card.className = 'recalled-item-card';

      // Hindsight returns memory objects with fact/content/text or string
      const text = m.content || m.text || m.fact || (typeof m === 'string' ? m : JSON.stringify(m));
      const type = m.type || 'fact';
      const score = m.score ? `Score: ${(m.score * 100).toFixed(0)}%` : '';

      card.innerHTML = `
        <span class="recalled-fact-text">${text}</span>
        <div class="recalled-fact-meta">
          <span class="recalled-type-badge">${type}</span>
          <span>${score}</span>
        </div>
      `;
      prepRecalledItems.appendChild(card);
    });
  }

  prepResultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// -------------------------------------------------------------
// HISTORY
// -------------------------------------------------------------
btnRefreshHistory.addEventListener('click', loadHistory);

async function loadHistory() {
  historyTableBody.innerHTML = '<tr><td colspan="5" class="table-empty">Loading meeting records...</td></tr>';
  try {
    const res = await fetch(ENDPOINTS.MEETINGS);
    if (!res.ok) throw new Error("Failed to load meetings");
    const data = await res.json();
    const meetings = data.meetings || [];

    if (meetings.length === 0) {
      historyTableBody.innerHTML = '<tr><td colspan="5" class="table-empty">No meetings processed yet. Process a meeting in Tab 1 to see records here.</td></tr>';
      return;
    }

    historyTableBody.innerHTML = '';
    meetings.forEach(m => {
      const tr = document.createElement('tr');
      const dateStr = new Date(m.created_at).toLocaleDateString() + ' ' + new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      tr.innerHTML = `
        <td><strong>#${m.id}</strong></td>
        <td>${m.title}</td>
        <td>${dateStr}</td>
        <td>${m.summary ? m.summary.substring(0, 100) + '...' : 'No summary'}</td>
        <td><span class="badge badge-success">${m.status}</span></td>
      `;
      historyTableBody.appendChild(tr);
    });
  } catch (err) {
    historyTableBody.innerHTML = `<tr><td colspan="5" class="table-empty">Failed to load meetings: ${err.message}</td></tr>`;
  }
}

// Initial Boot
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  // Pre-fill Sample 1 in the transcript input for instant zero-friction demo testing!
  inputTitle.value = SAMPLES.SAMPLE_1.title;
  inputTranscript.value = SAMPLES.SAMPLE_1.transcript;
});
