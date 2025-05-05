// Работа с фото профиля
const profileInput = document.getElementById('profilePhotoInput');
const profilePreview = document.getElementById('profilePreview');

profileInput.addEventListener('change', function(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      profilePreview.style.backgroundImage = `url(${e.target.result})`;
      profilePreview.textContent = '';
    };
    reader.readAsDataURL(file);
  }
});

// Автоматическое скрытие flash-сообщения
const flashMessage = document.getElementById('flashMessage');
if (flashMessage) {
  setTimeout(() => {
    flashMessage.style.opacity = '0';
    setTimeout(() => {
      flashMessage.remove();
    }, 500); // удаляем после исчезновения
  }, 3000); // ждём 3 секунды
}
