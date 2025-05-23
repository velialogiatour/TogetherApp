document.addEventListener('DOMContentLoaded', function () {
    const tabs = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            this.classList.add('active');
            document.getElementById('tab-' + this.dataset.tab).classList.add('active');

            // Удалить красную точку, если нажата вкладка "Меня лайкнули"
            if (this.dataset.tab === 'likedme') {
                const dot = this.querySelector('.red-dot');
                if (dot) {
                    dot.remove();
                }
            }
        });
    });
});


