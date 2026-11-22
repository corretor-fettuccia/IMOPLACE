/* Imóveis relacionados nas notícias: setas do carrossel e card que desliza durante a leitura. */
(function(){
  const sec=document.querySelector('.rel-imoveis');if(!sec)return;
  const faixa=sec.querySelector('.rel-faixa'),setas=sec.querySelector('.rel-setas');
  // Setas só no computador e só quando há o que rolar.
  function atualizar(){
    const rola=faixa.scrollWidth>faixa.clientWidth+4;
    setas.hidden=!rola||matchMedia('(max-width: 640px)').matches;
    const [ant,prox]=setas.querySelectorAll('.rel-seta');
    ant.disabled=faixa.scrollLeft<4;prox.disabled=faixa.scrollLeft+faixa.clientWidth>=faixa.scrollWidth-4;
  }
  setas.addEventListener('click',e=>{
    const b=e.target.closest('.rel-seta');if(!b)return;
    const card=faixa.querySelector('.rel-card');const passo=card?card.getBoundingClientRect().width+16:300;
    faixa.scrollBy({left:passo*Number(b.dataset.relDir),behavior:'smooth'});
  });
  faixa.addEventListener('scroll',atualizar,{passive:true});addEventListener('resize',atualizar);atualizar();

  const mini=document.querySelector('.rel-mini'),corpo=document.querySelector('.article-body');
  if(!mini||!corpo||!('IntersectionObserver' in window))return;
  const CHAVE='imoplace-rel-mini-fechado';
  let fechado=false;try{fechado=sessionStorage.getItem(CHAVE)==='1'}catch(e){}
  let passouMetade=false,carrosselVisto=false;
  function mostrar(v){
    if(v){mini.hidden=false;requestAnimationFrame(()=>mini.classList.add('visivel'));}
    else{mini.classList.remove('visivel');mini.hidden=true;}
  }
  function decidir(){mostrar(!fechado&&passouMetade&&!carrosselVisto);}
  function medir(){
    const r=corpo.getBoundingClientRect();
    passouMetade=r.top+r.height/2<innerHeight; // metade do texto já passou pela tela
    decidir();
  }
  // Some quando o carrossel do rodapé aparece: não mostra o mesmo imóvel duas vezes.
  new IntersectionObserver(es=>{carrosselVisto=es.some(e=>e.isIntersecting)||sec.getBoundingClientRect().top<innerHeight;decidir();}).observe(sec);
  addEventListener('scroll',medir,{passive:true});medir();
  mini.querySelector('.rel-mini-fechar').addEventListener('click',()=>{fechado=true;try{sessionStorage.setItem(CHAVE,'1')}catch(e){}mostrar(false);});
})();
