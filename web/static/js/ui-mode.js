/* small module to toggle theme and de-emphasis, persists to localStorage */
(function(){
  const KEY_THEME = 'metri:theme'; // 'auto'|'dark'|'light'
  const KEY_DEEMPH = 'metri:deemphasized'; // 'true'|'false'

  function applyDeemphasis(val){
    if(val === 'true') {
      document.documentElement.setAttribute('data-deemphasized','true');
    } else {
      document.documentElement.removeAttribute('data-deemphasized');
    }
  }

  function applyTheme(theme){
    if(theme === 'dark') {
      document.documentElement.classList.add('theme-dark');
      document.documentElement.classList.remove('theme-light');
    } else if(theme === 'light') {
      document.documentElement.classList.add('theme-light');
      document.documentElement.classList.remove('theme-dark');
    } else {
      document.documentElement.classList.remove('theme-dark','theme-light');
    }
  }

  // init from storage
  const storedTheme = localStorage.getItem(KEY_THEME) || 'auto';
  const storedDeemph = localStorage.getItem(KEY_DEEMPH) || 'false';
  applyTheme(storedTheme);
  applyDeemphasis(storedDeemph);

  // expose simple API
  window.MetriUI = {
    setTheme: function(theme){
      localStorage.setItem(KEY_THEME, theme);
      applyTheme(theme);
    },
    setDeemphasized: function(flag){
      localStorage.setItem(KEY_DEEMPH, flag ? 'true':'false');
      applyDeemphasis(flag ? 'true':'false');
    },
    isDeemphasized: function(){
      return document.documentElement.getAttribute('data-deemphasized') === 'true';
    }
  };

  // Optional: wire up toggles if present in DOM
  document.addEventListener('click', function(e){
    if(e.target.matches('[data-toggle-deemph]')){
      const next = !(window.MetriUI.isDeemphasized());
      window.MetriUI.setDeemphasized(next);
    }
    if(e.target.matches('[data-theme]')){
      const theme = e.target.getAttribute('data-theme');
      window.MetriUI.setTheme(theme);
    }
  });
})();