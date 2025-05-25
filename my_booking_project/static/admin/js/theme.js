'use strict';
{
    window.addEventListener('load', function () {

        function setTheme(mode) {
            if (!['light', 'dark', 'auto'].includes(mode)) {
                console.error(`Invalid theme mode: ${mode}. Falling back to auto.`);
                mode = 'auto';
            }

            // Установка data-theme на <html>
            document.documentElement.setAttribute('data-theme', mode);
            localStorage.setItem('theme', mode);

            // Применение предпочтения системы, если auto
            if (mode === 'auto') {
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
            }
        }

        function cycleTheme() {
            const current = localStorage.getItem('theme') || 'auto';
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            if (prefersDark) {
                // auto (dark) -> light -> dark
                if (current === 'auto') {
                    setTheme('light');
                } else if (current === 'light') {
                    setTheme('dark');
                } else {
                    setTheme('auto');
                }
            } else {
                // auto (light) -> dark -> light
                if (current === 'auto') {
                    setTheme('dark');
                } else if (current === 'dark') {
                    setTheme('light');
                } else {
                    setTheme('auto');
                }
            }
        }

        function initTheme() {
            const saved = localStorage.getItem('theme');
            setTheme(saved || 'light');  // ← устанавливаем светлую по умолчанию
        }

        function setupTheme() {
            const buttons = document.getElementsByClassName('theme-toggle');
            Array.from(buttons).forEach(btn => {
                btn.addEventListener('click', cycleTheme);
            });
            initTheme();
        }

        setupTheme();
    });
}
