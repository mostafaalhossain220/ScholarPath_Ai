/**
 * ScholarPath AI — Sakura petal engine
 *
 * - Ambient petals drift down in three depth layers with gentle wind gusts.
 * - Moving the cursor releases an evenly spaced stream of petals that inherit
 *   the cursor's motion, then float, flutter and fade out.
 * - Clicking releases a small burst with a soft ring.
 *
 * Smoothness: petals are pre-rendered once into sprites (no gradients per frame),
 * the canvas is scaled for retina screens, motion is time-based (same speed on
 * 60/120/144 Hz screens), and the loop pauses when the tab is hidden.
 * Respects the "reduce motion" system setting.
 */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function init() {
    const canvas = document.getElementById("sakura-canvas");
    if (!canvas || reduceMotion) return;
    const ctx = canvas.getContext("2d");

    let width = 0;
    let height = 0;
    let dpr = 1;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    // ------------------------------------------------------------------
    // Petal sprites (drawn once per colour, reused every frame)
    // ------------------------------------------------------------------
    const PALETTES = [
      ["#ffc2d4", "#ff6b93", "#e11d58"],
      ["#ffe0ea", "#ff86a8", "#ec4880"],
      ["#fff1f5", "#ffa3bd", "#f05d8a"],
      ["#ffd6e2", "#fb7185", "#e11d48"],
      ["#fde2f3", "#f9a8d4", "#db2777"],
    ];
    const SPRITE = 48; // logical px

    function makeSprite([light, mid, deep]) {
      const c = document.createElement("canvas");
      const scale = 2; // keep sprites crisp on retina
      c.width = c.height = SPRITE * scale;
      const g = c.getContext("2d");
      g.scale(scale, scale);
      g.translate(SPRITE / 2, SPRITE / 2);
      const s = SPRITE * 0.42;

      g.beginPath();
      g.moveTo(0, s * 0.85);
      g.bezierCurveTo(-s * 0.7, s * 0.45, -s * 0.8, -s * 0.38, -s * 0.3, -s * 0.82);
      g.quadraticCurveTo(-s * 0.12, -s * 0.72, 0, -s * 0.6);
      g.quadraticCurveTo(s * 0.12, -s * 0.72, s * 0.3, -s * 0.82);
      g.bezierCurveTo(s * 0.8, -s * 0.38, s * 0.7, s * 0.45, 0, s * 0.85);
      g.closePath();

      const grad = g.createLinearGradient(-s * 0.4, -s * 0.85, s * 0.4, s * 0.85);
      grad.addColorStop(0, light);
      grad.addColorStop(0.55, mid);
      grad.addColorStop(1, deep);
      g.fillStyle = grad;
      g.shadowColor = "rgba(225, 29, 72, 0.25)";
      g.shadowBlur = 3;
      g.fill();
      g.shadowBlur = 0;

      // Soft sheen + vein
      const sheen = g.createRadialGradient(-s * 0.2, -s * 0.3, 0, -s * 0.2, -s * 0.3, s * 0.7);
      sheen.addColorStop(0, "rgba(255,255,255,0.55)");
      sheen.addColorStop(1, "rgba(255,255,255,0)");
      g.fillStyle = sheen;
      g.fill();

      g.strokeStyle = "rgba(255,255,255,0.5)";
      g.lineWidth = 0.9;
      g.beginPath();
      g.moveTo(0, s * 0.7);
      g.quadraticCurveTo(s * 0.05, 0, 0, -s * 0.45);
      g.stroke();
      return c;
    }

    const sprites = PALETTES.map(makeSprite);
    const randomSprite = () => sprites[(Math.random() * sprites.length) | 0];

    function drawPetal(p, alpha) {
      if (alpha <= 0.01) return;
      const flip = Math.cos(p.flip);
      const size = p.size * (p.grow !== undefined ? p.grow : 1);
      ctx.save();
      ctx.globalAlpha = alpha * themeAlpha;
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.scale(flip * (size / SPRITE) * 2.1, (size / SPRITE) * 2.1);
      ctx.drawImage(p.sprite, -SPRITE / 2, -SPRITE / 2, SPRITE, SPRITE);
      ctx.restore();
    }

    // ------------------------------------------------------------------
    // Ambient petals
    // ------------------------------------------------------------------
    const ambient = [];
    const ambientCount = () => Math.round(Math.min(22, Math.max(8, (width * height) / 85000)));

    function newAmbient(spawnAnywhere) {
      const z = 0.45 + Math.random() * 0.75; // depth: small/slow/faint → big/fast/bright
      return {
        sprite: randomSprite(),
        z,
        x: Math.random() * (width + 120) - 60,
        y: spawnAnywhere ? Math.random() * height : -30 - Math.random() * 80,
        size: 7 + z * 11,
        vy: 0.35 + z * 0.55,
        sway: 0.6 + Math.random() * 0.9,
        phase: Math.random() * Math.PI * 2,
        phaseSpeed: 0.012 + Math.random() * 0.014,
        rot: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.025,
        flip: Math.random() * Math.PI * 2,
        flipSpeed: 0.015 + Math.random() * 0.025,
        alpha: 0.45 + z * 0.45,
      };
    }

    for (let i = 0; i < ambientCount(); i++) ambient.push(newAmbient(true));

    // ------------------------------------------------------------------
    // Cursor trail + click bursts
    // ------------------------------------------------------------------
    const trail = [];
    const rings = [];
    const MAX_TRAIL = 14; // keep the cursor effect very light
    const pointer = { x: -1, y: -1, vx: 0, vy: 0, has: false, carry: 0 };

    function spawnTrail(x, y, vx, vy, burst) {
      if (trail.length >= MAX_TRAIL) trail.shift();
      const angle = burst ? Math.random() * Math.PI * 2 : 0;
      const speed = burst ? 1 + Math.random() * 1.4 : 0;
      trail.push({
        sprite: randomSprite(),
        x: x + (Math.random() - 0.5) * 6,
        y: y + (Math.random() - 0.5) * 6,
        vx: burst ? Math.cos(angle) * speed : vx * 0.12 + (Math.random() - 0.5) * 0.7,
        vy: burst ? Math.sin(angle) * speed - 1 : vy * 0.12 + (Math.random() - 0.2) * 0.6,
        size: (burst ? 6 : 5) + Math.random() * 4,
        rot: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.09,
        flip: Math.random() * Math.PI * 2,
        flipSpeed: 0.04 + Math.random() * 0.05,
        age: 0,
        life: burst ? 1000 + Math.random() * 400 : 800 + Math.random() * 400, // ms
        grow: 0,
      });
    }

    function onMove(e) {
      const x = e.clientX;
      const y = e.clientY;
      const touch = e.pointerType === "touch";
      if (!pointer.has) {
        pointer.x = x; pointer.y = y; pointer.has = true;
        return;
      }
      const dx = x - pointer.x;
      const dy = y - pointer.y;
      const dist = Math.hypot(dx, dy);
      pointer.vx = pointer.vx * 0.6 + dx * 0.4;
      pointer.vy = pointer.vy * 0.6 + dy * 0.4;

      // Evenly spaced along the path, so fast flicks still give a smooth stream
      const spacing = touch ? 120 : 85;
      pointer.carry += dist;
      while (pointer.carry >= spacing && dist > 0) {
        pointer.carry -= spacing;
        const t = 1 - pointer.carry / dist;
        spawnTrail(pointer.x + dx * t, pointer.y + dy * t, pointer.vx, pointer.vy, false);
      }
      pointer.x = x;
      pointer.y = y;
    }

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerdown", (e) => {
      const n = e.pointerType === "touch" ? 2 : 4;
      for (let i = 0; i < n; i++) spawnTrail(e.clientX, e.clientY, 0, 0, true);
      rings.push({ x: e.clientX, y: e.clientY, age: 0 });
    }, { passive: true });
    document.addEventListener("pointerleave", () => { pointer.has = false; });

    // ------------------------------------------------------------------
    // Loop
    // ------------------------------------------------------------------
    let themeAlpha = 1;
    let last = performance.now();
    let running = true;
    let windTime = 0;

    const easeOutBack = (t) => 1 + 2.2 * Math.pow(t - 1, 3) + 1.2 * Math.pow(t - 1, 2);

    function frame(now) {
      if (!running) return;
      const ms = Math.min(now - last, 50);
      last = now;
      const k = ms / 16.667; // 1.0 at 60 fps
      windTime += ms;

      themeAlpha = document.documentElement.getAttribute("data-theme") === "dark" ? 0.82 : 1;
      ctx.clearRect(0, 0, width, height);

      // Layered sine "wind" with occasional gusts
      const wind = Math.sin(windTime * 0.00023) * 0.45 + Math.sin(windTime * 0.0011) * 0.18 +
                   Math.max(0, Math.sin(windTime * 0.00009)) * 0.5;

      // Ambient
      const target = ambientCount();
      while (ambient.length < target) ambient.push(newAmbient(false));
      if (ambient.length > target) ambient.length = target;

      for (let i = 0; i < ambient.length; i++) {
        const p = ambient[i];
        p.phase += p.phaseSpeed * k;
        p.flip += p.flipSpeed * k;
        p.rot += (p.rotSpeed + wind * 0.004) * k;
        p.y += p.vy * k;
        p.x += (Math.sin(p.phase) * p.sway + wind * (0.6 + p.z)) * k;
        if (p.y > height + 40 || p.x < -80 || p.x > width + 80) ambient[i] = newAmbient(false);
        drawPetal(p, p.alpha);
      }

      // Click rings
      for (let i = rings.length - 1; i >= 0; i--) {
        const r = rings[i];
        r.age += ms;
        const t = r.age / 550;
        if (t >= 1) { rings.splice(i, 1); continue; }
        ctx.save();
        ctx.globalAlpha = (1 - t) * 0.22 * themeAlpha;
        ctx.strokeStyle = "#fb7185";
        ctx.lineWidth = 2 * (1 - t) + 0.5;
        ctx.beginPath();
        ctx.arc(r.x, r.y, 4 + t * 18, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }

      // Trail
      for (let i = trail.length - 1; i >= 0; i--) {
        const p = trail[i];
        p.age += ms;
        const t = p.age / p.life;
        if (t >= 1) { trail.splice(i, 1); continue; }
        p.vx = p.vx * Math.pow(0.965, k) + wind * 0.02 * k;
        p.vy = p.vy * Math.pow(0.975, k) + 0.028 * k; // light, floaty gravity
        p.x += (p.vx + Math.sin(p.age * 0.006 + p.flip) * 0.35) * k;
        p.y += p.vy * k;
        p.rot += p.rotSpeed * k;
        p.flip += p.flipSpeed * k;
        p.grow = easeOutBack(Math.min(1, p.age / 260));
        const fade = t < 0.6 ? 1 : 1 - (t - 0.6) / 0.4;
        drawPetal(p, 0.6 * fade * fade);
      }

      requestAnimationFrame(frame);
    }

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        running = false;
      } else if (!running) {
        running = true;
        last = performance.now();
        requestAnimationFrame(frame);
      }
    });

    requestAnimationFrame(frame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
