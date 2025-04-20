document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(form);
        const jsonData = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": formData.get("csrf_token")
                },
                body: JSON.stringify(jsonData)
            });

            const result = await response.json();
            if (response.ok) {
                window.location.href = "/questionary";
            } else {
                alert("Ошибка: " + result.message);
            }
        } catch (error) {
            console.error("Ошибка запроса:", error);
            alert("Ошибка сети. Попробуйте снова.");
        }
    });
});
