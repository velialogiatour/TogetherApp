// Глобальные функции для увеличенного фото
function openPhoto(src) {
  const modal = document.getElementById("photoModal");
  const modalImg = document.getElementById("modalImage");
  modalImg.src = src;
  modal.style.display = "flex";
}

function closePhoto() {
  const modal = document.getElementById("photoModal");
  const modalImg = document.getElementById("modalImage");
  modalImg.src = "";
  modal.style.display = "none";
}

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

  const sendPost = async (url, successMessage, errorMessage) => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken
        }
      });

      if (res.ok) {
        showToast(successMessage);
      } else {
        showToast(errorMessage, "error");
      }
    } catch (err) {
      console.error("Ошибка сети:", err);
      showToast("Ошибка подключения", "error");
    }
  };

  if (likeForm) {
    likeForm.addEventListener("click", async () => {
      const userId = likeForm.dataset.userId;
      await sendPost(`/like/${userId}`, "Лайк обработан!", "Ошибка при обработке лайка");
    });
  }

  if (blockForm) {
    blockForm.addEventListener("click", async () => {
      const userId = blockForm.dataset.userId;
      await sendPost(`/block/${userId}`, "Пользователь заблокирован!", "Ошибка при блокировке");
    });
  }

  // Закрытие модального окна по клику вне изображения
  const modal = document.getElementById("photoModal");
  const closeBtn = document.querySelector(".modal-close");

  closeBtn.addEventListener("click", closePhoto);

  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      closePhoto();
    }
  });
});
