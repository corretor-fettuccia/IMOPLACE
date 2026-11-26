/* ImoPlace — avatar do cachorrinho ao lado do WhatsApp flutuante (versão em sprites).
   Só um avatar: não tem clique nem botão próprio. Fica sempre no canto da página do imóvel que tem WhatsApp,
   com o botão flutuante à vista ou não (quando o botão do cartão de contato está na tela, o flutuante some e
   o cachorrinho continua). Só se esconde com o visualizador de fotos aberto e enquanto se digita no formulário.
   Ciclo (a cada 16 s): dorme → acorda → dança com pulinho → fala (balão com "pop", WhatsApp balança) → senta → deita → dorme.
   Quando a pessoa rola a página, ele acorda, pula e volta a cochilar.
   A folha de sprites (assets/img/tijolo-sprites.webp) só é baixada depois que a página termina de carregar,
   e o estilo vem neste arquivo para CSS e JS nunca ficarem fora de sincronia no cache. */
(function () {
  'use strict';
  var MSGS = [
    'Se viu alguma coisa que gostou, só clicar no WhatsApp ou cadastrar. Eu não mordo!',
    'Gostou de algum imóvel? Clica nesse negócio verde ali, ó…',
    'Quer saber de entrada e parcela? É só chamar no WhatsApp. Eu não mordo!',
    'Tá só olhando? Fica à vontade. Qualquer coisa, o WhatsApp tá aqui do lado.',
    'Se não encontrou o que está procurando, eu te ajudo também.',
    'Olha só, não uivo não… Se estiver procurando algo neste perfil, clica nesse botão verde aí!'
  ];
  var PRIMEIRA = 2000;  // ms entre o botão aparecer e o primeiro ciclo
  var CICLO = 16000;    // ms entre uma frase e a próxima (o ciclo inteiro cabe em 13 s)

  var me = document.currentScript;
  var FOLHA = new URL('../img/tijolo-sprites.webp', (me && me.src) || location.href).href;

  // Folha: quadros de 160 px (CSS) em 32 colunas × 6 linhas. [linha, quadros, duração, repete]
  var ANIM = {
    sleep: [0, 24, 2.0, true], wake: [1, 24, 1.2, false], dance: [2, 32, 1.6, false],
    talk: [3, 16, 0.8, true], idle: [4, 24, 2.0, true], lie: [5, 16, 0.9, false]
  };

  function estilo() {
    var css = '.imo-avatar{position:fixed;right:calc(max(20px,env(safe-area-inset-right)) + 56px);' +
      'bottom:calc(max(20px,calc(env(safe-area-inset-bottom) + 16px)) - 14px);z-index:29;width:160px;height:160px;' +
      'pointer-events:none;transform-origin:bottom right;font-family:var(--b,system-ui,sans-serif)}' +
      '.imo-avatar[hidden]{display:none}' +
      '.imo-spr{width:160px;height:160px;background-image:url("' + FOLHA + '");background-size:5120px 960px;background-repeat:no-repeat}' +
      '.imo-bubble{position:absolute;right:-60px;bottom:146px;width:270px;box-sizing:border-box;background:#fff;color:#0f1d2e;' +
      'border-radius:18px;padding:13px 16px;font-size:15px;line-height:1.45;box-shadow:0 14px 30px -10px rgba(6,19,39,.35);' +
      'opacity:0;transform:translateY(8px) scale(.95);transition:opacity .3s,transform .3s}' +
      '.imo-bubble.imo-show{opacity:1;transform:none;animation:imo-pop .5s cubic-bezier(.3,1.7,.5,1)}' +
      '@keyframes imo-pop{0%{opacity:0;transform:translateY(14px) scale(.6)}100%{opacity:1;transform:none}}' +
      '.imo-avatar.imo-pulo{animation:imo-pulo .9s ease-in-out 2}' +
      '@keyframes imo-pulo{0%,100%{translate:0 0;rotate:0deg}25%{translate:0 -14px;rotate:-5deg}50%{translate:0 0;rotate:0deg}70%{translate:0 -6px;rotate:4deg}}' +
      '.zap-flutuante.zap-chamando{animation:zap-chamar .55s ease-in-out 4!important}' +
      '@keyframes zap-chamar{0%,100%{transform:scale(1) rotate(0)}30%{transform:scale(1.14) rotate(-10deg)}60%{transform:scale(1.08) rotate(9deg)}}' +
      '.imo-bubble::after{content:"";position:absolute;right:122px;bottom:-9px;border:10px solid transparent;border-top-color:#fff;border-bottom:0}' +
      '@media (max-width:820px){.imo-avatar{right:calc(max(20px,env(safe-area-inset-right)) + 52px);transform:scale(.62)}' +
      '.imo-bubble{width:340px;font-size:24px;padding:16px 20px}}';
    Object.keys(ANIM).forEach(function (k) {
      var a = ANIM[k], n = a[1];
      var fim = a[3] ? -n * 160 : -(n - 1) * 160;
      css += '@keyframes imo-' + k + '{from{background-position-x:0}to{background-position-x:' + fim + 'px}}' +
        '.imo--' + k + '{background-position-y:' + (-a[0] * 160) + 'px;animation:imo-' + k + ' ' + a[2] + 's ' +
        (a[3] ? 'steps(' + n + ') infinite' : 'steps(' + n + ',jump-none) forwards') + '}';
    });
    css += '@media (prefers-reduced-motion:reduce){.imo-spr{animation:none!important}.imo-bubble{transition:none;animation:none!important}.zap-flutuante.zap-chamando,.imo-avatar.imo-pulo{animation:none!important}}';
    var el = document.createElement('style');
    el.textContent = css;
    document.head.appendChild(el);
  }

  var root = null, spr = null, bubble = null, timers = [], i = 0, ativo = false;

  function montar() {
    if (root) return;
    estilo();
    root = document.createElement('div');
    root.className = 'imo-avatar';
    root.hidden = true;
    root.setAttribute('aria-hidden', 'true');
    root.innerHTML = '<div class="imo-bubble" role="status"></div><div class="imo-spr imo--sleep"></div>';
    document.body.appendChild(root);
    spr = root.querySelector('.imo-spr');
    bubble = root.querySelector('.imo-bubble');
  }
  var dormindo = true, ultimaReacao = 0;
  function modo(m) { spr.className = 'imo-spr imo--' + m; dormindo = m === 'sleep'; }
  function pular() { root.classList.remove('imo-pulo'); void root.offsetWidth; root.classList.add('imo-pulo'); depois(function () { root.classList.remove('imo-pulo'); }, 1900); }
  function chamarZap() {
    var zap = document.querySelector('.zap-flutuante'); if (!zap) return;
    zap.classList.remove('zap-chamando'); void zap.offsetWidth; zap.classList.add('zap-chamando');
    depois(function () { zap.classList.remove('zap-chamando'); }, 2300);
  }
  function depois(fn, ms) { timers.push(setTimeout(fn, ms)); }
  function parar() { timers.forEach(clearTimeout); timers = []; }
  function ciclo() {
    var msg = MSGS[i % MSGS.length]; i++;
    modo('wake');
    depois(function () { modo('dance'); pular(); }, 1300);
    depois(function () { modo('talk'); bubble.textContent = msg; bubble.classList.add('imo-show'); pular(); chamarZap(); }, 3000);
    depois(function () { bubble.classList.remove('imo-show'); modo('idle'); }, 9500);
    depois(function () { modo('lie'); }, 12000);
    depois(function () { modo('sleep'); }, 13000);
    depois(ciclo, CICLO);
  }
  function sincronizar() {
    var zap = document.querySelector('.zap-flutuante');
    var visivel = !!zap && !document.querySelector('dialog[open]') && !document.querySelector('[data-digitando]');
    if (visivel === ativo) return;
    ativo = visivel;
    montar();
    parar();
    bubble.classList.remove('imo-show');
    root.hidden = !visivel;
    if (visivel) { modo('sleep'); depois(ciclo, PRIMEIRA); }
  }
  /* Reage à rolagem: se estiver dormindo, acorda, dá um pulinho e volta a cochilar. */
  function reagir() {
    if (!ativo || !dormindo || Date.now() - ultimaReacao < 6000) return;
    ultimaReacao = Date.now();
    modo('wake'); pular();
    setTimeout(function () { if (ativo && spr.className.indexOf('imo--wake') >= 0) modo('sleep'); }, 1500);
  }
  function iniciar() {
    sincronizar();
    window.addEventListener('scroll', reagir, { passive: true });
    // O imovel.js redesenha a página, abre o visualizador e marca a digitação: acompanha tudo.
    new MutationObserver(sincronizar).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['hidden', 'open', 'data-digitando'] });
  }
  // Baixa a folha de sprites sem pressa, depois que a página carregou, para o cachorrinho já estar pronto quando aparecer.
  window.addEventListener('load', function () { setTimeout(function () { new Image().src = FOLHA; }, 1200); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
