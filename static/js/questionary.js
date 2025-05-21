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
    }, 500);
  }, 3000);
}

// Динамическая подгрузка городов по выбранной стране
const countrySelect = document.getElementById('country');
const citySelect = document.getElementById('city');

const citiesByCountry = {
  "Россия": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород", "Челябинск", "Самара", "Уфа", "Ростов-на-Дону", "Красноярск", "Пермь", "Воронеж", "Омск", "Тюмень", "Томск", "Барнаул", "Иркутск"],
  "Беларусь": ["Минск", "Гомель", "Могилёв", "Витебск", "Гродно", "Брест"],
  "Казахстан": ["Алматы", "Астана", "Шымкент", "Караганда", "Актобе", "Тараз"],
  "Армения": ["Ереван", "Гюмри", "Ванадзор"],
  "Азербайджан": ["Баку", "Гянджа", "Сумгаит"],
  "Кыргызстан": ["Бишкек", "Ош", "Джалал-Абад"],
  "Таджикистан": ["Душанбе", "Худжанд", "Бохтар"],
  "Узбекистан": ["Ташкент", "Самарканд", "Бухара", "Наманган", "Андижан"],
  "Молдова": ["Кишинёв", "Бельцы", "Тирасполь"],
  "Грузия": ["Тбилиси", "Батуми", "Кутаиси"]
};

if (countrySelect && citySelect) {
  countrySelect.addEventListener('change', function () {
    const selected = this.value;
    const cities = citiesByCountry[selected] || [];

    citySelect.innerHTML = '<option value="">Выберите город</option>';

    cities.forEach(city => {
      const option = document.createElement('option');
      option.value = city;
      option.textContent = city;
      citySelect.appendChild(option);
    });
  });
}
