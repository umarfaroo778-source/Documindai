class DocumentManager {
    static documents = [];

    static init() {
        const dropzone = document.getElementById("uploadDropzone");
        const fileInput = document.getElementById("fileInput");

        if (dropzone && fileInput) {
            dropzone.addEventListener("click", () => fileInput.click());

            dropzone.addEventListener("dragover", (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            });

            dropzone.addEventListener("dragleave", () => {
                dropzone.classList.remove("dragover");
            });

            dropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
                if (e.dataTransfer.files.length) {
                    this.handleUpload(e.dataTransfer.files[0]);
                }
            });

            fileInput.addEventListener("change", (e) => {
                if (e.target.files.length) {
                    this.handleUpload(e.target.files[0]);
                }
            });
        }
    }

    static async loadDocuments() {
        if (!AuthManager.isAuthenticated()) return;
        try {
            this.documents = await ApiClient.getDocuments();
            this.renderDocumentList();
            this.updateDashboardStats();
        } catch (err) {
            console.error("Failed to load documents:", err);
        }
    }

    static async handleUpload(file) {
        const progressEl = document.getElementById("uploadProgress");
        const progressBar = document.getElementById("uploadProgressBar");
        if (progressEl && progressBar) {
            progressEl.classList.remove("d-none");
            progressBar.style.width = "40%";
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const doc = await ApiClient.uploadDocument(formData);
            if (progressBar) progressBar.style.width = "100%";
            App.showToast(`'${doc.original_filename}' uploaded & processed successfully!`, "success");
            
            // Close modal if open
            const uploadModal = bootstrap.Modal.getInstance(document.getElementById("uploadModal"));
            if (uploadModal) uploadModal.hide();

            await this.loadDocuments();
        } catch (err) {
            App.showToast(err.message, "danger");
        } finally {
            if (progressEl) setTimeout(() => progressEl.classList.add("d-none"), 1000);
        }
    }

    static renderDocumentList() {
        const tableBody = document.getElementById("documentsTableBody");
        const gridView = document.getElementById("documentsGrid");

        if (tableBody) {
            if (this.documents.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">
                            <i class="bi bi-file-earmark-text display-6 d-block mb-2"></i>
                            No documents uploaded yet. Upload your lecture notes or textbooks to get started!
                        </td>
                    </tr>`;
            } else {
                tableBody.innerHTML = this.documents.map(doc => `
                    <tr>
                        <td class="align-middle">
                            <div class="d-flex align-items-center">
                                <i class="bi ${this.getFileIcon(doc.file_type)} fs-4 text-primary me-3"></i>
                                <div>
                                    <strong class="d-block text-truncate" style="max-width: 260px;">${doc.original_filename}</strong>
                                    <small class="text-muted">${(doc.file_size / 1024).toFixed(1)} KB</small>
                                </div>
                            </div>
                        </td>
                        <td class="align-middle"><span class="badge bg-secondary">${doc.file_type.toUpperCase()}</span></td>
                        <td class="align-middle">${doc.page_count} ${doc.page_count === 1 ? 'Page' : 'Pages'}</td>
                        <td class="align-middle">
                            <span class="badge bg-${doc.status === 'ready' ? 'success' : 'warning'}">
                                ${doc.status.toUpperCase()}
                            </span>
                        </td>
                        <td class="align-middle text-muted">${new Date(doc.created_at).toLocaleDateString()}</td>
                        <td class="align-middle text-end">
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="ChatManager.selectDocument(${doc.id})">
                                <i class="bi bi-chat-text-fill me-1"></i> QA Chat
                            </button>
                            <button class="btn btn-sm btn-outline-secondary me-1" onclick="StudyToolsManager.openStudyHub(${doc.id})">
                                <i class="bi bi-journal-bookmark-fill me-1"></i> Study Tools
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="DocumentManager.confirmDelete(${doc.id})">
                                <i class="bi bi-trash-fill"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        }
    }

    static updateDashboardStats() {
        const totalDocsEl = document.getElementById("statTotalDocs");
        const totalPagesEl = document.getElementById("statTotalPages");
        const recentListEl = document.getElementById("recentDocsList");

        if (totalDocsEl) totalDocsEl.textContent = this.documents.length;
        if (totalPagesEl) {
            const sumPages = this.documents.reduce((acc, d) => acc + (d.page_count || 0), 0);
            totalPagesEl.textContent = sumPages;
        }

        if (recentListEl) {
            if (this.documents.length === 0) {
                recentListEl.innerHTML = `<p class="text-muted small mb-0">No recent documents found.</p>`;
            } else {
                recentListEl.innerHTML = this.documents.slice(0, 4).map(doc => `
                    <div class="d-flex align-items-center justify-content-between p-2 rounded hover-bg mb-2 border">
                        <div class="d-flex align-items-center text-truncate">
                            <i class="bi ${this.getFileIcon(doc.file_type)} text-primary fs-5 me-2"></i>
                            <span class="text-truncate fw-medium small">${doc.original_filename}</span>
                        </div>
                        <button class="btn btn-xs btn-primary ms-2" onclick="ChatManager.selectDocument(${doc.id})">Open</button>
                    </div>
                `).join('');
            }
        }
    }

    static async confirmDelete(docId) {
        if (confirm("Are you sure you want to delete this document? All chats and generated study materials will be removed.")) {
            try {
                await ApiClient.deleteDocument(docId);
                App.showToast("Document deleted successfully", "info");
                await this.loadDocuments();
            } catch (err) {
                App.showToast(err.message, "danger");
            }
        }
    }

    static getFileIcon(ext) {
        switch (ext.toLowerCase()) {
            case 'pdf': return 'bi-file-earmark-pdf-fill';
            case 'docx': case 'doc': return 'bi-file-earmark-word-fill';
            default: return 'bi-file-earmark-text-fill';
        }
    }
}
