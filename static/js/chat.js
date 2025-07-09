const messagesDiv = document.getElementById('messages');
const form = document.getElementById('messageForm');
const input = document.getElementById('messageInput');
const errorBox = document.getElementById('errorBox');

const receiverIdInput = document.getElementById('receiver_id');
const receiverId = receiverIdInput ? Number(receiverIdInput.value) : null;

/**
 * @typedef {Object} Message
 * @property {number} id
 * @property {string} text
 * @property {number} sender_id
 * @property {boolean} is_read
 * @property {string} created_at
 */

/**
 * Создаёт DOM-элемент для сообщения
 * @param {Message} m
 * @returns {HTMLElement}
 */
function renderMessage(m) {
  const div = document.createElement('div');
  div.classList.add('message', m.sender_id === receiverId ? 'received' : 'sent');
  div.innerHTML = `
    <div class="message-text">${m.text}</div>
    <div class="status">
      ${m.created_at}${m.sender_id !== receiverId ? (m.is_read ? ' — Прочитано' : ' — Не прочитано') : ''}
    </div>
  `;
  div.dataset.id = m.id;
  return div;
}

function fetchMessages() {
  if (!receiverId) return;

  fetch(`/chat_updates/${receiverId}`)
    .then(res => res.json())
    .then(data => {
      messagesDiv.innerHTML = '';
      data.forEach(m => {
        const el = renderMessage(m);
        messagesDiv.appendChild(el);
      });
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    })
    .catch(err => {
      console.error("Ошибка загрузки сообщений:", err);
    });
}

if (form) {
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const content = input.value.trim();

    if (!receiverId || isNaN(receiverId) || receiverId <= 0) {
      errorBox.textContent = 'Ошибка: получатель не определён.';
      return;
    }

    if (!content) return;

    const formData = new FormData();
    formData.append('receiver_id', receiverId);
    formData.append('message', content);

    fetch('/send_message', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          input.value = '';
          errorBox.textContent = '';
          fetchMessages();
        } else {
          errorBox.textContent = data.error || 'Ошибка при отправке';
        }
      })
      .catch(err => {
        console.error("Ошибка сети:", err);
        errorBox.textContent = "Ошибка сети. Попробуйте снова.";
      });
  });
}

// Автообновление сообщений
setInterval(fetchMessages, 3000);
fetchMessages();

// 🔔 Автоматическое скрытие flash-сообщений
const flash = document.querySelector('.flash');
if (flash) {
  setTimeout(() => {
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-10px)';
    setTimeout(() => flash.remove(), 500);
  }, 3000);
}
