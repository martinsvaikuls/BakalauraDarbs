
let map;
let markers = [];
let routeLayers = [];

const OBJECT_TYPES = ["technicians", "tasks", "depots", "shops"];
const colorMap = { technicians: "green", tasks: "orange", shops: "purple", depots: "blue" };
const rowColorMap = {
    tech: "rgba(0, 128, 0, 0.08)",
    task: "rgba(255, 165, 0, 0.08)",
    shop: "rgba(128, 0, 128, 0.08)",
    depot: "rgba(0, 0, 255, 0.08)"
};
//tr.style.borderLeft = `4px solid ${solidColorMap[type]}`;
const radiusMap = { technicians: 4, tasks: 4, depots: 6, shops: 6 };
const opacityMap = { technicians: 0.5, tasks: 0.8, depots: 0.9, shops: 0.9 };

// --------------------
// --- UI Functions ---
// --------------------
function toggleSection(showId) {
    const sections = ["login-section", "register-section", "app-section"];
    sections.forEach(id => document.getElementById(id).style.display = (id === showId ? "block" : "none"));
}

function showRegister() { toggleSection("register-section"); }
function showLogin() { toggleSection("login-section"); }

function showApp(user) {
    const token = localStorage.getItem("token");
    if (!token) return showLogin();
    toggleSection("app-section");
    document.getElementById("welcome-msg").innerText = `Welcome!`;
    
    initMap();  // must be first
    loadAllObjects();
}

// --------------------
// --- Auth Functions ---
// --------------------
async function authRequest(url, payload) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    return await res.json();
}

async function handleLogin() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const data = await authRequest("/clients/login", { email, password });
    if (data.token) {
        localStorage.setItem("token", data.token);
        showApp(data);
    } else {
        document.getElementById("login-msg").innerText = data.error || "Login failed";
    }
}

async function handleRegister() {
    const name = document.getElementById("register-name").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;
    const data = await authRequest("/clients/register", { client_name: name, email, password });

    if (data.token) {
        localStorage.setItem("token", data.token);
        alert(`Account created! Welcome ${data.client_name}`);
        showLogin();
    } else {
        document.getElementById("register-msg").innerText = data.error || "Registration failed";
    }
}

function logout() {
    if (!localStorage.getItem("token")) return alert("Already logged out!");
    localStorage.removeItem("token");
    document.getElementById("map").innerHTML = "";
    toggleSection("login-section");
}

// --------------------
// --- Map Functions ---
// --------------------
let lastMove = 0;

function initMap() {
    if (map) return; // prevent re-init

    map = L.map('map', {
        maxZoom: 18,
        minZoom: 3,
        zoomControl: true,
        fadeAnimation: false,
        updateWhenIdle: true,   // tiles load only after panning/zooming stops
        updateWhenZooming: false
    }).setView([56.9496, 24.1052], 10);

    // OSM tiles (light usage, safe for demo)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        subdomains: ['a', 'b', 'c'],
        maxZoom: 19,
        detectRetina: true
    }).addTo(map);
}

// --------------------
// --- Route Functions ---
// --------------------
let pollInterval = null;

async function runALNS() {

    const token = localStorage.getItem("token");

    try {

        polling = false;

        // Clear previous routes
        if (window.routeLayers) {

            window.routeLayers.forEach(layer => {
                map.removeLayer(layer);
            });
        }

        window.routeLayers = [];

        // Remove previous route tables
        const oldSection =
            document.getElementById("section-routes");

        if (oldSection) {
            oldSection.remove();
        }

        // Start ALNS
        const res = await fetch("/planning/run", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {

            const text = await res.text();

            alert("ALNS failed: " + text);

            return;
        }

        polling = true;

        pollRoutes();

    } catch (err) {

        alert("ALNS request error: " + err);
    }
}

async function pollRoutes() {

    if (!polling) return;

    try {

        const res =
            await fetch("/planning/routes/current");

        const data = await res.json();

        document.getElementById("iteration-label").innerText =
            `Iteration: ${data.iteration.current} / ${data.iteration.total}`;

        document.getElementById("tasks-label").innerText =
            `Tasks left in iteration: ${data.tasks.tasks}`;

        renderRoutes(data.routes);

        renderRoutesList(data.routes);

        await loadMetrics();

        // Stop polling
        if (data.iteration.current >= data.iteration.total) {

            polling = false;

            console.log("ALNS finished");

            return;
        }

    } catch (err) {

        console.error(
            "Failed to load current routes:",
            err
        );
    }

    // Poll every 5 seconds
    setTimeout(pollRoutes, 5000);
}

// --------------------
// --- Route Rendering ---
// --------------------

function renderRoutes(routes) {

    if (window.routeLayers) {

        window.routeLayers.forEach(layer => {
            map.removeLayer(layer);
        });
    }

    window.routeLayers = [];

    routes.forEach(route => {

        if (!route.coords || route.coords.length === 0) {
            return;
        }

        const latlngs = route.coords
            .map(p => [
                parseFloat(p.lat),
                parseFloat(p.long)
            ])
            .filter(p =>
                !isNaN(p[0]) && !isNaN(p[1])
            );

        if (latlngs.length === 0) {
            return;
        }

        const polyline = L.polyline(latlngs, {
            color: "blue",
            opacity: 0.5,
            weight: 3,
            smoothFactor: 1
        }).addTo(map);

        window.routeLayers.push(polyline);
    });
}


function renderRoutesList(routes) {

    const container =
        document.getElementById("objects-container2");

    // Remove old section
    const oldSection =
        document.getElementById("section-routes");

    if (oldSection) {
        oldSection.remove();
    }

    // Create new section
    const section = document.createElement("div");

    section.id = "section-routes";

    section.innerHTML = `<h3>Routes</h3>`;

    routes.forEach(route => {

        if (!route.coords || !Array.isArray(route.coords)) {
            return;
        }

        const routeDiv = document.createElement("div");

        // Route title
        const title = document.createElement("h4");

        title.textContent = `Tech ID: ${route.tech_id}`;

        routeDiv.appendChild(title);

        // Table
        const table = document.createElement("table");

        // Header
        const thead = document.createElement("thead");

        const headerRow = document.createElement("tr");

        ["Type", "ID", "Start Time", "End Time"]
            .forEach(text => {

                const th = document.createElement("th");

                th.textContent = text;

                headerRow.appendChild(th);
            });

        thead.appendChild(headerRow);

        table.appendChild(thead);

        // Body
        const tbody = document.createElement("tbody");

        route.coords.forEach(stop => {

            const tr = document.createElement("tr");

            // Light row tint
            const type =
                stop.type?.toLowerCase();

            if (rowColorMap[type]) {

                tr.style.backgroundColor =
                    rowColorMap[type];
            }

            const values = [
                stop.type,
                stop.id,
                stop.start_time,
                stop.end_time
            ];

            values.forEach(value => {

                const td =
                    document.createElement("td");

                td.textContent = value || "-";

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);

        routeDiv.appendChild(table);

        section.appendChild(routeDiv);
    });

    container.appendChild(section);
}

let weightChart = null;
let incomeChart = null;
let weatherChart = null;
let resourceChart = null;
let forgottenChart = null;

function createOrUpdateChart(chartRef, canvasId, datasets, labels) {

    const ctx =
        document
            .getElementById(canvasId)
            .getContext("2d");

    if (!chartRef.chart) {

        chartRef.chart = new Chart(ctx, {

            type: "line",

            data: {
                labels: labels,
                datasets: datasets
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,
                animation: false,

                interaction: {
                    mode: "index",
                    intersect: false
                },

                plugins: {
                    legend: {
                        display: true
                    }
                },

                elements: {
                    line: {
                        tension: 0.0,
                        borderWidth: 2
                    },
                    point: {
                        radius: 1
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        }
                    }
                }
            }
        });

    } else {

        chartRef.chart.data.labels = labels;
        chartRef.chart.data.datasets = datasets;
        chartRef.chart.update();
    }
}

function updateCharts(metrics) {

    if (!metrics || metrics.length === 0) {
        return;
    }

    // --------------------
    // Labels
    // --------------------

    const labels =
        metrics.map(m => m.iteration);

    // --------------------
    // Helper
    // --------------------

    const safe =
        (value) => Number(value) || 0;

    // --------------------
    // Data Arrays
    // --------------------

    const weights =
        metrics.map(m => safe(m.weight));

    const incomes =
        metrics.map(m => safe(m.totalIncome));

    const monetaryCosts =
        metrics.map(m => safe(m.totalMonetaryCost));

    const totalTimeCost =
        metrics.map(m => safe(m.totalTimeCost));

    const totalPathCost =
        metrics.map(m => safe(m.totalPathCost));

    const totalResourceCost =
        metrics.map(m => safe(m.totalResourceCost));
    
    const weatherCosts =
        metrics.map(m => safe(m.totalWeatherCost));

    const shopCosts =
        metrics.map(m => safe(m.totalShopCost));

    const depotCosts =
        metrics.map(m => safe(m.totalDepotCost));

    const forgottenCosts =
        metrics.map(m => safe(m.forgottenTaskCost));

    // --------------------
    // Weight Chart
    // --------------------

    createOrUpdateChart(

        { chart: weightChart },

        "weight-chart",

        [
            {
                label: "Optimization Weight",
                data: weights
            }
        ],

        labels
    );

    weightChart =
        arguments[0] && weightChart
            ? weightChart
            : Chart.getChart("weight-chart");

    // --------------------
    // Income Chart
    // --------------------

    createOrUpdateChart(

        { chart: incomeChart },

        "income-chart",

        [
            {
                label: "Income",
                data: incomes
            },
            {
                label: "Monetary Cost",
                data: monetaryCosts
            },
            {
                label: "Time Cost",
                data: totalTimeCost
            },
            {
                label: "Path Cost",
                data: totalPathCost
            },
            {
                label: "Resource Cost",
                data: totalResourceCost
            }


        ],

        labels
    );

    incomeChart =
        arguments[0] && incomeChart
            ? incomeChart
            : Chart.getChart("income-chart");

    // --------------------
    // Weather Chart
    // --------------------

    createOrUpdateChart(

        { chart: weatherChart },

        "weather-chart",

        [
            {
                label: "Weather Cost",
                data: weatherCosts
            }
        ],

        labels
    );

    weatherChart =
        arguments[0] && weatherChart
            ? weatherChart
            : Chart.getChart("weather-chart");

    // --------------------
    // Resource Chart
    // --------------------

    createOrUpdateChart(

        { chart: resourceChart },

        "resource-chart",

        [
            {
                label: "Shop Cost",
                data: shopCosts
            },
            {
                label: "Depot Cost",
                data: depotCosts
            }

        ],

        labels
    );

    resourceChart =
        arguments[0] && resourceChart
            ? resourceChart
            : Chart.getChart("resource-chart");

    // --------------------
    // Forgotten Tasks Chart
    // --------------------

    createOrUpdateChart(

        { chart: forgottenChart },

        "forgotten-chart",

        [
            {
                label: "Unassigned Task Lost Penalty",
                data: forgottenCosts
            }
        ],

        labels
    );

    forgottenChart =
        arguments[0] && forgottenChart
            ? forgottenChart
            : Chart.getChart("forgotten-chart");
}


async function loadMetrics() {

    try {

        const res = await fetch("/planning/metrics/current");

        const metrics = await res.json();

        renderMetrics(metrics);
        updateCharts(metrics);
    } catch (err) {

        console.error("Failed to load metrics:", err);
    }
}

function renderMetrics(metrics) {

    const container = document.getElementById("metrics-table");

    if (!metrics || metrics.length === 0) {

        container.innerHTML = "";
        return;
    }

    // Latest iteration only
    const latest = metrics[metrics.length - 1];

    const fields = [
        "iteration",
        "totalMonetaryCost",
        "totalPathCost",
        "totalTimeCost",
        "totalWeatherCost",
        "totalShopCost",
        "totalDepotCost",
        "totalResourceCost",
        "totalIncome",
        "forgottenTaskCost",
        "weight"
    ];

    const table = document.createElement("table");

    table.style.borderCollapse = "collapse";
    table.style.width = "100%";

    const tbody = document.createElement("tbody");

    fields.forEach(field => {

        const tr = document.createElement("tr");

        const tdName = document.createElement("td");
        tdName.textContent = field;
        tdName.style.border = "1px solid #ccc";
        tdName.style.padding = "4px 8px";

        const tdValue = document.createElement("td");
        tdValue.textContent = latest[field];
        tdValue.style.border = "1px solid #ccc";
        tdValue.style.padding = "4px 8px";

        tr.appendChild(tdName);
        tr.appendChild(tdValue);

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);

    // Replace old table
    container.innerHTML = "";
    container.appendChild(table);
}

// --------------------
// --- Object Functions ---
// --------------------


async function fetchObjects(objectType) {
    const res = await fetch(`/objects/${objectType}/load`);
    if (!res.ok) { alert(`Failed to load ${objectType}`); return []; }
    const data = await res.json();
    return data[objectType] || [];
}

async function getNextId(objectType) {
    const objects = await fetchObjects(objectType);
    const numericIds = objects.map(o => parseInt(o.id)).filter(n => !isNaN(n));
    return numericIds.length ? Math.max(...numericIds) + 1 : 1;
}

async function createObject(objectType, formPrefix) {
    const token = localStorage.getItem("token");
    const inputs = document.querySelectorAll(`#${formPrefix}-form [data-field]`);
    const payload = { id: (await getNextId(objectType)).toString() };

    inputs.forEach(input => {
        let val = input.value;
        if (input.dataset.type === "json") val = JSON.parse(val || "{}");
        else if (input.dataset.type === "float") val = parseFloat(val);
        else if (input.dataset.type === "int") val = parseInt(val);
        if (objectType === "tasks" && input.dataset.field === "created" && !val) val = new Date().toISOString();
        payload[input.dataset.field] = val;
    });

    const res = await fetch(`/${objectType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    document.getElementById(`${formPrefix}-msg`).innerText = data.message || data.error;
    loadObjectsAndRender(objectType);
}

async function loadObjectsAndRender(objectType) {
    const objects = await fetchObjects(objectType);
    renderObjectsOnMap(objects, objectType);
    renderObjectsList(objects, objectType);
}

function renderObjectsOnMap(objects, objectType) {
    // Remove only markers of this type
    const toRemove = markers.filter(m => m.type === objectType);
    toRemove.forEach(m => map.removeLayer(m.marker));
    markers = markers.filter(m => m.type !== objectType);

    // Add new markers
    objects.forEach(obj => {
        const lat = parseFloat(obj.home_lat ?? obj.lat);
        const lng = parseFloat(obj.home_long ?? obj.long);
        if (isNaN(lat) || isNaN(lng)) return;

        const marker = L.circleMarker([lat, lng], {
            color: colorMap[objectType] || "black",
            fillColor: colorMap[objectType] || "black",
            radius: radiusMap[objectType] || 5,
            fillOpacity: opacityMap[objectType] || 0.5,
            opacity: 0
        }).addTo(map);

        // Popup rendering deferred until click (saves rendering/tiles)
        marker.bindPopup(() => generatePopup(obj, objectType));

        markers.push({ type: objectType, id: obj.id, marker });
    });
}

function generatePopup(obj, objectType) {
    let html = `ID: ${obj.id || "-"}<br>`;
    if (obj.name) html += `Name: ${obj.name}<br>`;
    if (obj.skills) html += `Skills: ${JSON.stringify(obj.skills)}<br>`;
    if (obj.start_tw && obj.end_tw) html += `TW: ${obj.start_tw} - ${obj.end_tw}<br>`;
    return html;
}

function renderObjectsList(objects, objectType) {
    const container = document.getElementById("objects-container");

    // Clear previous section
    const oldSection = document.getElementById(`section-${objectType}`);
    if (oldSection) oldSection.remove();

    const section = document.createElement("div");
    section.id = `section-${objectType}`;
    section.style.marginBottom = "20px";
    section.innerHTML = `<h3>${objectType.charAt(0).toUpperCase() + objectType.slice(1)}</h3>`;

    const formatCoord = (coord) => coord ? parseFloat(coord).toFixed(4) : "-";

    if (objectType === "technicians") {
        // Group by master_id
        const grouped = {};
        objects.forEach(t => {
            const masterId = t.master_id || t.id;
            if (!grouped[masterId]) grouped[masterId] = [];
            grouped[masterId].push(t);
        });

        Object.keys(grouped).forEach(masterId => {
            const instances = grouped[masterId];
            const first = instances[0];

            const masterDiv = document.createElement("div");
            masterDiv.style.border = "1px solid #ccc";
            masterDiv.style.padding = "10px";
            masterDiv.style.marginBottom = "10px";
            masterDiv.style.borderRadius = "6px";

            // Header with master info
            const header = document.createElement("div");
            header.style.fontWeight = "bold";
            header.style.marginBottom = "6px";
            header.textContent = `Master ID: ${masterId}`;
            masterDiv.appendChild(header);

            const masterInfo = document.createElement("div");
            masterInfo.style.display = "flex";
            masterInfo.style.gap = "20px";

            // Skills
            if (first.skills) {
                const skillsDiv = document.createElement("div");
                skillsDiv.textContent = `Skills: ${Array.isArray(first.skills) ? first.skills.join(", ") : JSON.stringify(first.skills)}`;
                masterInfo.appendChild(skillsDiv);
            }

            // Location
            const locDiv = document.createElement("div");
            const lat = formatCoord(first.home_lat ?? first.lat);
            const lng = formatCoord(first.home_long ?? first.long);
            locDiv.textContent = `Location: ${lat}, ${lng}`;
            masterInfo.appendChild(locDiv);

            masterDiv.appendChild(masterInfo);

            // Instances as table
            const table = document.createElement("table");
            table.style.width = "100%";
            table.style.borderCollapse = "collapse";
            table.style.marginTop = "10px";

            const thead = document.createElement("thead");
            const headerRow = document.createElement("tr");
            ["Instance ID", "Time Window", "Delete"].forEach(text => {
                const th = document.createElement("th");
                th.textContent = text;
                th.style.borderBottom = "1px solid #aaa";
                th.style.textAlign = "left";
                th.style.padding = "4px 8px";
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            const tbody = document.createElement("tbody");
            instances.forEach(t => {
                const tr = document.createElement("tr");

                const tdId = document.createElement("td");
                tdId.textContent = t.id;
                tdId.style.padding = "4px 8px";
                tr.appendChild(tdId);

                const tdTW = document.createElement("td");
                tdTW.textContent = t.start_tw && t.end_tw ? `${t.start_tw} - ${t.end_tw}` : "-";
                tdTW.style.padding = "4px 8px";
                tr.appendChild(tdTW);

                const tdBtn = document.createElement("td");
                tdBtn.style.padding = "4px 8px";
                const btn = document.createElement("button");
                btn.textContent = "Delete";
                btn.onclick = () => deleteObject("technicians", t.id);
                tdBtn.appendChild(btn);
                tr.appendChild(tdBtn);

                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            masterDiv.appendChild(table);

            section.appendChild(masterDiv);
        });

    } else {
        // Tasks, Shops, Depots
        const table = document.createElement("table");
        table.style.width = "100%";
        table.style.borderCollapse = "collapse";

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        // Columns
        const columns = ["ID"];
        if (objectType === "tasks") columns.push("Skills");
        columns.push("Time Window", "Location", "Delete");  // Name removed

        columns.forEach(text => {
            const th = document.createElement("th");
            th.textContent = text;
            th.style.borderBottom = "1px solid #aaa";
            th.style.textAlign = "left";
            th.style.padding = "4px 8px";
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        objects.forEach(obj => {
            const tr = document.createElement("tr");

            const addTd = (value) => {
                const td = document.createElement("td");
                td.textContent = value || "-";
                td.style.padding = "4px 8px";
                return td;
            };

            tr.appendChild(addTd(obj.id));

            if (objectType === "tasks") {
                tr.appendChild(addTd(obj.skills ? (Array.isArray(obj.skills) ? obj.skills.join(", ") : JSON.stringify(obj.skills)) : "-"));
            }

            tr.appendChild(addTd(obj.start_tw && obj.end_tw ? `${obj.start_tw} - ${obj.end_tw}` : "-"));

            const lat = formatCoord(obj.home_lat ?? obj.lat);
            const lng = formatCoord(obj.home_long ?? obj.long);
            tr.appendChild(addTd(`${lat}, ${lng}`));

            const tdBtn = document.createElement("td");
            const btn = document.createElement("button");
            btn.textContent = "Delete";
            btn.onclick = () => deleteObject(objectType, obj.id);
            tdBtn.appendChild(btn);
            tdBtn.style.padding = "4px 8px";
            tr.appendChild(tdBtn);

            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        section.appendChild(table);
    }

    container.appendChild(section);
}



// --------------------
// --- Load All Objects ---
// --------------------
async function loadAllObjects() {
    const container = document.getElementById("objects-container");
    container.innerHTML = "";
    for (let type of OBJECT_TYPES) await loadObjectsAndRender(type);
}

// --------------------
// --- Delete Object ---
// --------------------

async function deleteObject(objectType, id) {
    if (!confirm(`Delete ${objectType} ${id}?`)) return;

    try {
        const res = await fetch(`/objects/${objectType}/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (data.ok) {
            console.log(`${objectType} ${id} deleted`);
            // Remove marker from map
            markers = markers.filter(m => {
                if (m.type === objectType && m.id === id) {
                    map.removeLayer(m.marker);
                    return false; // remove from array
                }
                return true;
            });
            // Optionally refresh list
            loadObjectsAndRender(objectType);
        } else {
            console.error(data.error);
            alert(`Failed to delete: ${data.error}`);
        }
    } catch (err) {
        console.error(err);
        alert(`Error deleting object: ${err}`);
    }
}


// --------------------
// --- Auto-login ---
// --------------------
document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("token")) showApp({ client_name: "User" });
});
//loadObjects("technicians").then(t=>renderObjectsOnMap(t,"technicians"));
//loadObjects("tasks").then(t=>renderObjectsOnMap(t,"tasks"));
