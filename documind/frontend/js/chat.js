class ChatManager {
    static activeDocumentId = null;
    static activeConversationId = null;

    static init() {
        const chatForm = document.getElementById("chatForm");
        const chatInput = document.getElementById("chatInput");

        if (chatForm) {
            chatForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const question = chatInput.value.trim();
                if (!question || !this.activeDocumentId) return;

                chatInput.value = "";
                await this.sendQuestion(question);
            });
        }
    }

    static async selectDocument(docId) {
        this.activeDocumentId = docId;
        this.activeConversationId = null;
        window.location.hash = "#workspace";

        const doc = DocumentManager.documents.find(d => d.id === docId);
        const docTitleEl = document.getElementById("chatDocTitle");
        const docBadgeEl = document.getElementById("chatDocBadge");

        if (docTitleEl) docTitleEl.textContent = doc ? doc.original_filename : "Document Workspace";
        if (docBadgeEl) docBadgeEl.textContent = doc ? `${doc.page_count} Pages` : "";

        // Reset chat message window
        const messagesContainer = document.getElementById("chatMessages");
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="text-center text-muted my-4">
                    <i class="bi bi-robot display-5 d-block text-primary mb-2"></i>
                    <p class="mb-1 fw-bold">DocuMind AI Assistant Connected</p>
                    <p class="small">Ask questions about <strong>${doc ? doc.original_filename : 'your document'}</strong>. Answers are strictly grounded in your text with page citations.</p>
                    <div class="d-flex flex-wrap justify-content-center gap-2 mt-3">
                        <button class="btn btn-sm btn-outline-secondary rounded-pill" onclick="ChatManager.askPreset('Summarize the main points of this document.')">💡 Summarize main points</button>
                        <button class="btn btn-sm btn-outline-secondary rounded-pill" onclick="ChatManager.askPreset('What are the key concepts and definitions?')">💡 Key concepts & definitions</button>
                    </div>
                </div>`;
        }

        // Load existing conversations if any
        try {
            const conversations = await ApiClient.getConversations(docId);
            if (conversations.length > 0) {
                this.activeConversationId = conversations[0].id;
                await this.loadHistory(this.activeConversationId);
            }
        } catch (err) {
            console.error("Failed to fetch conversation history:", err);
        }
    }

    static askPreset(text) {
        const chatInput = document.getElementById("chatInput");
        if (chatInput) {
            chatInput.value = text;
            document.getElementById("chatForm").dispatchEvent(new Event('submit'));
        }
    }

    static async sendQuestion(question) {
        const messagesContainer = document.getElementById("chatMessages");
        if (!messagesContainer) return;

        // Append User Message UI
        this.appendMessage("user", question, []);

        // Show Loading indicator
        const loadingId = "msg-loading-" + Date.now();
        messagesContainer.insertAdjacentHTML("beforeend", `
            <div id="${loadingId}" class="d-flex align-items-start gap-2 mb-3">
                <div class="avatar bg-primary text-white rounded-circle p-2 fs-6">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="card border-0 bg-light p-3 shadow-sm" style="max-width: 80%;">
                    <div class="d-flex align-items-center gap-2 text-muted">
                        <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                        <span class="small">Searching document chunks & generating grounded answer...</span>
                    </div>
                </div>
            </div>
        `);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await ApiClient.askQuestion(this.activeDocumentId, question, this.activeConversationId);
            this.activeConversationId = response.conversation_id;

            // Remove loading indicator
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            // Append Assistant Response
            this.appendMessage("assistant", response.answer, response.citations, response.grounded);
        } catch (err) {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            App.showToast(err.message, "danger");
        }
    }

    static async loadHistory(convId) {
        try {
            const messages = await ApiClient.getMessageHistory(convId);
            const messagesContainer = document.getElementById("chatMessages");
            if (!messagesContainer) return;

            messagesContainer.innerHTML = "";
            messages.forEach(m => {
                this.appendMessage(m.role, m.content, m.citations || [], true);
            });
        } catch (err) {
            console.error("Failed to load message history:", err);
        }
    }

    static appendMessage(role, content, citations = [], grounded = true) {
        const messagesContainer = document.getElementById("chatMessages");
        if (!messagesContainer) return;

        const isUser = role === "user";
        const formattedContent = this.formatMarkdown(content);

        let citationBadges = "";
        if (!isUser && citations.length > 0) {
            citationBadges = `
                <div class="mt-2 pt-2 border-top">
                    <small class="text-muted d-block fw-semibold mb-1"><i class="bi bi-bookmark-check-fill text-primary"></i> Source Citations:</small>
                    <div class="d-flex flex-wrap gap-1">
                        ${citations.map(c => `
                            <button class="btn btn-xs btn-outline-primary rounded-pill py-0 px-2 small" onclick="ChatManager.showSnippetModal(${c.page_number}, '${this.escapeHtml(c.snippet)}')">
                                <i class="bi bi-file-earmark-text me-1"></i> Page ${c.page_number}
                            </button>
                        `).join('')}
                    </div>
                </div>`;
        }

        let groundedBadge = "";
        if (!isUser) {
            if (grounded) {
                groundedBadge = `<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill mb-1"><i class="bi bi-shield-check"></i> Grounded Answer</span>`;
            } else {
                groundedBadge = `<span class="badge bg-warning-subtle text-warning border border-warning-subtle rounded-pill mb-1"><i class="bi bi-exclamation-triangle"></i> Low Grounding Score</span>`;
            }
        }

        const msgHtml = `
            <div class="d-flex align-items-start gap-2 mb-3 ${isUser ? 'flex-row-reverse' : ''}">
                <div class="avatar ${isUser ? 'bg-secondary' : 'bg-primary'} text-white rounded-circle p-2 fs-6 shadow-sm">
                    <i class="bi ${isUser ? 'bi-person-fill' : 'bi-robot'}"></i>
                </div>
                <div class="card border-0 ${isUser ? 'bg-primary text-white' : 'bg-light text-dark'} p-3 shadow-sm" style="max-width: 80%;">
                    ${groundedBadge}
                    <div class="message-body">${formattedContent}</div>
                    ${citationBadges}
                </div>
            </div>`;

        messagesContainer.insertAdjacentHTML("beforeend", msgHtml);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    static formatMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\[Page (\d+)\]/g, '<span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-0">Page $1</span>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
        return html;
    }

    static escapeHtml(str) {
        return str ? str.replace(/'/g, "\\'").replace(/"/g, "&quot;") : "";
    }

    static showSnippetModal(pageNum, snippet) {
        const bodyEl = document.getElementById("snippetModalBody");
        const titleEl = document.getElementById("snippetModalTitle");
        if (bodyEl && titleEl) {
            titleEl.textContent = `Source Reference - Page ${pageNum}`;
            bodyEl.textContent = snippet;
            const modal = new bootstrap.Modal(document.getElementById("snippetModal"));
            modal.show();
        }
    }
}
