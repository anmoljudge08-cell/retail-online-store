document.addEventListener("DOMContentLoaded", () => {
  const flashItems = document.querySelectorAll(".flash");

  flashItems.forEach((flash, index) => {
    setTimeout(() => {
      flash.classList.add("fade");
    }, 1800 + index * 220);
  });
});

console.log("Retail Store demo ready");
