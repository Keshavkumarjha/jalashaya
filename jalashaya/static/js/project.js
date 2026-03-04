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
});
