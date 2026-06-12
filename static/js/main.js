document.addEventListener('DOMContentLoaded', function () {
    // Proactively initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Universal search utility for Bootstrap Tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(function (input) {
        input.addEventListener('keyup', function () {
            const targetTableId = this.getAttribute('data-target');
            const targetTable = document.getElementById(targetTableId);
            const filter = this.value.toLowerCase();
            const rows = targetTable.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) { // Skip header
                let rowText = rows[i].textContent.toLowerCase();
                if (rowText.indexOf(filter) > -1) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        });
    });

    // Bootstrap Form Validation feedback loop
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});
