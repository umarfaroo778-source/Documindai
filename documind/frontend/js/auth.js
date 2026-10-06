class AuthManager {
    static init() {
        const loginForm = document.getElementById("loginForm");
        const registerForm = document.getElementById("registerForm");
        const logoutBtn = document.getElementById("logoutBtn");

        if (loginForm) {
            loginForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const email = document.getElementById("loginEmail").value.trim();
                const password = document.getElementById("loginPassword").value;
                const errorEl = document.getElementById("loginError");
                errorEl.classList.add("d-none");

                try {
                    const data = await ApiClient.login(email, password);
                    ApiClient.setToken(data.access_token);
                    ApiClient.setUser(data.user);
                    App.showToast("Welcome back to DocuMind!", "success");
                    App.updateUserInterface();
                    window.location.hash = "#dashboard";
                } catch (err) {
                    errorEl.textContent = err.message;
                    errorEl.classList.remove("d-none");
                }
            });
        }

        if (registerForm) {
            registerForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const name = document.getElementById("regName").value.trim();
                const email = document.getElementById("regEmail").value.trim();
                const password = document.getElementById("regPassword").value;
                const university = document.getElementById("regUniversity").value.trim();
                const errorEl = document.getElementById("registerError");
                errorEl.classList.add("d-none");

                try {
                    const data = await ApiClient.register(name, email, password, university);
                    ApiClient.setToken(data.access_token);
                    ApiClient.setUser(data.user);
                    App.showToast("Account created successfully!", "success");
                    App.updateUserInterface();
                    window.location.hash = "#dashboard";
                } catch (err) {
                    errorEl.textContent = err.message;
                    errorEl.classList.remove("d-none");
                }
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                ApiClient.removeToken();
                App.showToast("Logged out successfully.", "info");
                App.updateUserInterface();
                window.location.hash = "#login";
            });
        }
    }

    static isAuthenticated() {
        return !!ApiClient.getToken();
    }
}
