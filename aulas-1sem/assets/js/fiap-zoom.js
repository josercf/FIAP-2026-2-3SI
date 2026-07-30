/**
 * FIAP Zoom — Controle de tamanho de fonte para apresentacao em sala
 *
 * Atalhos:
 *   +  (ou =)   Aumentar fonte
 *   -           Diminuir fonte
 *   0           Resetar para o padrao
 *
 * O nivel e persistido no sessionStorage para manter entre slides.
 */
(function () {
  var BASE = 28;
  var STEP = 4;
  var MIN = 20;
  var MAX = 52;
  var KEY = 'fiap-font-size';

  var current = parseInt(sessionStorage.getItem(KEY), 10) || BASE;
  var indicator = null;
  var hideTimeout = null;

  function apply(size) {
    current = Math.max(MIN, Math.min(MAX, size));
    sessionStorage.setItem(KEY, current);
    document.querySelector('.reveal').style.fontSize = current + 'px';
    showIndicator();
  }

  function createIndicator() {
    indicator = document.createElement('div');
    indicator.style.cssText =
      'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
      'background:rgba(0,0,0,0.8);color:#fff;padding:8px 20px;border-radius:6px;' +
      'font-family:Montserrat,sans-serif;font-size:14px;font-weight:600;' +
      'z-index:9999;opacity:0;transition:opacity 0.3s;pointer-events:none;' +
      'white-space:nowrap;';
    document.body.appendChild(indicator);
  }

  function showIndicator() {
    if (!indicator) createIndicator();
    var pct = Math.round((current / BASE) * 100);
    indicator.textContent = 'Fonte: ' + current + 'px (' + pct + '%)  [ \u2212 ]  [ + ]  [ 0 reset ]';
    indicator.style.opacity = '1';
    clearTimeout(hideTimeout);
    hideTimeout = setTimeout(function () {
      indicator.style.opacity = '0';
    }, 2000);
  }

  document.addEventListener('keydown', function (e) {
    // Ignorar se estiver digitando em input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.key === '+' || e.key === '=') {
      e.preventDefault();
      apply(current + STEP);
    } else if (e.key === '-' || e.key === '_') {
      e.preventDefault();
      apply(current - STEP);
    } else if (e.key === '0' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      apply(BASE);
    }
  });

  // Aplicar tamanho salvo ao carregar
  if (current !== BASE) {
    // Aguardar Reveal inicializar
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { apply(current); });
    } else {
      apply(current);
    }
  }
})();
