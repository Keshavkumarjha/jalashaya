document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".order-now-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const productId = button.getAttribute("data-product-id");
      const productName = button.getAttribute("data-product-name");

      const idEl = document.getElementById("modal-product-id");
      const nameEl = document.getElementById("modal-product-name");

      if (idEl) idEl.value = productId;
      if (nameEl) nameEl.textContent = `Product: ${productName}`;
    });
  });

  const revealElements = document.querySelectorAll(".reveal-up");
  if ("IntersectionObserver" in window && revealElements.length) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("show");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 },
    );

    revealElements.forEach((el) => revealObserver.observe(el));
  } else {
    revealElements.forEach((el) => el.classList.add("show"));
  }

  const counters = document.querySelectorAll("[data-count]");
  counters.forEach((counter) => {
    const target = Number(counter.getAttribute("data-count") || 0);
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 45));

    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        counter.textContent = `${target}+`;
        clearInterval(interval);
        return;
      }
      counter.textContent = current;
    }, 25);
  });
});
