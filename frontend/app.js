/* =========================================================
   Dishanveshi – Frontend app.js (FINAL STABLE VERSION)
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  /* ---------------- CONFIG ---------------- */
  const API_BASE = window.APP_CONFIG?.API_BASE;
  const MAPS_KEY = window.APP_CONFIG?.GOOGLE_MAPS_API_KEY;

  if (!API_BASE) {
    alert("API_BASE missing. Check index.html config.");
    console.error("APP_CONFIG.API_BASE missing");
    return;
  }

  /* ---------------- ELEMENTS ---------------- */
  const loader = document.getElementById("loader");
  const auth = document.getElementById("auth");
  const app = document.getElementById("app");

  const authBtn = document.getElementById("authBtn");
  const switchAuth = document.getElementById("switchAuth");
  const authTitle = document.getElementById("authTitle");

  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");

  const newItinBtn = document.getElementById("newItinBtn");
  const sendBtn = document.getElementById("sendBtn");
  const destInput = document.getElementById("destInput");
  const chatText = document.getElementById("chatText");
  const messages = document.getElementById("messages");

  /* ---------------- STATE ---------------- */
  let token = localStorage.getItem("token");
  let isLogin = true;
  let map = null;

  /* ---------------- LOADER (SAFE) ---------------- */
  function showLoader() {
    if (loader) loader.classList.remove("hidden");
  }

  function hideLoader() {
    if (loader) loader.classList.add("hidden");
  }

  /* ---------------- VIEW ---------------- */
  function showApp() {
  // hide auth screen
  if (auth) auth.classList.add("hidden");

  // show app
  if (app) app.classList.remove("hidden");

  // FORCE hide loader (final fix)
  if (loader) {
       loader.classList.add("hidden");
       loader.style.display = "none";
    }
   }


  function showAuth() {
    auth?.classList.remove("hidden");
    app?.classList.add("hidden");
  }

  if (token) showApp();

  /* ---------------- AUTH SWITCH ---------------- */
  if (switchAuth) {
    switchAuth.onclick = () => {
      isLogin = !isLogin;
      authTitle.innerText = isLogin ? "Login" : "Sign Up";
      authBtn.innerText = isLogin ? "Login" : "Sign Up";
      switchAuth.innerText = isLogin
        ? "No account? Sign up"
        : "Have account? Login";
    };
  }

  /* ---------------- LOGIN / SIGNUP ---------------- */
  if (authBtn) {
    authBtn.onclick = async () => {
      const email = emailInput.value.trim();
      const password = passwordInput.value.trim();

      if (!email || !password) {
        alert("Please enter email and password");
        return;
      }

      showLoader();

      try {
        if (isLogin) {
          /* 🔐 OAuth2PasswordRequestForm (URL-ENCODED) */
          const params = new URLSearchParams();
          params.append("username", email);
          params.append("password", password);

          const res = await fetch(API_BASE + "/api/auth/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded"
            },
            body: params.toString()
          });

          if (!res.ok) {
            throw new Error("Invalid login");
          }

          const data = await res.json();
          token = data.access_token;
          localStorage.setItem("token", token);
          hideLoader();
           showApp();
        } else {
          /* SIGN UP */
          const res = await fetch(API_BASE + "/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
          });

          if (!res.ok) {
            throw new Error("Signup failed");
          }

          alert("Signup successful. Please login.");
          isLogin = true;
          switchAuth.click();
        }
      } catch (err) {
        alert("Authentication failed.");
        console.error("Auth error:", err);
         hideLoader();
      } finally {
        hideLoader();
      }
    };
  }

  /* ---------------- AUTH FETCH ---------------- */
  async function api(path, options = {}) {
    showLoader();
    try {
      const res = await fetch(API_BASE + path, {
        ...options,
        headers: {
          ...(options.headers || {}),
          "Content-Type": "application/json",
          Authorization: token ? "Bearer " + token : ""
        }
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }

      return await res.json();
    } finally {
      hideLoader();
    }
  }

  /* ---------------- ITINERARY ---------------- */
  if (newItinBtn) {
    newItinBtn.onclick = async () => {
      const destination = destInput.value || "Pune";

      try {
        const data = await api("/api/itinerary", {
          method: "POST",
          body: JSON.stringify({
            destination,
            days: 3,
            travel_type: "cultural",
            budget: "medium",
            mood: "relaxed",
            include_pois: true
          })
        });

        messages.innerHTML = "";
        data.plan.forEach(day => {
          const div = document.createElement("div");
          div.className = "card";
          div.innerText = `Day ${day.day}: ${day.summary}`;
          messages.appendChild(div);
        });
      } catch (err) {
        alert("Failed to generate itinerary");
        console.error(err);
      }
    };
  }

  /* ---------------- AI CHAT ---------------- */
  if (sendBtn) {
    sendBtn.onclick = async () => {
      const q = chatText.value.trim();
      if (!q) return;

      try {
        const r = await api("/api/ai/recommend", {
          method: "POST",
          body: JSON.stringify({
            mood: "neutral",
            places_list: q
          })
        });

        const div = document.createElement("div");
        div.className = "card";
        div.innerText = r.recommendation;
        messages.prepend(div);
      } catch (err) {
        alert("AI request failed");
        console.error(err);
      }
    };
  }

  /* ---------------- GOOGLE MAPS (SAFE) ---------------- */
  if (MAPS_KEY) {
    const script = document.createElement("script");
    script.src =
      "https://maps.googleapis.com/maps/api/js?key=" +
      MAPS_KEY +
      "&callback=initMap";
    script.async = true;
    script.onerror = () => console.warn("Google Maps failed to load");
    document.head.appendChild(script);
  }

  window.initMap = function () {
    try {
      map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 20.5937, lng: 78.9629 },
        zoom: 5
      });
    } catch {
      console.warn("Map init skipped");
    }
  };

  /* ---------------- LOGOUT ---------------- */
  window.logout = function () {
    localStorage.removeItem("token");
    location.reload();
  };
});
