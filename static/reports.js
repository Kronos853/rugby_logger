window.toggleReportComment = function (btn) {

  const target = document.getElementById(btn.dataset.target);

  if (!target) return;

  const isOpen = target.dataset.open === "1";

  if (isOpen) {

    target.innerHTML = "";

    target.dataset.open = "0";

    btn.textContent = "Комментарии";

    btn.setAttribute("aria-expanded", "false");

    return;

  }

  htmx.ajax("GET", btn.dataset.url, { target: "#" + btn.dataset.target, swap: "innerHTML" });

  target.dataset.open = "1";

  btn.textContent = "Скрыть";

  btn.setAttribute("aria-expanded", "true");

};



window.toggleReportPlayer = function (btn) {

  const target = document.getElementById(btn.dataset.target);

  if (!target) return;

  const isOpen = target.dataset.open === "1";

  if (isOpen) {

    target.innerHTML = "";

    target.dataset.open = "0";

    btn.textContent = "По игрокам";

    btn.setAttribute("aria-expanded", "false");

    return;

  }

  htmx.ajax("GET", btn.dataset.url, { target: "#" + btn.dataset.target, swap: "innerHTML" });

  target.dataset.open = "1";

  btn.textContent = "Скрыть";

  btn.setAttribute("aria-expanded", "true");

};



let activePlayerPanelButton = null;



function clearActivePlayerPanel() {

  if (activePlayerPanelButton) {

    activePlayerPanelButton.setAttribute("aria-expanded", "false");

    activePlayerPanelButton.textContent = "По игрокам";

    activePlayerPanelButton = null;

  }

  document.querySelectorAll(".report-action-row--active").forEach(function (row) {

    row.classList.remove("report-action-row--active");

  });

}



function loadEmptyPlayerPanel() {

  const panel = document.getElementById("report-player-panel");

  if (!panel) return;

  const emptyUrl = panel.dataset.emptyUrl;

  if (!emptyUrl) return;

  htmx.ajax("GET", emptyUrl, { target: "#report-player-panel", swap: "innerHTML" });

}



window.toggleReportPlayerPanel = function (btn) {

  const panel = document.getElementById("report-player-panel");

  if (!panel) return;



  const isOpen = btn.getAttribute("aria-expanded") === "true";

  if (isOpen) {

    clearActivePlayerPanel();

    loadEmptyPlayerPanel();

    return;

  }



  clearActivePlayerPanel();

  htmx.ajax("GET", btn.dataset.url, { target: "#report-player-panel", swap: "innerHTML" });

  btn.setAttribute("aria-expanded", "true");

  btn.textContent = "Скрыть";

  activePlayerPanelButton = btn;

  const row = btn.closest(".report-action-row");

  if (row) row.classList.add("report-action-row--active");

};



function initReportFormFields() {

  const typeSelect = document.getElementById("reportType");

  const teamWrap = document.getElementById("teamSelectWrap");

  const playerWrap = document.getElementById("playerSelectWrap");

  if (!typeSelect || !teamWrap || !playerWrap) return;



  function update() {

    const isTeam = typeSelect.value === "team";

    teamWrap.hidden = !isTeam;

    playerWrap.hidden = isTeam;

  }



  typeSelect.addEventListener("change", update);

  update();

}



document.addEventListener("DOMContentLoaded", function () {

  initReportFormFields();

  const form = document.getElementById("reportForm");

  if (form) {

    form.addEventListener("submit", function () {

      clearActivePlayerPanel();

    });

  }

});

