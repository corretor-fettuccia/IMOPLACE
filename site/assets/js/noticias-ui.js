'use strict';
for(const button of document.querySelectorAll('[data-news-category]'))button.addEventListener('click',()=>{
 for(const b of document.querySelectorAll('[data-news-category]'))b.classList.toggle('active',b===button);
 for(const card of document.querySelectorAll('.news-card'))card.hidden=!!button.dataset.newsCategory&&card.dataset.category!==button.dataset.newsCategory;
});
