// =========================================================
// LEXIGUARD GLOBAL APP HELPER, THEME & SIDEBAR SYSTEM
// =========================================================

window.LexiGuard = window.LexiGuard || {};

/**
 * Enhanced Toast Notification System
 * @param {string} message 
 * @param {string} type - 'info' | 'success' | 'error' | 'warning'
 * @param {number} duration - duration in ms (default: 4500ms)
 */
window.LexiGuard.showToast = function(message, type = 'info', duration = 4500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
    }

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    const iconStr = icons[type] || 'ℹ';
    const roleAttr = (type === 'error' || type === 'warning') ? 'role="alert"' : 'role="status"';

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', roleAttr === 'role="alert"' ? 'alert' : 'status');
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-weight: 700; font-size: 15px;">${iconStr}</span>
            <span>${message}</span>
        </div>
        <button type="button" class="toast-close-btn" aria-label="Close notification" onclick="this.closest('.toast').remove()">×</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.2s ease';
            setTimeout(() => toast.remove(), 200);
        }
    }, duration);
};

/**
 * Theme System Management (Light / Dark mode)
 */
window.LexiGuard.initTheme = function() {
    const savedTheme = localStorage.getItem('lexiguard_theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (systemDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', currentTheme);
    window.LexiGuard.updateThemeToggleIcon(currentTheme);
};

window.LexiGuard.toggleTheme = function() {
    const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const nextTheme = activeTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('lexiguard_theme', nextTheme);
    window.LexiGuard.updateThemeToggleIcon(nextTheme);

    window.LexiGuard.showToast(`Switched to ${nextTheme === 'dark' ? 'Dark' : 'Light'} Mode`, 'info', 2000);
};

window.LexiGuard.updateThemeToggleIcon = function(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
        btn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`);
        btn.setAttribute('title', `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`);
    }
};

/**
 * Collapsible Sidebar & Mobile Drawer System
 */
window.LexiGuard.initSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const mainWrapper = document.querySelector('.main-wrapper');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const mobileBtn = document.getElementById('sidebarToggleBtn') || document.getElementById('sidebarToggle');
    let overlay = document.querySelector('.sidebar-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    // Restore desktop collapsed state
    const isCollapsed = localStorage.getItem('lexiguard_sidebar_collapsed') === 'true';
    if (isCollapsed && sidebar && window.innerWidth > 768) {
        sidebar.classList.add('collapsed');
        if (mainWrapper) mainWrapper.classList.add('sidebar-collapsed');
    }

    // Desktop Collapse Toggle
    if (collapseBtn && sidebar) {
        collapseBtn.addEventListener('click', () => {
            const collapsed = sidebar.classList.toggle('collapsed');
            if (mainWrapper) mainWrapper.classList.toggle('sidebar-collapsed', collapsed);
            localStorage.setItem('lexiguard_sidebar_collapsed', collapsed ? 'true' : 'false');
            collapseBtn.setAttribute('aria-expanded', !collapsed);
        });
    }

    // Mobile Drawer Toggle
    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', () => {
            const isOpen = sidebar.classList.toggle('open');
            overlay.classList.toggle('active', isOpen);
            mobileBtn.setAttribute('aria-expanded', isOpen);
        });
    }

    // Close mobile drawer when clicking overlay
    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    // ESC Key listener to close mobile drawer & active modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (sidebar && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('active');
            }
        }
    });

    // Add tooltips to navigation links for collapsed sidebar mode
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        const textSpan = link.querySelector('span:not(.nav-icon)');
        if (textSpan && textSpan.textContent.trim()) {
            link.setAttribute('data-tooltip', textSpan.textContent.trim());
        }
    });
};

/**
 * Format document list to append version suffixes for duplicate filenames.
 * Example: Agreement.pdf, Agreement.pdf (2), Agreement.pdf (3)
 * Preserves original filename, document_id, and metadata intact.
 */
window.LexiGuard.formatDocumentDisplayLabels = function(documents) {
    if (!Array.isArray(documents)) return [];

    const nameCounts = {};
    documents.forEach(doc => {
        if (!doc || !doc.filename) return;
        const fn = String(doc.filename);
        nameCounts[fn] = (nameCounts[fn] || 0) + 1;
    });

    const tracker = {};
    return documents.map(doc => {
        if (!doc || !doc.filename) return doc;
        const fn = String(doc.filename);
        if (nameCounts[fn] > 1) {
            tracker[fn] = (tracker[fn] || 0) + 1;
            const idx = tracker[fn];
            const displayLabel = idx === 1 ? fn : `${fn} (${idx})`;
            return Object.assign({}, doc, { display_filename: displayLabel });
        }
        return Object.assign({}, doc, { display_filename: fn });
    });
};

/**
 * Multi-stage progress status tracker helper for async tasks (Analysis / Comparison).
 * Truthfully displays staged status steps without fake percentage numbers.
 */
window.LexiGuard.createProgressTracker = function(statusElement, stages, intervalMs = 1500) {
    if (!statusElement || !Array.isArray(stages) || stages.length === 0) {
        return { stop: () => {}, complete: () => {}, error: () => {} };
    }

    let currentIndex = 0;
    statusElement.setAttribute('aria-live', 'polite');

    function renderStage(idx) {
        if (idx < stages.length) {
            statusElement.innerHTML = `
                <span class="btn-loading" style="display: inline-block; margin-right: 6px;"></span>
                <span>${stages[idx]}</span>
            `;
        }
    }

    renderStage(0);

    const timer = setInterval(() => {
        if (currentIndex < stages.length - 1) {
            currentIndex++;
            renderStage(currentIndex);
        }
    }, intervalMs);

    return {
        stop: () => clearInterval(timer),
        complete: (successMessage = "Analysis complete") => {
            clearInterval(timer);
            statusElement.innerHTML = `
                <span style="color: #10B981; font-weight: 600;">✓ ${successMessage}</span>
            `;
        },
        error: (errorMessage = "Analysis failed — please try again.") => {
            clearInterval(timer);
            statusElement.innerHTML = `
                <span style="color: #EF4444; font-weight: 600;">✕ ${errorMessage}</span>
            `;
        }
    };
};

// Initialize Theme & Sidebar on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    window.LexiGuard.initTheme();
    window.LexiGuard.initSidebar();

    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', window.LexiGuard.toggleTheme);
    }
});

