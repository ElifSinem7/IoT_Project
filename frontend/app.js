import { CONFIG } from "./config.js";

const $ = (id) => document.getElementById(id);

// Global variables
let map;
let markers = [];
let circles = [];
let heatLayer = null;
let currentFilter = { city: "", district: "" };
let selectedLocation = null;
let chart;
let allLocations = [];

// Layer visibility states
let showMarkers = true;
let showCircles = true;
let showHeatmap = false;

// ✅ DEBUG MODE
const DEBUG = true;
function debugLog(message, data) {
  if (DEBUG) {
    console.log(`🔍 [DEBUG] ${message}`, data || '');
  }
}

// Show API info
$("apiBase").textContent = CONFIG.API_BASE;
debugLog("API Base URL:", CONFIG.API_BASE);

// API REQUESTS
function headers() {
  const h = { "accept": "application/json" };
  if (CONFIG.API_KEY && CONFIG.API_KEY.trim().length > 0) {
    h["x-api-key"] = CONFIG.API_KEY.trim();
  }
  return h;
}

function calculateScale(values, paddingRatio = 0.15) {
  const filtered = values.filter(v => v !== null && v !== undefined);

  if (filtered.length === 0) {
    return { suggestedMin: 0, suggestedMax: 1 };
  }

  const min = Math.min(...filtered);
  const max = Math.max(...filtered);

  if (min === max) {
    return {
      suggestedMin: min - 1,
      suggestedMax: max + 1
    };
  }

  const padding = (max - min) * paddingRatio;

  return {
    suggestedMin: min - padding,
    suggestedMax: max + padding
  };
}

async function apiGet(path) {
  const url = `${CONFIG.API_BASE}${path}`;
  debugLog(`API Request: ${path}`);
  
  const res = await fetch(url, { headers: headers() });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  
  const data = await res.json();
  debugLog(`API Response: ${path}`, data);
  
  return data;
}

// ==================== ALERT FONKSİYONLARI ====================

async function loadLatestAlert(deviceId) {
  try {
    const data = await apiGet(`/alerts/latest?device_id=${encodeURIComponent(deviceId)}`);
    
    if (data.found) {
      debugLog("Latest alert found:", data);
      return data;
    }
    return null;
  } catch (e) {
    console.error("Error loading latest alert:", e);
    return null;
  }
}

async function loadAlertHistory(deviceId, hours = 24, limit = 10) {
  try {
    const data = await apiGet(`/alerts/history?device_id=${encodeURIComponent(deviceId)}&hours=${hours}&limit=${limit}`);
    
    debugLog("Alert history loaded:", data);
    return data;
  } catch (e) {
    console.error("Error loading alert history:", e);
    return { device_id: deviceId, count: 0, items: [] };
  }
}

function displayAlertHistory(alerts) {
  const alertHistoryDiv = $("alertHistory");
  if (!alertHistoryDiv) return;
  
  if (alerts.count === 0) {
    alertHistoryDiv.innerHTML = '<p class="no-alerts">No recent alerts ✅</p>';
    return;
  }
  
  const html = `
    <div class="alert-list">
      ${alerts.items.map(item => {
        const timestamp = item.ts ? new Date(item.ts).toLocaleString('en-US') : 'N/A';
        return `
          <div class="alert-item ${item.status ? item.status.toLowerCase() : 'warn'}">
            <span class="alert-time">${timestamp}</span>
            <span class="alert-value">TVOC: ${item.tvoc_ppb || 'N/A'} ppb, eCO₂: ${item.eco2_ppm || 'N/A'} ppm</span>
            <span class="alert-status ${item.status ? item.status.toLowerCase() : 'warn'}">${item.status || 'ALERT'}</span>
          </div>
        `;
      }).join('')}
    </div>
  `;
  
  alertHistoryDiv.innerHTML = html;
}

// ==================== MAP FUNCTIONS ====================

function initMap() {
  map = L.map('map').setView(CONFIG.MAP_CENTER, CONFIG.MAP_ZOOM);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map);
  
  setupMapControls();
  debugLog("Map initialized");
}

function setupMapControls() {
  $("showMarkers").addEventListener("change", (e) => {
    showMarkers = e.target.checked;
    updateLayerVisibility();
  });
  
  $("showCircles").addEventListener("change", (e) => {
    showCircles = e.target.checked;
    updateLayerVisibility();
  });
  
  $("showHeatmap").addEventListener("change", (e) => {
    showHeatmap = e.target.checked;
    updateLayerVisibility();
  });
}

function updateLayerVisibility() {
  markers.forEach(marker => {
    if (showMarkers) {
      marker.addTo(map);
    } else {
      map.removeLayer(marker);
    }
  });
  
  circles.forEach(circle => {
    if (showCircles) {
      circle.addTo(map);
    } else {
      map.removeLayer(circle);
    }
  });
  
  if (heatLayer) {
    if (showHeatmap) {
      heatLayer.addTo(map);
    } else {
      map.removeLayer(heatLayer);
    }
  }
}

// ✅ Backend status fonksiyonları
function getStatusColor(status) {
  if (!status) return CONFIG.COLORS.NO_DATA;
  const st = status.toUpperCase();
  if (st === "HIGH") return CONFIG.COLORS.POOR;
  if (st === "NORMAL" || st === "OK") return CONFIG.COLORS.GOOD;
  if (st === "WARN") return CONFIG.COLORS.MODERATE;
  return CONFIG.COLORS.NO_DATA;
}

function getStatusText(status) {
  if (!status) return "NO DATA";
  const st = status.toUpperCase();
  if (st === "HIGH") return "HIGH";
  if (st === "NORMAL" || st === "OK") return "NORMAL";
  if (st === "WARN") return "MODERATE";
  return "NO DATA";
}

// Fallback TVOC fonksiyonları
function getQualityColor(tvoc) {
  if (tvoc === null || tvoc === undefined) return CONFIG.COLORS.NO_DATA;
  if (tvoc <= CONFIG.THRESHOLDS.GOOD) return CONFIG.COLORS.GOOD;
  if (tvoc <= CONFIG.THRESHOLDS.MODERATE) return CONFIG.COLORS.MODERATE;
  return CONFIG.COLORS.POOR;
}

function getQualityText(tvoc) {
  if (tvoc === null || tvoc === undefined) return "NO DATA";
  if (tvoc <= CONFIG.THRESHOLDS.GOOD) return "GOOD";
  if (tvoc <= CONFIG.THRESHOLDS.MODERATE) return "MODERATE";
  return "POOR";
}

function getQualityClass(tvoc) {
  if (tvoc === null || tvoc === undefined) return "no-data";
  if (tvoc <= CONFIG.THRESHOLDS.GOOD) return "good";
  if (tvoc <= CONFIG.THRESHOLDS.MODERATE) return "moderate";
  return "poor";
}

function getHeatIntensity(tvoc) {
  if (tvoc === null || tvoc === undefined) return 0.1;
  if (tvoc <= CONFIG.THRESHOLDS.GOOD) return 0.3;
  if (tvoc <= CONFIG.THRESHOLDS.MODERATE) return 0.6;
  return 1.0;
}

function getCircleRadius(tvoc) {
  if (tvoc === null || tvoc === undefined) return 2000;
  if (tvoc <= CONFIG.THRESHOLDS.GOOD) return 3000;
  if (tvoc <= CONFIG.THRESHOLDS.MODERATE) return 4000;
  return 5000;
}

function createMarkerIcon(color) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 3px 10px rgba(0,0,0,0.4);
      position: relative;
    ">
      <div style="
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 8px solid transparent;
        border-right: 8px solid transparent;
        border-top: 8px solid ${color};
        filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));
      "></div>
    </div>`,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
  });
}

function addMarker(location) {
  const { lat, lon, name, tvoc_ppb, eco2_ppm, temperature, humidity, pressure, last_update, status } = location;
  
  // ✅ Backend status varsa kullan, yoksa TVOC
  const color = status ? getStatusColor(status) : getQualityColor(tvoc_ppb);
  const quality = status ? getStatusText(status) : getQualityText(tvoc_ppb);
  
  debugLog(`Adding marker: ${name}`, {
    status,
    tvoc_ppb,
    eco2_ppm,
    temperature,
    humidity,
    quality,
    color
  });
  
  const circleRadius = getCircleRadius(tvoc_ppb);
  const circle = L.circle([lat, lon], {
    color: color,
    fillColor: color,
    fillOpacity: 0.2,
    radius: circleRadius,
    weight: 2
  });
  
  if (showCircles) {
    circle.addTo(map);
  }
  circles.push(circle);
  
  const marker = L.marker([lat, lon], {
    icon: createMarkerIcon(color)
  });
  
  const popupContent = `
    <div class="popup-content">
      <h4>${name}</h4>
      <p><strong>Quality:</strong> <span class="popup-quality ${getQualityClass(tvoc_ppb)}">${quality}</span></p>
      ${tvoc_ppb !== null && tvoc_ppb !== undefined ? `<p><strong>TVOC:</strong> ${tvoc_ppb} ppb</p>` : ''}
      ${eco2_ppm !== null && eco2_ppm !== undefined ? `<p><strong>eCO₂:</strong> ${eco2_ppm} ppm</p>` : ''}
      ${temperature !== null && temperature !== undefined ? `<p><strong>Temp:</strong> ${temperature.toFixed(1)}°C</p>` : ''}
      ${humidity !== null && humidity !== undefined ? `<p><strong>Humidity:</strong> ${humidity.toFixed(1)}%</p>` : ''}
      ${pressure !== null && pressure !== undefined ? `<p><strong>Pressure:</strong> ${pressure.toFixed(1)} hPa</p>` : ''}
      ${last_update ? `<p><strong>Updated:</strong> ${new Date(last_update).toLocaleTimeString()}</p>` : ''}
    </div>
  `;
  
  marker.bindPopup(popupContent);
  marker.on('click', () => showLocationDetail(location));
  
  if (showMarkers) {
    marker.addTo(map);
  }
  markers.push(marker);
}

async function loadMapData() {
  try {
    debugLog("Loading map data with filter:", currentFilter);
    
    let path = "/map/points";
    const params = [];
    if (currentFilter.city) params.push(`city=${encodeURIComponent(currentFilter.city)}`);
    if (currentFilter.district) params.push(`district=${encodeURIComponent(currentFilter.district)}`);
    if (params.length > 0) path += "?" + params.join("&");
    
    const data = await apiGet(path);
    debugLog("Map data received:", data.points?.length || 0, "points");
    
    allLocations = data.points || [];
    
    // Clear existing markers
    markers.forEach(m => map.removeLayer(m));
    circles.forEach(c => map.removeLayer(c));
    if (heatLayer) map.removeLayer(heatLayer);
    
    markers = [];
    circles = [];
    heatLayer = null;
    
    // Add new markers
    allLocations.forEach(location => addMarker(location));
    
    // Create heatmap layer
    const heatData = allLocations
      .filter(loc => loc.tvoc_ppb !== null && loc.tvoc_ppb !== undefined)
      .map(loc => [loc.lat, loc.lon, getHeatIntensity(loc.tvoc_ppb)]);
    
    if (heatData.length > 0) {
      heatLayer = L.heatLayer(heatData, {
        radius: 35,
        blur: 25,
        maxZoom: 10,
        gradient: {
          0.0: CONFIG.COLORS.GOOD,
          0.5: CONFIG.COLORS.MODERATE,
          1.0: CONFIG.COLORS.POOR
        }
      });
      
      if (showHeatmap) {
        heatLayer.addTo(map);
      }
    }
    
    updateLastUpdate();
    debugLog("Map updated with", allLocations.length, "locations");
    
  } catch (e) {
    console.error("Error loading map data:", e);
  }
}

async function loadCities() {
  try {
    const data = await apiGet("/locations/cities");
    debugLog("Cities loaded:", data.cities?.length || 0);
    
    const select = $("ilSelect");
    select.innerHTML = '<option value="">All Turkey</option>';
    
    (data.cities || []).forEach(city => {
      const option = document.createElement("option");
      option.value = city;
      option.textContent = city;
      select.appendChild(option);
    });
    
  } catch (e) {
    console.error("Error loading cities:", e);
  }
}

async function loadDistricts(city) {
  try {
    const data = await apiGet(`/locations/districts?city=${encodeURIComponent(city)}`);
    debugLog("Districts loaded for", city, ":", data.districts?.length || 0);
    
    const select = $("ilceSelect");
    select.disabled = false;
    select.innerHTML = '<option value="">All ' + city + '</option>';
    
    (data.districts || []).forEach(district => {
      const option = document.createElement("option");
      option.value = district;
      option.textContent = district;
      select.appendChild(option);
    });
    
  } catch (e) {
    console.error("Error loading districts:", e);
    $("ilceSelect").disabled = true;
  }
}

// ✅ YENI: Detail Panel Güncelleme Fonksiyonu (auto-refresh için)
function updateDetailPanel(location) {
  console.log("💥 UPDATING DETAIL PANEL:", location.name);
  
  selectedLocation = location;
  
  // NAME
  $("locationName").textContent = location.name || "Unknown Location";
  
  // ✅ BACKEND STATUS BADGE
  const backendStatus = location.status;
  let quality, qualityClass;
  
  if (backendStatus) {
    const st = backendStatus.toUpperCase();
    if (st === "HIGH") {
      quality = "HIGH";
      qualityClass = "poor";
    } else if (st === "NORMAL" || st === "OK") {
      quality = "NORMAL";
      qualityClass = "good";
    } else {
      quality = "MODERATE";
      qualityClass = "moderate";
    }
    console.log("✅ Using backend status:", backendStatus, "→", quality);
  } else {
    // Fallback: TVOC
    quality = getQualityText(location.tvoc_ppb);
    qualityClass = getQualityClass(location.tvoc_ppb);
    console.log("⚠️ No backend status, using TVOC");
  }
  
  const badge = $("qualityBadge");
  badge.textContent = quality;
  badge.className = `quality-badge ${qualityClass}`;
  
  // ✅ VALUES - FORCE UPDATE
  $("detailScore").textContent = location.score !== null && location.score !== undefined ? location.score : "-";
  $("detailTvoc").textContent = location.tvoc_ppb !== null && location.tvoc_ppb !== undefined 
    ? `${location.tvoc_ppb} ppb` 
    : "-";
  $("detailEco2").textContent = location.eco2_ppm !== null && location.eco2_ppm !== undefined 
    ? `${location.eco2_ppm} ppm` 
    : "-";
  $("detailTemp").textContent = location.temperature !== null && location.temperature !== undefined 
    ? `${location.temperature.toFixed(1)}°C` 
    : "-";
  $("detailHumidity").textContent = location.humidity !== null && location.humidity !== undefined 
    ? `${location.humidity.toFixed(1)}%` 
    : "-";
  $("detailPressure").textContent = location.pressure !== null && location.pressure !== undefined 
    ? `${location.pressure.toFixed(1)} hPa` 
    : "-";
  
  console.log("✅ Values updated:", {
    tvoc: location.tvoc_ppb,
    eco2: location.eco2_ppm,
    temp: location.temperature,
    hum: location.humidity,
    press: location.pressure,
    status: backendStatus
  });
  
  // TIMESTAMP
  let timestamp = "-";
  if (location.last_update) {
    try {
      const date = new Date(location.last_update);
      if (date.getFullYear() < 2020) {
        timestamp = "Just now";
      } else {
        timestamp = date.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    } catch (e) {
      timestamp = "Invalid date";
    }
  }
  $("detailTimestamp").textContent = timestamp;
  
  // ✅ ALERT SECTION - Always show it
  const alertSection = $("alertHistorySection");
  if (alertSection) {
    alertSection.style.display = "block";
    console.log("🚨 Alert section enabled");
  }
  
  console.log("💥 DETAIL PANEL UPDATE COMPLETE");
}

// ✅ Show Location Detail (ilk tıklama için)
async function showLocationDetail(location) {
  debugLog("🎯 Showing location detail:", {
    name: location.name,
    device_id: location.device_id || location.id,
    status: location.status,
    tvoc_ppb: location.tvoc_ppb,
    eco2_ppm: location.eco2_ppm,
    temperature: location.temperature
  });
  
  selectedLocation = location;
  
  $("noSelection").style.display = "none";
  $("detailPanel").style.display = "block";
  
  // Detail panel'i güncelle
  updateDetailPanel(location);
  
  // ✅ ALERT HISTORY LOAD
  const deviceId = location.device_id || location.id;
  const history = await loadAlertHistory(deviceId, 24, 5);
  displayAlertHistory(history);
  
  // LOAD CHART
  loadChartForLocation(deviceId);
  
  debugLog("✅ Location detail complete");
}

// CHART FUNCTIONS
function initChart() {
  const ctx = $("chart");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { 
          label: "TVOC (ppb)", 
          data: [],
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y-air'
        },
        { 
          label: "eCO₂ (ppm)", 
          data: [],
          borderColor: '#764ba2',
          backgroundColor: 'rgba(118, 75, 162, 0.1)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y-air'
        },
        { 
          label: "Temperature (°C)", 
          data: [],
          borderColor: '#FF6384',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          tension: 0.4,
          fill: false,
          yAxisID: 'y-env',
          borderDash: [5, 5]
        },
        { 
          label: "Humidity (%)", 
          data: [],
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          tension: 0.4,
          fill: false,
          yAxisID: 'y-env',
          borderDash: [3, 3]
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: {
        duration: 300  // ✅ Hızlı animasyon
      },
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          padding: 12,
          borderColor: '#667eea',
          borderWidth: 2
        }
      },
      scales: {
        x: { 
          ticks: { 
            maxTicksLimit: 10,
            font: { size: 11 }
          },
          grid: {
            display: false
          }
        },
        'y-air': {
          type: 'linear',
          position: 'left',
          title: {
            display: true,
            text: 'Air Quality',
            font: {
              size: 12,
              weight: 'bold'
            },
            color: '#667eea'
          },
          ticks: {
            font: { size: 11 },
            color: '#667eea'
          },
          grid: {
            color: 'rgba(102, 126, 234, 0.1)'
          },
          beginAtZero: false,
          grace: '10%'
        },
        'y-env': {
          type: 'linear',
          position: 'right',
          title: {
            display: true,
            text: 'Environment',
            font: {
              size: 12,
              weight: 'bold'
            },
            color: '#FF6384'
          },
          ticks: {
            font: { size: 11 },
            color: '#FF6384'
          },
          grid: {
            display: false
          },
          beginAtZero: false,
          grace: '10%'
        }
      }
    }
  });
  
  debugLog("Chart initialized with 4 datasets");
}

async function loadChartForLocation(deviceId) {
  if (!deviceId) return;
  
  try {
    debugLog("📊 Loading chart for:", deviceId);
    
    const device = encodeURIComponent(deviceId);
    const history = await apiGet(`/history?device_id=${device}&limit=120`);
    
    debugLog("📊 Chart data received:", history.items?.length || 0, "items");
    
    updateChart(history.items || []);
  } catch (e) {
    console.error("Error loading chart data:", e);
  }
}

function updateChart(items) {
  if (!items || items.length === 0) {
    chart.data.labels = [];
    chart.data.datasets.forEach(ds => ds.data = []);
    chart.update('none');  // ✅ Animasyonsuz güncelleme
    return;
  }

  const labels = items.map(x => {
    const date = new Date(x.ts || x.timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  });

  const tvoc = items.map(x => x.tvoc_ppb ?? null);
  const eco2 = items.map(x => x.eco2_ppm ?? null);
  const temp = items.map(x => x.temp_c ?? null);
  const humidity = items.map(x => x.hum_rh ?? null);

  chart.data.labels = labels;
  chart.data.datasets[0].data = tvoc;
  chart.data.datasets[1].data = eco2;
  chart.data.datasets[2].data = temp;
  chart.data.datasets[3].data = humidity;

  const airScale = calculateScale([...tvoc, ...eco2], 0.15);
  const envScale = calculateScale([...temp, ...humidity], 0.15);

  chart.options.scales['y-air'].suggestedMin = airScale.suggestedMin;
  chart.options.scales['y-air'].suggestedMax = airScale.suggestedMax;

  chart.options.scales['y-env'].suggestedMin = envScale.suggestedMin;
  chart.options.scales['y-env'].suggestedMax = envScale.suggestedMax;

  chart.update('none');  // ✅ Animasyonsuz güncelleme

  debugLog("📊 Chart updated", {
    airScale,
    envScale,
    points: items.length
  });
}

// EVENT LISTENERS
$("ilSelect").addEventListener("change", (e) => {
  currentFilter.city = e.target.value;
  currentFilter.district = "";
  $("ilceSelect").value = "";
  
  if (currentFilter.city) {
    loadDistricts(currentFilter.city);
  } else {
    $("ilceSelect").disabled = true;
    $("ilceSelect").innerHTML = '<option value="">Select city first</option>';
  }
});

$("ilceSelect").addEventListener("change", (e) => {
  currentFilter.district = e.target.value;
});

$("filterBtn").addEventListener("click", () => {
  debugLog("Filter button clicked");
  loadMapData();
});

$("refreshBtn").addEventListener("click", () => {
  debugLog("Refresh button clicked");
  if (selectedLocation) {
    loadChartForLocation(selectedLocation.device_id || selectedLocation.id);
  }
});

// HELPER FUNCTIONS
function updateLastUpdate() {
  const now = new Date().toLocaleTimeString('en-US');
  $("lastUpdate").textContent = now;
  debugLog("Last update timestamp:", now);
}

// ✅ AUTO REFRESH - IMPROVED
let refreshCount = 0;

async function autoRefresh() {
  refreshCount++;
  console.log(`🔄 AUTO REFRESH #${refreshCount} - ${new Date().toLocaleTimeString()}`);
  
  try {
    // Map data'yı yenile
    await loadMapData();
    
    // ✅ Eğer bir lokasyon seçiliyse, detail panel'i güncelle
    if (selectedLocation) {
      const deviceId = selectedLocation.device_id || selectedLocation.id;
      
      // Map data'dan güncel bilgiyi bul
      const updatedLocation = allLocations.find(loc => 
        (loc.device_id || loc.id) === deviceId
      );
      
      if (updatedLocation) {
        console.log("🔄 Updating detail panel with fresh data:", updatedLocation.name);
        updateDetailPanel(updatedLocation);
        
        // Alert history'yi yenile (daha seyrek)
        if (refreshCount % 3 === 0) {  // Her 3 refresh'te bir
          const history = await loadAlertHistory(deviceId, 24, 5);
          displayAlertHistory(history);
        }
      }
      
      // Chart'ı güncelle
      await loadChartForLocation(deviceId);
    }
    
    updateLastUpdate();
    console.log(`✅ AUTO REFRESH #${refreshCount} COMPLETE`);
  } catch (e) {
    console.error(`❌ AUTO REFRESH #${refreshCount} FAILED:`, e);
  }
}

// INITIALIZATION
async function init() {
  console.log("🚀 COMPLETE WORKING DASHBOARD INITIALIZING...");
  console.log("📍 API Base:", CONFIG.API_BASE);
  console.log("⏱️  Auto-refresh interval:", CONFIG.POLL_MS / 1000, "seconds");
  console.log("🔍 Debug mode: ENABLED");
  console.log("✅ Backend status support: ENABLED");
  console.log("✅ Auto-refresh detail panel: ENABLED");
  
  initMap();
  initChart();
  await loadCities();
  await loadMapData();
  
  // ✅ Auto refresh başlat
  setInterval(autoRefresh, CONFIG.POLL_MS);
  
  console.log("✅ DASHBOARD INITIALIZED");
  console.log("---");
}

// Start when page loads
init();