(function () {
  function text(id, value) {
    var element = document.getElementById(id);
    if (element) element.textContent = value;
  }

  function formatBool(value) {
    return value ? "Ready" : "Waiting";
  }

  async function refreshStatus() {
    if (!document.getElementById("fps")) return;
    try {
      var response = await fetch("/api/status", { cache: "no-store" });
      if (!response.ok) throw new Error("status unavailable");
      var status = await response.json();
      text("fps", Number(status.fps || 0).toFixed(1));
      text("target-count", String(status.target_count || 0));
      text("camera-running", formatBool(status.camera_running));
      text("detector-loaded", formatBool(status.detector_loaded));
      text("status-message", status.error || (status.camera_running ? "Live" : "Waiting for camera"));
    } catch (error) {
      text("status-message", "Status unavailable");
    }
  }

  function bboxText(bbox) {
    return [bbox.x1, bbox.y1, bbox.x2, bbox.y2].join(", ");
  }

  async function refreshDetections() {
    var body = document.getElementById("detections-body");
    if (!body) return;
    var empty = document.getElementById("empty-state");
    try {
      var response = await fetch("/api/detections/latest", { cache: "no-store" });
      if (!response.ok) throw new Error("detections unavailable");
      var snapshot = await response.json();
      text("snapshot-meta", "Latest frame: " + snapshot.timestamp + " | FPS: " + Number(snapshot.fps || 0).toFixed(1));
      body.innerHTML = "";
      var detections = snapshot.detections || [];
      if (empty) empty.style.display = detections.length ? "none" : "block";
      detections.forEach(function (detection) {
        var row = document.createElement("tr");
        row.innerHTML =
          "<td></td><td></td><td></td><td></td>";
        row.children[0].textContent = detection.class_name;
        row.children[1].textContent = Number(detection.confidence || 0).toFixed(2);
        row.children[2].textContent = bboxText(detection.bbox);
        row.children[3].textContent = snapshot.timestamp;
        body.appendChild(row);
      });
    } catch (error) {
      if (empty) {
        empty.style.display = "block";
        empty.textContent = "Detections unavailable.";
      }
    }
  }

  refreshStatus();
  refreshDetections();
  setInterval(refreshStatus, 1000);
  setInterval(refreshDetections, 1000);
})();
