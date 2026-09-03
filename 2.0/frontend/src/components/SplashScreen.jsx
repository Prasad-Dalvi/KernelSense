import React, { useState, useEffect } from 'react';
import { Sparkles, Terminal, ShieldCheck, Zap, ArrowRight } from 'lucide-react';
import { sound } from '../utils/soundEffects';
import splashLogoImg from '../assets/splash_logo.jpg';
import styles from './SplashScreen.module.css';

const BOOT_LOGS = [
  'INITIALIZING LINUX KERNEL v6.8.0-GENERIC SMP PREEMPT_DYNAMIC...',
  'MOUNTING VIRTUAL FILESYSTEMS: /proc /sys /dev /run...',
  'STARTING eBPF HARDWARE MONITORING & TRACEPOINT HOOKS...',
  'LOADING AUTONOMOUS AI NEURAL ORCHESTRATOR [v2.0]...',
  'ESTABLISHING ENCRYPTED IPC TELEMETRY BUS (127.0.0.1:8000)...',
  'ALL SUBSYSTEMS NOMINAL. LAUNCHING KERNELSENSE PLATFORM...',
];

export default function SplashScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [logIndex, setLogIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    sound.approve();

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => handleFinish(), 350);
          return 100;
        }
        const next = prev + Math.floor(Math.random() * 8 + 4);
        return Math.min(100, next);
      });
    }, 90);

    const logInterval = setInterval(() => {
      setLogIndex((prev) => Math.min(BOOT_LOGS.length - 1, prev + 1));
      sound.click();
    }, 400);

    return () => {
      clearInterval(interval);
      clearInterval(logInterval);
    };
  }, []);

  const handleFinish = () => {
    setIsFading(true);
    setTimeout(() => {
      onComplete?.();
    }, 500);
  };

  return (
    <div className={`${styles.splashOverlay} ${isFading ? styles.fadeOut : ''}`}>
      <div className={styles.ambientGlow} />

      <div className={styles.splashCard}>
        {/* Glowing 3D Emblem */}
        <div className={styles.emblemWrap}>
          <img src={splashLogoImg} alt="KernelSense Logo" className={styles.emblemImg} />
          <div className={styles.emblemRing} />
        </div>

        {/* Brand Title */}
        <div className={styles.brandGroup}>
          <h1 className={styles.title}>
            KERNEL<span className="grad-text-cyan">SENSE</span>
          </h1>
          <span className={styles.subtitle}>
            NEXT-GEN AI LINUX OPERATIONS PLATFORM
          </span>
        </div>

        {/* Progress Bar */}
        <div className={styles.progressContainer}>
          <div className={styles.progressHeader}>
            <span className={styles.progressLabel}>
              <Zap size={11} color="var(--color-cyan)" />
              <span>SYSTEM INITIALIZATION</span>
            </span>
            <span className={styles.progressPct}>{progress}%</span>
          </div>

          <div className={styles.progressBarBg}>
            <div className={styles.progressBarFill} style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Live Boot Log Stream */}
        <div className={styles.bootLogWrap}>
          <span className={styles.logPrompt}>$</span>
          <span className={styles.logText}>{BOOT_LOGS[logIndex]}</span>
          <span className="cursor-blink" style={{ color: 'var(--color-cyan)', marginLeft: 4 }}>█</span>
        </div>

        {/* Skip button */}
        <button className={styles.skipBtn} onClick={handleFinish}>
          <span>SKIP BOOT</span>
          <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}
