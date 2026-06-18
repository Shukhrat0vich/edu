/**
 * EduAnalytics — Main JavaScript
 * Handles: sidebar toggle, dark mode, chart theme
 */

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar Toggle ─────────────────────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');
  const closeBtn = document.getElementById('sidebarClose');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggleBtn?.addEventListener('click', function () {
    if (window.innerWidth < 992) {
      openSidebar();
    }
  });

  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // Close sidebar on resize to desktop
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 992) {
      closeSidebar();
    }
  });

  // ── Dark Mode ──────────────────────────────────────────────────────────────
  const html = document.getElementById('htmlRoot');
  const darkToggle = document.getElementById('darkModeToggle');
  const darkIcon = document.getElementById('darkModeIcon');
  const DARK_KEY = 'edu_dark_mode';

  function applyDarkMode(dark) {
    if (dark) {
      html.setAttribute('data-bs-theme', 'dark');
      if (darkIcon) {
        darkIcon.className = 'bi bi-sun-fill';
      }
      localStorage.setItem(DARK_KEY, '1');
    } else {
      html.setAttribute('data-bs-theme', 'light');
      if (darkIcon) {
        darkIcon.className = 'bi bi-moon-stars-fill';
      }
      localStorage.removeItem(DARK_KEY);
    }
    // Update Chart.js default colors
    updateChartDefaults(dark);
  }

  function updateChartDefaults(dark) {
    if (typeof Chart !== 'undefined') {
      Chart.defaults.color = dark ? '#94a3b8' : '#64748b';
      Chart.defaults.borderColor = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    }
  }

  // Load saved preference
  const savedDark = localStorage.getItem(DARK_KEY) === '1';
  applyDarkMode(savedDark);

  darkToggle?.addEventListener('click', function () {
    const isDark = html.getAttribute('data-bs-theme') === 'dark';
    applyDarkMode(!isDark);
  });

  // ── Auto-dismiss alerts ────────────────────────────────────────────────────
  setTimeout(function () {
    document.querySelectorAll('.alert.fade').forEach(function (alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // ── Tooltips ───────────────────────────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // ── Active nav link highlighting ───────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(function (link) {
    if (link.href && link.href !== window.location.origin + '/') {
      const linkPath = new URL(link.href).pathname;
      if (currentPath.startsWith(linkPath) && linkPath !== '/') {
        link.classList.add('active');
      }
    }
  });
});
