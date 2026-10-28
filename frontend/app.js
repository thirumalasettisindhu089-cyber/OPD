/**
 * SmartTriage AI - Frontend Application Logic
 * Talent AP Mega Hackathon 2026 - Problem H1
 * 
 * Zero external CDN dependencies. Pure Vanilla JavaScript.
 */

const PRESETS = {
  chest_pain: {
    patient_id: "PRESET_CARDIAC_01",
    age: 54,
    sex: "M",
    bp_systolic: 135,
    bp_diastolic: 88,
    heart_rate: 98,
    respiratory_rate: 20,
    temperature: 37.2,
    spo2: 96,
    known_conditions: "Hypertension",
    current_medications: "Amlodipine 5mg",
    chief_complaint: "gunde noppi severe ga undi, eeda thammudu cheyyi laakkuntundi, chematalu paduthunnayi"
  },
  critical_vitals: {
    patient_id: "PRESET_CRIT_SHOCK_02",
    age: 62,
    sex: "F",
    bp_systolic: 65,  // Critical hypotension (<70)
    bp_diastolic: 38,
    heart_rate: 148,  // Extreme tachycardia
    respiratory_rate: 34,
    temperature: 36.4,
    spo2: 81,         // Severe hypoxia (<85)
    known_conditions: "Type 2 Diabetes",
    current_medications: "Metformin 500mg",
    chief_complaint: "feeling unwell, very weak, unable to stand"
  },
  impossible_vitals: {
    patient_id: "PRESET_NOISY_INPUT_03",
    age: 45,
    sex: "F",
    bp_systolic: 0,    // Sensor disconnect / 0 BP
    bp_diastolic: 0,
    heart_rate: 82,
    respiratory_rate: 16,
    temperature: 96.0, // 96 C typed in Celsius box (actually Fahrenheit!)
    spo2: 104,         // SpO2 > 100% physically impossible
    known_conditions: "None",
    current_medications: "None",
    chief_complaint: "mild shivering and cold for 2 days, feeling tired"
  },
  telugu_dyspnea: {
    patient_id: "PRESET_TELUGU_RESP_04",
    age: 48,
    sex: "M",
    bp_systolic: 128,
    bp_diastolic: 84,
    heart_rate: 122,
    respiratory_rate: 32,
    temperature: 37.4,
    spo2: 88,
    known_conditions: "Asthma",
    current_medications: "Salbutamol Inhaler",
    chief_complaint: "saas aaguthondi, aayasam ekkuva undi, kallu thiruguthunnayi, inhaler pani cheyyatledu"
  },
  mild_fever: {
    patient_id: "PRESET_HINDI_MILD_05",
    age: 26,
    sex: "F",
    bp_systolic: 118,
    bp_diastolic: 78,
    heart_rate: 74,
    respiratory_rate: 16,
    temperature: 37.8,
    spo2: 99,
    known_conditions: "None",
    current_medications: "None",
    chief_complaint: "halka bukhar aur sardi hai do din se, bukhar nahi hai zyada"
  },
  pediatric_alert: {
    patient_id: "PRESET_PEDIATRIC_06",
    age: 4,            // Age < 12 -> Pediatric bypass
    sex: "M",
    bp_systolic: 85,   // Normal for child, would trigger adult hypotension rule if not bypassed
    bp_diastolic: 54,
    heart_rate: 115,   // Normal pediatric HR
    respiratory_rate: 24,
    temperature: 38.3,
    spo2: 98,
    known_conditions: "None",
    current_medications: "None",
    chief_complaint: "child has mild ear ache and crying since yesterday, eating food normally"
  },
  negation_case: {
    patient_id: "PRESET_NEGATION_07",
    age: 38,
    sex: "M",
    bp_systolic: 122,
    bp_diastolic: 80,
    heart_rate: 76,
    respiratory_rate: 16,
    temperature: 36.8,
    spo2: 99,
    known_conditions: "None",
    current_medications: "None",
    chief_complaint: "twisted ankle while jogging, swollen knee, denies chest pain, no shortness of breath, chhati dard nahi hai"
  }
};

const WAITING_TIME_MAP = {
  1: "⏱️ Maximum Safe Waiting Time: IMMEDIATE RESUSCITATION (0 minutes)",
  2: "⏱️ Maximum Safe Waiting Time: < 15 minutes (Direct Physician Attention)",
  3: "⏱️ Maximum Safe Waiting Time: < 60 minutes (Urgent Multi-Resource Workup)",
  4: "⏱️ Maximum Safe Waiting Time: < 120 minutes (Less Urgent / Single Resource)",
  5: "⏱️ Maximum Safe Waiting Time: < 240 minutes (Non-Urgent / Routine Refill)",
  0: "⚠️ ACTION REQUIRED: Cannot Safely Assess Algorithmic Urgency — Send to Nurse Now"
};

let allRulesData = [];

// DOM Ready initialization
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  fetchRules();
  fetchMetrics();

  // Run initial triage on default form values
  submitTriageForm();
});

// Theme Management
function initTheme() {
  const toggleBtn = document.getElementById("themeToggleBtn");
  const currentTheme = localStorage.getItem("smarttriage_theme") || "dark";
  document.documentElement.setAttribute("data-theme", currentTheme);

  toggleBtn.addEventListener("click", () => {
    const active = document.documentElement.getAttribute("data-theme");
    const next = active === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("smarttriage_theme", next);
  });
}

// Load Preset
function loadPreset(presetKey) {
  const p = PRESETS[presetKey];
  if (!p) return;

  document.getElementById("patientId").value = p.patient_id;
  document.getElementById("age").value = p.age;
  document.getElementById("sex").value = p.sex;
  document.getElementById("bpSystolic").value = p.bp_systolic ?? "";
  document.getElementById("bpDiastolic").value = p.bp_diastolic ?? "";
  document.getElementById("heartRate").value = p.heart_rate ?? "";
  document.getElementById("respRate").value = p.respiratory_rate ?? "";
  document.getElementById("temperature").value = p.temperature ?? "";
  document.getElementById("spo2").value = p.spo2 ?? "";
  document.getElementById("conditions").value = p.known_conditions ?? "None";
  document.getElementById("medications").value = p.current_medications ?? "None";
  document.getElementById("complaint").value = p.chief_complaint ?? "";

  submitTriageForm();
}

function resetForm() {
  document.getElementById("triageForm").reset();
  document.getElementById("patientId").value = "WALK-" + Math.floor(1000 + Math.random() * 9000);
}

function handleTriageSubmit(e) {
  e.preventDefault();
  submitTriageForm();
}

async function submitTriageForm() {
  const submitBtn = document.getElementById("submitTriageBtn");
  const latencyDisplay = document.getElementById("latencyDisplay");
  
  const payload = {
    patient_id: document.getElementById("patientId").value.trim() || "WALK_IN",
    age: parseInt(document.getElementById("age").value) || 35,
    sex: document.getElementById("sex").value,
    bp_systolic: parseFloat(document.getElementById("bpSystolic").value) || null,
    bp_diastolic: parseFloat(document.getElementById("bpDiastolic").value) || null,
    heart_rate: parseFloat(document.getElementById("heartRate").value) || null,
    respiratory_rate: parseFloat(document.getElementById("respRate").value) || null,
    temperature: parseFloat(document.getElementById("temperature").value) || null,
    spo2: parseFloat(document.getElementById("spo2").value) || null,
    known_conditions: document.getElementById("conditions").value.trim() || "None",
    current_medications: document.getElementById("medications").value.trim() || "None",
    chief_complaint: document.getElementById("complaint").value.trim()
  };

  try {
    submitBtn.disabled = true;
    submitBtn.innerHTML = "Processing Triage Assessment...";

    const res = await fetch("/api/triage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`API Error: ${res.statusText}`);
    }

    const data = await res.json();
    renderTriageResult(data);

    latencyDisplay.textContent = `⚡ Latency: ${data.latency_ms} ms`;
  } catch (err) {
    console.error("Triage submission error:", err);
    alert("Error performing triage: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      RUN SMART TRIAGE ASSESSMENT
    `;
  }
}

function renderTriageResult(data) {
  const banner = document.getElementById("triageBanner");
  const title = document.getElementById("triageLevelTitle");
  const overrideBadge = document.getElementById("ruleOverrideBadge");
  const deptName = document.getElementById("recommendedDept");
  const waitGuidance = document.getElementById("waitingTimeGuidance");
  const redFlagsList = document.getElementById("redFlagsList");
  const redFlagsWrapper = document.getElementById("redFlagsWrapper");
  const whyList = document.getElementById("clinicalWhyList");

  const level = data.triage_level;
  const color = data.color_code || "#3b82f6";

  // Update banner
  banner.style.borderColor = color;
  banner.style.boxShadow = `0 0 25px ${color}44`;
  title.style.color = color;
  title.textContent = data.triage_level_name;

  // Rule override badge
  if (data.rule_override) {
    overrideBadge.style.display = "inline-block";
    overrideBadge.textContent = `RULE OVERRIDE: ${data.rule_applied || "CRITICAL SAFETY"}`;
  } else {
    overrideBadge.style.display = "none";
  }

  // Department and wait time
  deptName.textContent = data.recommended_department;
  waitGuidance.style.color = color;
  waitGuidance.textContent = WAITING_TIME_MAP[level] || `Maximum Safe Waiting Time: Level ${level}`;

  // Red flags chips
  redFlagsList.innerHTML = "";
  if (data.red_flags && data.red_flags.length > 0) {
    redFlagsWrapper.style.display = "block";
    data.red_flags.forEach(rf => {
      const chip = document.createElement("div");
      chip.className = "red-flag-chip";
      chip.textContent = `⚠️ ${rf}`;
      redFlagsList.appendChild(chip);
    });
  } else {
    redFlagsWrapper.style.display = "none";
  }

  // Clinical reasoning / why list
  whyList.innerHTML = "";
  if (data.clinical_why && data.clinical_why.length > 0) {
    data.clinical_why.forEach(item => {
      const li = document.createElement("li");
      li.className = "why-item";
      li.textContent = item;
      whyList.appendChild(li);
    });
  }

  // Probabilities & Expected Costs
  for (let i = 1; i <= 5; i++) {
    const key = `Level ${i}`;
    const prob = (data.probabilities && data.probabilities[key]) ? data.probabilities[key] : 0.0;
    const cost = (data.expected_costs && data.expected_costs[key] !== undefined) ? data.expected_costs[key] : 0.0;
    const pct = Math.round(prob * 100);

    const bar = document.getElementById(`barL${i}`);
    const pctEl = document.getElementById(`pctL${i}`);
    const costEl = document.getElementById(`costL${i}`);

    if (bar) bar.style.width = `${pct}%`;
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (costEl) {
      costEl.textContent = `E[Cost]: ${cost}`;
      if (level === i) {
        costEl.style.fontWeight = "bold";
        costEl.style.color = color;
      } else {
        costEl.style.fontWeight = "normal";
        costEl.style.color = "var(--text-muted)";
      }
    }
  }
}

// Tabs Management
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));

  const targetContent = document.getElementById(tabId);
  if (targetContent) targetContent.classList.add("active");

  const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(btn => 
    btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(tabId)
  );
  if (activeBtn) activeBtn.classList.add("active");
}

// Fetch Deterministic Rules
async function fetchRules() {
  try {
    const res = await fetch("/api/rules");
    if (!res.ok) return;
    const data = await res.json();
    allRulesData = data.rules || [];
    renderRulesTable(allRulesData);
  } catch (err) {
    console.error("Failed to load rules:", err);
  }
}

function renderRulesTable(rules) {
  const tbody = document.getElementById("rulesTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  rules.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${r.id}</strong></td>
      <td><span style="color: var(--accent-cyan); font-weight: 600;">${r.category}</span></td>
      <td><code>${r.condition}</code></td>
      <td><strong>${r.urgency_level}</strong></td>
      <td>${r.action}</td>
      <td style="color: var(--text-secondary);">${r.rationale}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterRulesTable() {
  const query = document.getElementById("ruleFilterInput").value.toLowerCase().trim();
  if (!query) {
    renderRulesTable(allRulesData);
    return;
  }
  const filtered = allRulesData.filter(r => 
    r.id.toLowerCase().includes(query) ||
    r.category.toLowerCase().includes(query) ||
    r.condition.toLowerCase().includes(query) ||
    r.urgency_level.toLowerCase().includes(query) ||
    r.rationale.toLowerCase().includes(query)
  );
  renderRulesTable(filtered);
}

// Fetch Metrics & Simulation Results
async function fetchMetrics() {
  try {
    const res = await fetch("/api/metrics");
    if (!res.ok) return;
    const data = await res.json();
    
    // Update summary cards
    if (data.ablations && data.ablations.full_pipeline) {
      const full = data.ablations.full_pipeline;
      const recallEl = document.getElementById("metricEmergencyRecall");
      const costEl = document.getElementById("metricCost");
      const underEl = document.getElementById("metricCriticalUndertriage");
      const deptEl = document.getElementById("metricDeptAcc");

      if (recallEl) recallEl.textContent = `${(full.emergency_recall * 100).toFixed(1)}%`;
      if (costEl) costEl.textContent = full.mean_asymmetric_cost.toFixed(3);
      if (underEl) underEl.textContent = `${(full.critical_undertriage_rate * 100).toFixed(2)}%`;
      if (deptEl) deptEl.textContent = `${(full.department_accuracy * 100).toFixed(1)}%`;
    }

    // Update queue simulation
    if (data.queue_simulation) {
      const qs = data.queue_simulation;
      const savedEl = document.getElementById("simTimeSaved");
      const fcfsEl = document.getElementById("simFcfsWait");
      const smartEl = document.getElementById("simSmartWait");
      const tradeoffEl = document.getElementById("simL5Tradeoff");
      const takeawayEl = document.getElementById("simTakeawayText");

      if (savedEl) savedEl.textContent = `${qs.emergency_wait_reduction_min} min (-${qs.emergency_wait_reduction_pct}%)`;
      if (fcfsEl) fcfsEl.textContent = `${qs.fcfs.mean_wait_emergency_min} min`;
      if (smartEl) smartEl.textContent = `${qs.smart_triage.mean_wait_emergency_min} min`;
      if (tradeoffEl) tradeoffEl.textContent = `+${qs.non_urgent_wait_increase_min} min`;
      if (takeawayEl) takeawayEl.textContent = qs.clinical_takeaway;
    }
  } catch (err) {
    console.error("Failed to load metrics:", err);
  }
}
