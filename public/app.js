/* ╔══════════════════════════════════════════════════════════╗
   ║        ЛОГІКА КАРТИ ПОДІЙ СВІТЛОВОДСЬК (TELEGRAM WEBAPP)   ║
   ╚══════════════════════════════════════════════════════════╝ */

const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// API_BASE: якщо карта відкрита з Surge або іншого зовнішнього хоста,
// API запити йдуть на локальний сервер через спеціальний заголовок.
// Surge лише хостить статику — динамічні дані живуть на localhost:8080.
const API_BASE = window.location.hostname === 'svitlovodsk-map.surge.sh'
    ? 'https://svitlovodsk-map-247.onrender.com'
    : '';

let map = null;
let eventsLayer = null;
let routesLayer = null;
let districtsLayer = null;
let userLocMarker = null;

let allEventsData = [];
let routesData = [];
let districtsData = [];
let activeFilter = 'all';
let isRoutesVisible = false;
let isDistrictsVisible = true;
let isPinPickerActive = false;
let tempPickerMarker = null;
let currentOpenedEvent = null;

// Змінні для інтерактивного малювання секторів на карті
let isDrawingSector = false;
let drawPoints = [];
let drawPolygonLayer = null;
let drawVertexMarkers = [];

// Координати Світловодська
let cityCenter = [49.054000, 33.228000];

// Налаштування користувача (з localStorage)
let userSettings = {
    ttl_hours: parseInt(localStorage.getItem('user_ttl_hours')) || 4,
    radius_km: parseInt(localStorage.getItem('user_radius_km')) || 3
};

document.addEventListener('DOMContentLoaded', async () => {
    await loadInitialData();
    initMap();
    setupEventListeners();
    startCountdownTimer();
});

// Завантаження даних з сервера або локального сховища
async function loadInitialData() {
    try {
        const [configRes, eventsRes, routesRes, districtsRes] = await Promise.all([
            fetch(API_BASE + '/api/config').then(r => r.ok ? r.json() : null).catch(() => null),
            fetch(API_BASE + '/api/events').then(r => r.ok ? r.json() : null).catch(() => null),
            fetch(API_BASE + '/api/routes').then(r => r.ok ? r.json() : null).catch(() => null),
            fetch(API_BASE + '/api/districts').then(r => r.ok ? r.json() : null).catch(() => null)
        ]);

        if (configRes && configRes.city_center) {
            cityCenter = [configRes.city_center.lat, configRes.city_center.lng];
        }
        if (configRes && configRes.city_name) {
            document.getElementById('cityTitle').innerText = configRes.city_name;
        }
        if (districtsRes && districtsRes.districts) {
            districtsData = districtsRes.districts;
        }

        allEventsData = (eventsRes && eventsRes.events) ? eventsRes.events : JSON.parse(localStorage.getItem('local_events') || '[]');
        routesData = (routesRes && routesRes.routes) ? routesRes.routes : [];

        document.getElementById('ttlSelect').value = userSettings.ttl_hours.toString();
        document.getElementById('radiusSelect').value = userSettings.radius_km.toString();
    } catch (e) {
        console.error('Помилка завантаження даних:', e);
        allEventsData = JSON.parse(localStorage.getItem('local_events') || '[]');
    }
}

// Ініціалізація карти Leaflet (Світла тема з авто-фолбеком)
function initMap() {
    map = L.map('map', {
        zoomControl: false
    }).setView(cityCenter, 14);

    const osmTile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 19
    });

    const cartoTile = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
        maxZoom: 19
    });

    osmTile.on('tileerror', function() {
        if (map.hasLayer(osmTile)) {
            map.removeLayer(osmTile);
            cartoTile.addTo(map);
        }
    });

    osmTile.addTo(map);

    routesLayer = L.layerGroup().addTo(map);
    eventsLayer = L.layerGroup().addTo(map);

    renderRoutes();
    renderEvents();

    // Клік по карті в режимі вибору точки
    map.on('click', (e) => {
        if (isPinPickerActive) {
            onMapClickPinPicker(e.latlng);
        }
    });
}

// Рендер ліній маршрутів заторів (Зелені / Червоні лінії)
function renderRoutes() {
    if (!routesLayer) return;
    routesLayer.clearLayers();

    if (!isRoutesVisible) return;

    routesData.forEach(route => {
        const color = route.status === 'red' ? '#ef4444' : '#22c55e';
        const polyline = L.polyline(route.coordinates, {
            color: color,
            weight: 5,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round'
        }).bindPopup(`<b>${route.name}</b><br>Стан руху: ${route.status === 'red' ? '🔴 Затор' : '🟢 Вільний'}`);

        routesLayer.addLayer(polyline);
    });
}

// Рендер статусних кіл подій на карті
function renderEvents() {
    if (!eventsLayer) return;
    eventsLayer.clearLayers();

    const filtered = allEventsData.filter(ev => {
        if (activeFilter === 'all') return true;
        return ev.status === activeFilter;
    });

    filtered.forEach(ev => {
        const statusClass = ev.status || 'green';
        let iconHtml = '<i class="fa-solid fa-shield-halved"></i>';
        if (statusClass === 'red') {
            iconHtml = '<i class="fa-solid fa-triangle-exclamation"></i>';
        } else if (statusClass === 'yellow') {
            iconHtml = '<i class="fa-solid fa-circle-question"></i>';
        }

        // Сучасний 3D піновий маркер з неоновим сяйвом та радарним пульсом
        const customIcon = L.divIcon({
            className: 'custom-event-marker-wrapper',
            html: `
                <div class="marker-container ${statusClass}">
                    <div class="marker-pulse-radar ${statusClass}"></div>
                    <div class="marker-pin-head ${statusClass}">
                        ${iconHtml}
                    </div>
                    <div class="marker-pin-tail ${statusClass}"></div>
                </div>
            `,
            iconSize: [38, 48],
            iconAnchor: [19, 46]
        });

        const marker = L.marker([ev.lat, ev.lng], { icon: customIcon });
        
        marker.on('click', () => {
            openEventDetails(ev);
        });

        eventsLayer.addLayer(marker);
    });
}

// Відкриття карточки події (Bottom Sheet)
function openEventDetails(ev) {
    currentOpenedEvent = ev;

    const badge = document.getElementById('eventStatusBadge');
    badge.className = `status-pill ${ev.status}`;

    if (ev.status === 'green') {
        badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Спокійно';
    } else if (ev.status === 'red') {
        badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Щось трапилося';
    } else {
        badge.innerHTML = '<i class="fa-solid fa-circle-question"></i> Під питанням';
    }

    document.getElementById('eventTitle').innerText = ev.title;
    document.getElementById('eventDescription').innerText = ev.description;
    document.getElementById('eventAuthor').innerText = ev.author_name || 'Анонім';

    const createdDate = new Date(ev.created_at * 1000);
    document.getElementById('eventCreated').innerText = createdDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    document.getElementById('agreeCount').innerText = ev.upvotes || 0;
    document.getElementById('disagreeCount').innerText = ev.downvotes || 0;

    updateCountdownText(ev);

    document.getElementById('eventSheet').classList.remove('hidden');
}

function updateCountdownText(ev) {
    const remainingMin = ev.remaining_minutes || 240;
    const hours = Math.floor(remainingMin / 60);
    const mins = remainingMin % 60;
    
    let timeStr = 'Зникне через ';
    if (hours > 0) timeStr += `${hours}г `;
    timeStr += `${mins}хв`;

    document.getElementById('eventTimeCountdown').innerHTML = `<i class="fa-regular fa-clock"></i> ${timeStr}`;
}

function closeEventDetails() {
    document.getElementById('eventSheet').classList.add('hidden');
    currentOpenedEvent = null;
}

// Установка слухачів подій
function setupEventListeners() {
    // Фільтрація по легенді
    document.querySelectorAll('.legend-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.legend-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            activeFilter = item.dataset.filter;
            renderEvents();
        });
    });

    // Перемикач Маршрутів (якщо є)
    const toggleRoutesBtn = document.getElementById('toggleRoutesBtn');
    if (toggleRoutesBtn) {
        toggleRoutesBtn.addEventListener('click', () => {
            isRoutesVisible = !isRoutesVisible;
            toggleRoutesBtn.classList.toggle('active', isRoutesVisible);
            renderRoutes();
            showToast(isRoutesVisible ? 'Шари маршрутів увімкнено' : 'Шари маршрутів вимкнено');
        });
    }

    // Перемикач Районів міста
    const toggleDistrictsBtn = document.getElementById('toggleDistrictsBtn');
    if (toggleDistrictsBtn) {
        toggleDistrictsBtn.addEventListener('click', () => {
            isDistrictsVisible = !isDistrictsVisible;
            toggleDistrictsBtn.classList.toggle('active', isDistrictsVisible);
            renderDistricts();
            showToast(isDistrictsVisible ? 'Показ районів увімкнено' : 'Показ районів вимкнено');
        });
    }

    const openDistrictsEditBtn = document.getElementById('openDistrictsEditBtn');
    if (openDistrictsEditBtn) {
        openDistrictsEditBtn.addEventListener('click', () => {
            startDrawingSector();
        });
    }

    const finishDrawSectorBtn = document.getElementById('finishDrawSectorBtn');
    if (finishDrawSectorBtn) {
        finishDrawSectorBtn.addEventListener('click', finishDrawingSector);
    }

    const resetDrawSectorBtn = document.getElementById('resetDrawSectorBtn');
    if (resetDrawSectorBtn) {
        resetDrawSectorBtn.addEventListener('click', resetDrawingSector);
    }

    const cancelDrawSectorBtn = document.getElementById('cancelDrawSectorBtn');
    if (cancelDrawSectorBtn) {
        cancelDrawSectorBtn.addEventListener('click', cancelDrawingSector);
    }

    const closeSaveSectorModalBtn = document.getElementById('closeSaveSectorModalBtn');
    if (closeSaveSectorModalBtn) {
        closeSaveSectorModalBtn.addEventListener('click', closeSaveSectorModal);
    }

    const cancelSaveSectorBtn = document.getElementById('cancelSaveSectorBtn');
    if (cancelSaveSectorBtn) {
        cancelSaveSectorBtn.addEventListener('click', closeSaveSectorModal);
    }

    const saveSectorForm = document.getElementById('saveSectorForm');
    if (saveSectorForm) {
        saveSectorForm.addEventListener('submit', handleSaveSectorFormSubmit);
    }

    const closeDistrictsModalBtn = document.getElementById('closeDistrictsModalBtn');
    if (closeDistrictsModalBtn) {
        closeDistrictsModalBtn.addEventListener('click', closeDistrictsModal);
    }

    const cancelDistrictsBtn = document.getElementById('cancelDistrictsBtn');
    if (cancelDistrictsBtn) {
        cancelDistrictsBtn.addEventListener('click', closeDistrictsModal);
    }

    const districtsModalBackdrop = document.getElementById('districtsModalBackdrop');
    if (districtsModalBackdrop) {
        districtsModalBackdrop.addEventListener('click', closeDistrictsModal);
    }

    const addNewDistrictBtn = document.getElementById('addNewDistrictBtn');
    if (addNewDistrictBtn) {
        addNewDistrictBtn.addEventListener('click', () => {
            districtsData.push({
                id: 'dist_' + Date.now(),
                name: 'Новий район',
                color: '#3b82f6',
                center: [cityCenter[0], cityCenter[1]],
                coordinates: [
                    [cityCenter[0] + 0.003, cityCenter[1] - 0.005],
                    [cityCenter[0] + 0.003, cityCenter[1] + 0.005],
                    [cityCenter[0] - 0.003, cityCenter[1] + 0.005],
                    [cityCenter[0] - 0.003, cityCenter[1] - 0.005]
                ]
            });
            renderDistrictsList();
        });
    }

    const saveDistrictsBtn = document.getElementById('saveDistrictsBtn');
    if (saveDistrictsBtn) {
        saveDistrictsBtn.addEventListener('click', saveDistricts);
    }

    // Кнопка "Навігація" (GPS)
    document.getElementById('navLocationFab').addEventListener('click', locateUser);

    // Кнопка "+" (Додати мітку) - відразу відкриває модальне вікно з координатами центру карти
    document.getElementById('addEventFab').addEventListener('click', handleAddFabClick);
    document.getElementById('cancelPinBtn').addEventListener('click', stopPinPicker);
    
    const pickBtn = document.getElementById('pickOnMapBtn');
    if (pickBtn) {
        pickBtn.addEventListener('click', () => {
            closeAddModal();
            startPinPicker();
        });
    }

    // Закриття Bottom Sheet
    document.getElementById('closeSheetBtn').addEventListener('click', closeEventDetails);
    document.getElementById('sheetBackdrop').addEventListener('click', closeEventDetails);

    // Кнопки голосування
    document.getElementById('btnAgree').addEventListener('click', () => castVote('up'));
    document.getElementById('btnDisagree').addEventListener('click', () => castVote('down'));

    // Модальне вікно додавання
    document.getElementById('closeAddModalBtn').addEventListener('click', closeAddModal);
    document.getElementById('cancelAddBtn').addEventListener('click', closeAddModal);
    document.getElementById('addModalBackdrop').addEventListener('click', closeAddModal);
    document.getElementById('addEventForm').addEventListener('submit', handleAddEventSubmit);

    // Модальне вікно налаштувань
    document.getElementById('openSettingsBtn').addEventListener('click', openSettingsModal);
    document.getElementById('closeSettingsBtn').addEventListener('click', closeSettingsModal);
    document.getElementById('settingsModalBackdrop').addEventListener('click', closeSettingsModal);
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
}

// Обробник клика на FAB "+"
function handleAddFabClick() {
    const center = map ? map.getCenter() : { lat: cityCenter[0], lng: cityCenter[1] };
    document.getElementById('inputLat').value = center.lat.toFixed(6);
    document.getElementById('inputLng').value = center.lng.toFixed(6);
    openAddModal();
}

// Навігація до поточного місця користувача
function locateUser() {
    if (!navigator.geolocation) {
        showToast('Геолокація не підтримується');
        return;
    }
    showToast('Визначаємо вашу геолокацію...');
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const { latitude, longitude } = pos.coords;
            map.flyTo([latitude, longitude], 16);

            if (userLocMarker) map.removeLayer(userLocMarker);

            userLocMarker = L.circleMarker([latitude, longitude], {
                radius: 9,
                color: '#ffffff',
                weight: 2,
                fillColor: '#3b82f6',
                fillOpacity: 0.9
            }).addTo(map).bindPopup('<b>Ви тут!</b>').openPopup();
        },
        (err) => {
            console.error(err);
            showToast('Не вдалося отримати GPS-координати');
        }
    );
}

// Режим вибору точки на карті
function startPinPicker() {
    isPinPickerActive = true;
    document.getElementById('pinNotice').classList.remove('hidden');
    document.getElementById('addEventFab').classList.add('hidden');
    document.getElementById('navLocationFab').classList.add('hidden');
    showToast('Клікніть на потрібне місце на карті Світловодська');
}

function stopPinPicker() {
    isPinPickerActive = false;
    document.getElementById('pinNotice').classList.add('hidden');
    document.getElementById('addEventFab').classList.remove('hidden');
    document.getElementById('navLocationFab').classList.remove('hidden');

    if (tempPickerMarker) {
        map.removeLayer(tempPickerMarker);
        tempPickerMarker = null;
    }
}

function onMapClickPinPicker(latlng) {
    if (tempPickerMarker) map.removeLayer(tempPickerMarker);

    tempPickerMarker = L.marker([latlng.lat, latlng.lng]).addTo(map);

    document.getElementById('inputLat').value = latlng.lat.toFixed(6);
    document.getElementById('inputLng').value = latlng.lng.toFixed(6);

    stopPinPicker();
    openAddModal();
}

function openAddModal() {
    document.getElementById('addModal').classList.remove('hidden');
}

function closeAddModal() {
    document.getElementById('addModal').classList.add('hidden');
    document.getElementById('addEventForm').reset();
}

// Додавання нової події
async function handleAddEventSubmit(e) {
    e.preventDefault();

    const selectedRadio = document.querySelector('input[name="statusRadio"]:checked');
    const selectedStatus = selectedRadio ? selectedRadio.value : 'green';
    const user = tg?.initDataUnsafe?.user;
    const authorName = user ? (user.first_name + (user.last_name ? ' ' + user.last_name : '')) : 'Користувач';
    const authorId = user ? user.id : 0;

    let latVal = parseFloat(document.getElementById('inputLat').value);
    let lngVal = parseFloat(document.getElementById('inputLng').value);

    if (isNaN(latVal) || isNaN(lngVal)) {
        const center = map ? map.getCenter() : { lat: cityCenter[0], lng: cityCenter[1] };
        latVal = center.lat;
        lngVal = center.lng;
    }

    const payload = {
        status: selectedStatus,
        title: document.getElementById('eventTitleInput').value.trim(),
        description: document.getElementById('eventDescInput').value.trim(),
        lat: latVal,
        lng: lngVal,
        author_name: authorName,
        author_id: authorId,
        custom_ttl_hours: userSettings.ttl_hours
    };

    try {
        const res = await fetch(API_BASE + '/api/events/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(r => r.ok ? r.json() : null).catch(() => null);

        if (res && res.success) {
            closeAddModal();
            showToast('Подію успішно додано на карту!');
            await reloadEvents();
        } else {
            // Фолбек для локального додавання
            const localEv = {
                id: 'local_' + Date.now(),
                ...payload,
                created_at: Math.floor(Date.now() / 1000),
                expires_at: Math.floor(Date.now() / 1000) + (userSettings.ttl_hours * 3600),
                upvotes: 1,
                downvotes: 0,
                remaining_minutes: userSettings.ttl_hours * 60,
                voted_users: {}
            };
            allEventsData.unshift(localEv);
            localStorage.setItem('local_events', JSON.stringify(allEventsData));
            closeAddModal();
            renderEvents();
            showToast('Подію додано локально на карту!');
        }
    } catch (err) {
        console.error(err);
        closeAddModal();
        renderEvents();
    }
}

// Голосування (Погодитися / Не погодитися)
async function castVote(voteType) {
    if (!currentOpenedEvent) return;

    const user = tg?.initDataUnsafe?.user;
    const userId = user ? user.id : 12345;

    try {
        const res = await fetch(API_BASE + '/api/events/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_id: currentOpenedEvent.id,
                user_id: userId,
                vote_type: voteType
            })
        }).then(r => r.json());

        if (res.success) {
            showToast(voteType === 'up' ? 'Дякуємо! Час події подовжено на +30 хв' : 'Голос прийнято! Час події скорочено на -30 хв');
            currentOpenedEvent = res.event;
            document.getElementById('agreeCount').innerText = currentOpenedEvent.upvotes || 0;
            document.getElementById('disagreeCount').innerText = currentOpenedEvent.downvotes || 0;
            updateCountdownText(currentOpenedEvent);
            await reloadEvents();
        } else {
            showToast(res.message || 'Ви вже голосували');
        }
    } catch (err) {
        console.error(err);
        showToast('Не вдалося відправити голос');
    }
}

// Перезавантаження подій
async function reloadEvents() {
    try {
        const eventsRes = await fetch(API_BASE + '/api/events').then(r => r.json());
        allEventsData = eventsRes.events || [];
        renderEvents();
    } catch (e) {
        console.error(e);
    }
}

// Налаштування
function openSettingsModal() {
    document.getElementById('settingsModal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settingsModal').classList.add('hidden');
}

function saveSettings() {
    const ttl = parseInt(document.getElementById('ttlSelect').value);
    const radius = parseInt(document.getElementById('radiusSelect').value);

    userSettings.ttl_hours = ttl;
    userSettings.radius_km = radius;

    localStorage.setItem('user_ttl_hours', ttl);
    localStorage.setItem('user_radius_km', radius);

    closeSettingsModal();
    showToast(`Налаштування збережено: ${ttl} год відображення, ${radius} км радіус`);
    reloadEvents();
}

// Фоновий таймер відліку та авто-опитування нових подій з Telegram
function startCountdownTimer() {
    // Оновлення залишку хвилин щохвилини
    setInterval(() => {
        allEventsData.forEach(ev => {
            if (ev.remaining_minutes && ev.remaining_minutes > 0) {
                ev.remaining_minutes -= 1;
            }
        });
        if (currentOpenedEvent) {
            updateCountdownText(currentOpenedEvent);
        }
    }, 60000);

    // Автоматична перевірка та завантаження нових меток з сервера кожні 10 секунд (Real-Time з Telegram)
    setInterval(() => {
        reloadEvents();
    }, 10000);
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3500);
}

// --- ВІДОБРАЖЕННЯ ТА УПРАВЛІННЯ РАЙОНАМИ / СЕКТОРАМИ ---
function renderDistricts() {
    if (!districtsLayer) return;
    districtsLayer.clearLayers();
    if (!isDistrictsVisible) return;

    districtsData.forEach(d => {
        if (!d.coordinates || d.coordinates.length < 3) return;

        // Створюємо полігон району
        const polygon = L.polygon(d.coordinates, {
            color: d.color || '#3b82f6',
            fillColor: d.color || '#3b82f6',
            fillOpacity: 0.18,
            weight: 2,
            dashArray: '5, 5'
        });

        polygon.bindPopup(`
            <div style="font-family: 'Inter', sans-serif;">
                <b style="font-size: 15px; color: ${d.color || '#1e293b'};">${d.name}</b><br>
                <span style="font-size: 12px; color: #64748b;">Сектор / Район Світловодська</span>
            </div>
        `);

        districtsLayer.addLayer(polygon);

        // Напис з назвою району в центрі
        const center = d.center || d.coordinates[0];
        const labelIcon = L.divIcon({
            className: 'district-label-container',
            html: `<div class="district-label-marker" style="border-left: 3px solid ${d.color || '#3b82f6'};">${d.name}</div>`,
            iconSize: [140, 24],
            iconAnchor: [70, 12]
        });

        const labelMarker = L.marker(center, { icon: labelIcon, interactive: false });
        districtsLayer.addLayer(labelMarker);
    });
}

function openDistrictsModal() {
    renderDistrictsList();
    document.getElementById('districtsModal').classList.remove('hidden');
}

function closeDistrictsModal() {
    document.getElementById('districtsModal').classList.add('hidden');
}

// --- ЛОГІКА ІНТЕРАКТИВНОГО МАЛЮВАННЯ СЕКТОРІВ НА КАРТІ ---
function startDrawingSector() {
    isDrawingSector = true;
    drawPoints = [];
    clearDrawingPreview();

    const banner = document.getElementById('drawSectorBanner');
    if (banner) banner.classList.remove('hidden');

    const statusEl = document.getElementById('drawSectorStatus');
    if (statusEl) statusEl.innerText = 'Малювання сектора: ставте точки на карті (точок: 0)';

    showToast('Режим малювання: натискайте на карту, щоб поставити точки межі сектора');
}

function onMapClickDrawingSector(latlng) {
    drawPoints.push([latlng.lat, latlng.lng]);

    // Додаємо вершину (маркер)
    const marker = L.circleMarker([latlng.lat, latlng.lng], {
        radius: 6,
        color: '#ffffff',
        fillColor: '#ef4444',
        fillOpacity: 1,
        weight: 2
    }).addTo(map);
    drawVertexMarkers.push(marker);

    updateDrawingPreview();
}

function updateDrawingPreview() {
    const statusEl = document.getElementById('drawSectorStatus');
    if (statusEl) statusEl.innerText = `Малювання сектора: ставте точки на карті (точок: ${drawPoints.length})`;

    if (drawPolygonLayer) {
        map.removeLayer(drawPolygonLayer);
        drawPolygonLayer = null;
    }

    if (drawPoints.length >= 2) {
        drawPolygonLayer = L.polygon(drawPoints, {
            color: '#ef4444',
            fillColor: '#ef4444',
            fillOpacity: 0.25,
            weight: 3,
            dashArray: '4, 4'
        }).addTo(map);
    }
}

function resetDrawingSector() {
    drawPoints = [];
    clearDrawingPreview();
    const statusEl = document.getElementById('drawSectorStatus');
    if (statusEl) statusEl.innerText = 'Малювання сектора: ставте точки на карті (точок: 0)';
}

function cancelDrawingSector() {
    isDrawingSector = false;
    drawPoints = [];
    clearDrawingPreview();
    const banner = document.getElementById('drawSectorBanner');
    if (banner) banner.classList.add('hidden');
    showToast('Малювання сектора скасовано');
}

function clearDrawingPreview() {
    if (drawPolygonLayer) {
        map.removeLayer(drawPolygonLayer);
        drawPolygonLayer = null;
    }
    drawVertexMarkers.forEach(m => map.removeLayer(m));
    drawVertexMarkers = [];
}

function finishDrawingSector() {
    if (drawPoints.length < 3) {
        showToast('Потрібно поставити мінімум 3 точки для створення сектора');
        return;
    }

    // Відкриваємо модалку збереження
    const modal = document.getElementById('saveSectorModal');
    if (modal) modal.classList.remove('hidden');

    const nameInput = document.getElementById('sectorNameInput');
    if (nameInput) {
        nameInput.value = `Сектор ${districtsData.length + 1}`;
        nameInput.focus();
    }
}

function closeSaveSectorModal() {
    const modal = document.getElementById('saveSectorModal');
    if (modal) modal.classList.add('hidden');
}

async function handleSaveSectorFormSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('sectorNameInput').value.trim();
    const color = document.getElementById('sectorColorInput').value;

    if (!name) {
        showToast('Введіть назву сектора');
        return;
    }

    // Розраховуємо центр сектора
    let sumLat = 0, sumLng = 0;
    drawPoints.forEach(p => { sumLat += p[0]; sumLng += p[1]; });
    const center = [sumLat / drawPoints.length, sumLng / drawPoints.length];

    const newSector = {
        id: 'sec_' + Date.now(),
        name: name,
        color: color,
        keywords: [name.toLowerCase()],
        center: center,
        coordinates: drawPoints
    };

    districtsData.push(newSector);

    // Зберігаємо на сервер
    await saveDistricts();

    // Очищаємо режим малювання
    closeSaveSectorModal();
    cancelDrawingSector();

    // Гарантуємо ввімкнений шар районів
    isDistrictsVisible = true;
    const btn = document.getElementById('toggleDistrictsBtn');
    if (btn) btn.classList.add('active');
    renderDistricts();

    showToast(`Сектор "${name}" успішно створено та збережено!`);
}

function renderDistrictsList() {
    const list = document.getElementById('districtsList');
    if (!list) return;
    list.innerHTML = '';

    districtsData.forEach((d, idx) => {
        const coordsStr = JSON.stringify(d.coordinates);
        const card = document.createElement('div');
        card.className = 'district-item-card';
        card.innerHTML = `
            <div class="district-card-header">
                <input type="color" class="district-color-input" value="${d.color || '#3b82f6'}" data-idx="${idx}" key="color" />
                <input type="text" class="form-group district-name-input" value="${d.name}" placeholder="Назва району" data-idx="${idx}" key="name" />
                <button type="button" class="btn-secondary btn-sm remove-dist-btn" data-idx="${idx}"><i class="fa-solid fa-trash" style="color: #ef4444;"></i> Видалити</button>
            </div>
            <div class="form-group">
                <label>Межі району (координати масивом [lat, lng]):</label>
                <textarea rows="3" class="district-coords-textarea district-coords-input" data-idx="${idx}">${coordsStr}</textarea>
            </div>
        `;
        list.appendChild(card);
    });

    // Зміна кольору та назви
    list.querySelectorAll('.district-color-input, .district-name-input').forEach(el => {
        el.addEventListener('input', (e) => {
            const idx = parseInt(e.target.getAttribute('data-idx'));
            const key = e.target.getAttribute('key');
            districtsData[idx][key] = e.target.value;
        });
    });

    // Зміна координат у форматі JSON
    list.querySelectorAll('.district-coords-textarea').forEach(el => {
        el.addEventListener('change', (e) => {
            const idx = parseInt(e.target.getAttribute('data-idx'));
            try {
                const parsed = JSON.parse(e.target.value);
                if (Array.isArray(parsed)) {
                    districtsData[idx].coordinates = parsed;
                    let sumLat = 0, sumLng = 0;
                    parsed.forEach(p => { sumLat += p[0]; sumLng += p[1]; });
                    districtsData[idx].center = [sumLat / parsed.length, sumLng / parsed.length];
                }
            } catch (err) {
                showToast('Невірний формат координат');
            }
        });
    });

    // Видалення району
    list.querySelectorAll('.remove-dist-btn').forEach(el => {
        el.addEventListener('click', (e) => {
            const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
            districtsData.splice(idx, 1);
            renderDistrictsList();
        });
    });
}

async function saveDistricts() {
    try {
        const res = await fetch(API_BASE + '/api/districts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ districts: districtsData })
        }).then(r => r.json());

        if (res.success) {
            showToast('Райони успішно збережено!');
            closeDistrictsModal();
            renderDistricts();
        } else {
            showToast('Помилка збереження районів');
        }
    } catch (err) {
        console.error(err);
        showToast('Не вдалося зберегти райони');
    }
}
