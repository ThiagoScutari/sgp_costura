// SGP Costura - Unified Layout System with Sidebar Navigation
// Automatically injects navigation and applies role-based access control

const LAYOUT_CONFIG = {
    logoText: "DRX Têxtil",
    logoSubtext: "SGP Costura",

    // Navigation items with role-based access
    navItems: [
        {
            id: "dashboard",
            label: "Dashboard BI",
            icon: "analytics",
            path: "../page_07/page_07.html",
            roles: ["admin", "supervisor"]
        },
        {
            id: "gestao",
            label: "Gestão de OPs",
            icon: "inventory_2",
            path: "../page_03/page_03.html",
            roles: ["admin", "supervisor"]
        },
        {
            id: "cockpit",
            label: "Cockpit VAC",
            icon: "tune",
            path: "../page_04/page_04.html",
            roles: ["admin", "supervisor"]
        },
        {
            id: "monitor",
            label: "Monitor de Fábrica",
            icon: "monitor",
            path: "../page_01/page_01.html",
            roles: ["admin", "supervisor", "operator"]
        },
        {
            id: "checklist",
            label: "Checklist Final",
            icon: "checklist",
            path: "../page_05/page_05.html",
            roles: ["admin", "supervisor", "operator"]
        },
        {
            id: "config",
            label: "Configurações",
            icon: "settings",
            path: "../page_06/page_06.html",
            roles: ["admin"]
        }
    ]
};

// Initialize layout on page load
function initLayout() {
    // Ensure user is authenticated
    if (!isAuthenticated()) {
        window.location.href = '../login/login.html';
        return;
    }

    const user = getCurrentUser();

    // Inject sidebar
    injectSidebar(user);

    // Highlight active page
    highlightActivePage();
}

// Inject sidebar navigation
function injectSidebar(user) {
    // Create flexbox container for layout
    const layoutContainer = document.createElement('div');
    layoutContainer.className = 'sgp-layout-container';

    const sidebar = document.createElement('aside');
    sidebar.id = 'sgp-sidebar';
    sidebar.className = 'sgp-sidebar';

    // Check saved state
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }

    sidebar.innerHTML = `
        <!-- Toggle Button -->
        <button class="sidebar-toggle" onclick="toggleSidebar()" title="Ocultar/Mostrar Menu">
            <span class="material-symbols-outlined">menu</span>
        </button>
        
        <!-- Logo Section -->
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <span class="material-symbols-outlined logo-icon">factory</span>
                <div class="logo-text">
                    <div class="logo-title">${LAYOUT_CONFIG.logoText}</div>
                    <div class="logo-subtitle">${LAYOUT_CONFIG.logoSubtext}</div>
                </div>
            </div>
        </div>
        
        <!-- Navigation -->
        <nav class="sidebar-nav">
            ${generateNavItems(user.role)}
        </nav>
        
        <!-- User Section -->
        <div class="sidebar-footer">
            <div class="user-info">
                <span class="material-symbols-outlined user-icon">account_circle</span>
                <div class="user-details">
                    <div class="user-name">${user.username}</div>
                    <div class="user-role">${getRoleLabel(user.role)}</div>
                </div>
            </div>
            <button onclick="logout()" class="logout-btn">
                <span class="material-symbols-outlined">logout</span>
                <span class="logout-text">Sair</span>
            </button>
        </div>
    `;

    // Move all body content into layout container
    const mainContent = document.createElement('main');
    mainContent.className = 'sgp-main-content';

    // Move existing body children to main content
    while (document.body.firstChild) {
        mainContent.appendChild(document.body.firstChild);
    }

    // Build layout: sidebar + main content
    layoutContainer.appendChild(sidebar);
    layoutContainer.appendChild(mainContent);

    // Add layout container to body
    document.body.appendChild(layoutContainer);

    // Inject sidebar styles
    injectSidebarStyles();
}

// Toggle sidebar collapse/expand
function toggleSidebar() {
    const sidebar = document.getElementById('sgp-sidebar');

    sidebar.classList.toggle('collapsed');
    const isCollapsed = sidebar.classList.contains('collapsed');

    // Save state
    localStorage.setItem('sidebar-collapsed', isCollapsed);
}

// Generate navigation items based on user role
function generateNavItems(userRole) {
    return LAYOUT_CONFIG.navItems
        .filter(item => item.roles.includes(userRole))
        .map(item => `
            <a href="${item.path}" class="nav-item" data-page="${item.id}">
                <span class="material-symbols-outlined nav-icon">${item.icon}</span>
                <span class="nav-label">${item.label}</span>
            </a>
        `)
        .join('');
}

// Get role label in Portuguese
function getRoleLabel(role) {
    const labels = {
        'admin': 'Administrador',
        'supervisor': 'Supervisor',
        'operator': 'Operador'
    };
    return labels[role] || role;
}

// Highlight active page in navigation
function highlightActivePage() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        const itemPath = item.getAttribute('href');
        if (currentPath.includes(itemPath.split('/').pop().replace('.html', ''))) {
            item.classList.add('active');
        }
    });
}

// Inject sidebar CSS
function injectSidebarStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Layout Container - Flexbox */
        .sgp-layout-container {
            display: flex;
            width: 100%;
            min-height: 100vh;
        }
        
        /* Sidebar Styles */
        .sgp-sidebar {
            width: 280px;
            background: linear-gradient(180deg, #1b2227 0%, #0f1923 100%);
            border-right: 1px solid #374151;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            z-index: 50;
            position: relative;
            box-shadow: 4px 0 12px rgba(0, 0, 0, 0.3);
            transition: width 300ms ease;
        }
        
        .sgp-sidebar.collapsed {
            width: 70px;
        }
        
        .sgp-sidebar.collapsed .logo-text,
        .sgp-sidebar.collapsed .nav-label,
        .sgp-sidebar.collapsed .user-details,
        .sgp-sidebar.collapsed .logout-text {
            opacity: 0;
            width: 0;
            overflow: hidden;
        }
        
        .sgp-sidebar.collapsed .sidebar-logo {
            justify-content: center;
        }
        
        .sgp-sidebar.collapsed .user-info {
            justify-content: center;
        }
        
        .sidebar-toggle {
            position: absolute;
            top: 1rem;
            right: -15px;
            width: 30px;
            height: 30px;
            background-color: #359EFF;
            border: 2px solid #1b2227;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1001;
            transition: all 200ms ease;
        }
        
        .sidebar-toggle:hover {
            background-color: #2b7fd9;
            transform: scale(1.1);
        }
        
        .sidebar-toggle .material-symbols-outlined {
            font-size: 1.125rem;
            color: white;
        }
        
        .sidebar-header {
            padding: 1.5rem 1.25rem;
            border-bottom: 1px solid #374151;
        }
        
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 0.875rem;
            transition: justify-content 300ms ease;
        }
        
        .logo-icon {
            font-size: 2.5rem;
            color: #359EFF;
            flex-shrink: 0;
        }
        
        .logo-text {
            transition: opacity 300ms ease, width 300ms ease;
        }
        
        .logo-title {
            font-size: 1.125rem;
            font-weight: 900;
            color: #f3f4f6;
            letter-spacing: -0.025em;
            white-space: nowrap;
        }
        
        .logo-subtitle {
            font-size: 0.75rem;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            white-space: nowrap;
        }
        
        .sidebar-nav {
            flex: 1;
            padding: 1rem 0.75rem;
            overflow-y: auto;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: 0.875rem;
            padding: 0.875rem 1rem;
            margin-bottom: 0.375rem;
            border-radius: 0.75rem;
            color: #9ca3af;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 200ms ease;
            position: relative;
        }
        
        .nav-item:hover {
            background-color: rgba(53, 158, 255, 0.1);
            color: #359EFF;
        }
        
        .nav-item.active {
            background-color: rgba(53, 158, 255, 0.15);
            color: #359EFF;
            font-weight: 700;
        }
        
        .nav-item.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 60%;
            background-color: #359EFF;
            border-radius: 0 4px 4px 0;
        }
        
        .nav-icon {
            font-size: 1.375rem;
            flex-shrink: 0;
        }
        
        .nav-label {
            transition: opacity 300ms ease, width 300ms ease;
            white-space: nowrap;
        }
        
        .sidebar-footer {
            padding: 1rem 1.25rem;
            border-top: 1px solid #374151;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.875rem;
            padding: 0.75rem;
            background-color: rgba(55, 65, 81, 0.3);
            border-radius: 0.75rem;
            transition: justify-content 300ms ease;
        }
        
        .user-icon {
            font-size: 2rem;
            color: #359EFF;
            flex-shrink: 0;
        }
        
        .user-details {
            transition: opacity 300ms ease, width 300ms ease;
        }
        
        .user-name {
            font-size: 0.875rem;
            font-weight: 700;
            color: #f3f4f6;
            white-space: nowrap;
        }
        
        .user-role {
            font-size: 0.75rem;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            white-space: nowrap;
        }
        
        .logout-btn {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem;
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 0.75rem;
            color: #ef4444;
            font-weight: 700;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 200ms ease;
        }
        
        .logout-btn:hover {
            background-color: #ef4444;
            color: white;
        }
        
        .logout-text {
            transition: opacity 300ms ease, width 300ms ease;
        }
        
        /* Main Content - Flexbox */
        .sgp-main-content {
            flex-grow: 1;
            transition: all 300ms ease;
            overflow-x: hidden;
            padding: 2rem;
            min-height: 100vh;
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .sgp-sidebar {
                position: fixed;
                left: 0;
                top: 0;
                bottom: 0;
                transform: translateX(-100%);
                z-index: 1000;
            }
            
            .sgp-sidebar.mobile-open {
                transform: translateX(0);
            }
            
            .sgp-main-content {
                margin-left: 0 !important;
            }
        }
    `;

    document.head.appendChild(style);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLayout);
} else {
    initLayout();
}
