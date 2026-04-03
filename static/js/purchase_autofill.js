(function() {
    function fillPrices(select) {
        var row = select.closest('tr');
        if (!row) return;

        var productId = select.value;
        var costInput = row.querySelector('.field-cost_price input');
        var sellInput = row.querySelector('.field-sell_price input');

        if (!productId) return;

        fetch('/api/product-price/' + productId + '/')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (costInput && data.cost_price) {
                    costInput.value = data.cost_price;
                }
                if (sellInput && data.sell_price) {
                    sellInput.value = data.sell_price;
                }
            })
            .catch(function() {});
    }

    function setupAutofill() {
        document.querySelectorAll('.field-product select').forEach(function(select) {
            select.removeEventListener('change', handleChange);
            select.addEventListener('change', handleChange);
        });
    }

    function handleChange() {
        fillPrices(this);
    }

    // Следим за popup — когда товар создан через "+", select обновляется
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            if (m.type === 'childList' && m.target.tagName === 'SELECT') {
                fillPrices(m.target);
            }
        });
    });

    document.addEventListener('DOMContentLoaded', function() {
        setupAutofill();

        // Наблюдаем за всеми select полями товара
        document.querySelectorAll('.field-product select').forEach(function(select) {
            observer.observe(select, { childList: true });
        });
    });

    document.addEventListener('formset:added', function() {
        setTimeout(function() {
            setupAutofill();
            document.querySelectorAll('.field-product select').forEach(function(select) {
                observer.observe(select, { childList: true });
            });
        }, 100);
    });
})();