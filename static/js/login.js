document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("loginForm");
    const errorBox = document.getElementById("errorBox");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(form);
        const jsonData = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": formData.get("csrf_token")
                },
                body: JSON.stringify(jsonData)
            });

            const result = await response.json();
            if (response.ok && result.success) {
                window.location.href = "/basepage";
            } else {
                errorBox.innerHTML = `<div class="error-message">${result.message || "Ошибка входа"}</div>`;
            }
        } catch (error) {
            console.error("Ошибка запроса:", error);
            errorBox.innerHTML = `<div class="error-message">Ошибка сети. Попробуйте снова.</div>`;
        }
    });
});



