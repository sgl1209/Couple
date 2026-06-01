/**
 * 情侣网站 - 原生 JS
 * 计时器、图片预览、灯箱
 */

(function () {
  "use strict";

  // ---------- 相恋计时 & 纪念日倒计时 ----------
  function parseDate(str) {
    var parts = str.split("-");
    return new Date(
      parseInt(parts[0], 10),
      parseInt(parts[1], 10) - 1,
      parseInt(parts[2], 10)
    );
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function updateLoveTimer(startDateStr) {
    var el = document.getElementById("love-timer");
    if (!el || !startDateStr) return;

    var start = parseDate(startDateStr);
    var now = new Date();
    var diff = now - start;
    if (diff < 0) diff = 0;

    var days = Math.floor(diff / (1000 * 60 * 60 * 24));
    var hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    var minutes = Math.floor((diff / (1000 * 60)) % 60);
    var seconds = Math.floor((diff / 1000) % 60);

    var daysEl = document.getElementById("love-days");
    var hoursEl = document.getElementById("love-hours");
    var minsEl = document.getElementById("love-mins");
    var secsEl = document.getElementById("love-secs");

    if (daysEl) daysEl.textContent = days;
    if (hoursEl) hoursEl.textContent = pad(hours);
    if (minsEl) minsEl.textContent = pad(minutes);
    if (secsEl) secsEl.textContent = pad(seconds);
  }

  function updateAnniversaryCountdown(anniversaryStr) {
    var el = document.getElementById("anniversary-countdown");
    if (!el || !anniversaryStr) return;

    var target = parseDate(anniversaryStr);
    var now = new Date();
    now.setHours(0, 0, 0, 0);
    target.setHours(0, 0, 0, 0);

    var next = new Date(target);
    if (next <= now) {
      next.setFullYear(next.getFullYear() + 1);
    }

    var diff = next - now;
    var days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    var daysEl = document.getElementById("anni-days");
    var labelEl = document.getElementById("anni-label");
    if (daysEl) daysEl.textContent = days;
    if (labelEl) {
      labelEl.textContent =
        days === 0 ? "就是今天！纪念日快乐～" : "距离下一个纪念日还有";
    }
  }

  function initTimers() {
    var start = document.body.getAttribute("data-love-start");
    var anni = document.body.getAttribute("data-anniversary");
    if (start) {
      updateLoveTimer(start);
      setInterval(function () {
        updateLoveTimer(start);
      }, 1000);
    }
    if (anni) {
      updateAnniversaryCountdown(anni);
      setInterval(function () {
        updateAnniversaryCountdown(anni);
      }, 60000);
    }
  }

  // ---------- 上传图片预览 ----------
  function initPhotoPreview() {
    var input = document.getElementById("photo-input");
    var preview = document.getElementById("photo-preview");
    var previewImg = document.getElementById("preview-img");
    if (!input || !preview || !previewImg) return;

    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      if (!file) {
        preview.classList.remove("show");
        return;
      }
      if (!file.type.match(/^image\//)) {
        alert("请选择图片文件");
        input.value = "";
        preview.classList.remove("show");
        return;
      }
      var reader = new FileReader();
      reader.onload = function (e) {
        previewImg.src = e.target.result;
        preview.classList.add("show");
      };
      reader.readAsDataURL(file);
    });
  }

  // ---------- 照片灯箱 ----------
  function initLightbox() {
    var lightbox = document.getElementById("lightbox");
    var lightboxImg = document.getElementById("lightbox-img");
    var closeBtn = document.getElementById("lightbox-close");
    if (!lightbox || !lightboxImg) return;

    document.querySelectorAll("[data-lightbox]").forEach(function (item) {
      item.addEventListener("click", function () {
        var src = item.getAttribute("data-src") || item.querySelector("img")?.src;
        if (src) {
          lightboxImg.src = src;
          lightbox.classList.add("show");
        }
      });
    });

    function close() {
      lightbox.classList.remove("show");
      lightboxImg.src = "";
    }

    if (closeBtn) closeBtn.addEventListener("click", close);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) close();
    });
  }

  // ---------- 弹窗 ----------
  function initModals() {
    function openModal(id) {
      var overlay = document.getElementById(id);
      if (!overlay) return;
      overlay.classList.add("show");
      overlay.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }

    function closeModal(overlay) {
      if (!overlay) return;
      overlay.classList.remove("show");
      overlay.setAttribute("aria-hidden", "true");
      if (!document.querySelector(".modal-overlay.show")) {
        document.body.style.overflow = "";
      }
    }

    document.querySelectorAll("[data-open-modal]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openModal(btn.getAttribute("data-open-modal"));
      });
    });

    document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        closeModal(btn.closest(".modal-overlay"));
      });
    });

    document.querySelectorAll(".modal-overlay").forEach(function (overlay) {
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeModal(overlay);
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.show").forEach(closeModal);
      }
    });
  }

  // ---------- 导航高亮 ----------
  function initNavActive() {
    var path = window.location.pathname;
    document.querySelectorAll(".nav-links a[data-nav]").forEach(function (a) {
      var href = a.getAttribute("href");
      if (href === path || (path === "/" && href === "/")) {
        a.classList.add("active");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTimers();
    initModals();
    initPhotoPreview();
    initLightbox();
    initNavActive();
  });
})();
