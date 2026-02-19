document.addEventListener("DOMContentLoaded", () => {
    console.log("Телефонний довідник: JS завантажено.");

    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.focus();
    }

    document.querySelectorAll("[data-confirm]").forEach(el => {
        el.addEventListener("click", (e) => {
            const msg = el.getAttribute("data-confirm") || "Ви впевнені?";
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });
});
