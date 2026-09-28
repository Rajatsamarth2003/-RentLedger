document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.opacity = "0";
            el.style.transition = "opacity .4s ease";
        }, 3500);
    });
});


document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.target);
        if (!input) return;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        button.textContent = isPassword ? 'Hide' : 'Show';
    });
});
