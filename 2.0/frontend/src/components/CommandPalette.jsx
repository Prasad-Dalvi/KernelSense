import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Terminal, Bot, Activity, Cpu, HardDrive,
  History, Sparkles, Volume2, Monitor, Palette, X, ArrowRight,
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import styles from './CommandPalette.module.css';

export default function CommandPalette({ isOpen, onClose, onToggleTheme, onToggleMatrix, onToggleCrt }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const COMMANDS = [
    // Navigation
    { id: 'nav-dash', category: 'Navigation', title: 'Dashboard', desc: 'System overview & live metrics', icon: Activity, action: () => navigate('/') },
    { id: 'nav-asst', category: 'Navigation', title: 'AI Assistant', desc: 'Natural language terminal & diagnosis', icon: Bot, action: () => navigate('/assistant') },
    { id: 'nav-hlth', category: 'Navigation', title: 'System Health', desc: 'Overall health score & diagnostics', icon: Activity, action: () => navigate('/health') },
    { id: 'nav-proc', category: 'Navigation', title: 'Processes (ps aux)', desc: 'Inspect & manage running tasks', icon: Cpu, action: () => navigate('/processes') },
    { id: 'nav-stor', category: 'Navigation', title: 'Storage & Disk (df -h)', desc: 'Disk usage, large files & cleanup', icon: HardDrive, action: () => navigate('/storage') },
    { id: 'nav-hist', category: 'Navigation', title: 'History', desc: 'Past executed commands & AI actions', icon: History, action: () => navigate('/history') },

    // AI Quick Diagnoses
    { id: 'ai-slow',  category: 'AI Diagnostics', title: 'Diagnose: Laptop is running slow', desc: 'Run automated performance root cause analysis', icon: Sparkles, action: () => navigate('/assistant?q=Why%20is%20my%20laptop%20slow%3F') },
    { id: 'ai-wifi',  category: 'AI Diagnostics', title: 'Diagnose: WiFi & Network issues', desc: 'Check network routing, DNS and gateway', icon: Sparkles, action: () => navigate('/assistant?q=Diagnose%20WiFi%20connection%20issues') },
    { id: 'ai-mem',   category: 'AI Diagnostics', title: 'Diagnose: High memory consumption', desc: 'Find memory leaks and greedy processes', icon: Sparkles, action: () => navigate('/assistant?q=Show%20me%20high%20memory%20processes') },
    { id: 'ai-srv',   category: 'AI Diagnostics', title: 'Diagnose: Failing system services', desc: 'Check systemctl status and error units', icon: Sparkles, action: () => navigate('/assistant?q=What%20services%20are%20failing%3F') },

    // Terminal Themes
    { id: 'theme-matrix',    category: 'Theme Matrix', title: 'Theme: Matrix Phosphor Green', desc: 'Classic 1980s green terminal', icon: Palette, action: () => onToggleTheme('matrix') },
    { id: 'theme-cyber',     category: 'Theme Matrix', title: 'Theme: Cyberpunk Cyan / Neon', desc: 'Blade Runner holographic cyan', icon: Palette, action: () => onToggleTheme('cyberpunk') },
    { id: 'theme-amber',     category: 'Theme Matrix', title: 'Theme: Solar Amber VT220', desc: 'Warm amber CRT terminal', icon: Palette, action: () => onToggleTheme('amber') },
    { id: 'theme-crimson',   category: 'Theme Matrix', title: 'Theme: Hacker Crimson Red', desc: 'High alert red security matrix', icon: Palette, action: () => onToggleTheme('crimson') },

    // Toggles
    { id: 'toggle-sfx', category: 'System Controls', title: 'Toggle Synthesizer Sound FX', desc: 'Turn audio feedback on/off', icon: Volume2, action: () => sound.toggle() },
    { id: 'toggle-mat', category: 'System Controls', title: 'Toggle Matrix Rain Canvas', desc: 'Turn background rain on/off', icon: Terminal, action: () => onToggleMatrix?.() },
    { id: 'toggle-crt', category: 'System Controls', title: 'Toggle CRT Scanlines Filter', desc: 'Retro scanline overlay', icon: Monitor, action: () => onToggleCrt?.() },
  ];

  const filtered = COMMANDS.filter(cmd => {
    const q = query.toLowerCase();
    return cmd.title.toLowerCase().includes(q) || cmd.desc.toLowerCase().includes(q) || cmd.category.toLowerCase().includes(q);
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
      sound.click();
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % Math.max(1, filtered.length));
      sound.click();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      sound.click();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = filtered[selectedIndex];
      if (selected) {
        sound.nav();
        selected.action();
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={`${styles.palette} hud-card`} onClick={e => e.stopPropagation()} onKeyDown={handleKeyDown}>
        {/* Header Search Input */}
        <div className={styles.searchBar}>
          <Terminal size={16} className={styles.searchIcon} />
          <input
            ref={inputRef}
            type="text"
            className={styles.input}
            placeholder="Type a command or search (e.g. 'processes', 'diagnose wifi', 'theme')..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <div className={styles.escBadge} onClick={onClose}>
            <kbd>ESC</kbd>
          </div>
        </div>

        {/* Results List */}
        <div className={styles.results}>
          {filtered.length === 0 ? (
            <div className={styles.noResults}>
              <p>-- No matching operations found --</p>
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  className={`${styles.item} ${isSelected ? styles.selected : ''}`}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => {
                    sound.nav();
                    item.action();
                    onClose();
                  }}
                >
                  <div className={styles.itemIconWrap}>
                    <Icon size={14} className={styles.itemIcon} />
                  </div>
                  <div className={styles.itemContent}>
                    <div className={styles.itemTitleRow}>
                      <span className={styles.itemTitle}>{item.title}</span>
                      <span className={styles.itemCategory}>{item.category}</span>
                    </div>
                    <span className={styles.itemDesc}>{item.desc}</span>
                  </div>
                  {isSelected && <ArrowRight size={13} className={styles.selectedArrow} />}
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className={styles.footer}>
          <div className={styles.footerKeys}>
            <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
            <span><kbd>↵</kbd> select</span>
            <span><kbd>ESC</kbd> close</span>
          </div>
          <span className={styles.footerBrand}>KERNEL_SENSE_OPS // v2.0</span>
        </div>
      </div>
    </div>
  );
}
