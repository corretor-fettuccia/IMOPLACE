/* Página Anuncie: comodidades marcáveis e envio de exemplo */
$$('.chip').forEach(c => c.onclick = () => c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') !== 'true'));
$('#form').addEventListener('submit', e => {
  e.preventDefault();
  $('#ok').hidden = false;
  $('#ok').textContent = 'Exemplo: aqui o formulário seria enviado ao servidor para análise do anúncio.';
});
