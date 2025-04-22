document.addEventListener('DOMContentLoaded', () => {
    // Анимация появления формы через класс
    const authContainer = document.querySelector('.auth-container');
    if (authContainer) {
        authContainer.classList.add('hidden-init');
        requestAnimationFrame(() => {
            setTimeout(() => {
                authContainer.classList.remove('hidden-init');
                authContainer.classList.add('fade-in');
            }, 50);
        });
    }

    // Обработка отправки формы
    const handleFormSubmit = (form) => {
        form.addEventListener('submit', () => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Обработка...';
                submitBtn.style.opacity = '0.8';
            }
        });
    };

    document.querySelectorAll('form').forEach(handleFormSubmit);

    // Плавное скрытие flash-сообщений
    document.querySelectorAll('.flash').forEach(msg => {
        setTimeout(() => {
            msg.classList.add('fade-out');
            msg.addEventListener('transitionend', () => {
                if (msg.parentNode) msg.remove();
            });
        }, 5000);
    });
});
