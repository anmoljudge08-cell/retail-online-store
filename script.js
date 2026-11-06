
let cartCount = 0;

const countElement = document.getElementById("cart-count");
const messageElement = document.getElementById("cart-message");

document.querySelectorAll(".add-button").forEach((button) => {
  button.addEventListener("click", () => {
    cartCount++;

    countElement.textContent = cartCount;

    messageElement.textContent =
      `${button.dataset.name} added to your cart. Total items: ${cartCount}.`;
  });
});
