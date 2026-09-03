import React, { useEffect, useRef } from 'react';

/**
 * Cyber Matrix & Particle Canvas Background
 * 60 FPS hardware accelerated, adapts to active theme color.
 */
export default function CyberMatrixCanvas({ enabled = true }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Matrix characters: binary, hex, katakana and linux symbols
    const chars = '01010101ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@%&*<>{}[]λπµΩ';
    const fontSize = 14;
    const columns = Math.floor(width / fontSize);
    const drops = new Array(columns).fill(1).map(() => Math.floor(Math.random() * -50));

    // Particle nodes for subtle cyber grid
    const numParticles = Math.min(30, Math.floor(width / 50));
    const particles = Array.from({ length: numParticles }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: Math.random() * 2 + 1,
    }));

    let frame = 0;

    const render = () => {
      frame++;
      
      // Get active computed theme color
      const computedStyle = getComputedStyle(document.documentElement);
      const greenColor = computedStyle.getPropertyValue('--color-green').trim() || '#00ff66';
      const greenDim = computedStyle.getPropertyValue('--color-green-dim').trim() || 'rgba(0,255,102,0.08)';

      // Semi-transparent fade trail
      ctx.fillStyle = 'rgba(4, 7, 4, 0.22)';
      ctx.fillRect(0, 0, width, height);

      // Render subtle particle mesh
      ctx.strokeStyle = greenDim;
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        ctx.fillStyle = greenDim;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      // Render Matrix rain drops (every 2nd frame for smooth cinematic rate)
      if (frame % 2 === 0) {
        ctx.font = `${fontSize}px "JetBrains Mono", monospace`;
        
        for (let i = 0; i < drops.length; i++) {
          if (Math.random() > 0.65) {
            const char = chars[Math.floor(Math.random() * chars.length)];
            const x = i * fontSize;
            const y = drops[i] * fontSize;

            // First character glows brighter
            ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
            ctx.fillText(char, x, y);

            ctx.fillStyle = greenColor;
            ctx.globalAlpha = 0.35;
            ctx.fillText(char, x, y - fontSize);
            ctx.globalAlpha = 1.0;
          }

          if (drops[i] * fontSize > height && Math.random() > 0.975) {
            drops[i] = 0;
          }
          drops[i]++;
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
        opacity: 0.45,
      }}
    />
  );
}
