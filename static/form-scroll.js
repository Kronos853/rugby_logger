(() => {

  const SCROLL_KEY = "app-scroll-restore";



  function locationKey() {

    return window.location.pathname + window.location.search;

  }



  function isTaggingControl() {

    return document.body.classList.contains("tagging-control");

  }



  function inputScrollContainer() {

    return document.querySelector(".tagging-input-col");

  }



  function timelineScrollContainer() {

    return document.querySelector(".tagging-timeline-col .table-wrapper");

  }



  function usesFullPageSubmit(form) {

    if (

      form.hasAttribute("hx-post") ||

      form.hasAttribute("hx-get") ||

      form.hasAttribute("hx-put") ||

      form.hasAttribute("hx-delete")

    ) {

      return false;

    }

    const target = (form.getAttribute("target") || "_self").toLowerCase();

    if (target !== "_self" && target !== "") return false;

    return true;

  }



  function clampScroll(element, top, left) {

    const maxTop = Math.max(0, element.scrollHeight - element.clientHeight);

    element.scrollTop = Math.min(Math.max(0, top), maxTop);

    if (left !== undefined) {

      const maxLeft = Math.max(0, element.scrollWidth - element.clientWidth);

      element.scrollLeft = Math.min(Math.max(0, left), maxLeft);

    }

  }



  function saveScrollPosition() {

    const payload = { key: locationKey() };



    if (isTaggingControl()) {

      const input = inputScrollContainer();

      const timeline = timelineScrollContainer();

      payload.inputY = input ? input.scrollTop : 0;

      if (timeline) {

        payload.timelineY = timeline.scrollTop;

        payload.timelineX = timeline.scrollLeft;

      }

    } else {

      const container = inputScrollContainer();

      payload.y = container ? container.scrollTop : window.scrollY;

    }



    sessionStorage.setItem(SCROLL_KEY, JSON.stringify(payload));

  }



  function restoreScrollPosition() {

    const raw = sessionStorage.getItem(SCROLL_KEY);

    if (raw == null) return;

    sessionStorage.removeItem(SCROLL_KEY);



    let data;

    try {

      data = JSON.parse(raw);

    } catch {

      return;

    }

    if (data.key !== locationKey()) return;



    const apply = () => {

      if (isTaggingControl() || data.inputY !== undefined || data.timelineY !== undefined) {

        const input = inputScrollContainer();

        const timeline = timelineScrollContainer();

        const inputY = Number(data.inputY ?? data.y);

        if (input && Number.isFinite(inputY)) {

          clampScroll(input, inputY);

        }

        const timelineY = Number(data.timelineY);

        const timelineX = Number(data.timelineX ?? 0);

        if (timeline && Number.isFinite(timelineY)) {

          clampScroll(timeline, timelineY, timelineX);

        }

        return;

      }



      const y = Number(data.y);

      if (!Number.isFinite(y)) return;



      const container = inputScrollContainer();

      if (container) {

        clampScroll(container, y);

      } else {

        window.scrollTo(0, y);

      }

    };



    requestAnimationFrame(() => {

      apply();

      requestAnimationFrame(apply);

    });

  }



  window.appScrollRestore = {

    save: saveScrollPosition,

    clear: () => sessionStorage.removeItem(SCROLL_KEY),

  };



  document.querySelectorAll("form").forEach((form) => {

    if (!usesFullPageSubmit(form)) return;

    form.addEventListener("submit", saveScrollPosition);

  });



  restoreScrollPosition();

})();


