document.addEventListener("DOMContentLoaded", () => {
  const likeForm = document.getElementById("like-form");
  const blockForm = document.getElementById("block-form");

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

  const showToast = (message, type = "success") => {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  };

  if (likeForm) {
    likeForm.addEventListener("click", async () => {
      const userId = likeForm.dataset.userId;

      try {
        const res = await fetch(`/like/${userId}`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken
          }
        });

        if (res.ok) {
          showToast("Лайк обработан!");
        } else {
          showToast("Ошибка при обработке лайка", "error");
        }
      } catch (err) {
        console.error("Ошибка сети:", err);
        showToast("Ошибка подключения", "error");
      }
    });
  }

  if (blockForm) {
    blockForm.addEventListener("click", async () => {
      const userId = blockForm.dataset.userId;

      try {
        const res = await fetch(`/block/${userId}`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken
          }
        });

        if (res.ok) {
          showToast("Пользователь заблокирован!");
        } else {
          showToast("Ошибка при блокировке", "error");
        }
      } catch (err) {
        console.error("Ошибка сети:", err);
        showToast("Ошибка подключения", "error");
      }
    });
  }
});

// Увеличение фото по клику
function openPhoto(src) {
  const overlay = document.getElementById("overlay");
  const overlayImg = document.getElementById("overlay-img");

  overlayImg.src = src;
  overlay.style.display = "flex";
}

function closePhoto() {
  const overlay = document.getElementById("overlay");
  const overlayImg = document.getElementById("overlay-img");

  overlayImg.src = "";
  overlay.style.display = "none";
}
