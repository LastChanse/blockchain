document.addEventListener("DOMContentLoaded", function() {
    // Мы передадим статус из Django напрямую в HTML через data-атрибут
    const bodyElement = document.body;
    const isAuthenticated = bodyElement.getAttribute('data-authenticated') === 'true';

    if (!isAuthenticated) {
        const linksToProtect = [
            document.getElementById('link-clinic-data'),
            document.getElementById('link-clinic-doctor'),
            document.getElementById('link-portal-data')
        ];

        linksToProtect.forEach(function(link) {
            if (link) {
                link.addEventListener('click', function(event) {
                    event.preventDefault(); // Отменяем переход
                    alert("Для доступа к этой странице необходимо войти в систему!");
                    window.location.href = "/accounts/login/"; // Перекидываем на вход
                });
            }
        });
    }
});