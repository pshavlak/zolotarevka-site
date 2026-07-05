// Золотаревка — основной JS
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    var toggle = document.getElementById('menuToggle');
    var nav = document.getElementById('mainNav');
    if (toggle && nav) {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            nav.classList.toggle('nav--open');
        });
        document.addEventListener('click', function(e) {
            if (!nav.contains(e.target) && !toggle.contains(e.target)) {
                nav.classList.remove('nav--open');
            }
        });
    }
});
