document.addEventListener("DOMContentLoaded", () => {
  const flashItems = document.querySelectorAll(".flash");

  flashItems.forEach((flash, index) => {
    setTimeout(() => {
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-6px)";
      flash.style.transition = "all 0.22s ease";
    }, 2500 + index * 300);
  });
});

console.log("Retail Store demo ready");
