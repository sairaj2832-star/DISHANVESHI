// app.js — minimal frontend logic to call your backend
// Requires you to set window.APP_CONFIG.API_BASE and GOOGLE_MAPS_API_KEY in index.html (or create a config.js)

const API_BASE = (window.APP_CONFIG && window.APP_CONFIG.API_BASE) ? window.APP_CONFIG.API_BASE : "https://your-backend.example.com";
const GOOGLE_MAPS_API_KEY = (window.APP_CONFIG && window.APP_CONFIG.GOOGLE_MAPS_API_KEY) ? window.APP_CONFIG.GOOGLE_MAPS_API_KEY : "";

let map, markers = [], userToken = null;

// init map if key present
function initMapIfKey() {
  if(!GOOGLE_MAPS_API_KEY) {
    document.getElementById('map').innerHTML = '<div style="padding:16px;color:#a9c6c6">Map disabled — set GOOGLE_MAPS_API_KEY in config</div>';
    return;
  }
  const s = document.createElement('script');
  s.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places&callback=onMapsReady`;
  s.async = true; document.head.appendChild(s);
}
window.onMapsReady = function(){
  map = new google.maps.Map(document.getElementById('map'), {center:{lat:20.5937,lng:78.9629},zoom:5});
}

function addMessage(text, who='ai'){
  const c = document.createElement('div');
  c.className = 'card';
  c.innerHTML = `<div style="font-weight:600">${who==='user' ? 'You' : 'Dishanveshi'}</div><div style="margin-top:6px">${text}</div>`;
  const m = document.getElementById('messages');
  m.insertBefore(c, m.firstChild);
}

document.getElementById('sendBtn').onclick = async () => {
  const q = document.getElementById('chatText').value.trim();
  if(!q) return;
  addMessage(q, 'user');
  document.getElementById('chatText').value = '';
  try {
    const resp = await fetch(`${API_BASE}/api/ai/recommend`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ mood: 'neutral', places_list: q })
    });
    const data = await resp.json();
    addMessage(data.recommendation || JSON.stringify(data));
  } catch (e) {
    addMessage('Error contacting backend: ' + e.message);
  }
};

document.getElementById('newItinBtn').onclick = async () => {
  const dest = document.getElementById('destInput').value.trim() || 'Pune';
  addMessage(`Generating itinerary for ${dest}...`, 'user');
  const body = { destination: dest, days: 3, travel_type: 'cultural', budget: 'medium', mood: 'relaxed', include_pois: true };
  try {
    const r = await fetch(`${API_BASE}/api/itinerary`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const data = await r.json();
    if(!data.plan) { addMessage('No plan returned — check backend', 'ai'); return; }
    renderPlan(data);
  } catch (e) {
    addMessage('Itinerary error: ' + e.message);
  }
};

function clearMarkers(){ markers.forEach(m => m.setMap(null)); markers = []; }
function renderPlan(data){
  const msgs = document.getElementById('messages');
  msgs.innerHTML = '';
  clearMarkers();
  data.plan.forEach(day => {
    const card = document.createElement('div'); card.className = 'card';
    const placesHTML = (day.places || []).map(p => {
      const photo = (p.photos && p.photos.length) ? getPhotoUrl(p.photos[0]) : '';
      return `<div class="poi"><img src="${photo || 'https://via.placeholder.com/80'}" /><div><div style="font-weight:700">${p.name || 'Unknown'}</div><div class="metadata">${p.address || ''} • ${p.rating || ''}</div></div></div>`;
    }).join('');
    card.innerHTML = `<div style="font-weight:700">Day ${day.day}</div><div style="margin:8px 0">${day.summary}</div>${placesHTML}`;
    msgs.appendChild(card);
    if(Array.isArray(day.places)){
      day.places.forEach(p => {
        if(p.lat && p.lng && map) {
          const marker = new google.maps.Marker({ position: { lat: parseFloat(p.lat), lng: parseFloat(p.lng) }, map, title: p.name });
          markers.push(marker);
        }
      });
    }
  });
}

function getPhotoUrl(photo) {
  if(!photo) return '';
  const ref = photo.photo_reference || photo.photoReference || photo.photoReference;
  if(!ref) return '';
  return `https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=${ref}&key=${GOOGLE_MAPS_API_KEY}`;
}

// login simple prompt demo
document.getElementById('loginBtn').onclick = async () => {
  const email = prompt('Email'); if(!email) return;
  const pass = prompt('Password'); if(!pass) return;
  const form = new FormData(); form.append('username', email); form.append('password', pass);
  try {
    const r = await fetch(`${API_BASE}/api/auth/login`, { method: 'POST', body: form });
    const j = await r.json();
    if(j.access_token) {
      userToken = j.access_token; document.getElementById('userName').innerText = email.split('@')[0]; document.getElementById('account-area').innerText = email;
      addMessage('Logged in as ' + email, 'ai');
      loadSaved();
    } else {
      addMessage('Login failed: ' + JSON.stringify(j));
    }
  } catch (e) {
    addMessage('Login error: ' + e.message);
  }
};

async function loadSaved() {
  const panel = document.getElementById('savedList'); panel.innerHTML = '';
  if(!userToken) { panel.innerHTML = '<div class="muted">Sign in to view saved plans</div>'; return; }
  try {
    const r = await fetch(`${API_BASE}/api/itinerary/my`, { headers: { 'Authorization': 'Bearer ' + userToken } });
    const arr = await r.json();
    arr.forEach(it => {
      const d = document.createElement('div'); d.className = 'card';
      d.innerHTML = `<div style="font-weight:700">${it.destination} • ${new Date(it.created_at).toLocaleString()}</div>
                     <div class="muted" style="margin-top:6px">${(it.plan_json || '').slice(0,120)}...</div>`;
      panel.appendChild(d);
    });
  } catch (e) {
    panel.innerHTML = '<div class="muted">Error loading saved plans</div>';
  }
}

// start
initMapIfKey();
