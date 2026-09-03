import React, { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Bot, Activity, Cpu, HardDrive,
  History, Terminal, Volume2, VolumeX, Search, Sparkles,
  ChevronLeft, ChevronRight, Shield, Zap, Circle,
} from 'lucide-react';
import { isMockMode } from '../api/client';
import { sound } from '../utils/soundEffects';
import CommandPalette from '../components/CommandPalette';
import styles from './MainLayout.module.css';

const NAV_ITEMS = [
  { path: '/',          label: 'Dashboard',      icon: LayoutDashboard, key: '1' },
  { path: '/assistant', label: 'AI Assistant',   icon: Bot,             key: '2', badge: 'AI' },
  { path: '/health',    label: 'System Health',  icon: Activity,        key: '3' },
  { path: '/processes', label: 'Processes',      icon: Cpu,             key: '4' },
  { path: '/storage',   label: 'Storage & Disk', icon: HardDrive,       key: '5' },
  { path: '/history',   label: 'History',        icon: History,         key: '6' },
];

function TerminalClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className={styles.clockWrap}>
      <span className={styles.clockTime}>
        {time.toLocaleTimeString('en-US', { hour12: false })}
      </span>
      <span className={styles.clockDate}>
        {time.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
      </span>
    </div>
  );
}

export default function MainLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sfxEnabled, setSfxEnabled] = useState(sound.isEnabled());

  const location = useLocation();
  const navigate = useNavigate();

  const toggleSfx = () => {
    const next = sound.toggle();
    setSfxEnabled(next);
  };

  // Keyboard Shortcuts (1-9 navigation, Ctrl+K for palette)
  useEffect(() => {
    const handleKeyDown = (e) => {
      const tag = document.activeElement?.tagName?.toLowerCase();
      const isInput = tag === 'input' || tag === 'textarea';

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen(prev => !prev);
        return;
      }

      if (!isInput && !paletteOpen) {
        const num = parseInt(e.key, 10);
        if (num >= 1 && num <= NAV_ITEMS.length) {
          const target = NAV_ITEMS[num - 1];
          if (target) {
            e.preventDefault();
            sound.nav();
            navigate(target.path);
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate, paletteOpen]);

  const currentItem = NAV_ITEMS.find((n) => n.path === location.pathname);
  const currentLabel = currentItem?.label ?? 'Dashboard';

  return (
    <div className={`${styles.root} ${collapsed ? styles.collapsed : ''}`}>
      {/* Quick Ops Command Palette */}
      <CommandPalette
        isOpen={paletteOpen}
        onClose={() => setPaletteOpen(false)}
      />

      {/* ── Sidebar Navigation ── */}
      <aside className={styles.sidebar}>
        {/* Brand Header */}
        <div className={styles.brand} onClick={() => navigate('/')}>
          <div className={styles.logoIconWrap}>
            <Terminal size={18} className={styles.logoIcon} />
            <span className={styles.logoGlow} />
          </div>
          {!collapsed && (
            <div className={styles.brandTextWrap}>
              <span className={styles.brandName}>
                KERNEL<span className="grad-text-cyan">SENSE</span>
              </span>
              <span className={styles.brandTag}>AI LINUX PLATFORM</span>
            </div>
          )}
        </div>

        {isMockMode() && !collapsed && (
          <div className={styles.mockBadgeWrap}>
            <span className={styles.mockBadge}>
              <Zap size={10} /> SIMULATED TELEMETRY
            </span>
          </div>
        )}

        {/* Navigation List */}
        <nav className={styles.nav}>
          {!collapsed && <span className={styles.navGroupLabel}>CORE MODULES</span>}
          {NAV_ITEMS.map(({ path, label, icon: Icon, key, badge }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              onClick={() => sound.nav()}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              title={collapsed ? label : undefined}
            >
              {({ isActive }) => (
                <>
                  <div className={styles.navItemLeft}>
                    <div className={`${styles.navIconWrap} ${isActive ? styles.activeIcon : ''}`}>
                      <Icon size={16} />
                    </div>
                    {!collapsed && <span className={styles.navLabel}>{label}</span>}
                  </div>
                  {!collapsed && (
                    <div className={styles.navItemRight}>
                      {badge && <span className={styles.aiPill}>{badge}</span>}
                      <span className={styles.keyShortcut}>{key}</span>
                    </div>
                  )}
                  {isActive && <span className={styles.activeGlowBar} />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className={styles.sidebarFooter}>
          {!collapsed && (
            <div className={styles.connectionPill}>
              <span className={`${styles.statusDot} ${isMockMode() ? styles.dotMock : styles.dotLive}`} />
              <div className={styles.connectionText}>
                <span className={styles.connStatusTitle}>{isMockMode() ? 'MOCK ENGINE' : 'LIVE KERNEL'}</span>
                <span className={styles.connHost}>127.0.0.1:8000</span>
              </div>
            </div>
          )}
          <button
            className={styles.collapseBtn}
            onClick={() => { sound.click(); setCollapsed(c => !c); }}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>
      </aside>

      {/* ── Main Viewport ── */}
      <div className={styles.main}>
        {/* Modern Top Header */}
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.breadcrumb}>
              <span className={styles.breadRoot}>Linux 6.8</span>
              <span className={styles.breadSep}>/</span>
              <span className={styles.breadActive}>{currentLabel}</span>
            </div>
          </div>

          <div className={styles.headerCenter}>
            <button
              className={styles.searchLauncher}
              onClick={() => { sound.click(); setPaletteOpen(true); }}
            >
              <Search size={14} className={styles.searchIcon} />
              <span className={styles.searchText}>Quick operations &amp; AI diagnostics...</span>
              <kbd className={styles.searchKbd}>Ctrl K</kbd>
            </button>
          </div>

          <div className={styles.headerRight}>
            <button
              className={`${styles.iconBtn} ${sfxEnabled ? styles.iconBtnActive : ''}`}
              onClick={toggleSfx}
              title={`Audio Synthesizer: ${sfxEnabled ? 'ENABLED' : 'MUTED'}`}
            >
              {sfxEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
            </button>

            <TerminalClock />
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className={styles.content}>
          <div className="fade-in" style={{ height: '100%' }}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
