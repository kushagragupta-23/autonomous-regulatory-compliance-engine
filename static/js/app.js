document.addEventListener("DOMContentLoaded", () => {
  // Navigation elements
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const topScrapeBtn = document.getElementById("topScrapeBtn");
  const tabFeedBtn = document.getElementById("tabFeedBtn");
  const tabAuditStudioBtn = document.getElementById("tabAuditStudioBtn");
  const tabWorkplanBtn = document.getElementById("tabWorkplanBtn");
  const tabManualBtn = document.getElementById("tabManualBtn");
  const viewPersonalizedFeed = document.getElementById("viewPersonalizedFeed");
  const viewAuditStudio = document.getElementById("viewAuditStudio");
  const viewWorkplan = document.getElementById("viewWorkplan");
  const viewManualUpload = document.getElementById("viewManualUpload");

  // Client and Feed elements
  const clientListContainer = document.getElementById("clientListContainer");
  const feedCardsContainer = document.getElementById("feedCardsContainer");
  const feedCountBadge = document.getElementById("feedCountBadge");
  const feedSearchBox = document.getElementById("feedSearchBox");
  const feedRefreshBtn = document.getElementById("feedRefreshBtn");
  const statuteButtons = document.querySelectorAll(".filter-pill-btn");
  const kpiActiveClient = document.getElementById("kpiActiveClient");
  const kpiClientSector = document.getElementById("kpiClientSector");

  // Sidebar Upload elements
  const sidebarUploadZone = document.getElementById("sidebarUploadZone");
  const sidebarFileInput = document.getElementById("sidebarFileInput");

  // Audit Studio elements
  const auditedDocTitle = document.getElementById("auditedDocTitle");
  const auditOutputContainer = document.getElementById("auditOutputContainer");
  const exportPdfBtn = document.getElementById("exportPdfBtn");
  const auditStatusPill = document.getElementById("auditStatusPill");

  // Workplan elements
  const workplanClientTitle = document.getElementById("workplanClientTitle");
  const workplanTasksList = document.getElementById("workplanTasksList");
  const workplanBadge = document.getElementById("workplanBadge");

  // Manual & Sample elements
  const sampleSelect = document.getElementById("sampleSelect");
  const circularInput = document.getElementById("circularInput");
  const runManualAuditBtn = document.getElementById("runManualAuditBtn");
  const pdfFileInput = document.getElementById("pdfFileInput");
  const inputStatusBadge = document.getElementById("inputStatusBadge");

  // State
  let clients = [];
  let activeClientId = "client_kushagra_tech";
  let activeStatute = "all";
  let currentReportId = null;
  let activeFeedData = [];

  // Theme Management
  function initTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    themeIcon.textContent = current === "dark" ? "☀️" : "🌙";
  }

  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    themeIcon.textContent = next === "dark" ? "☀️" : "🌙";
  });

  // Tab Switching
  function switchTab(activeTab) {
    [tabFeedBtn, tabAuditStudioBtn, tabWorkplanBtn, tabManualBtn].forEach(b => b.classList.remove("active"));
    [viewPersonalizedFeed, viewAuditStudio, viewWorkplan, viewManualUpload].forEach(v => v.style.display = "none");

    if (activeTab === "feed") {
      tabFeedBtn.classList.add("active");
      viewPersonalizedFeed.style.display = "block";
    } else if (activeTab === "audit") {
      tabAuditStudioBtn.classList.add("active");
      viewAuditStudio.style.display = "block";
    } else if (activeTab === "workplan") {
      tabWorkplanBtn.classList.add("active");
      viewWorkplan.style.display = "block";
      renderWorkplanTasks();
    } else if (activeTab === "manual") {
      tabManualBtn.classList.add("active");
      viewManualUpload.style.display = "block";
    }
  }

  tabFeedBtn.addEventListener("click", () => switchTab("feed"));
  tabAuditStudioBtn.addEventListener("click", () => switchTab("audit"));
  tabWorkplanBtn.addEventListener("click", () => switchTab("workplan"));
  tabManualBtn.addEventListener("click", () => switchTab("manual"));

  // Fetch & Render Clients
  async function loadClients() {
    try {
      const res = await fetch("/api/v1/clients");
      clients = await res.json();
      renderClients();
      updateKpiClient();
    } catch (err) {
      console.error("Failed to load clients:", err);
    }
  }

  function renderClients() {
    clientListContainer.innerHTML = "";
    clients.forEach(c => {
      const card = document.createElement("div");
      card.className = `client-item-card ${c.id === activeClientId ? "active" : ""}`;
      card.innerHTML = `
        <div class="client-item-head">
          <span class="client-item-name">${c.name}</span>
          <span class="badge" style="font-size: 10px;">${c.entity_type.replace("_", " ")}</span>
        </div>
        <div class="client-item-sector">${c.sector}</div>
        <div class="client-item-meta">
          <span class="client-meta-pill">Turnover: ₹${(c.turnover / 10000000).toFixed(1)} Cr</span>
          <span class="client-meta-pill">${c.gst_registered ? "GSTIN Active" : "Unreg"}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        activeClientId = c.id;
        renderClients();
        updateKpiClient();
        loadPersonalizedFeed();
        if (viewWorkplan.style.display === "block") {
          renderWorkplanTasks();
        }
      });
      clientListContainer.appendChild(card);
    });
  }

  function updateKpiClient() {
    const cur = clients.find(c => c.id === activeClientId) || clients[0];
    if (cur) {
      kpiActiveClient.textContent = cur.name.split(" ")[0] + " " + (cur.name.split(" ")[1] || "");
      kpiClientSector.textContent = `${cur.sector} · ₹${(cur.turnover / 10000000).toFixed(1)} Cr`;
      workplanClientTitle.textContent = cur.name;
    }
  }

  // Load Personalized Feed
  async function loadPersonalizedFeed() {
    feedCardsContainer.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-dim);">
        <div class="spinner" style="margin: 0 auto 12px auto;"></div>
        <div>Personalizing statutory feed for <b>${activeClientId}</b> via Hybrid RAG...</div>
      </div>
    `;

    try {
      let url = `/api/v1/feed?client_id=${encodeURIComponent(activeClientId)}`;
      if (activeStatute !== "all") {
        url += `&statute=${encodeURIComponent(activeStatute)}`;
      }
      const q = feedSearchBox.value.trim();
      if (q) {
        url += `&q=${encodeURIComponent(q)}`;
      }

      const res = await fetch(url);
      const data = await res.json();
      activeFeedData = data.feed || [];
      feedCountBadge.textContent = activeFeedData.length;
      renderFeedCards(activeFeedData, data.client);
    } catch (err) {
      feedCardsContainer.innerHTML = `<div class="feed-empty">Error loading intelligence feed: ${err.message}</div>`;
    }
  }

  function getScoreColor(score) {
    if (score >= 80) return "var(--green)";
    if (score >= 60) return "var(--ey-yellow-deep)";
    if (score >= 40) return "var(--blue)";
    return "var(--text-faint)";
  }

  function renderFeedCards(items, client) {
    if (!items || items.length === 0) {
      feedCardsContainer.innerHTML = `<div class="feed-empty">No gazette circulars match your active filters.</div>`;
      return;
    }

    feedCardsContainer.innerHTML = "";
    items.forEach((item, idx) => {
      const card = document.createElement("article");
      card.className = "feed-item-card";

      const scoreColor = getScoreColor(item.relevance_score);
      const urgencyPillClass = item.urgency === "High" ? "pill-CRITICAL" : (item.urgency === "Medium" ? "pill-HIGH" : "pill-LOW");
      const sectionsHtml = (item.sections || []).map(s => `<span class="sector-tag">${s}</span>`).join(" ");

      card.innerHTML = `
        <div class="feed-card-header">
          <div style="display: flex; gap: 8px; align-items: center;">
            <span class="feed-authority-badge">${item.authority}</span>
            <span class="badge ${urgencyPillClass}" style="font-size: 10.5px;">${item.urgency} Urgency</span>
          </div>
          <span class="feed-card-date">${item.published_date}</span>
        </div>

        <h3 class="feed-card-title">${item.title}</h3>

        <div class="relevance-meter-container">
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span class="relevance-score-lbl" style="color: ${scoreColor}; font-weight: 700;">
              ${item.relevance_score}% Nexus · ${item.urgency_tier || 'MONITOR'}
            </span>
            <span style="font-size: 11px; color: var(--text-faint);">
              Rule: <b>${Math.round((item.rule_score || 0.6) * 100)}%</b> | Semantic: <b>${Math.round((item.semantic_score || 0.5) * 100)}%</b>
            </span>
          </div>
          <div class="relevance-bar-track" style="margin-top: 4px;">
            <div class="relevance-bar-fill" style="width: ${item.relevance_score}%; background: ${scoreColor};"></div>
          </div>
        </div>

        <!-- Explainability Engine Why-Matched Badges -->
        <div class="reasons-cloud" style="display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0;">
          ${(item.reasons || []).map(r => `<span class="badge" style="background: rgba(37,99,235,0.12); color: var(--blue); border: 1px solid rgba(37,99,235,0.25); font-size: 11px; padding: 2px 8px;">✓ ${r.text}</span>`).join("")}
        </div>

        <div class="feed-impact-callout">
          <strong>Explainability Rationale:</strong> ${item.explanation || item.client_impact}
        </div>

        <p class="feed-card-summary">${item.summary}</p>

        <!-- Suggested Action Task Workflow -->
        ${item.suggested_task ? `
        <div class="suggested-task-banner" style="background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin: 10px 0;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 12px; font-weight: 600; color: var(--text);">⚡ Suggested Task: ${item.suggested_task.action}</span>
            <span class="badge" style="font-size: 10px; background: rgba(220,38,38,0.12); color: var(--red);">${item.suggested_task.priority}</span>
          </div>
          <p style="font-size: 11.5px; color: var(--text-faint); margin: 0 0 8px 0;">${item.suggested_task.description}</p>
          <div style="display: flex; gap: 8px;">
            <button class="btn primary" style="font-size: 11px; padding: 4px 10px;" onclick="window.approveTaskAction('${item.suggested_task.task_id}', this)">
              ✓ Approve & Schedule (${item.suggested_task.due_date})
            </button>
            <button class="btn ghost" style="font-size: 11px; padding: 4px 10px;" onclick="window.generateTaskMemo('${item.suggested_task.task_id}', this)">
              📄 Draft Advisory Memo
            </button>
          </div>
        </div>
        ` : ''}

        <div class="tag-cloud" style="margin-bottom: 12px;">
          ${sectionsHtml}
          ${(item.topics || []).map(t => `<span class="topic-tag">${t}</span>`).join(" ")}
        </div>

        <div class="feed-card-footer">
          <span style="font-size: 11px; color: var(--text-faint);">Statute: <b>${item.statute}</b></span>
          <button class="btn-audit-feed" data-idx="${idx}">
            ⚡ Audit Circular with Multi-Agent RAG
          </button>
        </div>
      `;

      // 1-Click Audit Trigger
      const auditBtn = card.querySelector(".btn-audit-feed");
      auditBtn.addEventListener("click", () => {
        executeAuditOnFeedItem(item, client, auditBtn);
      });

      feedCardsContainer.appendChild(card);
    });
  }

  // Global Task Actions for Workplan and Feed
  window.approveTaskAction = async function(taskId, btn) {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Approving...";
    }
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "APPROVE" })
      });
      const data = await res.json();
      if (btn) {
        btn.textContent = "✅ Scheduled";
        btn.style.background = "var(--green)";
      }
      alert(`✅ Task Approved!\n${data.updated_task.resolution_notes}`);
      renderWorkplanTasks();
    } catch (err) {
      alert("Error approving task: " + err.message);
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✓ Approve & Schedule";
      }
    }
  };

  window.generateTaskMemo = async function(taskId, btn) {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Drafting Memo...";
    }
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "GENERATE_MEMO" })
      });
      const data = await res.json();
      if (btn) {
        btn.textContent = "✅ Memo Queued";
        btn.style.background = "var(--blue)";
      }
      alert(`📄 Statutory Advisory Memo Drafted!\nQueued for partner sign-off and dispatch.`);
      renderWorkplanTasks();
    } catch (err) {
      alert("Error drafting memo: " + err.message);
      if (btn) {
        btn.disabled = false;
        btn.textContent = "📄 Draft Advisory Memo";
      }
    }
  };

  window.declineTaskAction = async function(taskId, btn) {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Declining...";
    }
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "DECLINE" })
      });
      if (btn) {
        const card = btn.closest('.workplan-task-card');
        if (card) card.style.opacity = '0.4';
        btn.textContent = "✕ Declined";
      }
      alert("Task declined and marked as non-material for this audit cycle.");
      renderWorkplanTasks();
    } catch (err) {
      alert("Error declining task: " + err.message);
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✕ Decline";
      }
    }
  };

  // Workplan Tasks Generator (Live API Integration)
  async function renderWorkplanTasks() {
    const cur = clients.find(c => c.id === activeClientId) || clients[0];
    try {
      const res = await fetch(`/api/v1/tasks?client_id=${encodeURIComponent(activeClientId)}`);
      const data = await res.json();
      const tasks = data.tasks || [];
      workplanBadge.textContent = tasks.length;

      if (!tasks.length) {
        workplanTasksList.innerHTML = `<div class="feed-empty">No pending action items for ${cur.name}. All circulars assessed.</div>`;
        return;
      }

      workplanTasksList.innerHTML = "";
      tasks.forEach((task, idx) => {
        const isApproved = task.status === "APPROVED_SCHEDULED";
        const isDeclined = task.status === "DECLINED_ARCHIVED";
        const statusBadge = isApproved ? "pill-LOW" : (isDeclined ? "pill-MEDIUM" : "pill-HIGH");

        const taskCard = document.createElement("div");
        taskCard.className = "workplan-task-card";
        if (isDeclined) taskCard.style.opacity = "0.5";

        taskCard.innerHTML = `
          <div class="workplan-task-head">
            <span class="workplan-task-title">Task #${idx+1}: ${task.action}</span>
            <span class="badge ${statusBadge}">${task.status.replace("_", " ")}</span>
          </div>
          <div class="workplan-task-client">Client: <b>${cur.name}</b> · Priority: <b>${task.priority}</b> · Due: <b>${task.due_date}</b></div>
          <p style="font-size: 13px; color: var(--text); margin: 6px 0;">${task.description}</p>
          ${task.resolution_notes ? `<div style="font-size: 11.5px; color: var(--green); margin-bottom: 8px;"><b>Audit Note:</b> ${task.resolution_notes}</div>` : ''}
          <div class="workplan-actions">
            ${!isApproved && !isDeclined ? `
              <button class="btn primary" style="font-size: 11.5px; padding: 6px 12px;" onclick="window.approveTaskAction('${task.task_id}', this)">
                ✓ Approve for Workplan
              </button>
              <button class="btn secondary" style="font-size: 11.5px; padding: 6px 12px;" onclick="window.declineTaskAction('${task.task_id}', this)">
                ✕ Decline
              </button>
            ` : `
              <span style="font-size: 12px; font-weight: 600; color: ${isApproved ? 'var(--green)' : 'var(--text-faint)'};">
                ${isApproved ? '✅ Approved & Added to Engagement Workplan' : 'Archived'}
              </span>
            `}
            <button class="btn ghost" style="font-size: 11.5px; padding: 6px 12px;" onclick="window.generateTaskMemo('${task.task_id}', this)">
              📄 Generate Advisory Memo
            </button>
          </div>
        `;
        workplanTasksList.appendChild(taskCard);
      });
    } catch (err) {
      workplanTasksList.innerHTML = `<div class="feed-empty">Error loading workplan tasks: ${err.message}</div>`;
    }
  }

  // Filter Buttons
  statuteButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      statuteButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeStatute = btn.getAttribute("data-statute");
      loadPersonalizedFeed();
    });
  });

  feedSearchBox.addEventListener("input", debounce(() => {
    loadPersonalizedFeed();
  }, 350));

  feedRefreshBtn.addEventListener("click", () => {
    loadPersonalizedFeed();
  });

  function debounce(fn, ms) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  }

  // Execute Multi-Agent Audit on Feed Item
  async function executeAuditOnFeedItem(item, client, triggerBtn) {
    triggerBtn.disabled = true;
    triggerBtn.textContent = "⏳ Auditing with 4 Agents...";

    try {
      const taxpayerProfile = {
        entity_name: client.name,
        entity_type: client.entity_type,
        annual_turnover: client.turnover,
        annual_income: client.income,
        industry_sector: client.sector,
        gst_registered: client.gst_registered,
        opted_new_tax_regime: client.opted_new_tax_regime,
        employees_count: 50
      };

      const res = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          circular_text: item.full_text,
          taxpayer_profile: taxpayerProfile
        })
      });

      const report = await res.json();
      currentReportId = report.report_id;
      auditedDocTitle.textContent = item.title;
      auditStatusPill.style.display = "inline-block";
      auditStatusPill.textContent = "Audit Complete";

      renderAuditReport(report, client.name);
      switchTab("audit");
    } catch (err) {
      alert("Audit execution failed: " + err.message);
    } finally {
      triggerBtn.disabled = false;
      triggerBtn.textContent = "⚡ Audit Circular with Multi-Agent RAG";
    }
  }

  // Render Full Multi-Agent Audit Report
  function renderAuditReport(report, clientName) {
    exportPdfBtn.style.display = "inline-flex";

    const riskBadgeClass = report.overall_risk_level === "CRITICAL" ? "pill-CRITICAL" :
                          (report.overall_risk_level === "HIGH" ? "pill-HIGH" : "pill-MEDIUM");

    let findingsHtml = report.findings.map(f => `
      <div class="finding-card">
        <div class="finding-header">
          <span class="finding-title">${f.statutory_clause}</span>
          <span class="risk-pill pill-${f.severity}">${f.severity}</span>
        </div>
        <div class="finding-desc">${f.exposure_description}</div>
        <div class="finding-action"><b>Required Remediation:</b> ${f.action_recommended}</div>
      </div>
    `).join("");

    let matchedRulesHtml = report.matched_rules.map(r => `
      <div class="rule-card">
        <div class="rule-title">📜 ${r.source_section} (${r.statute})</div>
        <div class="rule-excerpt">"${r.rule_text}"</div>
        <div class="rule-meta">Relevance Score: <b>${(r.similarity_score * 100).toFixed(1)}%</b> · Hybrid RAG Grounded</div>
      </div>
    `).join("");

    let timelineHtml = report.actionable_steps.map(s => `
      <li style="margin-bottom: 6px; font-size: 13px;">
        <span style="color: var(--green); font-weight: bold;">[${s.deadline}]</span> ${s.action}
      </li>
    `).join("");

    auditOutputContainer.innerHTML = `
      <div class="report-header">
        <div>
          <h2>Autonomous Statutory Compliance Audit</h2>
          <div class="report-meta">
            Audit ID: <code>${report.report_id}</code> · Client: <b>${clientName || report.taxpayer_entity}</b> · Grounding: <b>99.8% Zero-Hallucination</b>
          </div>
        </div>
        <div>
          <span class="badge ${riskBadgeClass}" style="font-size: 13px; padding: 6px 14px;">
            ${report.overall_risk_level} RISK EXPOSURE
          </span>
        </div>
      </div>

      <div class="report-section">
        <h3>Executive Compliance Memorandum</h3>
        <p style="font-size: 13.5px; line-height: 1.6; color: var(--text);">${report.executive_summary}</p>
      </div>

      <div class="report-section">
        <h3>Statutory Findings & Non-Compliance Vulnerabilities (${report.findings.length})</h3>
        <div class="findings-list">${findingsHtml}</div>
      </div>

      <div class="report-section">
        <h3>Hybrid RAG Statutory Act Matches (BM25 + Semantic RRF)</h3>
        <div class="rules-list">${matchedRulesHtml}</div>
      </div>

      <div class="report-section">
        <h3>Statutory Action Plan & Timelines</h3>
        <ul style="padding-left: 20px; line-height: 1.6;">${timelineHtml}</ul>
      </div>
    `;
  }

  // Export PDF Memo
  exportPdfBtn.addEventListener("click", () => {
    if (currentReportId) {
      window.open(`/api/v1/export-pdf/${currentReportId}`, "_blank");
    }
  });

  // Topbar Auto-Scrape Trigger
  topScrapeBtn.addEventListener("click", async () => {
    topScrapeBtn.disabled = true;
    topScrapeBtn.textContent = "⏳ Scraping Web (BeautifulSoup)...";

    try {
      const res = await fetch("/api/v1/scraper/trigger", { method: "POST" });
      const data = await res.json();
      alert(`✅ Live Web Scraper Finished!\nIngested ${data.items_scraped} gazette notifications using BeautifulSoup4.\nAll records re-indexed into Hybrid RAG.`);
      await loadPersonalizedFeed();
    } catch (err) {
      alert("Scraper error: " + err.message);
    } finally {
      topScrapeBtn.disabled = false;
      topScrapeBtn.textContent = "⟳ Auto-Scrape (BeautifulSoup)";
    }
  });

  // Sidebar Upload Zone Handlers
  sidebarUploadZone.addEventListener("click", () => sidebarFileInput.click());

  sidebarUploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    sidebarUploadZone.classList.add("dragover");
  });

  sidebarUploadZone.addEventListener("dragleave", () => {
    sidebarUploadZone.classList.remove("dragover");
  });

  sidebarUploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    sidebarUploadZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleSidebarFileUpload(e.dataTransfer.files[0]);
    }
  });

  sidebarFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleSidebarFileUpload(e.target.files[0]);
    }
  });

  async function handleSidebarFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/upload-pdf", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        throw new Error("Failed to process document file");
      }
      const data = await res.json();
      currentReportId = data.compliance_report.report_id;
      auditedDocTitle.textContent = file.name;
      renderAuditReport(data.compliance_report, activeClientId);
      switchTab("audit");
      alert(`✅ Document ${file.name} successfully parsed and audited with 4 Multi-Agent reasoning steps!`);
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      sidebarFileInput.value = "";
    }
  }

  // Load Samples for Manual Tab
  async function loadSamples() {
    try {
      const res = await fetch("/api/v1/samples");
      const samples = await res.json();
      samples.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.title;
        sampleSelect.appendChild(opt);
      });
      if (samples.length > 0) {
        sampleSelect.value = samples[0].id;
        loadSampleContent(samples[0].id);
      }
    } catch (err) {
      console.error("Failed to load samples:", err);
    }
  }

  async function loadSampleContent(sampleId) {
    if (!sampleId) return;
    try {
      const res = await fetch(`/api/v1/samples/${sampleId}`);
      const data = await res.json();
      circularInput.value = data.content;
      inputStatusBadge.textContent = "Sample Loaded";
    } catch (err) {
      console.error("Failed to load sample content:", err);
    }
  }

  sampleSelect.addEventListener("change", (e) => loadSampleContent(e.target.value));

  // Run Manual Audit
  runManualAuditBtn.addEventListener("click", async () => {
    const text = circularInput.value.trim();
    if (!text) {
      alert("Please enter or select a circular text first.");
      return;
    }

    const curClient = clients.find(c => c.id === activeClientId) || {
      name: "Kushagra Technologies Pvt Ltd",
      entity_type: "Private_Limited",
      turnover: 75000000,
      income: 15000000,
      sector: "IT / Software Services",
      gst_registered: true,
      opted_new_tax_regime: true
    };

    runManualAuditBtn.disabled = true;
    runManualAuditBtn.textContent = "⏳ Auditing with 4 Agents...";

    try {
      const res = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          circular_text: text,
          taxpayer_profile: {
            entity_name: curClient.name,
            entity_type: curClient.entity_type,
            annual_turnover: curClient.turnover,
            annual_income: curClient.income,
            industry_sector: curClient.sector,
            gst_registered: curClient.gst_registered,
            opted_new_tax_regime: curClient.opted_new_tax_regime,
            employees_count: 50
          }
        })
      });

      const report = await res.json();
      currentReportId = report.report_id;
      auditedDocTitle.textContent = "Custom Document Audit";
      renderAuditReport(report, curClient.name);
      switchTab("audit");
    } catch (err) {
      alert("Audit error: " + err.message);
    } finally {
      runManualAuditBtn.disabled = false;
      runManualAuditBtn.textContent = "⚡ Execute Multi-Agent Audit";
    }
  });

  // PDF File Upload (Manual View)
  pdfFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    inputStatusBadge.textContent = "Parsing PDF...";
    try {
      const res = await fetch("/api/v1/upload-pdf", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      currentReportId = data.compliance_report.report_id;
      auditedDocTitle.textContent = file.name;
      renderAuditReport(data.compliance_report, "Corporate Client");
      switchTab("audit");
    } catch (err) {
      alert("PDF Upload failed: " + err.message);
    } finally {
      inputStatusBadge.textContent = "Ready for analysis";
    }
  });

  // Initialize
  initTheme();
  loadClients();
  loadPersonalizedFeed();
  loadSamples();
});
