document.addEventListener("DOMContentLoaded", () => {
  startApp();
});

function startApp() {
const API_BASE = window.APP_CONFIG?.API_BASE;
const GOOGLE_MAPS_API_KEY = window.APP_CONFIG?.GOOGLE_MAPS_API_KEY;

if (!API_BASE) {
  alert("API_BASE missing. Frontend misconfigured.");
  throw new Error("API_BASE missing");
}


let token = localStorage.getItem("token");
let map, markers=[];

const loader = document.getElementById("loader");
const auth = document.getElementById("auth");
const app = document.getElementById("app");

function showLoader() {
  if (loader) {
    loader.classList.remove("hidden");
  }
}

function hideLoader() {
  if (loader) {
    loader.classList.add("hidden");
  }
}


function showApp(){
  auth.classList.add("hidden");
  app.classList.remove("hidden");
}

if(token) showApp();

async function api(path, options={}){
  showLoader();
  try{
    const r = await fetch(API_BASE+path,{
      ...options,
      headers:{
        "Content-Type":"application/json",
        Authorization: token ? "Bearer "+token : ""
      }
    });
    if(!r.ok) throw new Error(await r.text());
    return await r.json();
  }finally{hideLoader()}
}

/* AUTH */
let isLogin=true;
switchAuth.onclick=()=>{
  isLogin=!isLogin;
  authTitle.innerText=isLogin?"Login":"Sign Up";
  authBtn.innerText=isLogin?"Login":"Sign Up";
  switchAuth.innerText=isLogin?"No account? Sign up":"Have account? Login";
};

authBtn.onclick=async()=>{
  const email=document.getElementById("email").value;
  const password=document.getElementById("password").value;
  const path=isLogin?"/api/auth/login":"/api/auth/signup";
  const res=await api(path,{method:"POST",body:JSON.stringify({email,password})});
  if(res.access_token){
    token=res.access_token;
    localStorage.setItem("token",token);
    showApp();
  }
};

function logout(){
  localStorage.clear();location.reload();
}

/* ITINERARY */
newItinBtn.onclick=async()=>{
  const dest=destInput.value||"Pune";
  const data=await api("/api/itinerary",{method:"POST",body:JSON.stringify({destination:dest})});
  messages.innerHTML="";
  data.plan.forEach(d=>{
    const c=document.createElement("div");
    c.className="card";
    c.innerText=`Day ${d.day}: ${d.summary}`;
    messages.appendChild(c);
  });
};

/* AI */
sendBtn.onclick=async()=>{
  const q=chatText.value;
  const r=await api("/api/ai/recommend",{method:"POST",body:JSON.stringify({places_list:q})});
  const c=document.createElement("div");
  c.className="card";c.innerText=r.recommendation;
  messages.prepend(c);
};

/* MAP */
if(GOOGLE_MAPS_API_KEY){
  const s=document.createElement("script");
  s.src=`https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&callback=initMap`;
  s.async=true;document.head.appendChild(s);
}
window.initMap=()=>map=new google.maps.Map(document.getElementById("map"),{center:{lat:20.5,lng:78.9},zoom:5});
}
