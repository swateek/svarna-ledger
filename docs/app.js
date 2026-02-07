$(document).ready(function () {
    const table = $('#gold-prices-table').DataTable({
        ajax: {
            url: 'data/gold_prices.json',
            dataSrc: ''
        },
        columns: [
            { data: 'date' },
            { data: 'source' },
            { data: 'purity' },
            {
                data: 'price_per_gm',
                render: function (data) {
                    return '₹' + data.toLocaleString('en-IN');
                }
            },
            {
                data: 'created_dt',
                render: function (data) {
                    if (!data) return 'N/A';
                    const date = new Date(data);
                    return date.toLocaleString();
                }
            }
        ],
        order: [[0, 'desc']], // Sort by date descending by default
        responsive: true,
        language: {
            search: "_INPUT_",
            searchPlaceholder: "search"
        },
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50],
        initComplete: function () {
            // Apply the default filter on initialization based on active tab
            const defaultFilter = $('.tab-btn.active').data('purity');
            if (defaultFilter) {
                this.api().column(2).search(defaultFilter).draw();
            }
        }
    });

    // Handle the custom purity tabs
    $('.tab-btn').on('click', function () {
        // Update active class
        $('.tab-btn').removeClass('active');
        $(this).addClass('active');

        // Apply filter
        const purity = $(this).data('purity');
        table.column(2).search(purity).draw();
    });
});
