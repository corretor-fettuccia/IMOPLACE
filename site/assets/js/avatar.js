/* ImoPlace — avatar do cachorrinho ao lado do WhatsApp flutuante.
   Só um avatar: não tem clique nem botão próprio. Aparece e some junto com o .zap-flutuante
   (que o imovel.js mostra quando o botão do cartão de contato sai da tela).
   A cada ciclo: coreografia curta, balão com uma frase, volta a sentar e cochila. */
(function () {
  'use strict';
  var MSGS = [
    'Se viu alguma coisa que gostou, só clicar no WhatsApp ou cadastrar. Eu não mordo!',
    'Gostou de algum imóvel? Clica nesse negócio verde ali, ó…',
    'Quer saber de entrada e parcela? É só chamar no WhatsApp. Eu não mordo!',
    'Tá só olhando? Fica à vontade. Qualquer coisa, o WhatsApp tá aqui do lado.',
    'Se não encontrou o que está procurando, eu te ajudo também.'
  ];
  var PRIMEIRA = 3500;  // ms entre o botão aparecer e a primeira coreografia
  var CICLO = 25000;    // ms entre uma frase e a próxima

  var SVG = '<svg viewBox="0 0 140 130" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
    '<ellipse cx="72" cy="123" rx="40" ry="5" fill="rgba(20,30,50,.15)"/>' +
    '<g class="imo-body">' +
    '<path class="imo-tail" d="M40 96 C26 94 16 84 19 68" fill="none" stroke="#8A5A3B" stroke-width="8" stroke-linecap="round"/>' +
    '<ellipse class="imo-ln" cx="62" cy="96" rx="30" ry="24" fill="#fff"/>' +
    '<ellipse cx="54" cy="90" rx="12" ry="9" fill="#8A5A3B"/>' +
    '<ellipse class="imo-ln" cx="44" cy="111" rx="15" ry="9" fill="#fff"/>' +
    '<rect class="imo-ln" x="68" y="88" width="11" height="32" rx="5.5" fill="#fff"/>' +
    '<rect class="imo-ln imo-paw" x="83" y="88" width="11" height="32" rx="5.5" fill="#fff"/>' +
    '<path d="M70 71 Q88 82 104 71" fill="none" stroke="#0a3a7a" stroke-width="6" stroke-linecap="round"/>' +
    '<path class="imo-ln" d="M83 80 L88 75 L93 80 L93 88 L83 88 Z" fill="#ff8a00"/>' +
    '<g class="imo-head">' +
    '<path class="imo-ln" d="M72 36 C59 40 59 63 70 67 C77 60 79 46 72 36 Z" fill="#8A5A3B"/>' +
    '<circle class="imo-ln" cx="90" cy="52" r="24" fill="#fff"/>' +
    '<path class="imo-ln imo-ear" d="M100 33 L111 10 L117 38 Z" fill="#8A5A3B"/>' +
    '<ellipse cx="101" cy="48" rx="9" ry="10" fill="#8A5A3B"/>' +
    '<ellipse class="imo-ln" cx="108" cy="62" rx="14" ry="10" fill="#fff"/>' +
    '<path class="imo-tongue" d="M109 67 Q113 79 118 67 Z" fill="#E86F7E"/>' +
    '<path class="imo-ln" d="M107 66 Q112 70 118 66" fill="none"/>' +
    '<ellipse cx="119" cy="58" rx="5" ry="4" fill="#2B2B2B"/>' +
    '<g class="imo-eyes-open"><circle cx="88" cy="48" r="3.6" fill="#2B2B2B"/><circle cx="101" cy="48" r="3.6" fill="#2B2B2B"/>' +
    '<circle cx="89" cy="47" r="1.1" fill="#fff"/><circle cx="102" cy="47" r="1.1" fill="#fff"/></g>' +
    '<g class="imo-eyes-closed"><path class="imo-ln" d="M84 49 Q88 52 92 49" fill="none"/>' +
    '<path d="M97 49 Q101 52 105 49" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/></g>' +
    '</g></g>' +
    '<g class="imo-zzz" fill="#0a3a7a" font-family="Arial,sans-serif" font-weight="700">' +
    '<text x="118" y="24" font-size="16">z</text><text x="128" y="10" font-size="12">z</text></g></svg>';

  var root = null, dog = null, bubble = null, timers = [], i = 0, ativo = false;

  function montar() {
    if (root) return;
    root = document.createElement('div');
    root.className = 'imo-avatar';
    root.hidden = true;
    root.innerHTML = '<div class="imo-bubble" role="status" aria-live="polite"></div><div class="imo-dog imo--sleep">' + SVG + '</div>';
    document.body.appendChild(root);
    dog = root.querySelector('.imo-dog');
    bubble = root.querySelector('.imo-bubble');
  }
  function modo(m) { dog.className = 'imo-dog imo--' + m; }
  function depois(fn, ms) { timers.push(setTimeout(fn, ms)); }
  function parar() { timers.forEach(clearTimeout); timers = []; }
  function ciclo() {
    var msg = MSGS[i % MSGS.length]; i++;
    modo('dance');
    depois(function () { modo('talk'); bubble.textContent = msg; bubble.classList.add('imo-show'); }, 1800);
    depois(function () { bubble.classList.remove('imo-show'); modo('idle'); }, 10000);
    depois(function () { modo('sleep'); }, 18000);
    depois(ciclo, CICLO);
  }
  function sincronizar() {
    var zap = document.querySelector('.zap-flutuante');
    var visivel = !!zap && !zap.hidden;
    if (visivel === ativo) return;
    ativo = visivel;
    montar();
    parar();
    bubble.classList.remove('imo-show');
    root.hidden = !visivel;
    if (visivel) { modo('sleep'); depois(ciclo, PRIMEIRA); }
  }
  function iniciar() {
    sincronizar();
    // O imovel.js redesenha a página e liga/desliga o botão: acompanha as duas coisas.
    new MutationObserver(sincronizar).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['hidden'] });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
