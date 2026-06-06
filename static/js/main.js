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

  // ---------- 心形空白格上传 ----------  
  function initHeartUploadSlots() {
    var slots = Array.prototype.slice.call(
      document.querySelectorAll(".js-heart-upload-slot")
    );
    if (!slots.length) return;

    var uploadTrigger = document.querySelector(
      '[data-open-modal="modal-upload-photo"]'
    );
    var pageInput = document.getElementById("photo-page-input");
    var fileInput = document.getElementById("photo-input");
    var heartWall = document.getElementById("heart-wall");
    if (!uploadTrigger || !pageInput || !heartWall) return;

    var currentPage = heartWall.getAttribute("data-page");
    if (currentPage) {
      pageInput.value = currentPage;
    }

    slots.forEach(function (slot) {
      slot.addEventListener("click", function () {
        if (document.body.classList.contains("photo-managing")) return;
        uploadTrigger.click();
        if (fileInput) {
          setTimeout(function () {
            fileInput.focus();
          }, 0);
        }
      });
    });
  }
  // ---------- 照片灯箱 ----------
  function initLightbox() {
    var lightbox = document.getElementById("lightbox");
    var lightboxImg = document.getElementById("lightbox-img");
    var closeBtn = document.getElementById("lightbox-close");
    if (!lightbox || !lightboxImg) return;

    // 图片加载失败时隐藏破图
    document.querySelectorAll(".heart-cell img, .photo-item img").forEach(function (img) {
      img.addEventListener("error", function () {
        var photoItem = img.closest(".heart-cell, .photo-item, div");
        if (photoItem && photoItem.parentElement) {
          photoItem.parentElement.style.display = "none";
        } else if (photoItem) {
          photoItem.style.display = "none";
        }
      });
    });

    document.querySelectorAll("[data-lightbox]").forEach(function (item) {
      item.addEventListener("click", function () {
        if (document.body.classList.contains("photo-managing")) return;
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

  // ---------- 照片管理模式（多选删除） ----------
  function initPhotoManageMode() {
    var toggleBtn = document.getElementById("photo-manage-toggle");
    var manageBar = document.getElementById("photo-manage-bar");
    var cancelBtn = document.getElementById("photo-manage-cancel");
    var deleteBtn = document.getElementById("photo-delete-selected");
    var selectedInput = document.getElementById("selected-photo-ids");
    var selectedCount = document.getElementById("photo-selected-count");
    var deleteForm = document.getElementById("photo-batch-delete-form");
    var items = Array.prototype.slice.call(document.querySelectorAll("[data-photo-id]"));
    if (!toggleBtn || !manageBar || !selectedInput || !selectedCount || !items.length) return;

    var selected = new Set();
    var managing = false;

    function renderSelection() {
      items.forEach(function (item) {
        var photoId = item.getAttribute("data-photo-id");
        item.classList.toggle("photo-selected", selected.has(photoId));
      });
      selectedCount.textContent = selected.size;
      selectedInput.value = Array.from(selected).join(",");
      if (deleteBtn) deleteBtn.disabled = selected.size === 0;
    }

    function enterManageMode() {
      managing = true;
      document.body.classList.add("photo-managing");
      manageBar.classList.remove("hidden");
      toggleBtn.textContent = "退出管理";
      items.forEach(function (item) {
        item.classList.add("photo-manage-mode");
      });
      renderSelection();
    }

    function exitManageMode() {
      managing = false;
      selected.clear();
      document.body.classList.remove("photo-managing");
      manageBar.classList.add("hidden");
      toggleBtn.textContent = "管理照片";
      items.forEach(function (item) {
        item.classList.remove("photo-manage-mode");
        item.classList.remove("photo-selected");
      });
      renderSelection();
    }

    toggleBtn.addEventListener("click", function () {
      if (managing) {
        exitManageMode();
      } else {
        enterManageMode();
      }
    });

    if (cancelBtn) {
      cancelBtn.addEventListener("click", function () {
        exitManageMode();
      });
    }

    items.forEach(function (item) {
      item.addEventListener("click", function (e) {
        if (!managing) return;
        e.preventDefault();
        e.stopPropagation();
        var photoId = item.getAttribute("data-photo-id");
        if (!photoId) return;
        if (selected.has(photoId)) {
          selected.delete(photoId);
        } else {
          selected.add(photoId);
        }
        renderSelection();
      });
    });

    if (deleteForm) {
      deleteForm.addEventListener("submit", function (e) {
        if (!selectedInput.value) {
          e.preventDefault();
          alert("请先选择要删除的照片");
        }
      });
    }
  }

  // ---------- 长文本折叠 ----------
  function initCollapsibleTextWithin(root) {
    var scope = root || document;
    var blocks = Array.prototype.slice.call(
      scope.querySelectorAll(".js-collapsible-text")
    );
    if (!blocks.length) return;

    blocks.forEach(function (block) {
      if (block.dataset.collapseReady === "1") return;

      var lines = parseInt(block.getAttribute("data-collapse-lines") || "6", 10);
      if (!lines || lines < 2) lines = 6;
      block.style.setProperty("--collapse-lines", String(lines));
      block.classList.add("collapsible-text");
      block.classList.add("is-collapsed");

      var needsToggle = block.scrollHeight - block.clientHeight > 6;
      if (!needsToggle) {
        block.classList.remove("is-collapsed");
        block.dataset.collapseReady = "1";
        return;
      }

      var toggleBtn = document.createElement("button");
      toggleBtn.type = "button";
      toggleBtn.className = "text-toggle-btn";
      toggleBtn.textContent = "展开";
      toggleBtn.addEventListener("click", function () {
        var expanded = block.classList.toggle("is-expanded");
        block.classList.toggle("is-collapsed", !expanded);
        toggleBtn.textContent = expanded ? "收起" : "展开";
      });

      block.insertAdjacentElement("afterend", toggleBtn);
      block.dataset.collapseReady = "1";
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
        var modalId = btn.getAttribute("data-open-modal");

        if (modalId === "timeline-edit-modal") {
          var eventId = btn.getAttribute("data-event-id");
          var eventDate = btn.getAttribute("data-event-date");
          var eventTitle = btn.getAttribute("data-event-title");
          var eventContent = btn.getAttribute("data-event-content");
          var form = document.getElementById("timeline-edit-form");
          var dateInput = document.getElementById("edit-event-date");
          var titleInput = document.getElementById("edit-event-title");
          var contentInput = document.getElementById("edit-event-content");

          if (form && eventId) form.action = "/timeline/edit/" + eventId;
          if (dateInput) dateInput.value = eventDate || "";
          if (titleInput) titleInput.value = eventTitle || "";
          if (contentInput) contentInput.value = eventContent || "";
        }

        openModal(modalId);
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

  window.initCollapsibleTextWithin = initCollapsibleTextWithin;

  document.addEventListener("DOMContentLoaded", function () {
    initTimers();
    initModals();
    initPhotoPreview();
    initHeartUploadSlots();
    initLightbox();
    initPhotoManageMode();
    initCollapsibleTextWithin(document);
    initNavActive();
  });
})();
