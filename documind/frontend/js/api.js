const API_BASE = "http://127.0.0.1:8000/api";

class ApiClient {
    static getToken() {
        return localStorage.getItem("documind_token");
    }

    static setToken(token) {
        localStorage.setItem("documind_token", token);
    }

    static removeToken() {
        localStorage.removeItem("documind_token");
        localStorage.removeItem("documind_user");
    }

    static getUser() {
        const u = localStorage.getItem("documind_user");
        return u ? JSON.parse(u) : null;
    }

    static setUser(user) {
        localStorage.setItem("documind_user", JSON.stringify(user));
    }

    static getHeaders(isMultipart = false) {
        const token = this.getToken();
        const headers = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        if (!isMultipart) {
            headers["Content-Type"] = "application/json";
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        const isMultipart = options.body instanceof FormData;
        options.headers = {
            ...this.getHeaders(isMultipart),
            ...(options.headers || {})
        };

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            if (response.status === 401) {
                this.removeToken();
                window.location.hash = "#login";
                throw new Error("Session expired. Please log in again.");
            }

            if (response.status === 204) {
                return null;
            }

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "An unexpected error occurred");
            }
            return data;
        } catch (err) {
            console.error(`API Error on ${endpoint}:`, err);
            throw err;
        }
    }

    // Auth
    static async register(name, email, password, university) {
        return this.request("/auth/register", {
            method: "POST",
            body: JSON.stringify({ name, email, password, university })
        });
    }

    static async login(email, password) {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString()
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Invalid login credentials");
        }
        return data;
    }

    static async getMe() {
        return this.request("/auth/me");
    }

    // Documents
    static async getDocuments() {
        return this.request("/documents");
    }

    static async uploadDocument(formData) {
        return this.request("/documents/upload", {
            method: "POST",
            body: formData
        });
    }

    static async deleteDocument(docId) {
        return this.request(`/documents/${docId}`, { method: "DELETE" });
    }

    // Chat
    static async askQuestion(documentId, question, conversationId = null) {
        return this.request("/chat/ask", {
            method: "POST",
            body: JSON.stringify({
                document_id: documentId,
                question: question,
                conversation_id: conversationId
            })
        });
    }

    static async getConversations(documentId) {
        return this.request(`/chat/conversations/${documentId}`);
    }

    static async getMessageHistory(conversationId) {
        return this.request(`/chat/history/${conversationId}`);
    }

    // Study Tools
    static async getSummary(documentId) {
        return this.request(`/summaries/generate/${documentId}`, { method: "POST" });
    }

    static async getQuiz(documentId) {
        return this.request(`/quizzes/generate/${documentId}`, { method: "POST" });
    }

    static async getFlashcards(documentId) {
        return this.request(`/flashcards/generate/${documentId}`, { method: "POST" });
    }

    static async getNotes(documentId) {
        return this.request(`/notes/generate/${documentId}`, { method: "POST" });
    }
}
