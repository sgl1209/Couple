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

  // ---------- 签到转盘 ----------
  function initCheckinSpin() {
    var panel = document.getElementById("checkin-panel");
    var wheel = document.getElementById("checkin-wheel");
    var wheelWrap = wheel ? wheel.closest(".checkin-wheel-wrap") : null;
    var wheelPointer = wheelWrap
      ? wheelWrap.querySelector(".checkin-wheel-pointer")
      : null;
    var spinBtn = document.getElementById("checkin-spin-btn");
    var spinStatus = document.getElementById("checkin-spin-status");
    var rewardsDataEl = document.getElementById("checkin-rewards-data");
    var pointsEl = document.getElementById("checkin-points");
    var targetEl = document.getElementById("checkin-target");
    var progressFillEl = document.getElementById("checkin-progress-fill");
    var progressTextEl = document.getElementById("checkin-progress-text");
    var redeemBtn = document.getElementById("checkin-redeem-btn");
    var redeemConfirmBtn = document.getElementById("checkin-redeem-confirm-btn");
    var redeemModal = document.getElementById("checkin-redeem-modal");
    var redeemStatus = document.getElementById("checkin-redeem-status");
    var wishNoteInput = document.getElementById("checkin-wish-note-input");
    var wishNoteCountEl = document.getElementById("checkin-wish-note-count");
    var historyListEl = document.getElementById("checkin-history-list");
    var historyEmptyEl = document.getElementById("checkin-history-empty");
    var historyPeriodLabelEl = document.getElementById("checkin-history-period-label");
    var historyFilterBtns = Array.prototype.slice.call(
      document.querySelectorAll("[data-checkin-history-period]")
    );
    if (!panel || !wheel || !spinBtn || !spinStatus || !rewardsDataEl) return;

    var isPlayer = panel.getAttribute("data-is-player") === "1";
    var currentHistoryPeriod = "month";
    if (historyListEl) {
      var defaultPeriod = historyListEl.getAttribute("data-history-default-period");
      if (defaultPeriod === "week" || defaultPeriod === "month") {
        currentHistoryPeriod = defaultPeriod;
      }
    }
    var rewards = [];
    try {
      rewards = JSON.parse(rewardsDataEl.textContent || "[]");
    } catch (_err) {
      rewards = [];
    }
    if (!Array.isArray(rewards) || !rewards.length) return;

    var segmentAngle = 360 / rewards.length;
    var spinning = false;
    var wheelRotation = 0;
    var spinDurationMs = 4200;
    var redeemConfirmDefaultText = redeemConfirmBtn
      ? redeemConfirmBtn.textContent
      : "提交心愿纸条";
    function getWishNoteValue() {
      if (!wishNoteInput) return "";
      return (wishNoteInput.value || "").trim();
    }
    function syncWishNoteCount() {
      if (!wishNoteInput || !wishNoteCountEl) return;
      wishNoteCountEl.textContent = String((wishNoteInput.value || "").length);
    }
    function closeModalOverlay(overlay) {
      if (!overlay) return;
      overlay.classList.remove("show");
      overlay.setAttribute("aria-hidden", "true");
      if (!document.querySelector(".modal-overlay.show")) {
        document.body.style.overflow = "";
      }
    }

    function setInlineStatus(el, text, isError) {
      if (!el) return;
      el.textContent = text || "";
      el.classList.toggle("is-error", !!isError);
    }
    function setSpinAnimationState(isActive) {
      if (wheel) wheel.classList.toggle("is-spinning", !!isActive);
      if (wheelPointer) wheelPointer.classList.toggle("is-spinning", !!isActive);
    }
    function playSpinResultAnimation() {
      if (!wheelWrap) return;
      wheelWrap.classList.remove("is-result");
      void wheelWrap.offsetWidth;
      wheelWrap.classList.add("is-result");
      window.setTimeout(function () {
        wheelWrap.classList.remove("is-result");
      }, 720);
    }

    function applyJarState(jarState) {
      if (!jarState) return;
      if (pointsEl) pointsEl.textContent = jarState.points;
      if (targetEl) targetEl.textContent = jarState.target_points;
      if (progressFillEl) {
        progressFillEl.style.width = String(jarState.progress || 0) + "%";
      }
      if (progressTextEl) progressTextEl.textContent = jarState.progress;
      if (redeemBtn) {
        redeemBtn.disabled = !(isPlayer && jarState.can_redeem);
      }
    }

    function highlightReward(index) {
      document.querySelectorAll("[data-reward-row]").forEach(function (item) {
        item.classList.toggle(
          "is-active",
          item.getAttribute("data-reward-row") === String(index)
        );
      });
      document.querySelectorAll(".checkin-wheel-item").forEach(function (item) {
        item.classList.toggle(
          "is-active",
          item.getAttribute("data-reward-index") === String(index)
        );
      });
    }
    function setHistoryPeriodLabel(periodText, periodValue) {
      if (!historyPeriodLabelEl) return;
      if (periodText) {
        historyPeriodLabelEl.textContent = periodText;
        return;
      }
      historyPeriodLabelEl.textContent = periodValue === "week" ? "本周" : "本月";
    }

    function setHistoryFilterActive(period) {
      historyFilterBtns.forEach(function (btn) {
        btn.classList.toggle(
          "is-active",
          btn.getAttribute("data-checkin-history-period") === period
        );
      });
    }

    function setHistoryFilterLoading(isLoading) {
      historyFilterBtns.forEach(function (btn) {
        btn.disabled = !!isLoading;
      });
    }

    function renderHistory(logs) {
      if (!historyListEl) return;
      historyListEl.innerHTML = "";

      var list = Array.isArray(logs) ? logs : [];
      list.forEach(function (log) {
        var itemEl = document.createElement("div");
        itemEl.className =
          "checkin-history-item" + (log && log.is_jackpot ? " is-jackpot" : "");

        var timeEl = document.createElement("p");
        timeEl.className = "checkin-history-time";
        timeEl.textContent = (log && log.created_at) || "--";
        itemEl.appendChild(timeEl);

        var rewardEl = document.createElement("p");
        rewardEl.className = "checkin-history-reward";
        var pointsValue = parseInt((log && log.points) || 0, 10);
        if (isNaN(pointsValue)) pointsValue = 0;
        rewardEl.appendChild(
          document.createTextNode(
            ((log && log.reward_icon) || "🎁") +
              " " +
              ((log && log.reward_name) || "奖励") +
              " "
          )
        );
        var strongEl = document.createElement("strong");
        strongEl.textContent = "+" + pointsValue;
        rewardEl.appendChild(strongEl);
        itemEl.appendChild(rewardEl);

        historyListEl.appendChild(itemEl);
      });

      var hasLogs = list.length > 0;
      historyListEl.classList.toggle("hidden", !hasLogs);
      if (historyEmptyEl) {
        historyEmptyEl.classList.toggle("hidden", hasLogs);
      }
    }

    function loadHistory(period) {
      var targetPeriod = period === "week" ? "week" : "month";
      setHistoryFilterActive(targetPeriod);
      setHistoryFilterLoading(true);

      return fetch("/checkin/history?period=" + encodeURIComponent(targetPeriod), {
        method: "GET",
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, data: data };
          });
        })
        .then(function (result) {
          if (!result.ok || !result.data || !result.data.ok) {
            var errMsg =
              (result.data && result.data.message) || "历史记录加载失败，请稍后重试";
            throw new Error(errMsg);
          }
          currentHistoryPeriod =
            result.data.period === "week" ? "week" : "month";
          renderHistory(result.data.logs || []);
          setHistoryPeriodLabel(result.data.period_text, currentHistoryPeriod);
          setHistoryFilterActive(currentHistoryPeriod);
        })
        .catch(function (err) {
          setInlineStatus(
            spinStatus,
            err.message || "历史记录加载失败，请稍后重试",
            true
          );
        })
        .then(function () {
          setHistoryFilterLoading(false);
        });
    }

    if (historyListEl && !historyListEl.children.length) {
      historyListEl.classList.add("hidden");
    }
    setHistoryFilterActive(currentHistoryPeriod);
    setHistoryPeriodLabel("", currentHistoryPeriod);
    historyFilterBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        var period = btn.getAttribute("data-checkin-history-period");
        loadHistory(period);
      });
    });
    if (wishNoteInput) {
      syncWishNoteCount();
      wishNoteInput.addEventListener("input", syncWishNoteCount);
    }

    spinBtn.addEventListener("click", function () {
      if (spinning || spinBtn.disabled) return;
      spinning = true;
      spinBtn.disabled = true;
      spinBtn.textContent = "转盘中...";
      setInlineStatus(spinStatus, "正在抽取今天的奖励...");
      setSpinAnimationState(true);

      fetch("/checkin/spin", { method: "POST" })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, data: data };
          });
        })
        .then(function (result) {
          if (!result.ok || !result.data || !result.data.ok) {
            var errMsg =
              (result.data && result.data.message) || "签到失败，请稍后重试";
            throw new Error(errMsg);
          }

          var reward = result.data.reward || {};
          var rewardIndex =
            typeof reward.index === "number" && reward.index >= 0
              ? reward.index
              : 0;
          var finalOffset = (360 - rewardIndex * segmentAngle) % 360;
          wheelRotation += 360 * 6 + finalOffset;
          wheel.style.transform = "rotate(" + wheelRotation + "deg)";

          window.setTimeout(function () {
            setSpinAnimationState(false);
            playSpinResultAnimation();
            highlightReward(rewardIndex);
            applyJarState(result.data.points_jar);
            spinBtn.textContent = "今日已签到";
            setInlineStatus(
              spinStatus,
              "签到成功：" +
                (reward.icon || "🎁") +
                " " +
                (reward.name || "奖励") +
                "（+" +
                (reward.points || 0) +
                "）"
            );
            loadHistory(currentHistoryPeriod);
            spinning = false;
          }, spinDurationMs);
        })
        .catch(function (err) {
          setSpinAnimationState(false);
          spinning = false;
          spinBtn.disabled = false;
          spinBtn.textContent = "开始转盘";
          setInlineStatus(spinStatus, err.message || "签到失败，请稍后再试", true);
        });
    });

    if (redeemBtn) {
      redeemBtn.addEventListener("click", function () {
        if (redeemBtn.disabled) return;
        setInlineStatus(redeemStatus, "");
        if (wishNoteInput) {
          syncWishNoteCount();
          window.setTimeout(function () {
            wishNoteInput.focus();
          }, 0);
        }
      });
    }

    if (redeemConfirmBtn) {
      redeemConfirmBtn.addEventListener("click", function () {
        if (redeemConfirmBtn.disabled) return;
        var wishNote = getWishNoteValue();
        if (!wishNote) {
          setInlineStatus(redeemStatus, "请先写下心愿纸条再提交～", true);
          if (wishNoteInput) {
            wishNoteInput.focus();
          }
          return;
        }

        redeemConfirmBtn.disabled = true;
        redeemConfirmBtn.textContent = "提交中...";
        if (redeemBtn) redeemBtn.disabled = true;
        setInlineStatus(redeemStatus, "正在提交心愿纸条...");

        fetch("/checkin/redeem", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            wish_note: wishNote,
          }),
        })
          .then(function (res) {
            return res.json().then(function (data) {
              return { ok: res.ok, data: data };
            });
          })
          .then(function (result) {
            if (!result.ok || !result.data || !result.data.ok) {
              var errMsg =
                (result.data && result.data.message) || "提交失败，请稍后重试";
              throw new Error(errMsg);
            }
            applyJarState(result.data.points_jar);
            closeModalOverlay(redeemModal);
            if (wishNoteInput) {
              wishNoteInput.value = "";
              syncWishNoteCount();
            }
            setInlineStatus(
              redeemStatus,
              result.data.message || "心愿纸条提交成功，积分罐已清零，开启下一轮积攒吧～"
            );
          })
          .catch(function (err) {
            setInlineStatus(
              redeemStatus,
              err.message || "提交失败，请稍后重试",
              true
            );
            if (redeemBtn) redeemBtn.disabled = false;
          })
          .then(function () {
            redeemConfirmBtn.disabled = false;
            redeemConfirmBtn.textContent = redeemConfirmDefaultText;
          });
      });
    }
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
    initCheckinSpin();
  });
})();
