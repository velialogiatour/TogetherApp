document.addEventListener("DOMContentLoaded", function () {
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
});
