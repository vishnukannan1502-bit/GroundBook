let groundCards = [];
const filterButtons = [...document.querySelectorAll(".filter-chip")];
const searchForm = document.getElementById("searchForm");
const sportInput = document.getElementById("sportInput");
const locationInput = document.getElementById("locationInput");
const dateInput = document.getElementById("dateInput");
const emptyState = document.getElementById("emptyState");
const bookingModal = document.getElementById("bookingModal");
const bookingForm = document.getElementById("bookingForm");
const toast = document.getElementById("toast");
let selectedGround = "";
let selectedGroundId = null;

const today = new Date();
const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().split("T")[0];
dateInput.min = localToday;
document.getElementById("bookingDate").min = localToday;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2800);
}

async function loadGrounds() {
  try {
    const response = await fetch("/api/grounds");
    const grounds = await response.json();

    const grid = document.getElementById("groundGrid");

    grid.innerHTML = grounds.map(ground => {
      const sportClass = ground.sport.toLowerCase();

      return `
        <article class="ground-card"
          data-sport="${ground.sport}"
          data-location="${ground.location.toLowerCase()}"
          data-ground-id="${ground.id}">

          <div class="ground-image image-${sportClass}">
            <span class="image-tag">AVAILABLE</span>
            <button class="heart-btn">♡</button>
          </div>

          <div class="ground-info">
            <div class="card-topline">
              <span class="sport-label">${ground.sport}</span>
              <span class="rating">★ ${ground.rating}</span>
            </div>

            <h3>${ground.name}</h3>
            <p class="location">⌖ ${ground.location}</p>

            <div class="card-bottom">
              <div>
                <strong>₹${ground.price_per_hour}</strong>
                <small> / hour</small>
              </div>

              <button class="book-btn"
                data-ground="${ground.name}"
                data-ground-id="${ground.id}">
                Book now →
              </button>
            </div>
          </div>
        </article>
      `;
    }).join("");

    groundCards = [...document.querySelectorAll(".ground-card")];

    groundCards.forEach(card => {
      card.querySelector(".book-btn").addEventListener("click", event => {
        const button = event.currentTarget;
        selectedGround = button.dataset.ground;
        selectedGroundId = Number(button.dataset.groundId);
        document.getElementById("modalGround").textContent = selectedGround;
        document.getElementById("bookingDate").value = dateInput.value || "";
        bookingModal.showModal();
      });
    });

    applyFilters();

  } catch (error) {
    showToast("Unable to load grounds. Please check the server.");
  }
}


function applyFilters() {
  const sport = sportInput.value;
  const location = locationInput.value.trim().toLowerCase();
  let visible = 0;

  groundCards.forEach(card => {
    const matchesSport = sport === "all" || card.dataset.sport === sport;
    const matchesLocation = !location || card.dataset.location.includes(location);
    const show = matchesSport && matchesLocation;
    card.hidden = !show;
    if (show) visible++;
  });
  emptyState.hidden = visible !== 0;

  filterButtons.forEach(button => {
    button.classList.toggle("selected", button.dataset.filter === sport);
  });
}

filterButtons.forEach(button => {
  button.addEventListener("click", () => {
    sportInput.value = button.dataset.filter;
    applyFilters();
  });
});

document.querySelectorAll("[data-quick]").forEach(button => {
  button.addEventListener("click", () => {
    sportInput.value = button.dataset.quick;
    applyFilters();
    document.getElementById("grounds").scrollIntoView({ behavior: "smooth" });
  });
});

searchForm.addEventListener("submit", event => {
  event.preventDefault();
  applyFilters();
  document.getElementById("grounds").scrollIntoView({ behavior: "smooth" });
  const dateText = dateInput.value ? ` for ${dateInput.value}` : "";
  showToast(`Showing matching grounds${dateText}. Choose a ground to continue.`);
});

document.querySelectorAll(".book-btn").forEach(button => {
  button.addEventListener("click", () => {
    selectedGround = button.dataset.ground;
    selectedGroundId = Number(button.dataset.groundId);
    document.getElementById("modalGround").textContent = selectedGround;
    document.getElementById("bookingDate").value = dateInput.value || "";
    bookingModal.showModal();
  });
});

document.querySelectorAll(".heart-btn").forEach(button => {
  button.addEventListener("click", () => {
    button.classList.toggle("saved");
    button.textContent = button.classList.contains("saved") ? "♥" : "♡";
    showToast(button.classList.contains("saved") ? "Ground added to your favourites." : "Removed from favourites.");
  });
});

bookingForm.addEventListener("submit", async event => {
  event.preventDefault();
  const name = document.getElementById("customerName").value.trim();
  const date = document.getElementById("bookingDate").value;
  const slot = document.getElementById("timeSlot").value;
  if (!name || !date || !slot) return;

  const submitButton = bookingForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = "Booking...";
  try {
    const response = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ground_id: selectedGroundId,
        customer_name: name,
        booking_date: date,
        time_slot: slot
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Booking could not be completed.");
    bookingModal.close();
    bookingForm.reset();
    showToast(`Booking confirmed! Your booking ID is ${result.booking_id}.`);
  } catch (error) {
    showToast(error.message || "Could not connect to the server. Please try again.");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Confirm booking";
  }
});

const authModal = document.getElementById("authModal");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");

document.getElementById("loginBtn").addEventListener("click", () => {
  authModal.hidden = false;
  loginForm.hidden = false;
  signupForm.hidden = true;
});

document.getElementById("signupBtn").addEventListener("click", () => {
  authModal.hidden = false;
  loginForm.hidden = true;
  signupForm.hidden = false;
});

document.getElementById("closeAuthBtn").addEventListener("click", () => {
  authModal.hidden = true;
});

document.getElementById("showSignupBtn").addEventListener("click", () => {
  loginForm.hidden = true;
  signupForm.hidden = false;
});

document.getElementById("showLoginBtn").addEventListener("click", () => {
  signupForm.hidden = true;
  loginForm.hidden = false;
});

const menuToggle = document.getElementById("menuToggle");
const mainNav = document.getElementById("mainNav");
menuToggle.addEventListener("click", () => {
  const isOpen = mainNav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.textContent = isOpen ? "×" : "☰";
});
mainNav.querySelectorAll("a").forEach(link => {
  link.addEventListener("click", () => {
    mainNav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.textContent = "☰";
  });
});

loadGrounds();
signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = document.getElementById("signupName").value.trim();
  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;
  const errorBox = document.getElementById("authError");

  errorBox.textContent = "";

  try {
    const response = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });

    const result = await response.json();

    if (!response.ok) {
      errorBox.textContent = result.error || "Registration failed.";
      return;
    }

    signupForm.reset();
    signupForm.hidden = true;
    loginForm.hidden = false;

    document.getElementById("authTitle").textContent = "Account created!";
    document.getElementById("authMessage").textContent =
      "Please log in with your new account.";

    showToast("Registration successful!");
  } catch (error) {
    errorBox.textContent = "Unable to connect to the server.";
  }
});
loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const errorBox = document.getElementById("authError");

  errorBox.textContent = "";

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const result = await response.json();

    if (!response.ok) {
      errorBox.textContent = result.error || "Login failed.";
      return;
    }

    loginForm.reset();
    authModal.hidden = true;

    showToast("Welcome, " + result.name + "!");
    checkLoginStatus();

  } catch (error) {
    errorBox.textContent = "Unable to connect to the server.";
  }
});
async function checkLoginStatus() {
  try {
    const response = await fetch("/api/session");
    const result = await response.json();

    const loginBtn = document.getElementById("loginBtn");
    const signupBtn = document.getElementById("signupBtn");

    if (result.logged_in) {
      loginBtn.style.display = "none";
      signupBtn.style.display = "none";

      let userDisplay = document.getElementById("userDisplay");

      if (!userDisplay) {
        userDisplay = document.createElement("span");
        userDisplay.id = "userDisplay";
        document.querySelector(".header-actions").prepend(userDisplay);
      }

      userDisplay.textContent = "Welcome, " + result.name;
      let logoutBtn = document.getElementById("logoutBtn");

if (!logoutBtn) {
  logoutBtn = document.createElement("button");
  logoutBtn.id = "logoutBtn";
  logoutBtn.className = "login-btn";
  logoutBtn.textContent = "Log out";

  document.querySelector(".header-actions").appendChild(logoutBtn);

  logoutBtn.addEventListener("click", async () => {
    const response = await fetch("/api/logout", {
      method: "POST"
    });

    if (response.ok) {
      showToast("Logged out successfully!");
      window.location.reload();
    }
  });
}
    }
  } catch (error) {
    console.error("Session check failed:", error);
  }
}

checkLoginStatus();

