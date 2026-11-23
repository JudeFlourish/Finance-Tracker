// ask before deleting, I deleted wrong expense by mistake few times
// every form with class "confirm-form" asks its data-confirm question first
const confirmForms = document.querySelectorAll(".confirm-form");
for (let i = 0; i < confirmForms.length; i++) {
    confirmForms[i].addEventListener("submit", function (event) {
        if (!confirm(confirmForms[i].dataset.confirm)) {
            event.preventDefault();
        }
    });
}
