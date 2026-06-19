
/* ============================================================
   DARK MODE — Manual do Escriturário Escolar
   Aplica o tema salvo IMEDIATAMENTE (evita "flash" de tela clara)
   e injeta o botão de alternância na navbar de qualquer página.
   Inclua este arquivo com <script> normal (não precisa de defer/async)
   logo após abrir a tag <head> ou no topo do <body>, antes do CSS
   carregar, para o efeito de "sem flash" funcionar melhor — mas ele
   funciona corretamente em qualquer posição do documento.
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'manual-theme';

  function getTema() {
    return localStorage.getItem(STORAGE_KEY) || 'light';
  }

  function aplicarTema(tema) {
    document.documentElement.setAttribute('data-theme', tema);
  }

  // Aplica imediatamente, antes do DOM terminar de carregar.
  aplicarTema(getTema());

  function alternarTema() {
    var atual = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    var novo = atual === 'dark' ? 'light' : 'dark';
    aplicarTema(novo);
    localStorage.setItem(STORAGE_KEY, novo);
  }

  function criarBotao() {
    var li = document.createElement('li');
    li.className = 'nav-item';

    var a = document.createElement('a');
    a.href = '#';
    a.className = 'nav-link dark-mode-toggle-btn';
    a.title = 'Alternar modo claro/escuro';
    a.setAttribute('role', 'button');
    a.innerHTML = '<i class="fas fa-moon"></i><i class="fas fa-sun"></i>';
    a.addEventListener('click', function (e) {
      e.preventDefault();
      alternarTema();
    });

    li.appendChild(a);
    return li;
  }

  function injetarBotao() {
    // Evita duplicar se o script for incluído mais de uma vez.
    if (document.querySelector('.dark-mode-toggle-btn')) return;

    // Tenta encaixar dentro da navbar superior do AdminLTE.
    var navbarDireita = document.querySelector('.main-header .navbar-nav.ms-auto, .main-header .navbar-nav.ml-auto');
    if (navbarDireita) {
      navbarDireita.insertBefore(criarBotao(), navbarDireita.firstChild);
      return;
    }

    var navbar = document.querySelector('.main-header .navbar-nav');
    if (navbar) {
      navbar.appendChild(criarBotao());
      return;
    }

    // Fallback: páginas sem a navbar padrão (ex.: páginas avulsas de
    // procedimento) recebem um botão flutuante no canto da tela.
    var btn = document.createElement('button');
    btn.className = 'dark-mode-toggle-btn btn btn-sm btn-secondary';
    btn.title = 'Alternar modo claro/escuro';
    btn.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;border-radius:50%;width:44px;height:44px;';
    btn.innerHTML = '<i class="fas fa-moon"></i><i class="fas fa-sun"></i>';
    btn.addEventListener('click', alternarTema);
    document.body.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injetarBotao);
  } else {
    injetarBotao();
  }

  // Caso a sidebar/navbar seja carregada via $.load() depois do DOMContentLoaded
  // (como acontece no index.html), tentamos novamente após um pequeno delay.
  window.addEventListener('load', function () {
    setTimeout(injetarBotao, 300);
  });

  window.alternarTemaManual = alternarTema;
})();