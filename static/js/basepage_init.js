document.addEventListener("DOMContentLoaded", function () {
  // 💬 Автоисчезновение flash-сообщений
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-20px)";
      setTimeout(() => {
        flash.style.display = "none";
      }, 500);
    }, 3000);
  });

  // ✅ Фикс отступа шапки после входа/перенаправления
  requestAnimationFrame(() => {
    const searchBar = document.querySelector('.search-bar');
    if (searchBar) {
      searchBar.style.transform = 'translateY(0)';
      searchBar.style.opacity = '1';
    }
  });
});
