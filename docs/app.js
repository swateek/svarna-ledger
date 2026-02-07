$(document).ready(function () {
    let priceChart;
    let goldData = [];

    const table = $('#gold-prices-table').DataTable({
        ajax: {
            url: 'data/gold_prices.json',
            dataSrc: function (json) {
                goldData = json;
                return json;
            }
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
        order: [[0, 'desc']],
        responsive: true,
        language: {
            search: "_INPUT_",
            searchPlaceholder: "search table"
        },
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50],
        initComplete: function (settings, json) {
            initChart(json);
        }
    });

    // Purity filter tabs logic
    $('.tab-btn').on('click', function () {
        $('.tab-btn').removeClass('active');
        $(this).addClass('active');
        refreshView();
    });

    // Time range filter buttons logic
    $('.time-btn').on('click', function () {
        $('.time-btn').removeClass('active');
        $(this).addClass('active');
        refreshView();
    });

    function refreshView() {
        const purity = $('.tab-btn.active').data('purity');
        const range = $('.time-btn.active').data('range');

        // Update table filter
        table.column(2).search('^' + purity + '$', true, false);

        // Notify DataTable that custom filters need to be re-applied
        $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
            const rangeFilter = $('.time-btn.active').data('range');
            const itemDateStr = data[0]; // Assuming 'date' is the first column
            const itemDate = new Date(itemDateStr);
            const now = new Date();
            const currentMonth = now.getMonth();
            const currentYear = now.getFullYear();

            if (rangeFilter === 'this-month') {
                return itemDate.getMonth() === currentMonth && itemDate.getFullYear() === currentYear;
            } else if (rangeFilter === 'last-month') {
                const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1;
                const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear;
                return itemDate.getMonth() === lastMonth && itemDate.getFullYear() === lastMonthYear;
            } else if (rangeFilter === 'this-year') {
                return itemDate.getFullYear() === currentYear;
            } else if (rangeFilter === 'all') {
                return true;
            }
            return true;
        });

        table.draw();

        // Clear the search function to avoid stacking
        $.fn.dataTable.ext.search.pop();

        // Update chart
        updateChart(goldData, purity, range);
    }

    function initChart(data) {
        const ctx = document.getElementById('gold-price-chart').getContext('2d');
        const initialPurity = $('.tab-btn.active').data('purity') || '24K';
        const initialRange = $('.time-btn.active').data('range') || 'this-month';

        const chartData = processDataForChart(data, initialPurity, initialRange);

        priceChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#e0e0e0',
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            font: { family: 'Inter', size: 12, weight: '500' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(18, 18, 18, 0.95)',
                        titleColor: '#d4af37',
                        bodyColor: '#e0e0e0',
                        borderColor: '#333',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        bodyFont: { family: 'Inter' },
                        titleFont: { family: 'Inter', weight: '700' },
                        boxPadding: 6
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#666',
                            font: { family: 'Inter', size: 11 },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: { color: '#222', drawBorder: false },
                        ticks: {
                            color: '#666',
                            font: { family: 'Inter', size: 11 },
                            callback: function (value) {
                                return '₹' + value.toLocaleString('en-IN');
                            }
                        }
                    }
                }
            }
        });
    }

    function processDataForChart(data, purityFilter, rangeFilter) {
        let filtered = data.filter(item => item.purity === purityFilter);

        // Time Filtering
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();

        if (rangeFilter === 'this-month') {
            filtered = filtered.filter(item => {
                const itemDate = new Date(item.date);
                return itemDate.getMonth() === currentMonth && itemDate.getFullYear() === currentYear;
            });
        } else if (rangeFilter === 'last-month') {
            const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1;
            const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear;
            filtered = filtered.filter(item => {
                const itemDate = new Date(item.date);
                return itemDate.getMonth() === lastMonth && itemDate.getFullYear() === lastMonthYear;
            });
        } else if (rangeFilter === 'this-year') {
            filtered = filtered.filter(item => {
                const itemDate = new Date(item.date);
                return itemDate.getFullYear() === currentYear;
            });
        }

        // Sort by date ascending for chart
        filtered.sort((a, b) => new Date(a.date) - new Date(b.date));

        const sources = [...new Set(filtered.map(item => item.source))];
        const dates = [...new Set(filtered.map(item => item.date))];

        const colors = {
            'Tanishq': { border: '#d4af37', bg: 'rgba(212, 175, 55, 0.1)' },
            'Malabar Gold & Diamonds': { border: '#4ecdc4', bg: 'rgba(78, 205, 196, 0.1)' },
            'Google': { border: '#3498db', bg: 'rgba(52, 152, 219, 0.1)' }
        };

        const ctx = document.getElementById('gold-price-chart').getContext('2d');

        const datasets = sources.map(source => {
            const sourceData = dates.map(date => {
                const entry = filtered.find(item => item.date === date && item.source === source);
                return entry ? entry.price_per_gm : null;
            });

            const colorSet = colors[source] || { border: '#888', bg: 'rgba(136, 136, 136, 0.1)' };

            // Create Gradient
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, colorSet.bg.replace('0.1', '0.2'));
            gradient.addColorStop(1, 'rgba(18, 18, 18, 0)');

            return {
                label: source,
                data: sourceData,
                borderColor: colorSet.border,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4, // Smoothed lines
                cubicInterpolationMode: 'monotone',
                pointRadius: 0, // Hide points by default for "Google-look"
                pointHoverRadius: 5,
                pointBackgroundColor: colorSet.border,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                borderWidth: 2.5,
                spanGaps: true
            };
        });

        return {
            labels: dates.map(d => {
                const date = new Date(d);
                return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
            }),
            datasets: datasets
        };
    }

    function updateChart(data, purity, range) {
        if (!priceChart) return;
        const newData = processDataForChart(data, purity, range);
        priceChart.data = newData;
        priceChart.update();
    }
});
