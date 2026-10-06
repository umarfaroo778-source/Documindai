class App {
    static init() {
        AuthManager.init();
        DocumentManager.init();
        ChatManager.init();

        window.addEventListener("hashchange", () => this.handleRouting());
        this.updateUserInterface();
        this.handleRouting();
        this.initTheme();
    }

    static handleRouting() {
        let hash = window.location.hash || "#dashboard";
        
        if (!AuthManager.isAuthenticated() && hash !== "#login" && hash !== "#register") {
            hash = "#login";
            window.location.hash = "#login";
        }

        if (AuthManager.isAuthenticated() && (hash === "#login" || hash === "#register")) {
            hash = "#dashboard";
            window.location.hash = "#dashboard";
        }

        // Hide all views
        document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("d-none"));

        // Show target view
        const targetSec = document.querySelector(hash + "-view");
        if (targetSec) {
            targetSec.classList.remove("d-none");
        } else {
            document.getElementById("dashboard-view")?.classList.remove("d-none");
        }

        // Active nav state
        document.querySelectorAll(".nav-link").forEach(link => {
            if (link.getAttribute("href") === hash) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });

        // Trigger view specific re-loads
        if (hash === "#dashboard" || hash === "#documents") {
            DocumentManager.loadDocuments();
        }
    }

    static updateUserInterface() {
        const isAuth = AuthManager.isAuthenticated();
        const user = ApiClient.getUser();

        document.querySelectorAll(".auth-only").forEach(el => {
            if (isAuth) el.classList.remove("d-none");
            else el.classList.add("d-none");
        });

        document.querySelectorAll(".guest-only").forEach(el => {
            if (isAuth) el.classList.add("d-none");
            else el.classList.remove("d-none");
        });

        if (isAuth && user) {
            const userNameEls = document.querySelectorAll(".user-name");
            const userEmailEls = document.querySelectorAll(".user-email");
            const userUnivEls = document.querySelectorAll(".user-univ");

            userNameEls.forEach(el => el.textContent = user.name);
            userEmailEls.forEach(el => el.textContent = user.email);
            userUnivEls.forEach(el => el.textContent = user.university || "University Student");
        }
    }

    static showToast(message, type = "info") {
        const toastContainer = document.getElementById("toastContainer");
        if (!toastContainer) return;

        const id = "toast-" + Date.now();
        const icon = type === "success" ? "bi-check-circle-fill" : type === "danger" ? "bi-exclamation-triangle-fill" : "bi-info-circle-fill";
        
        const html = `
            <div id="${id}" class="toast align-items-center text-white bg-${type} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center gap-2">
                        <i class="bi ${icon} fs-5"></i>
                        <span>${message}</span>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>`;

        toastContainer.insertAdjacentHTML("beforeend", html);
        const toastEl = document.getElementById(id);
        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();

        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    static initTheme() {
        const toggleBtn = document.getElementById("themeToggleBtn");
        const storedTheme = localStorage.getItem("documind_theme") || "light";
        document.documentElement.setAttribute("data-bs-theme", storedTheme);

        if (toggleBtn) {
            this.updateThemeIcon(storedTheme);
            toggleBtn.addEventListener("click", () => {
                const current = document.documentElement.getAttribute("data-bs-theme");
                const next = current === "dark" ? "light" : "dark";
                document.documentElement.setAttribute("data-bs-theme", next);
                localStorage.setItem("documind_theme", next);
                this.updateThemeIcon(next);
            });
        }
    }

    static updateThemeIcon(theme) {
        const icon = document.getElementById("themeToggleIcon");
        if (icon) {
            icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => App.init());
