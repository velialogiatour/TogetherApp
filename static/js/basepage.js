let currentPage = 1;
let isLoading = false;

document.addEventListener("DOMContentLoaded", () => {
  const filterToggle = document.getElementById("filter-toggle");
  const filterPanel = document.getElementById("filter-panel");

  // Открытие/закрытие фильтра
  if (filterToggle && filterPanel) {
    filterToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      filterPanel.classList.toggle("hidden");
    });

    // Закрытие при клике вне панели
    document.addEventListener("click", (e) => {
      if (!filterPanel.contains(e.target) && !filterToggle.contains(e.target)) {
        filterPanel.classList.add("hidden");
      }
    });
  }

  // Прокрутка для автоподгрузки
  window.addEventListener("scroll", handleScroll);

  // Запуск проверки непрочитанных
  checkUnread();
  setInterval(checkUnread, 20000);
});

function handleScroll() {
  const scrollY = window.scrollY;
  const visible = window.innerHeight;
  const full = document.body.offsetHeight;

  if (scrollY + visible >= full - 100) {
    loadMoreProfiles();
  }
}

function loadMoreProfiles() {
  if (isLoading) return;
  isLoading = true;
  const loading = document.getElementById('loading');
  loading.style.display = 'block';

  const query = new URLSearchParams(window.location.search);
  const nextPage = currentPage + 1;
  query.set('page', nextPage);

  fetch(`/basepage_data?${query.toString()}`)
    .then(res => res.ok ? res.json() : [])
    .then(data => {
      if (data.length === 0) {
        window.removeEventListener("scroll", handleScroll);
        loading.textContent = "Анкеты закончились";
        return;
      }

      const container = document.querySelector(".cards-container");
      data.forEach(profile => {
        const card = document.createElement("a");
        card.href = `/view_profile/${profile.id}`;
        card.className = "profile-card";
        card.innerHTML = `
          <img src="${profile.profile_photo}" alt="Фото" class="profile-photo" />
          <div class="profile-info">
            <h3>${profile.name}, ${profile.age}</h3>
            <p>${profile.city}, ${profile.country}</p>
            <p>Знак: ${profile.zodiac_sign}</p>
          </div>`;
        container.appendChild(card);
      });

      currentPage++;
    })
    .catch(err => console.error("Ошибка загрузки:", err))
    .finally(() => {
      isLoading = false;
      loading.style.display = "none";
    });
}

// 🔴 Подсветка новых лайков и сообщений
function checkUnread() {
  fetch('/api/unread_counts')
    .then(res => res.json())
    .then(data => {
      const likesIcon = document.getElementById('likes-icon');
      const likesIndicator = document.getElementById('likes-indicator');
      const messagesIcon = document.getElementById('messages-icon');
      const messagesIndicator = document.getElementById('messages-indicator');

      if (likesIcon && likesIndicator) {
        if (data.likes > 0) {
          likesIcon.classList.add('has-new');
          likesIndicator.style.display = 'inline-block';
        } else {
          likesIcon.classList.remove('has-new');
          likesIndicator.style.display = 'none';
        }
      }

      if (messagesIcon && messagesIndicator) {
        if (data.messages > 0) {
          messagesIcon.classList.add('has-new');
          messagesIndicator.style.display = 'inline-block';
        } else {
          messagesIcon.classList.remove('has-new');
          messagesIndicator.style.display = 'none';
        }
      }
    })
    .catch(err => console.error("Ошибка получения уведомлений:", err));
}
