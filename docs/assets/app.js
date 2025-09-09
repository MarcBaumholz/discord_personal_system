(function(){
  const root = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const STORAGE_KEY = 'bots-theme';

  function applyTheme(theme){
    if(theme === 'light') root.setAttribute('data-theme','light');
    else root.removeAttribute('data-theme');
    if(toggle){ toggle.textContent = theme === 'light' ? '🌙' : '☀️'; }
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if(stored){ applyTheme(stored); }
  else {
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    applyTheme(prefersLight ? 'light' : 'dark');
  }

  if(toggle){
    toggle.addEventListener('click', () => {
      const current = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next = current === 'light' ? 'dark' : 'light';
      localStorage.setItem(STORAGE_KEY, next);
      applyTheme(next);
    });
  }

  // Smooth scroll for same-page anchors
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if(!a) return;
    const id = a.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if(!el) return;
    e.preventDefault();
    el.scrollIntoView({behavior:'smooth', block:'start'});
  });

  // Auto-update timestamp functionality
  function updateLastModified() {
    const lastUpdatedElement = document.getElementById('lastUpdated');
    const pageLastUpdatedElement = document.getElementById('pageLastUpdated');
    
    // Get the last modified date from the document
    const lastModified = new Date(document.lastModified);
    
    // Format the date in a user-friendly way
    const options = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Berlin'
    };
    
    const formattedDate = lastModified.toLocaleDateString('de-DE', options);
    
    // Update main page timestamp
    if (lastUpdatedElement) {
      lastUpdatedElement.textContent = `Last Updated: ${formattedDate}`;
    }
    
    // Update bot detail page timestamp
    if (pageLastUpdatedElement) {
      pageLastUpdatedElement.textContent = formattedDate;
    }
  }

  // Update timestamp when page loads
  document.addEventListener('DOMContentLoaded', updateLastModified);
  
  // Also update immediately in case DOMContentLoaded already fired
  updateLastModified();
})();
