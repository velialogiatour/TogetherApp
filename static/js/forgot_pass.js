document.addEventListener('DOMContentLoaded', () => {
    // Анимация появления формы
    const authContainer = document.querySelector('.auth-container');
    if (authContainer) {
        authContainer.style.opacity = '0';
        authContainer.style.transform = 'translateY(20px)';
        authContainer.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';

        requestAnimationFrame(() => {
            setTimeout(() => {
                authContainer.style.opacity = '1';
                authContainer.style.transform = 'translateY(0)';
            }, 50);
        });
    }

    // Обработка отправки форм
    function handleFormSubmit(form) {
        form.addEventListener('submit', () => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Обработка...';
                submitBtn.style.opacity = '0.8';
            }
        });
    }

    document.querySelectorAll('form').forEach(handleFormSubmit);

    // Плавное скрытие flash-сообщений
    document.querySelectorAll('.flash').forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(() => {
                if (msg.parentNode) msg.remove();
            }, 500);
        }, 5000);
    });
});
