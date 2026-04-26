(function () {
    function styleDjangoForms() {
        var fields = document.querySelectorAll("input, select, textarea");

        fields.forEach(function (field) {
            var type = (field.getAttribute("type") || "").toLowerCase();
            if (type === "hidden") {
                return;
            }

            if (type === "checkbox" || type === "radio") {
                field.classList.add("form-check-input");
                return;
            }

            if (field.tagName === "SELECT") {
                field.classList.add("form-select");
                return;
            }

            field.classList.add("form-control");
        });

        var checkboxLabels = document.querySelectorAll("input[type='checkbox'] + label, input[type='radio'] + label");
        checkboxLabels.forEach(function (label) {
            label.classList.add("form-check-label");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", styleDjangoForms);
    } else {
        styleDjangoForms();
    }
})();
