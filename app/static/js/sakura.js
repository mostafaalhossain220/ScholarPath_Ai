/**
 * ScholarPath AI - Enhanced Cherry Blossom (Sakura) Particle & Cursor Engine
 * Vivid, organic notched petals with natural flutter, 3D spin, and interactive cursor physics.
 */
(function () {
  function initSakura() {
    let canvas = document.getElementById("sakura-canvas");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "sakura-canvas";
      document.body.prepend(canvas);
    }

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", function () {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    // Rich, vibrant cherry blossom petal colors
    const petalPalettes = [
      { base: "#ff4071", highlight: "#ffa6c1", shadow: "#e61a53" }, // deep sakura pink
      { base: "#ff5c8a", highlight: "#ffccd8", shadow: "#db2777" }, // vibrant blossom
      { base: "#ff7597", highlight: "#ffe4ec", shadow: "#e11d48" }, // sweet cherry rose
      { base: "#f43f5e", highlight: "#fecdd3", shadow: "#be123c" }, // rich rose
      { base: "#fb7185", highlight: "#fff1f2", shadow: "#e11d48" }, // soft pastel blossom
    ];

    const TOTAL_AMBIENT = Math.min(55, Math.max(28, Math.floor(width / 32)));
    const ambientPetals = [];
    const cursorPetals = [];

    // Helper to create an ambient falling petal
    function createAmbientPetal(startY) {
      const palette = petalPalettes[Math.floor(Math.random() * petalPalettes.length)];
      return {
        x: Math.random() * (width + 60) - 30,
        y: startY !== undefined ? startY : Math.random() * -height * 0.6,
        size: 10 + Math.random() * 12,
        speedY: 1.1 + Math.random() * 1.8,
        speedX: -0.5 + Math.random() * 1.4,
        oscillationSpeed: 0.018 + Math.random() * 0.025,
        oscillationAngle: Math.random() * Math.PI * 2,
        flipSpeed: 0.03 + Math.random() * 0.04,
        flipAngle: Math.random() * Math.PI * 2,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 1.8,
        opacity: 0.82 + Math.random() * 0.18,
        palette: palette,
      };
    }

    for (let i = 0; i < TOTAL_AMBIENT; i++) {
      ambientPetals.push(createAmbientPetal(Math.random() * height));
    }

    // Draw realistic notched sakura petal
    function drawSakuraPetal(p, alphaMultiplier) {
      const alpha = (p.opacity || 1) * (alphaMultiplier !== undefined ? alphaMultiplier : 1);
      if (alpha <= 0.01) return;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      const scaleX = Math.cos(p.flipAngle || 0);
      ctx.scale(scaleX, 1);

      ctx.beginPath();
      const s = p.size;
      
      // Bottom stem tip
      ctx.moveTo(0, s * 0.8);
      
      // Left curve
      ctx.bezierCurveTo(-s * 0.65, s * 0.4, -s * 0.75, -s * 0.4, -s * 0.28, -s * 0.8);
      
      // Top iconic notched cleft of sakura petal
      ctx.lineTo(0, -s * 0.62);
      ctx.lineTo(s * 0.28, -s * 0.8);
      
      // Right curve back to stem tip
      ctx.bezierCurveTo(s * 0.75, -s * 0.4, s * 0.65, s * 0.4, 0, s * 0.8);
      ctx.closePath();

      // Vibrant 2-tone gradient
      const grad = ctx.createLinearGradient(0, -s * 0.8, 0, s * 0.8);
      grad.addColorStop(0, p.palette.highlight);
      grad.addColorStop(0.5, p.palette.base);
      grad.addColorStop(1, p.palette.shadow);

      ctx.globalAlpha = alpha;
      ctx.fillStyle = grad;
      ctx.fill();

      // Subtle translucent petal vein
      ctx.strokeStyle = "rgba(255, 255, 255, 0.45)";
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.moveTo(0, s * 0.7);
      ctx.lineTo(0, -s * 0.45);
      ctx.stroke();

      ctx.restore();
    }

    // Cursor interaction
    let lastX = 0, lastY = 0;
    let throttleTimer = 0;

    function spawnCursorPetals(x, y, count, isBurst) {
      for (let i = 0; i < count; i++) {
        const palette = petalPalettes[Math.floor(Math.random() * petalPalettes.length)];
        const angle = isBurst ? Math.random() * Math.PI * 2 : (Math.PI / 2) + (Math.random() - 0.5) * 1.8;
        const speed = isBurst ? 2 + Math.random() * 4.5 : 1.2 + Math.random() * 2.5;

        cursorPetals.push({
          x: x + (Math.random() - 0.5) * 12,
          y: y + (Math.random() - 0.5) * 12,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 8 + Math.random() * 10,
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 4,
          flipAngle: Math.random() * Math.PI * 2,
          flipSpeed: 0.05 + Math.random() * 0.06,
          life: 1.0,
          decay: isBurst ? 0.015 + Math.random() * 0.012 : 0.02 + Math.random() * 0.015,
          opacity: 0.95,
          palette: palette,
        });
      }

      if (cursorPetals.length > 80) {
        cursorPetals.splice(0, cursorPetals.length - 80);
      }
    }

    window.addEventListener("mousemove", function (e) {
      const now = Date.now();
      const dist = Math.hypot(e.clientX - lastX, e.clientY - lastY);

      if (dist > 15 && now - throttleTimer > 28) {
        throttleTimer = now;
        lastX = e.clientX;
        lastY = e.clientY;
        spawnCursorPetals(e.clientX, e.clientY, 2, false);
      }
    });

    window.addEventListener("click", function (e) {
      spawnCursorPetals(e.clientX, e.clientY, 8, true);
    });

    window.addEventListener("touchmove", function (e) {
      if (e.touches && e.touches[0]) {
        spawnCursorPetals(e.touches[0].clientX, e.touches[0].clientY, 2, false);
      }
    }, { passive: true });

    // Main animation loop
    function update() {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw ambient falling sakura petals
      for (let i = 0; i < ambientPetals.length; i++) {
        const p = ambientPetals[i];
        p.oscillationAngle += p.oscillationSpeed;
        p.flipAngle += p.flipSpeed;
        p.rotation += p.rotationSpeed;

        p.y += p.speedY;
        p.x += Math.sin(p.oscillationAngle) * 1.3 + p.speedX;

        if (p.y > height + 30 || p.x < -40 || p.x > width + 40) {
          ambientPetals[i] = createAmbientPetal();
        }

        drawSakuraPetal(p, 1);
      }

      // 2. Draw interactive cursor trail petals
      for (let i = cursorPetals.length - 1; i >= 0; i--) {
        const cp = cursorPetals[i];
        cp.x += cp.vx;
        cp.y += cp.vy;
        cp.vy += 0.05; // gravity
        cp.vx *= 0.98; // air drag
        cp.rotation += cp.rotationSpeed;
        cp.flipAngle += cp.flipSpeed;
        cp.life -= cp.decay;

        if (cp.life <= 0) {
          cursorPetals.splice(i, 1);
        } else {
          drawSakuraPetal(cp, cp.life);
        }
      }

      requestAnimationFrame(update);
    }

    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSakura);
  } else {
    initSakura();
  }
})();
