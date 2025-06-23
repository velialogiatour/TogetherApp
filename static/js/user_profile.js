document.addEventListener("DOMContentLoaded", function () {
  const editBtn = document.getElementById("editBtn");
  const saveBtn = document.getElementById("saveBtn");
  const form = document.getElementById("profileForm");

  const fieldTypes = {
    age: "number",
    gender: "text",
    country: "text",
    city: "text",
    height: "number",
    zodiac_sign: "text",
    interests: "textarea",
    description: "textarea"
  };

  editBtn.addEventListener("click", () => {
    editBtn.style.display = "none";
    saveBtn.style.display = "inline-block";

    for (const [field, type] of Object.entries(fieldTypes)) {
      const span = form.querySelector(`[data-field="${field}"]`);
      if (!span) continue;

      const value = span.textContent.trim();
      let input;

      if (type === "textarea") {
        input = document.createElement("textarea");
        input.rows = 3;
      } else {
        input = document.createElement("input");
        input.type = type;
      }

      input.name = field;
      input.className = "input";
      input.value = value;
      input.required = true;

      span.replaceWith(input);
    }
  });

  // Выпадающее меню ⋮
  const menuToggle = document.getElementById("menuToggle");
  const dropdown = document.getElementById("dropdownMenu");

  menuToggle.addEventListener("click", () => {
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", (e) => {
    if (!menuToggle.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = "none";
    }
  });

  // Модальное окно для увеличения фото
  const modal = document.getElementById("photoModal");
  const modalImg = document.getElementById("modalImage");
  const modalClose = document.querySelector(".modal-close");

  document.querySelectorAll(".previewable").forEach(img => {
    img.addEventListener("click", () => {
      modalImg.src = img.getAttribute("data-full") || img.src;
      modal.style.display = "block";
    });
  });

  modalClose.addEventListener("click", () => {
    modal.style.display = "none";
  });

  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });

  // Автоматическое скрытие уведомлений .toast
  const toast = document.querySelector(".toast");
  if (toast) {
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  }
});

// Подтверждение удаления аккаунта
document.addEventListener("DOMContentLoaded", () => {
  const deleteLink = document.querySelector('a[href*="delete_account"]');
  const modal = document.getElementById("confirmModal");

  if (deleteLink) {
    deleteLink.addEventListener("click", (e) => {
      e.preventDefault();
      modal.style.display = "flex";
    });
  }
});

function closeModal() {
  const modal = document.getElementById("confirmModal");
  modal.style.display = "none";
}
