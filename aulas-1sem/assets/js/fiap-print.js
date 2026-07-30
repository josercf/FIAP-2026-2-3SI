/**
 * FIAP Print-to-PDF System for Reveal.js
 * Adiciona botão de impressão e gerencia o fluxo de exportação para PDF
 */

(function () {
  'use strict';

  // Verifica se estamos em modo print-pdf
  var printMode = /print-pdf/gi.test(window.location.search);

  /**
   * Cria o botão flutuante de impressão (FAB)
   */
  function createPrintButton() {
    // Não cria botão se estiver em modo print-pdf
    if (printMode) return;

    var btn = document.createElement('button');
    btn.id = 'fiap-print-btn';
    btn.className = 'fiap-print-fab';
    btn.setAttribute('aria-label', 'Imprimir slides em PDF');
    btn.setAttribute('title', 'Imprimir PDF');

    // Ícone SVG de impressora
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">' +
      '<path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/>' +
      '</svg>';

    btn.addEventListener('click', handlePrintClick);

    document.body.appendChild(btn);
  }

  /**
   * Handler do clique no botão de impressão
   * Abre a mesma página em modo print-pdf do Reveal.js
   */
  function handlePrintClick() {
    var currentUrl = window.location.href.split('?')[0].split('#')[0];
    var printUrl = currentUrl + '?print-pdf';

    // Abre em nova aba para que o usuário possa usar Ctrl+P / Cmd+P
    var printWindow = window.open(printUrl, '_blank');

    // Aguarda a janela carregar e dispara a impressão automaticamente
    if (printWindow) {
      printWindow.addEventListener('load', function () {
        setTimeout(function () {
          printWindow.print();
        }, 1500); // Aguarda o Reveal.js renderizar todos os slides
      });
    }
  }

  /**
   * Em modo print-pdf, configura o Reveal.js e ajusta o layout
   */
  function setupPrintMode() {
    if (!printMode) return;

    // Adiciona classe ao body para estilos CSS
    document.body.classList.add('print-pdf-mode');

    // Aguarda o Reveal inicializar para fazer ajustes
    if (typeof Reveal !== 'undefined') {
      var checkReady = setInterval(function () {
        if (typeof Reveal.isReady === 'function' && Reveal.isReady()) {
          clearInterval(checkReady);
          afterRevealReady();
        }
      }, 200);

      // Timeout de segurança
      setTimeout(function () {
        clearInterval(checkReady);
        afterRevealReady();
      }, 5000);
    }
  }

  /**
   * Ajustes pós-inicialização do Reveal em modo print
   */
  function afterRevealReady() {
    // Força todos os fragments a ficarem visíveis
    var fragments = document.querySelectorAll('.fragment');
    fragments.forEach(function (frag) {
      frag.classList.add('visible');
      frag.classList.remove('current-fragment');
      frag.style.opacity = '1';
      frag.style.visibility = 'visible';
      frag.style.transform = 'none';
    });

    // Remove quiz interatividade (mostra resposta correta)
    var quizOptions = document.querySelectorAll('.quiz-options li[data-correct="true"]');
    quizOptions.forEach(function (opt) {
      opt.style.borderColor = '#27ae60';
      opt.style.background = '#eafaf1';
    });

    // Mostra todos os feedbacks dos quizzes como corretos
    var feedbacks = document.querySelectorAll('.quiz-feedback');
    feedbacks.forEach(function (fb) {
      fb.classList.add('show', 'correct');
      fb.style.display = 'block';
      var msg = fb.dataset.correctMsg || '';
      fb.innerHTML = '<strong>Resposta:</strong> ' + msg;
    });
  }

  /**
   * Inicialização
   */
  function init() {
    createPrintButton();
    setupPrintMode();
  }

  // Boot
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(init, 100);
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }

})();
