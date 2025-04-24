document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Удалить активный класс у всех
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            // Добавить активный класс к текущему
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            document.getElementById(`tab-${target}`).classList.add('active');
        });
    });
});
