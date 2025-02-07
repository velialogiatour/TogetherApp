document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");

    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const rememberMe = document.getElementById("remember").checked;

        if (email && password) {
            try {
                const response = await fetch("/api/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ email, password, rememberMe })
                });

                const data = await response.json();

                if (response.ok) {
                    alert("Вход выполнен успешно!");
                    window.location.href = "/basepage";
                } else {
                    alert("Ошибка: " + data.message);
                }
            } catch (error) {
                alert("Произошла ошибка при отправке данных на сервер.");
                console.error("Ошибка:", error);
            }
        } else {
            alert("Пожалуйста, введите email и пароль.");
        }
    });
});