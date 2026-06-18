/* ============================================================
 * SIDEBAR DIREITA — Favoritos & Histórico
 * Manual do Escriturário Escolar
 * ------------------------------------------------------------
 * Arquivo único que centraliza toda a lógica de favoritos e
 * histórico usada tanto no index.html (SPA) quanto nas páginas
 * externas (módulos como declaracoes_de_matricula.html).
 *
 * Por que este arquivo existe:
 * Antes, cada HTML tinha sua própria cópia (levemente diferente)
 * dessas funções. Isso causou dois bugs:
 *   1) Tabs da sidebar direita usando data-toggle (Bootstrap 4)
 *      enquanto o projeto carrega Bootstrap 5 (precisa ser
 *      data-bs-toggle) — por isso a URL mudava para #tab-fav/
 *      #tab-his mas o conteúdo da aba nunca trocava.
 *   2) Duplicação de updateFavoritesUI/updateHistoryUI com
 *      pequenas diferenças (ex: nomes de id diferentes em cada
 *      página), o que deixava o comportamento inconsistente.
 *
 * Como usar:
 * Inclua este arquivo com <script> DEPOIS do jQuery e do
 * bootstrap.bundle.min.js, e ANTES de qualquer script inline
 * que chame toggleFavorite/loadModule/etc.
 *
 *   <script src="assets/js/sidebar-direita.js"></script>
 *
 * O caminho do src deve respeitar a profundidade da página,
 * exatamente como já é feito com sidebar.html (ex: dentro de
 * Manual/procedimentos/algo/ ficaria
 *   ../../assets/js/sidebar-direita.js).
 *
 * O HTML da sidebar direita pode usar QUALQUER um dos dois
 * padrões de IDs abaixo — o script detecta automaticamente:
 *   Padrão A (index.html):      #tab-favorites-btn / #tab-favorites
 *                                 #tab-history-btn  / #tab-history
 *   Padrão B (páginas externas): #tab-fav / #tab-hist
 *                                 (gatilhos via data-bs-toggle="tab")
 * ============================================================ */

(function (window, document) {
  'use strict';

  // ------------------------------------------------------------
  // Estado (carregado do localStorage)
  // ------------------------------------------------------------
  var favorites = JSON.parse(localStorage.getItem('manual_favorites') || '[]');
  var history   = JSON.parse(localStorage.getItem('manual_history')   || '[]');

  // ------------------------------------------------------------
  // Helpers de persistência
  // ------------------------------------------------------------
  function saveFavorites() {
    localStorage.setItem('manual_favorites', JSON.stringify(favorites));
    updateFavoritesUI();
  }

  function saveHistory() {
    localStorage.setItem('manual_history', JSON.stringify(history));
    updateHistoryUI();
  }

  function getFavoritesCount() {
    return favorites.length;
  }

  // ------------------------------------------------------------
  // Índice de módulos (data/indice.json)
  // ------------------------------------------------------------
  // Usado para resolver a URL ABSOLUTA real de um módulo antes de
  // navegar. Isso é necessário porque, em páginas externas, um
  // simples "location.href = id + '.html'" é relativo à PASTA DA
  // PÁGINA ATUAL — então favoritar/navegar a partir de páginas em
  // pastas diferentes (ex: modulos/sere/ vs modulos/matricula/)
  // gerava URLs erradas como
  //   .../modulos/sere/declaracoes_de_matricula.html
  // quando o arquivo real está em
  //   .../modulos/matricula/declaracoes_de_matricula.html
  //
  // O caminho do indice.json varia com a profundidade da página:
  // no index.html (raiz) é 'data/indice.json'; nas páginas de
  // módulo (2 níveis abaixo) é '../../data/indice.json'.
  var indiceModulosCache = null;
  var indiceModulosPromise = null;

  function caminhoIndiceModulos() {
    // Todas as páginas externas de módulo ficam 2 níveis abaixo de
    // Manual/ (confirmado: sempre usam "../../sidebar.html" também),
    // por isso o caminho relativo é fixo aqui.
    return '../../data/indice.json';
  }

  function carregarIndiceModulos() {
    if (typeof window.garantirIndiceCarregado === 'function') {
      return window.garantirIndiceCarregado();
    }
    if (indiceModulosCache) return Promise.resolve(indiceModulosCache);
    if (indiceModulosPromise) return indiceModulosPromise;

    indiceModulosPromise = fetch(caminhoIndiceModulos())
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        indiceModulosCache = data;
        return data;
      });

    return indiceModulosPromise;
  }

  function buscarUrlNoIndice(moduleId, data) {
    var grupos = [
      data && data.procedimentos && data.procedimentos.itens,
      data && data.legislacoes && data.legislacoes.itens
    ];
    for (var g = 0; g < grupos.length; g++) {
      var lista = grupos[g];
      if (!lista) continue;
      for (var i = 0; i < lista.length; i++) {
        if (lista[i].id === moduleId) return lista[i].url;
      }
    }
    return null;
  }

  // ------------------------------------------------------------
  // Resolve o link de destino de um item (favorito ou histórico).
  // - Se existir window.loadModule (estamos no index.html / SPA),
  //   usamos ele para navegar sem reload de página (loadModule já
  //   resolve URLs externas corretamente via indice.json).
  // - Caso contrário (páginas externas autônomas), buscamos a URL
  //   ABSOLUTA real no indice.json antes de navegar. Só usamos o
  //   fallback relativo "id + '.html'" se o id não constar no
  //   índice (e avisamos no console, já que isso indica um item
  //   desatualizado ou fora do índice).
  // ------------------------------------------------------------
  // ------------------------------------------------------------
  // Fallback de loadModule() para páginas externas (não-index.html)
  // ------------------------------------------------------------
  // loadModule() "de verdade" só existe dentro do index.html, pois
  // depende do objeto `modules` e do #content-area do SPA. Só que o
  // sidebar.html é compartilhado por TODAS as páginas, e seus links
  // chamam onclick="loadModule('algumId')" diretamente — então, fora
  // do index.html, esse clique falhava silenciosamente (função
  // inexistente).
  //
  // Aqui criamos uma versão "de fora": primeiro tentamos resolver o
  // id no indice.json (mesma lógica do irParaModulo) — se for um
  // procedimento/legislação cadastrado, navegamos direto pra URL real,
  // sem dar a volta pelo index.html. Só quando o id NÃO está no índice
  // (ou seja, é um módulo interno só-SPA, como "documentos", "mapa",
  // "eca" etc.) é que redirecionamos para o index.html pedindo pra
  // abrir esse módulo.
  //
  // No próprio index.html, a função real (definida no script inline,
  // que carrega DEPOIS deste arquivo) sobrescreve este fallback — então
  // este bloco nunca chega a ser usado lá.
  function loadModuleFallbackExterno(moduleId) {
    carregarIndiceModulos()
      .then(function (data) {
        var url = buscarUrlNoIndice(moduleId, data);
        if (url) {
          window.location.href = url;
        } else {
          window.location.href = '../../index.html?modulo=' + encodeURIComponent(moduleId);
        }
      })
      .catch(function (err) {
        console.error('[sidebar-direita] falha ao carregar indice.json:', err);
        // Melhor esforço: assume que é um módulo interno do SPA.
        window.location.href = '../../index.html?modulo=' + encodeURIComponent(moduleId);
      });
  }

  if (typeof window.loadModule !== 'function') {
    window.loadModule = loadModuleFallbackExterno;
  }

  function irParaModulo(id) {
    if (typeof window.loadModule === 'function') {
      window.loadModule(id);
      return;
    }

    carregarIndiceModulos()
      .then(function (data) {
        var url = buscarUrlNoIndice(id, data);
        if (url) {
          window.location.href = url;
        } else {
          console.warn(
            '[sidebar-direita] id "' + id + '" não encontrado em indice.json; ' +
            'usando caminho relativo como fallback (pode apontar para a pasta errada).'
          );
          window.location.href = id + '.html';
        }
      })
      .catch(function (err) {
        console.error('[sidebar-direita] falha ao carregar indice.json:', err);
        // Fallback: ao menos tenta navegar, mesmo sabendo que pode
        // resolver para a pasta errada se a página atual não for a
        // mesma pasta do destino.
        window.location.href = id + '.html';
      });
  }
  window.irParaModulo = irParaModulo;

  // ------------------------------------------------------------
  // Favoritos
  // ------------------------------------------------------------
  function toggleFavorite(moduleId, title) {
    var index = favorites.findIndex(function (f) { return f.id === moduleId; });
    if (index > -1) {
      favorites.splice(index, 1);
      showToast('Removido dos favoritos', 'info');
    } else {
      favorites.push({ id: moduleId, title: title });
      showToast('Adicionado aos favoritos', 'success');
    }
    saveFavorites();
    updateFavoriteStar(moduleId);
  }

  // Atualiza visualmente TODAS as estrelas (cabeçalho, card,
  // botão "Favoritar" etc.) referentes a um módulo específico.
  function updateFavoriteStar(moduleId) {
    var isFavorite = favorites.some(function (f) { return f.id === moduleId; });
    document.querySelectorAll('.btn-favorite[data-module="' + moduleId + '"]').forEach(function (el) {
      // Usamos uma classe própria (favorito-marcado) em vez de "active"
      // porque "active" é reservada pelo Bootstrap para o estado
      // "pressionado" de botões (.btn.active fica com fundo sólido),
      // o que pintava o botão inteiro de amarelo em vez de só o ícone.
      el.classList.toggle('favorito-marcado', isFavorite);
      var icon = el.matches('i') ? el : el.querySelector('i');
      if (icon) {
        icon.classList.toggle('text-warning', isFavorite);
      }
    });
  }

  // CSS mínimo para o estado "favoritado" funcionar mesmo em páginas
  // que não tenham a regra .favorito-marcado já definida no <style>.
  (function injetarCSSFavorito() {
    if (document.getElementById('sidebar-direita-css')) return;
    var style = document.createElement('style');
    style.id = 'sidebar-direita-css';
    style.textContent =
      '.btn-favorite.favorito-marcado{color:var(--warning-color,#ffc107);}' +
      '.btn-favorite.favorito-marcado i{color:var(--warning-color,#ffc107);}' +
      // Para botões do Bootstrap (outline-warning), só troca a cor do
      // ícone/texto, sem preencher o fundo (isso é o que .active fazia
      // errado antes).
      '.btn.btn-favorite.favorito-marcado{background-color:transparent;}';
    document.head.appendChild(style);
  })();

  // Atualiza o estado de TODAS as estrelas presentes na página
  // (útil quando vários módulos/cards estão visíveis ao mesmo
  // tempo, como acontece no index.html).
  function updateAllFavoriteStars() {
    document.querySelectorAll('.btn-favorite').forEach(function (el) {
      var moduleId = el.getAttribute('data-module');
      if (moduleId) updateFavoriteStar(moduleId);
    });
  }

  function renderListaFavoritos() {
    var container = document.getElementById('favorites-list');
    var btnLimpar = document.getElementById('btn-clear-favorites');
    if (!container) return;

    if (favorites.length === 0) {
      container.innerHTML = '<i class="fas fa-star fa-2x mb-2 d-block"></i>Nenhum favorito ainda.';
      if (btnLimpar) btnLimpar.style.display = 'none';
      return;
    }

    container.innerHTML = favorites.map(function (fav) {
      return '<div class="favorite-item" data-go="' + escapeAttr(fav.id) + '">' +
               '<i class="fas fa-star text-warning"></i> ' + escapeHtml(fav.title) +
             '</div>';
    }).join('');

    if (btnLimpar) btnLimpar.style.display = '';
  }

  function updateFavoritesUI() {
    // Contadores (presentes só no index.html, mas é seguro
    // chamar mesmo quando os elementos não existem)
    var countBadge = document.getElementById('favorites-count');
    if (countBadge) countBadge.textContent = favorites.length;

    var dashboardCount = document.getElementById('dashboard-favorites-count');
    if (dashboardCount) dashboardCount.textContent = favorites.length;

    renderListaFavoritos();
    updateAllFavoriteStars();
  }

  function clearFavorites() {
    if (confirm('Deseja limpar todos os favoritos?')) {
      favorites = [];
      saveFavorites();
      showToast('Favoritos limpos', 'info');
    }
  }

  // ------------------------------------------------------------
  // Histórico
  // ------------------------------------------------------------
  function addToHistory(moduleId, title) {
    history = history.filter(function (h) { return h.id !== moduleId; });
    history.unshift({ id: moduleId, title: title, timestamp: new Date().toISOString() });
    if (history.length > 20) history.pop();
    saveHistory();
  }

  function renderListaHistorico() {
    var container = document.getElementById('history-list');
    var btnLimpar = document.getElementById('btn-clear-history');
    if (!container) return;

    if (history.length === 0) {
      container.innerHTML = '<i class="fas fa-history fa-2x mb-2 d-block"></i>Seu histórico aparecerá aqui.';
      if (btnLimpar) btnLimpar.style.display = 'none';
      return;
    }

    container.innerHTML = history.slice(0, 10).map(function (h) {
      return '<div class="history-item" data-go="' + escapeAttr(h.id) + '">' +
               '<i class="fas fa-history"></i> ' + escapeHtml(h.title) +
             '</div>';
    }).join('');

    if (btnLimpar) btnLimpar.style.display = '';
  }

  function updateHistoryUI() {
    renderListaHistorico();
  }

  function clearHistory() {
    if (confirm('Deseja limpar o histórico?')) {
      history = [];
      saveHistory();
      showToast('Histórico limpo', 'info');
    }
  }

  // ------------------------------------------------------------
  // Pequenos helpers de segurança/escape (evita HTML injection
  // caso algum título de módulo venha com caracteres especiais)
  // ------------------------------------------------------------
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  function escapeAttr(str) {
    return String(str).replace(/"/g, '&quot;');
  }

  // ------------------------------------------------------------
  // Delegação de clique para os itens de favoritos/histórico.
  // Usamos delegação (no document) em vez de onclick inline
  // porque o conteúdo é recriado dinamicamente via innerHTML;
  // isso também evita problemas de propagação de evento que
  // causavam o "desmarcar ao clicar".
  // ------------------------------------------------------------
  document.addEventListener('click', function (e) {
    var item = e.target.closest('.favorite-item, .history-item');
    if (!item) return;
    e.preventDefault();
    e.stopPropagation();
    var id = item.getAttribute('data-go');
    if (id) irParaModulo(id);
  });

  // ------------------------------------------------------------
  // Toast simples de feedback
  // ------------------------------------------------------------
  function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toast-container');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.innerHTML = (type === 'success' ? '✓' : 'ℹ️') + ' ' + escapeHtml(message);
    container.appendChild(toast);
    setTimeout(function () {
      toast.style.transition = 'opacity .3s';
      toast.style.opacity = '0';
      setTimeout(function () { toast.remove(); }, 300);
    }, 3000);
  }

  // ------------------------------------------------------------
  // Inicialização das ABAS da sidebar direita (Favoritos/Histórico)
  // ------------------------------------------------------------
  // Suporta os dois padrões de markup existentes hoje no projeto:
  //   A) index.html:        #tab-favorites-btn / #tab-history-btn
  //   B) páginas externas:  links com href="#tab-fav" / "#tab-hist"
  //
  // Garantimos que TODOS os links de aba dentro da sidebar direita
  // usem data-bs-toggle="tab" (Bootstrap 5). Se algum HTML antigo
  // ainda tiver data-toggle="tab" (Bootstrap 4), corrigimos em
  // tempo de execução para não depender de editar todos os HTMLs
  // de uma vez.
  function inicializarTabsSidebarDireita(escopo) {
    var raiz = escopo || document;
    var links = raiz.querySelectorAll('#right-sidebar [data-toggle="tab"], #right-sidebar [data-bs-toggle="tab"]');

    links.forEach(function (link) {
      // Normaliza para o atributo que o Bootstrap 5 realmente lê
      if (link.hasAttribute('data-toggle') && !link.hasAttribute('data-bs-toggle')) {
        link.setAttribute('data-bs-toggle', 'tab');
      }
    });

    // Deixa o Bootstrap 5 inicializar (ou reconhecer) os tab triggers
    if (window.bootstrap && window.bootstrap.Tab) {
      links.forEach(function (link) {
        window.bootstrap.Tab.getOrCreateInstance(link);
      });
    }
  }
  window.inicializarTabsSidebarDireita = inicializarTabsSidebarDireita;

  // Abre a sidebar direita (control-sidebar do AdminLTE) e
  // seleciona a aba desejada ('favorites' ou 'history').
  function abrirSidebarDireita(aba) {
    var body = document.body;
    var csWidget = window.jQuery && window.jQuery('[data-widget="control-sidebar"]').data('lte.controlsidebar');

    if (!body.classList.contains('control-sidebar-slide-open')) {
      if (csWidget && window.jQuery) {
        window.jQuery('[data-widget="control-sidebar"]').ControlSidebar('show');
      } else {
        body.classList.add('control-sidebar-slide-open');
      }
    }

    setTimeout(function () {
      // Tenta os dois padrões de id possíveis para o botão da aba
      var btnId = aba === 'history' ? 'tab-history-btn' : 'tab-favorites-btn';
      var btn = document.getElementById(btnId);

      if (!btn) {
        // Padrão B (páginas externas): seleciona pelo href
        var href = aba === 'history' ? '#tab-hist' : '#tab-fav';
        btn = document.querySelector('#right-sidebar a[href="' + href + '"]');
      }

      if (btn && window.bootstrap && window.bootstrap.Tab) {
        window.bootstrap.Tab.getOrCreateInstance(btn).show();
      } else if (btn) {
        btn.click();
      }
    }, 50);
  }
  window.abrirSidebarDireita = abrirSidebarDireita;

  // Liga os botões da navbar superior (estrela / relógio) que
  // abrem a sidebar direita em cada aba.
  function ligarBotoesAbrirSidebar() {
    var btnFav = document.getElementById('btn-toggle-favorites');
    if (btnFav) {
      btnFav.addEventListener('click', function (e) {
        e.preventDefault();
        abrirSidebarDireita('favorites');
      });
    }

    var btnHist = document.getElementById('btn-toggle-history');
    if (btnHist) {
      btnHist.addEventListener('click', function (e) {
        e.preventDefault();
        abrirSidebarDireita('history');
      });
    }
  }

  // ------------------------------------------------------------
  // Expõe globalmente (mantém compatibilidade com onclick="" que
  // ainda existam nos HTMLs, ex: onclick="toggleFavorite(...)")
  // ------------------------------------------------------------
  window.toggleFavorite     = toggleFavorite;
  window.updateFavoriteStar = updateFavoriteStar;
  window.updateFavoritesUI  = updateFavoritesUI;
  window.clearFavorites     = clearFavorites;
  window.addToHistory       = addToHistory;
  window.updateHistoryUI    = updateHistoryUI;
  window.clearHistory       = clearHistory;
  window.showToast          = showToast;
  window.getFavoritesCount  = getFavoritesCount;

  // ------------------------------------------------------------
  // Auto-inicialização
  // ------------------------------------------------------------
  // Roda assim que o DOM estiver pronto. Isso cobre a maioria das
  // páginas externas (onde a sidebar direita já está no HTML
  // estático). No index.html, a sidebar ESQUERDA é carregada via
  // $.load('sidebar.html'), mas a sidebar DIREITA (#right-sidebar)
  // já está no HTML principal, então este DOMContentLoaded também
  // a cobre.
  document.addEventListener('DOMContentLoaded', function () {
    updateFavoritesUI();
    updateHistoryUI();
    inicializarTabsSidebarDireita();
    ligarBotoesAbrirSidebar();
  });

})(window, document);