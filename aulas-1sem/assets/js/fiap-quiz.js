/**
 * FIAP Quiz System for Reveal.js
 * Sistema de quizzes interativos para as aulas
 *
 * Suporta dois padrões de markup:
 *
 * 1) Label/radio (recomendado):
 *    <ul class="quiz-options">
 *      <label><input type="radio" name="q1" value="a"> Opção A</label>
 *      <label><input type="radio" name="q1" value="b"> Opção B</label>
 *    </ul>
 *
 * 2) Button (legacy):
 *    <ul>
 *      <li><button class="quiz-option" data-value="a">Opção A</button></li>
 *    </ul>
 *
 * Em ambos os casos, a section deve ter:
 *   data-correct="valor_correto"
 *   data-quiz-feedback="Texto de feedback"
 */

(function () {
  'use strict';

  function initQuizzes() {
    var quizSlides = document.querySelectorAll('.quiz-slide');
    for (var i = 0; i < quizSlides.length; i++) {
      setupQuiz(quizSlides[i]);
    }
  }

  function setupQuiz(slide) {
    // Detectar qual padrão está sendo usado
    var labels = slide.querySelectorAll('.quiz-options label');
    var buttons = slide.querySelectorAll('button.quiz-option');

    if (labels.length > 0) {
      initLabelQuiz(slide, labels);
    } else if (buttons.length > 0) {
      initButtonQuiz(slide, buttons);
    }
  }

  /**
   * Padrão label/radio: ul.quiz-options > label > input[type="radio"]
   */
  function initLabelQuiz(slide, labels) {
    var feedbackEl = slide.querySelector('.quiz-feedback');
    var correctAnswer = slide.getAttribute('data-correct');
    var feedbackText = slide.getAttribute('data-quiz-feedback') || '';
    var answered = false;

    for (var i = 0; i < labels.length; i++) {
      (function(label) {
        label.addEventListener('click', function () {
          if (answered) return;

          var radio = label.querySelector('input[type="radio"]');
          if (!radio) return;
          radio.checked = true;

          answered = true;
          var selectedValue = radio.value;
          var isCorrect = selectedValue === correctAnswer;

          // Estilizar todas as labels
          for (var j = 0; j < labels.length; j++) {
            var lbl = labels[j];
            var inp = lbl.querySelector('input[type="radio"]');
            lbl.style.pointerEvents = 'none';
            lbl.style.transition = 'all 0.3s ease';

            if (inp && inp.value === correctAnswer) {
              lbl.style.background = '#eafaf1';
              lbl.style.borderColor = '#27ae60';
              lbl.style.borderLeftColor = '#27ae60';
              lbl.style.color = '#1e8449';
              lbl.style.fontWeight = '700';
            } else if (lbl === label && !isCorrect) {
              lbl.style.background = '#fdedec';
              lbl.style.borderColor = '#e74c3c';
              lbl.style.borderLeftColor = '#e74c3c';
              lbl.style.color = '#c0392b';
              lbl.style.textDecoration = 'line-through';
            } else {
              lbl.style.opacity = '0.4';
            }
          }

          showFeedback(feedbackEl, isCorrect, feedbackText);
        });
      })(labels[i]);
    }

    // Guardar referências para reset
    slide._quizLabels = labels;
    slide._quizAnswered = function() { return answered; };
    slide._quizReset = function() { answered = false; };
  }

  /**
   * Padrão button (legacy): button.quiz-option com data-value
   */
  function initButtonQuiz(slide, buttons) {
    var feedbackEl = slide.querySelector('.quiz-feedback');
    var correctAnswer = slide.getAttribute('data-correct');
    var feedbackText = slide.getAttribute('data-quiz-feedback') || '';
    var answered = false;

    for (var i = 0; i < buttons.length; i++) {
      (function(btn) {
        btn.addEventListener('click', function () {
          if (answered) return;
          answered = true;

          var selectedValue = btn.getAttribute('data-value');
          var isCorrect = selectedValue === correctAnswer;

          // Estilizar todos os botões
          for (var j = 0; j < buttons.length; j++) {
            var b = buttons[j];
            b.style.pointerEvents = 'none';
            b.style.transition = 'all 0.3s ease';

            if (b.getAttribute('data-value') === correctAnswer) {
              b.style.background = '#eafaf1';
              b.style.borderColor = '#27ae60';
              b.style.borderLeftColor = '#27ae60';
              b.style.color = '#1e8449';
              b.style.fontWeight = '700';
            } else if (b === btn && !isCorrect) {
              b.style.background = '#fdedec';
              b.style.borderColor = '#e74c3c';
              b.style.borderLeftColor = '#e74c3c';
              b.style.color = '#c0392b';
              b.style.textDecoration = 'line-through';
            } else {
              b.style.opacity = '0.4';
            }
          }

          showFeedback(feedbackEl, isCorrect, feedbackText);
        });
      })(buttons[i]);
    }

    slide._quizButtons = buttons;
    slide._quizAnswered = function() { return answered; };
    slide._quizReset = function() { answered = false; };
  }

  /**
   * Exibir feedback do quiz
   */
  function showFeedback(feedbackEl, isCorrect, feedbackText) {
    if (!feedbackEl) return;

    feedbackEl.style.display = 'block';
    feedbackEl.style.padding = '14px 22px';
    feedbackEl.style.borderRadius = '8px';
    feedbackEl.style.fontSize = '0.75em';
    feedbackEl.style.fontWeight = '600';
    feedbackEl.style.lineHeight = '1.5';
    feedbackEl.style.marginTop = '15px';

    if (isCorrect) {
      feedbackEl.style.background = '#eafaf1';
      feedbackEl.style.borderLeft = '5px solid #27ae60';
      feedbackEl.style.color = '#1e8449';
      feedbackEl.className = 'quiz-feedback correct';
      feedbackEl.innerHTML = 'Correto! ' + feedbackText;
    } else {
      feedbackEl.style.background = '#fdedec';
      feedbackEl.style.borderLeft = '5px solid #e74c3c';
      feedbackEl.style.color = '#c0392b';
      feedbackEl.className = 'quiz-feedback incorrect';
      feedbackEl.innerHTML = 'Incorreto. ' + feedbackText;
    }
  }

  /**
   * Reset do quiz ao mudar de slide (permite refazer ao voltar)
   */
  function resetQuizOnSlideChange() {
    Reveal.on('slidechanged', function(event) {
      var prevSlide = event.previousSlide;
      if (!prevSlide || !prevSlide.classList.contains('quiz-slide')) return;

      // Reset labels
      var labels = prevSlide.querySelectorAll('.quiz-options label');
      for (var i = 0; i < labels.length; i++) {
        labels[i].style.pointerEvents = '';
        labels[i].style.background = '';
        labels[i].style.borderColor = '';
        labels[i].style.borderLeftColor = '';
        labels[i].style.color = '';
        labels[i].style.fontWeight = '';
        labels[i].style.textDecoration = '';
        labels[i].style.opacity = '';
      }

      // Reset buttons
      var buttons = prevSlide.querySelectorAll('button.quiz-option');
      for (var j = 0; j < buttons.length; j++) {
        buttons[j].style.pointerEvents = '';
        buttons[j].style.background = '';
        buttons[j].style.borderColor = '';
        buttons[j].style.borderLeftColor = '';
        buttons[j].style.color = '';
        buttons[j].style.fontWeight = '';
        buttons[j].style.textDecoration = '';
        buttons[j].style.opacity = '';
      }

      // Reset radios
      var radios = prevSlide.querySelectorAll('input[type="radio"]');
      for (var k = 0; k < radios.length; k++) {
        radios[k].checked = false;
      }

      // Reset feedback
      var feedbackEl = prevSlide.querySelector('.quiz-feedback');
      if (feedbackEl) {
        feedbackEl.style.display = 'none';
        feedbackEl.className = 'quiz-feedback';
        feedbackEl.innerHTML = '';
      }

      // Reset answered state
      if (prevSlide._quizReset) {
        prevSlide._quizReset();
      }

      // Re-init quiz
      setupQuiz(prevSlide);
    });
  }

  /**
   * Timer para exercícios
   */
  window.startTimer = function (elementId, minutes) {
    var el = document.getElementById(elementId);
    if (!el) return;
    var totalSeconds = minutes * 60;
    var interval = setInterval(function() {
      var mins = Math.floor(totalSeconds / 60);
      var secs = totalSeconds % 60;
      el.textContent = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
      if (totalSeconds <= 0) {
        clearInterval(interval);
        el.textContent = '00:00';
        el.style.color = '#e74c3c';
        el.style.fontWeight = '700';
      }
      totalSeconds--;
    }, 1000);
    return interval;
  };

  function boot() {
    initQuizzes();
    if (typeof Reveal !== 'undefined' && Reveal.isReady && Reveal.isReady()) {
      resetQuizOnSlideChange();
    } else if (typeof Reveal !== 'undefined') {
      Reveal.on('ready', function() {
        initQuizzes();
        resetQuizOnSlideChange();
      });
    }
  }

  if (document.readyState === 'complete') {
    setTimeout(boot, 500);
  } else {
    window.addEventListener('load', function() { setTimeout(boot, 500); });
  }

})();
