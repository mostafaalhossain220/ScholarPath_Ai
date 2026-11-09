/**
 * Sakura Petals Falling Animation
 * High-performance canvas animation with realistic flutter, rotation, and drifting.
 */
(function () {
  function initSakura() {
    const canvas = document.getElementById("sakura-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", function () {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const petalColors = [
      { r: 255, g: 183, b: 197 }, // soft pink
      { r: 255, g: 204, b: 213 }, // blush
      { r: 255, g: 192, b: 203 }, // light pink
      { r: 251, g: 207, b: 232 }, // soft rose
      { r: 255, g: 228, b: 235 }, // very pale blossom
    ];

    const TOTAL_PETALS = Math.min(45, Math.floor(width / 30));
    const petals = [];

    function createPetal() {
      const color = petalColors[Math.floor(Math.random() * petalColors.length)];
      return {
        x: Math.random() * width,
        y: Math.random() * -height * 0.8,
        size: 9 + Math.random() * 11,
        speedY: 1.2 + Math.random() * 1.8,
        speedX: -0.5 + Math.random() * 1.2,
        oscillationSpeed: 0.02 + Math.random() * 0.03,
        oscillationAngle: Math.random() * Math.PI * 2,
        flipSpeed: 0.03 + Math.random() * 0.04,
        flipAngle: Math.random() * Math.PI * 2,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 1.5,
        opacity: 0.65 + Math.random() * 0.35,
        color: color,
      };
    }

    for (let i = 0; i < TOTAL_PETALS; i++) {
      const p = createPetal();
      p.y = Math.random() * height; // initial distribution
      petals.push(p);
    }

    function drawPetal(p) {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      const scaleX = Math.cos(p.flipAngle);
      ctx.scale(scaleX, 1);

      ctx.beginPath();
      // Draw organic petal bezier shape
      const s = p.size;
      ctx.moveTo(0, -s * 0.7);
      ctx.bezierCurveTo(s * 0.5, -s * 0.7, s * 0.8, -s * 0.1, s * 0.3, s * 0.7);
      ctx.bezierCurveTo(0, s * 0.85, -0.1 * s, s * 0.85, -s * 0.3, s * 0.7);
      ctx.bezierCurveTo(-s * 0.8, -s * 0.1, -s * 0.5, -s * 0.7, 0, -s * 0.7);
      ctx.closePath();

      // Subtle gradient on petal
      const grad = ctx.createLinearGradient(0, -s * 0.7, 0, s * 0.8);
      grad.addColorStop(0, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.opacity})`);
      grad.addColorStop(1, `rgba(${p.color.r - 20}, ${p.color.g - 30}, ${p.color.b - 20}, ${p.opacity * 0.85})`);
      ctx.fillStyle = grad;
      ctx.fill();

      ctx.restore();
    }

    function update() {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < petals.length; i++) {
        const p = petals[i];
        p.oscillationAngle += p.oscillationSpeed;
        p.flipAngle += p.flipSpeed;
        p.rotation += p.rotationSpeed;

        p.y += p.speedY;
        p.x += Math.sin(p.oscillationAngle) * 1.2 + p.speedX;

        // Reset if moved out of view
        if (p.y > height + 20 || p.x < -30 || p.x > width + 30) {
          petals[i] = createPetal();
        }

        drawPetal(p);
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
