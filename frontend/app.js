document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = window.APP_CONFIG.API_BASE;
  const MAPS_KEY = window.APP_CONFIG.GOOGLE_MAPS_API_KEY;

  const loader = document.getElementById("loader");
  const authBtn = document.getElementById("authBtn");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");

  const newItinBtn = document.getElementById("newItinBtn");
  const destInput = document.getElementById("destInput");
  const messages = document.getElementById("messages");

  const sendBtn = document.getElementById("sendBtn");
  const chatText = document.getElementById("chatText");

  let token = localStorage.getItem("token");

  function showLoader() { loader.classList.remove("hidden"); }
  function hideLoader() { loader.classList.add("hidden"); }

  /* ---------------- LOGIN (DEMO SAFE) ---------------- */
  authBtn.onclick = async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
      alert("Enter email and password");
      return;
    }

    showLoader();
    try {
      const res = await fetch(API_BASE + "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) throw new Error("Login failed");

      const data = await res.json();
      token = data.access_token;
      localStorage.setItem("token", token);
      alert("Login successful");
    } catch {
      alert("Login failed (demo backend issue)");
    } finally {
      hideLoader();
    }
  };

  /* ---------------- ITINERARY ---------------- */
  newItinBtn.onclick = async () => {
    if (!token) {
      alert("Please login first");
      return;
    }

    showLoader();
    try {
      const res = await fetch(API_BASE + "/api/itinerary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token
        },
        body: JSON.stringify({
          destination: destInput.value || "Pune",
          days: 3,
          travel_type: "cultural",
          budget: "medium",
          mood: "relaxed",
          include_pois: false
        })
      });

      const data = await res.json();
      messages.innerHTML = "";

      data.plan.forEach(day => {
        const div = document.createElement("div");
        div.className = "card";
        div.innerText = `Day ${day.day}: ${day.summary}`;
        messages.appendChild(div);
      });
    } catch {
      alert("Itinerary failed");
    } finally {
      hideLoader();
    }
  };

  /* ---------------- AI ---------------- */
  sendBtn.onclick = async () => {
    if (!token) {
      alert("Please login first");
      return;
    }

    showLoader();
    try {
      const res = await fetch(API_BASE + "/api/ai/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token
        },
        body: JSON.stringify({
          mood: "neutral",
          places_list: chatText.value
        })
      });

      const data = await res.json();
      alert(data.recommendation);
    } catch {
      alert("AI failed");
    } finally {
      hideLoader();
    }
  };

  /* ---------------- GOOGLE MAP ---------------- */
  if (MAPS_KEY) {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${MAPS_KEY}&callback=initMap`;
    s.async = true;
    document.head.appendChild(s);
  }

  window.initMap = function () {
    new google.maps.Map(document.getElementById("map"), {
      center: { lat: 20.5937, lng: 78.9629 },
      zoom: 5
    });
  };
});
