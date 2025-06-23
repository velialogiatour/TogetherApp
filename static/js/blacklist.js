document.addEventListener("DOMContentLoaded", function () {
  const flash = document.querySelector(".flash-message");
  const toast = document.querySelector(".toast");

  [flash, toast].forEach(el => {
    if (el) {
      setTimeout(() => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 500);
      }, 3000);
    }
  });
});
