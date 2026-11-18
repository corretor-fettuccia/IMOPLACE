/* Imoplace 3.4.2 — formulário de contato da ficha. */
(function () {
  'use strict';

  const config = {
    "endpoint": "https://script.google.com/macros/s/AKfycbxxA_8OOrK8oSJk6dFSC4bSvIHxICKLYG6ZpalORyFnM5fe-I4eLil-KGsKyoD31NMWlg/exec",
    "product": "Imoplace - [codigoimovel]",
    "successMessage": "Nosso consultor entrará em contato!",
    "quickTitle": "Antes de finalizar, só me confirma rapidinho…",
    "confirmText": "Concluir envio",
    "questions": [
      {
        "label": "Qual é o seu objetivo?",
        "options": [
          "Moradia",
          "Investimento"
        ]
      },
      {
        "label": "Em qual momento está a sua procura?",
        "options": [
          "Imediata",
          "Já tenho decisão tomada",
          "Próximos meses",
          "Só pesquisando"
        ]
      },
      {
        "label": "O que é mais importante para você agora?",
        "options": [
          "Valores e condições",
          "Localização",
          "Projeto e diferenciais",
          "Potencial de investimento",
          "Sem envolver banco"
        ]
      },
      {
        "label": "Prefere o contato em qual período?",
        "options": [
          "Manhã",
          "Almoço",
          "Tarde",
          "Noite"
        ]
      }
    ]
  };

  function mount(root) {
    const slot = root.querySelector('[data-lead-property]');
    if (!slot || slot.dataset.leadMounted || !/^[A-Za-z0-9_-]{1,80}$/.test(slot.dataset.leadProperty)) return;
    slot.dataset.leadMounted = 'true';
    slot.innerHTML = `
      <form aria-labelledby="contact-title" autocomplete="on">
        <h2 id="contact-title">Prefere receber um contato?</h2>
        <input name="nome" autocomplete="name" aria-label="Nome" placeholder="Nome" required>
        <input name="email" autocomplete="email" type="email" aria-label="E-mail" placeholder="E-mail" required>
        <input name="telefone" autocomplete="tel" type="tel" aria-label="Telefone" placeholder="Telefone" required>
        <textarea name="msg" aria-label="Mensagem opcional" placeholder="Mensagem (opcional)" rows="1"></textarea>
        <button class="btn btn-accent" type="submit" disabled>Solicitar contato</button>
      </form>
      <p id="status" role="status"></p>
      <dialog class="imoplace-lead-dialog" aria-labelledby="qualification-title">
        <h2 id="qualification-title"></h2>
        <form id="qualification">
          <div id="questions"></div>
          <div class="actions">
            <button class="btn btn-line cancel" type="button">Voltar</button>
            <button class="btn btn-accent" type="submit" id="confirm"></button>
          </div>
          <p id="qualification-status" role="status" hidden></p>
        </form>
      </dialog>`;
    const lead = slot.querySelector('form');
    const leadButton = lead.querySelector('button[type="submit"]');
    const status = slot.querySelector('#status');
    const dialog = slot.querySelector('dialog');
    const qualification = slot.querySelector('#qualification');
    const qualificationStatus = slot.querySelector('#qualification-status');
    const confirmButton = slot.querySelector('#confirm');
    const backButton = qualification.querySelector('.cancel');
    const propertyId = slot.dataset.leadProperty;
    let sending = false;

    dialog.querySelector('#qualification-title').textContent = config.quickTitle;
    confirmButton.textContent = config.confirmText;
    leadButton.disabled = false;
    lead.elements.telefone.addEventListener('input', () => lead.elements.telefone.setCustomValidity(''));

    const questions = slot.querySelector('#questions');
    config.questions.forEach((question, index) => {
      const group = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = question.label;
      const options = document.createElement('div');
      options.className = 'imoplace-lead-options';
      group.append(legend, options);
      for (const option of question.options) {
        const label = document.createElement('label');
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'question_' + index;
        radio.value = option;
        radio.required = true;
        label.append(radio, option);
        options.append(label);
      }
      questions.append(group);
    });

    function buildPayload() {
      const data = new FormData(lead);
      for (const name of ['nome', 'email', 'telefone', 'msg']) {
        data.set(name, String(data.get(name) ?? '').trim());
      }
      data.set('produto', config.product.replace('[codigoimovel]', () => propertyId));
      data.set('codigoimovel', propertyId);
      data.set('dataHora', new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }));
      const answers = new FormData(qualification);
      const blocks = config.questions.map((question, index) => {
        const block = question.label + '\n' + answers.get('question_' + index) + ';';
        data.set('qualificacao_' + (index + 1), block);
        return block;
      });
      if (blocks.length) {
        const complement = blocks.join('\n\n');
        data.set('complementacaoRapida', complement);
        data.set('msg', [data.get('msg'), 'Informações complementares:', complement].filter(Boolean).join('\n\n'));
      }
      return data;
    }

    async function sendLead() {
      if (sending || !lead.reportValidity()) return;
      sending = true;
      leadButton.disabled = confirmButton.disabled = backButton.disabled = true;
      qualificationStatus.hidden = true;
      const payload = buildPayload();
      status.textContent = 'Enviando…';
      if (dialog.open) {
        qualificationStatus.textContent = 'Enviando…';
        qualificationStatus.hidden = false;
      }
      try {
        const response = await fetch(config.endpoint, { method: 'POST', body: payload, credentials: 'omit' });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const body = (await response.text()).trim();
        if (!body || body.startsWith('<')) throw new Error('Resposta inesperada da API');
        if (body.startsWith('{')) {
          const result = JSON.parse(body);
          if (result.ok === false || result.success === false || result.error ||
              ['error', 'erro', 'failed', 'failure'].includes(String(result.status).toLowerCase())) {
            throw new Error('API recusou o envio');
          }
        } else if (/^(erro|error|falha)\b/i.test(body)) {
          throw new Error('API recusou o envio');
        }
        if (dialog.open) dialog.close();
        lead.reset();
        qualification.reset();
        status.textContent = config.successMessage;
        // Analytics recebe apenas o ID público do imóvel, depois da confirmação.
        try {
          window.ImoplaceTracking?.track?.('generate_lead', { property_id: propertyId });
          window.ImoplaceTracking?.meta?.('Lead', { content_ids: [propertyId] });
        } catch (error) {
          console.warn('Imoplace: falha ao registrar o evento de lead.', error);
        }
        status.tabIndex = -1;
        status.focus();
      } catch {
        const message = 'Não foi possível confirmar o envio. Seus dados estão preenchidos para nova tentativa.';
        status.textContent = message;
        qualificationStatus.textContent = message;
        qualificationStatus.hidden = false;
      } finally {
        sending = false;
        leadButton.disabled = confirmButton.disabled = backButton.disabled = false;
      }
    }

    lead.addEventListener('submit', event => {
      event.preventDefault();
      if (sending || dialog.open) return;
      const phone = lead.elements.telefone;
      const digits = phone.value.replace(/\D/g, '');
      const validPhone = /^\d{10,11}$/.test(digits) || /^55\d{10,11}$/.test(digits);
      phone.setCustomValidity(validPhone ? '' : 'Informe um telefone com DDD.');
      if (!lead.reportValidity()) return;
      if (!lead.elements.nome.value.trim()) {
        status.textContent = 'Preencha o nome.';
        lead.elements.nome.focus();
        return;
      }
      status.textContent = '';
      qualificationStatus.hidden = true;
      dialog.showModal();
    });
    qualification.addEventListener('submit', event => {
      event.preventDefault();
      void sendLead();
    });
    backButton.addEventListener('click', () => dialog.close());
    dialog.addEventListener('cancel', event => {
      if (sending) event.preventDefault();
    });
    slot.hidden = false;
  }

  window.ImoplaceLead = { mount };
})();
