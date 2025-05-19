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
