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

document.addEventListener("DOMContentLoaded", initReportFormFields);
