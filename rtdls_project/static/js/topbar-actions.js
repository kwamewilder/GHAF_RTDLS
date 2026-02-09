(function () {
    const searchForms = Array.from(document.querySelectorAll('.portal-search'));
    if (!searchForms.length) {
        return;
    }

    searchForms.forEach((form) => {
        form.addEventListener('submit', (event) => {
            const input = form.querySelector('input[name="q"]');
            if (!input) {
                return;
            }
            input.value = (input.value || '').trim();
            if (!input.value) {
                event.preventDefault();
            }
        });
    });
})();
