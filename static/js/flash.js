document.addEventListener("DOMContentLoaded", function () {
    // Обработка старого формата .flash
    const flashes = document.querySelectorAll(".flash");

    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = "0";
            flash.style.transform = "translateY(-20px)";
            setTimeout(() => {
                flash.style.display = "none";
            }, 500);
        }, 3000);
    });

    // Обработка новых уведомлений в .toast
    const toasts = document.querySelectorAll(".toast");

    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(-20px)";
            setTimeout(() => {
                toast.remove();
            }, 500);
        }, 3000);
    });
});
