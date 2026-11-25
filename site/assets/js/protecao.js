/* ImoPlace — restrições de interface (não são proteção de código-fonte).
 * Ativadas por padrão em páginas públicas. Navegadores podem contorná-las.
 */
(() => {
  'use strict';
  const flags = Object.freeze({
    bloquearMenuContexto: true,
    bloquearAtalhosDevTools: true,
    bloquearSelecaoTexto: true,
    bloquearCopia: true
  });
  const editavel = alvo => alvo instanceof Element &&
    Boolean(alvo.closest('input, textarea, select, [contenteditable=""], [contenteditable="true"], [role="textbox"]'));

  if (flags.bloquearSelecaoTexto) {
    const estilo = document.createElement('style');
    estilo.textContent = `
      html, body, body *:not(input):not(textarea):not(select):not(option):not([contenteditable]) {
        -webkit-user-select: none;
        user-select: none;
        -webkit-touch-callout: none;
      }
      img, picture, svg { -webkit-user-drag: none; }
      input, textarea, select, option, [contenteditable], [role="textbox"] {
        -webkit-user-select: text;
        user-select: text;
      }
    `;
    document.head.appendChild(estilo);
    document.addEventListener('selectstart', e => {
      if (!editavel(e.target)) e.preventDefault();
    });
  }

  // Copiar, recortar e arrastar texto/imagens (inclui Ctrl+C pelo menu do navegador).
  if (flags.bloquearCopia) {
    ['copy', 'cut', 'dragstart'].forEach(tipo => {
      document.addEventListener(tipo, e => {
        if (!editavel(e.target)) e.preventDefault();
      }, true);
    });
  }

  if (flags.bloquearMenuContexto) {
    document.addEventListener('contextmenu', e => {
      if (!editavel(e.target)) e.preventDefault();
    });
  }

  if (flags.bloquearAtalhosDevTools) {
    document.addEventListener('keydown', e => {
      if (editavel(e.target)) return;
      const tecla = (e.key || '').toLowerCase();
      const devTools = e.key === 'F12' ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i', 'j', 'c'].includes(tecla)) ||
        ((e.ctrlKey || e.metaKey) && tecla === 'u');
      const copia = flags.bloquearCopia && (e.ctrlKey || e.metaKey) && !e.shiftKey &&
        ['c', 'x', 'a', 's'].includes(tecla);
      if (devTools || copia) {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);
  }
})();
