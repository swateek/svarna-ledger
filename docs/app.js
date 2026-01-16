$(document).ready(function () {
    $('#gold-prices-table').DataTable({
        ajax: {
            url: 'data/gold_prices.json',
            dataSrc: ''
        },
        columns: [
            { data: 'date' },
            { data: 'source' },
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
        order: [[3, 'desc']], // Sort by created_dt descending by default
        responsive: true,
        language: {
            search: "_INPUT_",
            searchPlaceholder: "search"
        },
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50]
    });
});
