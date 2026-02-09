(function () {
    const passwordInput = document.getElementById('id_password');
    const toggleButton = document.getElementById('passwordToggle');
    const recaptchaContainer = document.querySelector('.captcha-live');

    if (!passwordInput || !toggleButton) {
        return;
    }

    toggleButton.addEventListener('click', function () {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
    });

    function fitRecaptcha() {
        if (!recaptchaContainer) {
            return;
        }

        const iframeWrapper = recaptchaContainer.querySelector('.g-recaptcha > div');
        if (!iframeWrapper) {
            return;
        }

        const baseWidth = 304;
        const availableWidth = recaptchaContainer.clientWidth - 4;
        const scale = Math.min(1, availableWidth / baseWidth);

        iframeWrapper.style.transform = `scale(${scale})`;
        recaptchaContainer.style.minHeight = `${Math.ceil(88 * scale)}px`;
    }

    let attempts = 0;
    const waiter = setInterval(function () {
        fitRecaptcha();
        attempts += 1;
        if (attempts >= 30 || document.querySelector('.g-recaptcha > div')) {
            clearInterval(waiter);
        }
    }, 150);

    window.addEventListener('resize', fitRecaptcha);
})();
