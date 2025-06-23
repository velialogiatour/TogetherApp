document.addEventListener("DOMContentLoaded", () => {
  const filterToggle = document.getElementById("filter-toggle");
  const filterPanel = document.getElementById("filter-panel");
  const clearFiltersButton = document.getElementById("clear-filters");
  const searchInput = document.getElementById("search-input");
  const filterForm = document.querySelector(".filters");
  const noProfiles = document.getElementById("no-profiles");

  // Переключение панели фильтра
  if (filterToggle && filterPanel) {
    filterToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      filterPanel.classList.toggle("open");
      filterPanel.classList.remove("hidden");
    });

    document.addEventListener("click", (e) => {
      const isClickInside = filterPanel.contains(e.target) || filterToggle.contains(e.target);
      if (!isClickInside && filterPanel.classList.contains("open")) {
        filterPanel.classList.remove("open");
        filterPanel.classList.add("hidden");
      }
    });
  }

  // Кнопка сброса фильтров
  if (clearFiltersButton) {
    clearFiltersButton.addEventListener("click", () => {
      const url = new URL(window.location.origin + "/basepage");

      if (searchInput) {
        searchInput.value = "";
      }

      if (filterForm) {
        filterForm.reset();
      }

      history.replaceState({}, "", url.toString());
      loadProfiles();
    });
  }

  // Поиск по слову (автоматически)
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        const url = new URL(window.location.origin + "/basepage_data");
        if (query) url.searchParams.set("query", query);

        history.replaceState({}, "", "/basepage?" + url.searchParams.toString());
        fetchProfiles(url);
      }, 400);
    });
  }

  // Сабмит фильтра без перезагрузки + сброс полей
  if (filterForm) {
    filterForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const formData = new FormData(filterForm);
      const url = new URL(window.location.origin + "/basepage_data");

      for (const [key, value] of formData.entries()) {
        if (value && value.trim() !== "") {
          url.searchParams.set(key, value.trim());
        }
      }

      history.replaceState({}, "", "/basepage?" + url.searchParams.toString());
      fetchProfiles(url);

      filterForm.reset();
    });
  }

  // Загрузка анкет
  function fetchProfiles(url) {
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        let container = document.querySelector(".cards-container");

        if (!container) {
          container = document.createElement("div");
          container.className = "cards-container";
          document.body.appendChild(container);
        }

        container.innerHTML = "";

        const results = data.profiles || data;

        if (data.empty || results.length === 0) {
          noProfiles.classList.add("visible");
        } else {
          noProfiles.classList.remove("visible");

          results.forEach((profile) => {
            const card = document.createElement("a");
            card.className = "profile-card";
            card.href = `/view_profile/${profile.id}`;

            const matchBlock = (profile.match_probability && profile.match_probability > 0)
              ? `<p class="match-probability"><span class="label">Совпадение:</span> ${profile.match_probability}%</p>`
              : "";

            card.innerHTML = `
              <img src="${profile.profile_photo}" alt="Фото" class="profile-photo" />
              <div class="profile-info">
                <h3>${profile.name}, ${profile.age}</h3>
                <p>${profile.city}, ${profile.country}</p>
                <p>Знак: ${profile.zodiac_sign}</p>
                ${matchBlock}
              </div>
            `;
            container.appendChild(card);
          });
        }
      })
      .catch((err) => {
        console.error("Ошибка загрузки анкет:", err);
      });
  }

  function loadProfiles() {
    const url = new URL(window.location.origin + "/basepage_data");
    fetchProfiles(url);
  }

  // Проверка количества непрочитанных лайков и сообщений
  function checkUnreadCounts() {
    fetch("/api/unread_counts")
      .then((res) => res.json())
      .then((data) => {
        const likesIndicator = document.getElementById("likes-indicator");
        const messagesIndicator = document.getElementById("messages-indicator");

        if (data.likes > 0 && likesIndicator) {
          likesIndicator.classList.add("visible");
        } else if (likesIndicator) {
          likesIndicator.classList.remove("visible");
        }

        if (data.messages > 0 && messagesIndicator) {
          messagesIndicator.classList.add("visible");
        } else if (messagesIndicator) {
          messagesIndicator.classList.remove("visible");
        }
      })
      .catch((err) => {
        console.error("Ошибка получения количества уведомлений:", err);
      });
  }

  // Загрузка анкет при первом открытии
  if (!document.querySelector(".profile-card")) {
    loadProfiles();
  }

  // Проверка индикаторов
  checkUnreadCounts();
});
