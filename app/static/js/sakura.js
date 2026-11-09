/**
 * Full-Site Sakura Petals & Cursor Trail Particle System
 * Features:
 *  1. Ambient fluttering falling cherry blossom petals
 *  2. Interactive cursor motion trail (spawns gentle petals & blossom sparks as cursor moves)
 *  3. Click burst effect (spawns mini petal cluster on click)
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

    const petalColors = [
      { r: 255, g: 183, b: 197 }, // soft pink
      { r: 255, g: 192, b: 203 }, // light pink
      { r: 251, g: 207, b: 232 }, // soft rose
      { r: 255, g: 218, b: 228 }, // pale sakura
      { r: 244, g: 114, b: 182 }, // accent blossom
    ];

    // Ambient floating petals
    const AMBIENT_COUNT = Math.min(38, Math.max(18, Math.floor(width / 40)));
    const ambientPetals = [];
    // Cursor spawned petals
    const cursorPetals = [];

    function createAmbientPetal(startY) {
      const color = petalColors[Math.floor(Math.random() * petalColors.length)];
      return {
        x: Math.random() * (width + 60) - 30,
        y: startY !== undefined ? startY : Math.random() * -height * 0.5,
        size: 8 + Math.random() * 11,
        speedY: 0.9 + Math.random() * 1.6,
        speedX: -0.4 + Math.random() * 1.3,
        oscillationSpeed: 0.015 + Math.random() * 0.025,
        oscillationAngle: Math.random() * Math.PI * 2,
        flipSpeed: 0.025 + Math.random() * 0.035,
        flipAngle: Math.random() * Math.PI * 2,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 1.6,
        opacity: 0.65 + Math.random() * 0.3,
        color: color,
      };
    }

    // Populate initial ambient petals
    for (let i = 0; i < AMBIENT_COUNT; i++) {
      ambientPetals.push(createAmbientPetal(Math.random() * height));
    }

    // Function to draw organic petal shape
    function drawPetal(p, alphaMultiplier) {
      const alpha = (p.opacity || 1) * (alphaMultiplier !== undefined ? alphaMultiplier : 1);
      if (alpha <= 0.01) return;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      const scaleX = Math.cos(p.flipAngle || 0);
      ctx.scale(scaleX, 1);

      ctx.beginPath();
      const s = p.size;
      ctx.moveTo(0, -s * 0.7);
      ctx.bezierCurveTo(s * 0.5, -s * 0.7, s * 0.8, -s * 0.1, s * 0.3, s * 0.7);
      ctx.bezierCurveTo(0, s * 0.85, -0.1 * s, s * 0.85, -s * 0.3, s * 0.7);
      ctx.bezierCurveTo(-s * 0.8, -s * 0.1, -s * 0.5, -s * 0.7, 0, -s * 0.7);
      ctx.closePath();

      const grad = ctx.createLinearGradient(0, -s * 0.7, 0, s * 0.8);
      grad.addColorStop(0, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${alpha})`);
      grad.addColorStop(
        1,
        `rgba(${Math.max(0, p.color.r - 25)}, ${Math.max(0, p.color.g - 35)}, ${Math.max(0, p.color.b - 25)}, ${alpha * 0.85})`
      );
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.restore();
    }

    // Cursor movement handler
    let lastX = 0, lastY = 0;
    let throttleTimer = 0;

    function spawnCursorPetal(x, y, isBurst) {
      const color = petalColors[Math.floor(Math.random() * petalColors.length)];
      const angle = isBurst ? Math.random() * Math.PI * 2 : Math.random() * Math.PI + Math.PI / 2;
      const speed = isBurst ? 1.5 + Math.random() * 3.5 : 0.8 + Math.random() * 1.8;

      cursorPetals.push({
        x: x + (Math.random() - 0.5) * 10,
        y: y + (Math.random() - 0.5) * 10,
        vx: Math.cos(angle) * speed + (Math.random() - 0.5) * 0.5,
        vy: isBurst ? Math.sin(angle) * speed : 1.2 + Math.random() * 1.8,
        size: 7 + Math.random() * 9,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 3,
        flipAngle: Math.random() * Math.PI * 2,
        flipSpeed: 0.04 + Math.random() * 0.05,
        life: 1.0,
        decay: isBurst ? 0.016 + Math.random() * 0.012 : 0.02 + Math.random() * 0.015,
        color: color,
      });

      // Keep array bounded for peak performance
      if (cursorPetals.length > 70) {
        cursorPetals.shift();
      }
    }

    window.addEventListener("mousemove", function (e) {
      const now = Date.now();
      const dist = Math.hypot(e.clientX - lastX, e.clientY - lastY);

      if (dist > 18 && now - throttleTimer > 35) {
        throttleTimer = now;
        lastX = e.clientX;
        lastY = e.clientY;
        spawnCursorPetal(e.clientX, e.clientY, false);
      }
    });

    // Gentle burst on click
    window.addEventListener("click", function (e) {
      const count = 6;
      for (let i = 0; i < count; i++) {
        spawnCursorPetal(e.clientX, e.clientY, true);
      }
    });

    // Touch devices support
    window.addEventListener("touchmove", function (e) {
      if (e.touches && e.touches[0]) {
        spawnCursorPetal(e.touches[0].clientX, e.touches[0].clientY, false);
      }
    }, { passive: true });

    // Main animation loop
    function update() {
      ctx.clearRect(0, 0, width, height);

      // 1. Update & draw ambient petals
      for (let i = 0; i < ambientPetals.length; i++) {
        const p = ambientPetals[i];
        p.oscillationAngle += p.oscillationSpeed;
        p.flipAngle += p.flipSpeed;
        p.rotation += p.rotationSpeed;

        p.y += p.speedY;
        p.x += Math.sin(p.oscillationAngle) * 1.1 + p.speedX;

        if (p.y > height + 25 || p.x < -40 || p.x > width + 40) {
          ambientPetals[i] = createAmbientPetal();
        }

        drawPetal(p, 1);
      }

      // 2. Update & draw cursor trail petals
      for (let i = cursorPetals.length - 1; i >= 0; i--) {
        const cp = cursorPetals[i];
        cp.x += cp.vx;
        cp.y += cp.vy;
        cp.vy += 0.04; // gentle gravity
        cp.vx *= 0.98; // slight drag
        cp.rotation += cp.rotationSpeed;
        cp.flipAngle += cp.flipSpeed;
        cp.life -= cp.decay;

        if (cp.life <= 0) {
          cursorPetals.splice(i, 1);
        } else {
          drawPetal(cp, cp.life);
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
