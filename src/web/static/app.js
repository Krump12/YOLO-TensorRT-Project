(function () {
  var translations = {
    en: {
      loginTitle: "YOLO Web Login",
      username: "Username",
      password: "Password",
      login: "Log in",
      logout: "Logout",
      dashboard: "Dashboard",
      history: "History",
      analysis: "Analysis",
      chat: "Q&A",
      dashboardTitle: "Live Detection",
      historyTitle: "Detection History",
      analysisTitle: "Agent Analysis",
      chatTitle: "Agent Q&A",
      targets: "Targets",
      camera: "Camera",
      detector: "Detector",
      latestResults: "Realtime detection results",
      noCurrentTargets: "No current targets.",
      class: "Class",
      confidence: "Confidence",
      bbox: "Bounding box",
      timestamp: "Timestamp",
      details: "Details",
      historySubtitle: "Recent target detections from the latest 48 hours.",
      classFilter: "Class filter",
      minConfidence: "Min confidence",
      apply: "Apply",
      noHistory: "No target detections in the latest 48 hours.",
      startAnalysis: "Start analysis",
      noAnalysis: "No analysis results yet.",
      question: "Question",
      ask: "Ask",
      ready: "Ready",
      waiting: "Waiting",
      live: "Live",
      statusUnavailable: "Status unavailable",
      detectionsUnavailable: "Detections unavailable."
    },
    zh: {
      loginTitle: "YOLO 网页登录",
      username: "用户名",
      password: "密码",
      login: "登录",
      logout: "退出",
      dashboard: "实时监测",
      history: "检测历史",
      analysis: "Agent 分析",
      chat: "Agent 问答",
      dashboardTitle: "实时检测",
      historyTitle: "检测历史",
      analysisTitle: "Agent 分析",
      chatTitle: "Agent 问答",
      targets: "目标数",
      camera: "摄像头",
      detector: "推理",
      latestResults: "实时检测结果",
      noCurrentTargets: "当前无目标。",
      class: "类别",
      confidence: "置信度",
      bbox: "检测框",
      timestamp: "时间",
      details: "详情",
      historySubtitle: "最近 48 小时有目标检测结果。",
      classFilter: "类别筛选",
      minConfidence: "最低置信度",
      apply: "应用",
      noHistory: "最近 48 小时没有有目标检测结果。",
      startAnalysis: "开始分析",
      noAnalysis: "暂无分析结果。",
      question: "问题",
      ask: "提问",
      ready: "正常",
      waiting: "等待",
      live: "实时",
      statusUnavailable: "状态不可用",
      detectionsUnavailable: "检测结果不可用。"
    }
  };

  function currentLanguage() {
    return localStorage.getItem("yolo-dashboard-language") || "zh";
  }

  function t(key) {
    var lang = currentLanguage();
    return (translations[lang] && translations[lang][key]) || translations.en[key] || key;
  }

  function text(id, value) {
    var element = document.getElementById(id);
    if (element) element.textContent = value;
  }

  function applyLanguage(language) {
    localStorage.setItem("yolo-dashboard-language", language);
    document.documentElement.lang = language;
    document.querySelectorAll("[data-i18n]").forEach(function (element) {
      var value = t(element.getAttribute("data-i18n"));
      if (element.tagName === "TITLE") document.title = value;
      else element.textContent = value;
    });
    document.querySelectorAll("[data-lang]").forEach(function (button) {
      button.classList.toggle("active", button.getAttribute("data-lang") === language);
    });
  }

  function initLanguage() {
    document.querySelectorAll("[data-lang]").forEach(function (button) {
      button.addEventListener("click", function () {
        applyLanguage(button.getAttribute("data-lang"));
      });
    });
    applyLanguage(currentLanguage());
  }

  function formatBool(value) {
    return value ? t("ready") : t("waiting");
  }

  function bboxText(bbox) {
    return [bbox.x1, bbox.y1, bbox.x2, bbox.y2].join(", ");
  }

  async function api(path, options) {
    var response = await fetch(path, Object.assign({ cache: "no-store" }, options || {}));
    if (!response.ok) throw new Error(path + " failed");
    return response.json();
  }

  async function refreshStatus() {
    if (!document.getElementById("fps")) return;
    try {
      var status = await api("/api/status");
      text("fps", Number(status.fps || 0).toFixed(1));
      text("target-count", String(status.target_count || 0));
      text("camera-running", formatBool(status.camera_running));
      text("detector-loaded", formatBool(status.detector_loaded));
      text("status-message", status.error || (status.camera_running ? t("live") : t("waiting")));
    } catch (error) {
      text("status-message", t("statusUnavailable"));
    }
  }

  async function refreshLatestDetections() {
    var body = document.getElementById("latest-detections-body");
    if (!body) return;
    var empty = document.getElementById("dashboard-empty");
    try {
      var snapshot = await api("/api/detections/latest");
      body.innerHTML = "";
      var detections = snapshot.detections || [];
      if (empty) empty.style.display = detections.length ? "none" : "block";
      detections.forEach(function (detection) {
        var row = document.createElement("tr");
        row.innerHTML = "<td></td><td></td><td></td><td></td>";
        row.children[0].textContent = detection.class_name;
        row.children[1].textContent = Number(detection.confidence || 0).toFixed(2);
        row.children[2].textContent = bboxText(detection.bbox);
        row.children[3].textContent = snapshot.timestamp;
        body.appendChild(row);
      });
    } catch (error) {
      if (empty) empty.textContent = t("detectionsUnavailable");
    }
  }

  async function refreshDetections() {
    var body = document.getElementById("detections-body");
    if (!body) return;
    var empty = document.getElementById("empty-state");
    var className = document.getElementById("class-filter");
    var confidence = document.getElementById("confidence-filter");
    var params = new URLSearchParams({ hours: "48" });
    if (className && className.value) params.set("class_name", className.value);
    if (confidence && confidence.value) params.set("min_confidence", confidence.value);
    try {
      var data = await api("/api/detections/recent?" + params.toString());
      text("snapshot-meta", t("historySubtitle"));
      body.innerHTML = "";
      var detections = data.detections || [];
      if (empty) empty.style.display = detections.length ? "none" : "block";
      detections.forEach(function (detection) {
        var row = document.createElement("tr");
        row.innerHTML = "<td></td><td></td><td></td><td></td><td><button type=\"button\"></button></td>";
        row.children[0].textContent = detection.class_name;
        row.children[1].textContent = Number(detection.confidence || 0).toFixed(2);
        row.children[2].textContent = bboxText(detection.bbox);
        row.children[3].textContent = detection.detected_at;
        row.children[4].children[0].textContent = t("details");
        row.children[4].children[0].addEventListener("click", function () {
          showDetectionDetail(detection.detection_id);
        });
        body.appendChild(row);
      });
    } catch (error) {
      if (empty) {
        empty.style.display = "block";
        empty.textContent = t("detectionsUnavailable");
      }
    }
  }

  async function showDetectionDetail(id) {
    var panel = document.getElementById("detection-detail");
    if (!panel) return;
    var detection = await api("/api/detections/" + encodeURIComponent(id));
    panel.hidden = false;
    panel.innerHTML =
      "<h2>" + t("details") + "</h2>" +
      "<p>ID: " + detection.detection_id + "</p>" +
      "<p>" + t("class") + ": " + detection.class_name + "</p>" +
      "<p>" + t("confidence") + ": " + Number(detection.confidence).toFixed(2) + "</p>" +
      "<p>" + t("timestamp") + ": " + detection.detected_at + "</p>" +
      "<p>" + t("bbox") + ": " + bboxText(detection.bbox) + "</p>";
  }

  async function refreshAnalysis() {
    var list = document.getElementById("analysis-list");
    if (!list) return;
    var empty = document.getElementById("analysis-empty");
    var data = await api("/api/agent/analysis/recent?hours=48");
    list.innerHTML = "";
    var analyses = data.analyses || [];
    if (empty) empty.style.display = analyses.length ? "none" : "block";
    analyses.forEach(function (item) {
      var card = document.createElement("article");
      card.className = "analysis-card severity-" + item.severity;
      card.innerHTML =
        "<h2>" + (item.pest_or_disease_name || item.status) + "</h2>" +
        "<p>Severity: " + item.severity + "</p>" +
        "<p>" + item.conclusion + "</p>" +
        "<p>" + item.recommendation + "</p>" +
        "<p>Manual review: " + (item.need_manual_review ? "Yes" : "No") + "</p>";
      list.appendChild(card);
    });
  }

  async function startAnalysis() {
    await api("/api/agent/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hours: 48, trigger_type: "manual" })
    });
    setTimeout(refreshAnalysis, 300);
  }

  async function submitChat(event) {
    event.preventDefault();
    var question = document.getElementById("chat-question");
    var answer = document.getElementById("chat-answer");
    if (!question || !answer) return;
    answer.hidden = false;
    answer.textContent = "...";
    var data = await api("/api/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question.value, language: currentLanguage(), hours: 48 })
    });
    answer.innerHTML =
      "<h2>" + t("chatTitle") + "</h2>" +
      "<p>" + data.answer + "</p>" +
      "<p>Detections: " + (data.related_detection_ids || []).join(", ") + "</p>" +
      "<p>Analysis: " + (data.related_analysis_ids || []).join(", ") + "</p>";
  }

  initLanguage();
  var apply = document.getElementById("apply-detection-filters");
  if (apply) apply.addEventListener("click", refreshDetections);
  var start = document.getElementById("start-analysis");
  if (start) start.addEventListener("click", startAnalysis);
  var chatForm = document.getElementById("chat-form");
  if (chatForm) chatForm.addEventListener("submit", submitChat);

  refreshStatus();
  refreshLatestDetections();
  refreshDetections();
  refreshAnalysis();
  setInterval(refreshStatus, 1000);
  setInterval(refreshLatestDetections, 1000);
})();
