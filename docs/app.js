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
            refreshView();
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

        const range = $(this).data('range');
        if (range === 'custom') {
            $('#custom-range-picker').fadeIn();
            // Set default dates if empty
            if (!$('#start-date').val() || !$('#end-date').val()) {
                const now = new Date();
                const thirtyDaysAgo = new Date();
                thirtyDaysAgo.setDate(now.getDate() - 30);
                $('#start-date').val(thirtyDaysAgo.toISOString().split('T')[0]);
                $('#end-date').val(now.toISOString().split('T')[0]);
            }
        } else {
            $('#custom-range-picker').fadeOut();
        }

        refreshView();
    });

    $('.date-input').on('change', function () {
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
            } else if (rangeFilter === 'custom') {
                const startDateStr = $('#start-date').val();
                const endDateStr = $('#end-date').val();
                if (!startDateStr || !endDateStr) return true;

                const start = new Date(startDateStr);
                const end = new Date(endDateStr);
                end.setHours(23, 59, 59, 999); // Inclusion of end day

                return itemDate >= start && itemDate <= end;
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

        // Update historical stats
        updateHistoricalStats(goldData, purity);
    }

    function updateHistoricalStats(data, purity) {
        const filtered = data.filter(item => item.purity === purity);
        if (filtered.length === 0) return;

        // 1. Current Value Logic
        // Find latest date in the dataset for this purity
        const latestDate = filtered.reduce((max, item) => item.date > max ? item.date : max, filtered[0].date);
        const latestEntries = filtered.filter(item => item.date === latestDate);

        // Pick the entry with the highest price for that date (if multiple sources)
        const currentItem = latestEntries.sort((a, b) => b.price_per_gm - a.price_per_gm)[0];

        // 2. 30-day stats
        const now = new Date();
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(now.getDate() - 30);

        const last30Days = filtered.filter(item => new Date(item.date) >= thirtyDaysAgo);

        let thirtyDayLow = { price_per_gm: 'N/A' };
        let thirtyDayHigh = { price_per_gm: 'N/A' };

        if (last30Days.length > 0) {
            const sorted30 = [...last30Days].sort((a, b) => a.price_per_gm - b.price_per_gm);
            thirtyDayLow = sorted30[0];
            thirtyDayHigh = sorted30[sorted30.length - 1];
        }

        // Update DOM
        $('#current-price').text('₹' + currentItem.price_per_gm.toLocaleString('en-IN'));
        $('#current-source').text(currentItem.source);
        $('#current-date').text(new Date(currentItem.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }));

        const timestamp = currentItem.modified_dt || currentItem.created_dt;
        if (timestamp) {
            const time = new Date(timestamp);
            $('#current-time').text('Refreshed: ' + time.toLocaleString());
        } else {
            $('#current-time').text('');
        }

        $('#30-day-high').text(thirtyDayHigh.price_per_gm !== 'N/A' ? '₹' + thirtyDayHigh.price_per_gm.toLocaleString('en-IN') : 'N/A');
        $('#month-high-purity').text(purity + ' Gold');

        $('#30-day-low').text(thirtyDayLow.price_per_gm !== 'N/A' ? '₹' + thirtyDayLow.price_per_gm.toLocaleString('en-IN') : 'N/A');
        $('#month-low-purity').text(purity + ' Gold');
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
        } else if (rangeFilter === 'custom') {
            const startDateStr = $('#start-date').val();
            const endDateStr = $('#end-date').val();
            if (startDateStr && endDateStr) {
                const start = new Date(startDateStr);
                const end = new Date(endDateStr);
                end.setHours(23, 59, 59, 999);
                filtered = filtered.filter(item => {
                    const itemDate = new Date(item.date);
                    return itemDate >= start && itemDate <= end;
                });
            }
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
