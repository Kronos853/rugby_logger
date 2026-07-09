(() => {
  const CHANNEL_NAME = "sports-video-logger";
  const channel = new BroadcastChannel(CHANNEL_NAME);
  const video = document.getElementById("video-player");
  const fileInput = document.getElementById("video-file");
  const setup = document.getElementById("video-setup");
  const timestampInput = document.getElementById("timestamp-sec");
  const timeLabel = document.getElementById("video-time-label");
  const capturePeriodInput = document.getElementById("capture-period");

  function formatTimestamp(seconds) {
    const total = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(total / 60);
    const secs = total % 60;
    return `${minutes}-${secs < 10 ? "0" : ""}${secs}`;
  }

  function syncCapturePeriod() {
    const checked = document.querySelector('form.half-selector input[name="period"]:checked');
    if (checked && capturePeriodInput) {
      capturePeriodInput.value = checked.value;
    }
  }

  function send(msg) {
    channel.postMessage(msg);
  }

  function applyVideoTime(seconds) {
    const sec = Math.max(0, Math.floor(Number(seconds) || 0));
    if (timestampInput) timestampInput.value = String(sec);
    if (timeLabel) timeLabel.textContent = formatTimestamp(sec);
    send({ type: "SEEK", time: sec });
  }

  function initTaggingTimeline() {
    document.querySelectorAll("form.timeline-delete-form").forEach((form) => {
      if (form.dataset.timelineBound === "1") return;
      form.dataset.timelineBound = "1";
      form.addEventListener("submit", (e) => {
        if (!window.confirm("Удалить запись?")) {
          e.preventDefault();
          if (window.appScrollRestore) window.appScrollRestore.clear();
        }
      });
    });

    document.querySelectorAll("tr.timeline-row").forEach((row) => {
      if (row.dataset.timelineBound === "1") return;
      row.dataset.timelineBound = "1";
      row.addEventListener("click", (e) => {
        if (e.target.closest("button, a, input, label, form")) return;
        const form = row.querySelector("form.timeline-select-form");
        if (form) form.requestSubmit();
      });
    });

    const selectedMeta = document.getElementById("selected-event-meta");
    if (selectedMeta) {
      applyVideoTime(selectedMeta.dataset.timestampSec);
      const period = selectedMeta.dataset.period;
      if (period) {
        const radio = document.querySelector(
          `form.half-selector input[name="period"][value="${period}"]`
        );
        if (radio) {
          radio.checked = true;
          syncCapturePeriod();
        }
      }
    }
  }

  window.initTaggingTimeline = initTaggingTimeline;

  function initTaggingControl() {
    document.querySelectorAll('form.half-selector input[name="period"]').forEach((radio) => {
      if (radio.dataset.periodBound === "1") return;
      radio.dataset.periodBound = "1";
      radio.addEventListener("change", syncCapturePeriod);
    });
    syncCapturePeriod();
    initTaggingTimeline();
  }

  initTaggingControl();

  if (document.body.classList.contains("tagging-control")) {
    document.body.addEventListener("htmx:afterSettle", () => {
      initTaggingTimeline();
    });
  }

  if (video && fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      video.src = URL.createObjectURL(file);
      video.style.display = "block";
      if (setup) setup.style.display = "none";
      video.play().catch(() => {});
      send({ type: "CONNECTED" });
    });

    video.addEventListener("timeupdate", () => {
      send({ type: "TIME_UPDATE", time: video.currentTime });
    });
  }

  if (timestampInput || timeLabel) {
    const captureForm = document.getElementById("capture-form");
    if (captureForm) {
      captureForm.addEventListener("submit", () => {
        syncCapturePeriod();
        send({ type: "PAUSE" });
      });
    }

    channel.onmessage = (event) => {
      const msg = event.data || {};
      if (msg.type === "TIME_UPDATE") {
        const sec = Math.floor(msg.time || 0);
        if (timestampInput) timestampInput.value = String(sec);
        if (timeLabel) timeLabel.textContent = formatTimestamp(sec);
      }
      if (msg.type === "CONNECTED") {
        send({ type: "CONNECTED" });
      }
    };

    document.addEventListener("keydown", (e) => {
      if (e.code === "Space") {
        const tag = (e.target && e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea") return;
        e.preventDefault();
        send({ type: "TOGGLE_PLAY" });
      }
    });
  }

  if (video) {
    channel.onmessage = (event) => {
      const msg = event.data || {};
      if (msg.type === "PAUSE") video.pause();
      if (msg.type === "TOGGLE_PLAY") {
        if (video.paused) video.play().catch(() => {});
        else video.pause();
      }
      if (msg.type === "SEEK") {
        video.currentTime = Number(msg.time || 0);
        video.pause();
      }
      if (msg.type === "CONNECTED") {
        send({ type: "TIME_UPDATE", time: video.currentTime });
      }
    };
  }
})();
