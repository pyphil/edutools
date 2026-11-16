/* eduCards board interactions */
(function () {
  'use strict';

  var board = document.getElementById('ec-board');
  if (!board) { return; }

  var csrfToken = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var canSort = board.dataset.canSort === '1';
  var sortables = [];
  var dragging = false;
  var POLL_MS = 10000;
  var pdfWorkerSrc = (document.getElementById('ec-board-js') || { dataset: {} }).dataset.pdfWorker || '';

  function post(url, payload) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: payload ? JSON.stringify(payload) : null
    }).then(function (response) {
      if (!response.ok) { throw new Error('HTTP ' + response.status); }
      return response.json();
    });
  }

  function toast(text, variant) {
    var holder = document.querySelector('.ec-toasts');
    if (!holder || !window.bootstrap) { return; }
    var el = document.createElement('div');
    el.className = 'toast align-items-center text-bg-' + (variant || 'dark');
    el.setAttribute('role', 'status');
    el.innerHTML = '<div class="d-flex"><div class="toast-body"></div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Schließen"></button></div>';
    el.querySelector('.toast-body').textContent = text;
    holder.appendChild(el);
    el.addEventListener('hidden.bs.toast', function () { el.remove(); });
    new bootstrap.Toast(el, { delay: 3500 }).show();
  }

  // ------------------------------------------------------------------ drag & drop
  function columnCardIds(list) {
    return Array.prototype.map.call(list.querySelectorAll(':scope > .ec-card'), function (card) {
      return card.dataset.cardId;
    });
  }

  function saveColumn(list) {
    return post(board.dataset.reorderCardsUrl, {
      category_id: list.dataset.categoryId,
      card_ids: columnCardIds(list)
    }).then(function (data) { board.dataset.version = data.version; });
  }

  function updateCounts() {
    board.querySelectorAll('.ec-column').forEach(function (column) {
      var count = column.querySelector('.ec-column-count');
      if (count) { count.textContent = column.querySelectorAll('.ec-column-body > .ec-card').length; }
    });
  }

  function initSortable() {
    sortables.forEach(function (s) { s.destroy(); });
    sortables = [];
    if (!canSort || typeof Sortable === 'undefined') { return; }

    board.querySelectorAll('.ec-column-body').forEach(function (list) {
      sortables.push(Sortable.create(list, {
        group: 'ec-cards',
        animation: 160,
        draggable: '.ec-card',
        filter: 'a, button, input, textarea, select, summary, .ec-comments, .ec-video, .pdfjs-preview',
        preventOnFilter: false,
        delay: 180,
        delayOnTouchOnly: true,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        onStart: function () { dragging = true; },
        onEnd: function (evt) {
          dragging = false;
          if (evt.from === evt.to && evt.oldIndex === evt.newIndex) { return; }
          var jobs = [saveColumn(evt.to)];
          if (evt.from !== evt.to) { jobs.push(saveColumn(evt.from)); }
          updateCounts();
          Promise.all(jobs).catch(function () {
            toast('Die neue Reihenfolge konnte nicht gespeichert werden.', 'danger');
          });
        }
      }));
    });

    var columns = document.getElementById('ec-columns');
    if (columns) {
      sortables.push(Sortable.create(columns, {
        animation: 160,
        handle: '.ec-column-drag',
        draggable: '.ec-column',
        direction: board.classList.contains('layout-columns') ? 'horizontal' : 'vertical',
        onStart: function () { dragging = true; },
        onEnd: function (evt) {
          dragging = false;
          if (evt.oldIndex === evt.newIndex) { return; }
          var ids = Array.prototype.map.call(columns.querySelectorAll(':scope > .ec-column'), function (c) {
            return c.dataset.categoryId;
          });
          post(board.dataset.reorderColumnsUrl, { category_ids: ids })
            .then(function (data) { board.dataset.version = data.version; })
            .catch(function () { toast('Die Spaltenreihenfolge konnte nicht gespeichert werden.', 'danger'); });
        }
      }));
    }
  }

  // ------------------------------------------------------------------ PDF previews
  function renderPdfPreviews(root) {
    if (typeof pdfjsLib === 'undefined') { return; }
    pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;
    root.querySelectorAll('.pdfjs-preview:not([data-rendered])').forEach(function (preview) {
      preview.dataset.rendered = '1';
      var canvas = preview.querySelector('canvas');
      if (!preview.dataset.pdfUrl || !canvas) { return; }
      pdfjsLib.getDocument(preview.dataset.pdfUrl).promise.then(function (pdf) {
        return pdf.getPage(1);
      }).then(function (page) {
        var width = preview.clientWidth || 280;
        var viewport = page.getViewport({ scale: 1 });
        var scale = Math.min((width * (window.devicePixelRatio || 1)) / viewport.width, 2.5);
        var scaled = page.getViewport({ scale: scale });
        canvas.width = Math.ceil(scaled.width);
        canvas.height = Math.ceil(scaled.height);
        return page.render({ canvasContext: canvas.getContext('2d'), viewport: scaled }).promise;
      }).catch(function () {
        canvas.style.display = 'none';
        var fallback = document.createElement('div');
        fallback.className = 'text-muted small p-3 text-center';
        fallback.textContent = 'PDF-Vorschau konnte nicht geladen werden.';
        preview.appendChild(fallback);
      });
    });
  }

  // ------------------------------------------------------------------ search
  var searchInput = document.getElementById('ec-search');
  function applySearch() {
    if (!searchInput) { return; }
    var term = searchInput.value.trim().toLowerCase();
    board.querySelectorAll('.ec-card').forEach(function (card) {
      var match = !term || card.textContent.toLowerCase().indexOf(term) !== -1;
      card.style.display = match ? '' : 'none';
      card.classList.toggle('ec-hit', !!term && match);
    });
  }
  if (searchInput) {
    searchInput.addEventListener('input', applySearch);
    document.addEventListener('keydown', function (e) {
      var tag = (document.activeElement || {}).tagName;
      if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA' && !document.activeElement.isContentEditable) {
        e.preventDefault();
        searchInput.focus();
      }
      if (e.key === 'Escape' && document.activeElement === searchInput) {
        searchInput.value = '';
        applySearch();
        searchInput.blur();
      }
    });
  }

  // ------------------------------------------------------------------ delegated clicks
  document.addEventListener('click', function (e) {
    var like = e.target.closest('[data-ec-react]');
    if (like) {
      e.preventDefault();
      like.disabled = true;
      post(like.dataset.ecReact).then(function (data) {
        like.classList.toggle('is-liked', data.liked);
        like.setAttribute('aria-pressed', data.liked ? 'true' : 'false');
        like.querySelector('span').textContent = data.count;
        like.classList.add('pop');
        setTimeout(function () { like.classList.remove('pop'); }, 160);
      }).catch(function () {
        toast('Das hat nicht geklappt. Bitte versuche es erneut.', 'danger');
      }).then(function () { like.disabled = false; });
      return;
    }

    var yt = e.target.closest('[data-ec-youtube]');
    if (yt) {
      var holder = yt.closest('.ec-video');
      var iframe = document.createElement('iframe');
      iframe.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(holder.dataset.youtubeId) + '?autoplay=1&rel=0';
      iframe.title = 'YouTube-Video';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      holder.innerHTML = '';
      holder.appendChild(iframe);
      holder.dataset.playing = '1';
      return;
    }

    var present = e.target.closest('[data-ec-present]');
    if (present) {
      togglePresentation();
      return;
    }

    var jump = e.target.closest('[data-ec-jump]');
    if (jump) {
      e.preventDefault();
      var target = board.querySelector(jump.dataset.ecJump);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        target.classList.add('ec-hit');
        setTimeout(function () { target.classList.remove('ec-hit'); }, 2000);
      }
      return;
    }

    if (e.target.closest('[data-ec-refresh]')) {
      refreshBoard(true);
    }
  });

  // Submit comment with Enter (Shift+Enter for a new line)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey && e.target.matches('.ec-comment-form textarea')) {
      e.preventDefault();
      if (e.target.value.trim()) { e.target.form.requestSubmit(); }
    }
  });

  // ------------------------------------------------------------------ lightbox
  var lightbox = document.getElementById('ec-lightbox');
  if (lightbox) {
    lightbox.addEventListener('show.bs.modal', function (e) {
      var trigger = e.relatedTarget;
      if (!trigger) { return; }
      var img = lightbox.querySelector('img');
      img.src = trigger.dataset.src;
      img.alt = trigger.dataset.title || '';
      lightbox.querySelector('[data-ec-lightbox-open]').href = trigger.dataset.src;
      lightbox.querySelector('[data-ec-lightbox-download]').href = trigger.dataset.download;
    });
  }

  // ------------------------------------------------------------------ presentation mode
  function togglePresentation() {
    var on = !document.body.classList.contains('ec-present');
    document.body.classList.toggle('ec-present', on);
    try {
      if (on && document.documentElement.requestFullscreen && !document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else if (!on && document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen();
      }
    } catch (err) { /* fullscreen not available */ }
  }
  document.addEventListener('fullscreenchange', function () {
    if (!document.fullscreenElement) { document.body.classList.remove('ec-present'); }
  });

  // ------------------------------------------------------------------ live updates
  var live = document.getElementById('ec-live');

  function isBusy() {
    var active = document.activeElement;
    if (dragging) { return true; }
    if (active && board.contains(active) && (active.matches('input, textarea, select') || active.isContentEditable)) { return true; }
    if (board.querySelector('.dropdown-menu.show')) { return true; }
    if (board.querySelector('.ec-video[data-playing]')) { return true; }
    if (document.querySelector('.modal.show')) { return true; }
    return false;
  }

  function snapshot() {
    var state = { scrollX: 0, columns: {}, open: [], details: [] };
    var columns = document.getElementById('ec-columns');
    if (columns) { state.scrollX = columns.scrollLeft; }
    board.querySelectorAll('.ec-column-body').forEach(function (list) {
      state.columns[list.dataset.categoryId] = list.scrollTop;
    });
    board.querySelectorAll('.collapse.show').forEach(function (el) { state.open.push(el.id); });
    board.querySelectorAll('details.ec-more[open]').forEach(function (el) {
      var card = el.closest('.ec-card');
      if (card) { state.details.push(card.id); }
    });
    return state;
  }

  function restore(state) {
    var columns = document.getElementById('ec-columns');
    if (columns) { columns.scrollLeft = state.scrollX; }
    board.querySelectorAll('.ec-column-body').forEach(function (list) {
      if (state.columns[list.dataset.categoryId] !== undefined) {
        list.scrollTop = state.columns[list.dataset.categoryId];
      }
    });
    state.open.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.classList.add('show');
        var toggle = board.querySelector('[data-bs-target="#' + id + '"]');
        if (toggle) { toggle.setAttribute('aria-expanded', 'true'); }
      }
    });
    state.details.forEach(function (id) {
      var details = document.querySelector('#' + id + ' details.ec-more');
      if (details) { details.open = true; }
    });
  }

  function refreshBoard(force) {
    if (!force && isBusy()) {
      if (live) { live.classList.add('show'); }
      return Promise.resolve();
    }
    var state = snapshot();
    return fetch(board.dataset.partialUrl, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (response) {
        if (!response.ok) { throw new Error('HTTP ' + response.status); }
        return response.text();
      })
      .then(function (html) {
        board.innerHTML = html;
        restore(state);
        afterRender();
        if (live) { live.classList.remove('show'); }
      })
      .catch(function () { /* keep the current board on network errors */ });
  }

  function poll() {
    if (document.hidden) { return; }
    fetch(board.dataset.stateUrl, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) {
        if (data && data.version && data.version !== board.dataset.version) {
          board.dataset.version = data.version;
          refreshBoard(false);
        }
      })
      .catch(function () { /* offline – try again later */ });
  }

  setInterval(poll, POLL_MS);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) { poll(); } });

  // ------------------------------------------------------------------ init
  function updateTotal() {
    var total = document.getElementById('ec-card-total');
    if (total) { total.textContent = board.querySelectorAll('.ec-card').length; }
  }

  function afterRender() {
    initSortable();
    renderPdfPreviews(board);
    applySearch();
    updateTotal();
  }

  // Open the comments of a card when the URL points to it (e.g. after posting a comment)
  if (location.hash && /^#card-\d+$/.test(location.hash)) {
    var card = document.querySelector(location.hash);
    if (card) {
      var comments = card.querySelector('.collapse');
      if (comments && card.querySelector('.ec-comment')) { comments.classList.add('show'); }
      setTimeout(function () { card.scrollIntoView({ block: 'center', inline: 'center' }); }, 50);
      card.classList.add('ec-hit');
      setTimeout(function () { card.classList.remove('ec-hit'); }, 2000);
    }
  }

  afterRender();
})();
