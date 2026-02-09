(function () {
    function text(id, value) {
        var node = document.getElementById(id);
        if (node) {
            node.textContent = value;
        }
    }

    function toTwoDigits(value) {
        var num = parseInt(value, 10) || 0;
        return String(num).padStart(2, '0');
    }

    function loadJsonScript(id, fallback) {
        var node = document.getElementById(id);
        if (!node) return fallback;
        try {
            return JSON.parse(node.textContent);
        } catch (_error) {
            return fallback;
        }
    }

    function parseTimeLabel(isoValue) {
        if (!isoValue) return '';
        var date = new Date(isoValue);
        if (Number.isNaN(date.getTime())) return '';
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    var statusData = loadJsonScript('status-distribution-data', {
        airborne: 0,
        landed: 0,
        scheduled: 0,
        delayed: 0,
        cancelled: 0,
    });

    var altitudeTrend = loadJsonScript('altitude-trend-data', []);
    var ghanaBbox = loadJsonScript('ghana-bbox-data', {
        lamin: 4.5,
        lomin: -3.5,
        lamax: 11.5,
        lomax: 1.5,
    });
    var scopeOptions = loadJsonScript('opensky-scopes-data', []);
    var selectedScope = loadJsonScript('opensky-default-scope-data', 'africa');
    var openskyFeedUrl = loadJsonScript('opensky-feed-url-data', '/dashboard/api/opensky/');
    var openskyLegacyFeedUrl = loadJsonScript('opensky-legacy-feed-url-data', '/dashboard/api/opensky/ghana/');
    var feedCandidates = [openskyFeedUrl, openskyLegacyFeedUrl];
    var preferredFeedUrl = openskyFeedUrl;

    var statusChart = null;
    var altitudeChart = null;
    var mapInstance = null;
    var flightLayer = null;
    var mapScope = selectedScope;

    function chartTheme() {
        return {
            font: {
                family: "'Segoe UI', sans-serif",
                size: 11,
            },
            color: '#6f7687',
        };
    }

    function createCharts() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.font = chartTheme().font;
        Chart.defaults.color = chartTheme().color;

        var statusCtx = document.getElementById('status-chart');
        if (statusCtx) {
            statusChart = new Chart(statusCtx, {
                type: 'bar',
                data: {
                    labels: ['Airborne', 'Landed', 'Scheduled', 'Delayed', 'Cancelled'],
                    datasets: [
                        {
                            data: [
                                statusData.airborne || 0,
                                statusData.landed || 0,
                                statusData.scheduled || 0,
                                statusData.delayed || 0,
                                statusData.cancelled || 0,
                            ],
                            backgroundColor: ['#5b6cff', '#ea4c89', '#7a7f89', '#ef4444', '#c9ced8'],
                            borderRadius: 8,
                            borderSkipped: false,
                            maxBarThickness: 30,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                        },
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                            grid: { color: '#edf0f6' },
                        },
                    },
                },
            });
        }

        var altitudeCtx = document.getElementById('altitude-chart');
        if (altitudeCtx) {
            altitudeChart = new Chart(altitudeCtx, {
                type: 'line',
                data: {
                    labels: altitudeTrend.map(function (row) {
                        return row.time;
                    }),
                    datasets: [
                        {
                            data: altitudeTrend.map(function (row) {
                                return row.altitude;
                            }),
                            borderColor: '#ec4899',
                            backgroundColor: 'rgba(236, 72, 153, 0.14)',
                            borderWidth: 2.5,
                            pointRadius: 0,
                            tension: 0.35,
                            fill: false,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                        },
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                            grid: { color: '#edf0f6' },
                        },
                    },
                },
            });
        }
    }

    function refreshStatusChart(distribution) {
        if (!statusChart || !distribution) return;
        statusChart.data.datasets[0].data = [
            distribution.airborne || 0,
            distribution.landed || 0,
            distribution.scheduled || 0,
            distribution.delayed || 0,
            distribution.cancelled || 0,
        ];
        statusChart.update('none');
    }

    function refreshAltitudeChart(trendRows) {
        if (!altitudeChart || !trendRows) return;
        altitudeChart.data.labels = trendRows.map(function (row) {
            return row.time;
        });
        altitudeChart.data.datasets[0].data = trendRows.map(function (row) {
            return row.altitude;
        });
        altitudeChart.update('none');
    }

    function refreshMetrics(metrics) {
        if (!metrics) return;
        text('metric-flights-today', metrics.flights_today || 0);
        text('metric-active-missions', toTwoDigits(metrics.active_missions || 0));

        var onTime = Number(metrics.on_time_departure_rate || 0).toFixed(1);
        text('metric-on-time-rate', onTime + '%');
        text('metric-delayed-arrivals', toTwoDigits(metrics.delayed_arrivals || 0));

        if (metrics.live_feed) {
            text('feed-speed', metrics.live_feed.speed_knots || 0);
            text('feed-altitude', metrics.live_feed.altitude_feet || 0);
            text('feed-flight-level', metrics.live_feed.flight_level || 'FL000');
            text('feed-mach', metrics.live_feed.mach || 0);
            text('metric-last-updated', metrics.live_feed.updated_time || 'N/A');
        }

        refreshStatusChart(metrics.status_distribution || {});
        refreshAltitudeChart(metrics.altitude_trend || []);
    }

    function initOpenSkyMap() {
        if (typeof L === 'undefined') {
            text('map-status', 'Map engine unavailable in this browser.');
            return;
        }

        var node = document.getElementById('opensky-map');
        if (!node) return;

        mapInstance = L.map(node, {
            zoomControl: true,
            attributionControl: true,
            minZoom: 2,
            maxZoom: 11,
        });

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 19,
            attribution: '&copy; OpenSky Network &copy; Esri',
        }).addTo(mapInstance);

        var ghanaBounds = [
            [ghanaBbox.lamin || 4.5, ghanaBbox.lomin || -3.5],
            [ghanaBbox.lamax || 11.5, ghanaBbox.lomax || 1.5],
        ];

        L.rectangle(ghanaBounds, {
            color: '#6478ff',
            weight: 1,
            fill: false,
            dashArray: '5,5',
        }).addTo(mapInstance);

        mapInstance.setView([8, 0], 3);
        flightLayer = L.layerGroup().addTo(mapInstance);
    }

    function buildFlightMarkerIcon(flight) {
        var heading = Number(flight && flight.heading ? flight.heading : 0);
        if (!Number.isFinite(heading)) {
            heading = 0;
        }

        var markerClass = 'flight-marker flight-marker-airborne';
        if (flight && flight.on_ground) {
            markerClass = 'flight-marker flight-marker-ground';
        }
        if (flight && flight.is_demo) {
            markerClass = markerClass + ' flight-marker-demo';
        }

        var iconHtml =
            '<div class="' + markerClass + '" style="transform: rotate(' + heading + 'deg)">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true">' +
            '<path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2.5 1.5V22l4-1 4 1v-1.5L13 19v-5.5L21 16z"/>' +
            '</svg>' +
            '</div>';

        return L.divIcon({
            className: 'flight-div-icon',
            html: iconHtml,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            popupAnchor: [0, -12],
        });
    }

    function renderOpenSkyFlights(feed) {
        if (!mapInstance || !flightLayer) return;

        var flights = (feed && feed.flights) ? feed.flights : [];
        var scope = (feed && feed.query_scope) ? feed.query_scope : selectedScope;
        var scopeLabel = (feed && feed.query_scope_label) ? feed.query_scope_label : scope;
        var queryBox = (feed && feed.query_bbox) ? feed.query_bbox : null;
        var simulated = !!(feed && feed.simulated);
        flightLayer.clearLayers();
        text('map-active-count', flights.length);

        if (scope !== mapScope || queryBox) {
            mapScope = scope;
            if (queryBox && typeof queryBox.lamin !== 'undefined' && typeof queryBox.lomin !== 'undefined') {
                mapInstance.fitBounds([
                    [queryBox.lamin, queryBox.lomin],
                    [queryBox.lamax, queryBox.lomax],
                ], { padding: [12, 12] });
            } else {
                mapInstance.setView([8, 0], 3);
            }
        }

        if (!flights.length) {
            text('map-status', 'No OpenSky flights currently reported for ' + scopeLabel + '.');
            text('map-updated', '');
            return;
        }

        flights.forEach(function (flight) {
            var marker = L.marker(
                [flight.latitude, flight.longitude],
                { icon: buildFlightMarkerIcon(flight) }
            );

            var popup =
                '<strong>' + (flight.callsign || flight.icao24 || 'Unknown') + '</strong><br>' +
                'Origin: ' + (flight.origin_country || 'N/A') + '<br>' +
                'Speed: ' + (flight.speed_knots || 0) + ' knots<br>' +
                'Altitude: ' + (flight.altitude_ft || 0) + ' ft<br>' +
                'Heading: ' + (flight.heading || 0) + '°' +
                (flight.is_demo ? '<br><em>Simulated</em>' : '');

            marker.bindPopup(popup);
            marker.addTo(flightLayer);
        });

        if (simulated) {
            text('map-status', 'OpenSky unavailable. Showing simulated demo flights for ' + scopeLabel + '.');
        } else {
            text('map-status', 'OpenSky feed active for ' + scopeLabel + '.');
        }
        text('map-updated', feed.generated_at ? 'Updated ' + parseTimeLabel(feed.generated_at) : '');
    }

    function refreshOpenSkyFeed(scope) {
        var activeScope = scope || selectedScope;
        var orderedCandidates = [preferredFeedUrl]
            .concat(feedCandidates.filter(function (candidate) {
                return candidate && candidate !== preferredFeedUrl;
            }));

        function buildFeedUrl(baseUrl) {
            if (!baseUrl) return '';
            var separator = baseUrl.indexOf('?') === -1 ? '?' : '&';
            return baseUrl + separator + 'scope=' + encodeURIComponent(activeScope);
        }

        function parseJsonResponse(response) {
            if (response.redirected && response.url.indexOf('/accounts/login/') !== -1) {
                throw new Error('Session expired. Please log in again.');
            }
            if (!response.ok) {
                throw new Error('OpenSky endpoint returned HTTP ' + response.status + '.');
            }
            return response.text().then(function (rawText) {
                try {
                    return JSON.parse(rawText);
                } catch (_error) {
                    throw new Error('OpenSky endpoint returned non-JSON response.');
                }
            });
        }

        function attemptFetch(index) {
            if (index >= orderedCandidates.length) {
                return Promise.reject(new Error('Unable to reach OpenSky feed. Retrying...'));
            }

            var candidate = orderedCandidates[index];
            return fetch(buildFeedUrl(candidate), {
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                },
                cache: 'no-store',
            })
                .then(parseJsonResponse)
                .then(function (data) {
                    preferredFeedUrl = candidate;
                    return data;
                })
                .catch(function (error) {
                    if (index + 1 < orderedCandidates.length) {
                        return attemptFetch(index + 1);
                    }
                    throw error;
                });
        }

        attemptFetch(0)
            .then(function (data) {
                renderOpenSkyFlights(data);
            })
            .catch(function (error) {
                text('map-status', error && error.message ? error.message : 'Unable to reach OpenSky feed. Retrying...');
                text('map-updated', '');
            });
    }

    function initScopeSelector() {
        var selector = document.getElementById('map-scope-select');
        if (!selector) return;

        if (!scopeOptions || !scopeOptions.length) {
            selector.disabled = true;
            return;
        }

        if (selectedScope) {
            selector.value = selectedScope;
        }

        selector.addEventListener('change', function () {
            selectedScope = selector.value || selectedScope;
            text('map-status', 'Loading OpenSky ' + selectedScope + ' feed...');
            refreshOpenSkyFeed(selectedScope);
        });
    }

    createCharts();
    initOpenSkyMap();
    initScopeSelector();
    refreshOpenSkyFeed(selectedScope);
    window.setInterval(function () {
        refreshOpenSkyFeed(selectedScope);
    }, 30000);

    var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    var wsUrl = protocol + window.location.host + '/ws/dashboard/';
    var reconnectAttempts = 0;
    var reconnectTimer = null;

    function scheduleReconnect() {
        if (reconnectTimer) {
            return;
        }
        var delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts));
        reconnectAttempts += 1;
        reconnectTimer = window.setTimeout(function () {
            reconnectTimer = null;
            connectDashboardSocket();
        }, delay);
    }

    function connectDashboardSocket() {
        var socket = new WebSocket(wsUrl);

        socket.onopen = function () {
            reconnectAttempts = 0;
        };

        socket.onmessage = function (event) {
            var data = JSON.parse(event.data);
            refreshMetrics(data.metrics);
        };

        socket.onerror = function () {
            socket.close();
        };

        socket.onclose = function () {
            scheduleReconnect();
        };
    }

    connectDashboardSocket();
})();
