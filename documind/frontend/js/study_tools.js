class StudyToolsManager {
    static currentDocId = null;
    static currentQuiz = null;
    static currentQuizAnswers = {};
    static currentFlashcards = [];
    static currentFlashcardIdx = 0;
    static isCardFlipped = false;

    static async openStudyHub(docId) {
        this.currentDocId = docId;
        window.location.hash = "#study-hub";

        const doc = DocumentManager.documents.find(d => d.id === docId);
        const titleEl = document.getElementById("studyDocTitle");
        if (titleEl) titleEl.textContent = doc ? doc.original_filename : "Study Assistant Hub";

        // Default to Summary Tab
        await this.loadSummary();
    }

    // --- 1. Summaries ---
    static async loadSummary() {
        if (!this.currentDocId) return;
        const container = document.getElementById("summaryContainer");
        if (!container) return;

        container.innerHTML = `
            <div class="text-center my-5 py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted fw-medium">Generating executive summary & key takeaways...</p>
            </div>`;

        try {
            const data = await ApiClient.getSummary(this.currentDocId);
            container.innerHTML = `
                <div class="card border-0 shadow-sm mb-4">
                    <div class="card-body p-4">
                        <div class="d-flex align-items-center justify-content-between mb-3">
                            <h5 class="fw-bold text-primary mb-0"><i class="bi bi-file-text-fill me-2"></i>Executive Summary</h5>
                            <button class="btn btn-sm btn-outline-secondary" onclick="StudyToolsManager.copySummaryText()">
                                <i class="bi bi-clipboard me-1"></i> Copy
                            </button>
                        </div>
                        <p class="lead fs-6 text-dark" id="execSummaryText">${data.executive_summary}</p>
                        
                        <h6 class="fw-bold text-secondary mt-4 mb-3"><i class="bi bi-card-checklist me-2"></i>Key Takeaways & Bullet Points</h6>
                        <ul class="list-group list-group-flush">
                            ${data.key_takeaways.map(t => `
                                <li class="list-group-item bg-transparent ps-0 d-flex align-items-start gap-2">
                                    <i class="bi bi-check-circle-fill text-success fs-5"></i>
                                    <span>${t}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>`;
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        }
    }

    static copySummaryText() {
        const textEl = document.getElementById("execSummaryText");
        if (textEl) {
            navigator.clipboard.writeText(textEl.textContent);
            App.showToast("Summary copied to clipboard!", "success");
        }
    }

    // --- 2. MCQ Quiz Player ---
    static async loadQuiz() {
        if (!this.currentDocId) return;
        const container = document.getElementById("quizContainer");
        if (!container) return;

        container.innerHTML = `
            <div class="text-center my-5 py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted fw-medium">Synthesizing multiple choice practice quiz...</p>
            </div>`;

        try {
            this.currentQuiz = await ApiClient.getQuiz(this.currentDocId);
            this.currentQuizAnswers = {};
            this.renderQuiz();
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        }
    }

    static renderQuiz() {
        const container = document.getElementById("quizContainer");
        if (!container || !this.currentQuiz) return;

        const qList = this.currentQuiz.questions;

        let html = `
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-white py-3 border-0 d-flex align-items-center justify-content-between">
                    <h5 class="fw-bold text-primary mb-0"><i class="bi bi-patch-question-fill me-2"></i>${this.currentQuiz.title}</h5>
                    <span class="badge bg-primary fs-6">${qList.length} Questions</span>
                </div>
                <div class="card-body p-4">
                    <form id="quizForm" onsubmit="StudyToolsManager.submitQuiz(event)">
                        ${qList.map((q, qIdx) => `
                            <div class="card border mb-4 p-3 rounded shadow-xs" id="quiz-q-${qIdx}">
                                <h6 class="fw-bold mb-3 text-dark">
                                    <span class="badge bg-secondary me-2">Q${qIdx + 1}</span> ${q.question}
                                </h6>
                                <div class="options-group">
                                    ${q.options.map((opt, optIdx) => `
                                        <div class="form-check mb-2">
                                            <input class="form-check-input" type="radio" name="q_${qIdx}" id="q_${qIdx}_opt_${optIdx}" value="${optIdx}" onchange="StudyToolsManager.selectQuizAnswer(${qIdx}, ${optIdx})">
                                            <label class="form-check-label w-100 p-2 rounded hover-bg border" for="q_${qIdx}_opt_${optIdx}">
                                                ${opt}
                                            </label>
                                        </div>
                                    `).join('')}
                                </div>
                                <div class="explanation-box d-none mt-3 p-3 rounded bg-light border-start border-4 border-info">
                                    <small class="fw-bold text-info d-block mb-1"><i class="bi bi-info-circle-fill me-1"></i> Explanation:</small>
                                    <small class="text-dark">${q.explanation}</small>
                                </div>
                            </div>
                        `).join('')}

                        <div class="d-flex align-items-center justify-content-between mt-4">
                            <div id="quizResultBadge" class="fs-5 fw-bold text-success d-none"></div>
                            <button type="submit" class="btn btn-primary px-4 py-2 fw-semibold">
                                <i class="bi bi-send-check-fill me-1"></i> Submit Quiz & Score
                            </button>
                        </div>
                    </form>
                </div>
            </div>`;

        container.innerHTML = html;
    }

    static selectQuizAnswer(qIdx, optIdx) {
        this.currentQuizAnswers[qIdx] = optIdx;
    }

    static submitQuiz(event) {
        event.preventDefault();
        if (!this.currentQuiz) return;

        const qList = this.currentQuiz.questions;
        let score = 0;

        qList.forEach((q, qIdx) => {
            const userSelected = this.currentQuizAnswers[qIdx];
            const qCard = document.getElementById(`quiz-q-${qIdx}`);
            const expBox = qCard.querySelector('.explanation-box');

            if (expBox) expBox.classList.remove('d-none');

            const radioInputs = qCard.querySelectorAll('input[type="radio"]');
            radioInputs.forEach(r => r.disabled = true);

            if (userSelected === q.correct_option_index) {
                score++;
                qCard.classList.add('border-success', 'bg-success-subtle');
            } else {
                qCard.classList.add('border-danger', 'bg-danger-subtle');
            }
        });

        const resultBadge = document.getElementById('quizResultBadge');
        if (resultBadge) {
            const percentage = Math.round((score / qList.length) * 100);
            resultBadge.innerHTML = `<i class="bi bi-trophy-fill text-warning me-1"></i> Score: ${score} / ${qList.length} (${percentage}%)`;
            resultBadge.classList.remove('d-none');
        }

        App.showToast(`Quiz completed! You scored ${score}/${qList.length}`, "success");
    }

    // --- 3. Flashcards 3D Player ---
    static async loadFlashcards() {
        if (!this.currentDocId) return;
        const container = document.getElementById("flashcardsContainer");
        if (!container) return;

        container.innerHTML = `
            <div class="text-center my-5 py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted fw-medium">Building interactive flashcard study deck...</p>
            </div>`;

        try {
            const data = await ApiClient.getFlashcards(this.currentDocId);
            this.currentFlashcards = data.cards;
            this.currentFlashcardIdx = 0;
            this.isCardFlipped = false;
            this.renderFlashcards();
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        }
    }

    static renderFlashcards() {
        const container = document.getElementById("flashcardsContainer");
        if (!container || this.currentFlashcards.length === 0) return;

        const card = this.currentFlashcards[this.currentFlashcardIdx];
        const total = this.currentFlashcards.length;
        const currentNum = this.currentFlashcardIdx + 1;
        const progressPct = Math.round((currentNum / total) * 100);

        container.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <!-- Progress Bar -->
                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <small class="text-muted fw-semibold">Card ${currentNum} of ${total}</small>
                        <small class="text-primary fw-semibold">${progressPct}% Completed</small>
                    </div>
                    <div class="progress mb-4" style="height: 6px;">
                        <div class="progress-bar bg-primary" role="progressbar" style="width: ${progressPct}%;"></div>
                    </div>

                    <!-- 3D Flip Card -->
                    <div class="flashcard-wrapper mb-4" onclick="StudyToolsManager.toggleCardFlip()">
                        <div class="flashcard-inner ${this.isCardFlipped ? 'flipped' : ''}">
                            <div class="flashcard-front card border-0 shadow text-center p-5 rounded-4 bg-white d-flex flex-column justify-content-center align-items-center">
                                <span class="badge bg-primary-subtle text-primary mb-3">QUESTION / PROMPT</span>
                                <h4 class="fw-bold text-dark px-3">${card.front}</h4>
                                <small class="text-muted mt-4"><i class="bi bi-arrow-repeat me-1"></i> Click to flip for answer</small>
                            </div>
                            <div class="flashcard-back card border-0 shadow text-center p-5 rounded-4 bg-primary text-white d-flex flex-column justify-content-center align-items-center">
                                <span class="badge bg-white text-primary mb-3">ANSWER / EXPLANATION</span>
                                <p class="fs-5 fw-medium px-3 text-white">${card.back}</p>
                                <small class="text-white-50 mt-4"><i class="bi bi-arrow-repeat me-1"></i> Click to flip back</small>
                            </div>
                        </div>
                    </div>

                    <!-- Controls -->
                    <div class="d-flex align-items-center justify-content-between">
                        <button class="btn btn-outline-secondary px-4 rounded-pill" onclick="StudyToolsManager.prevFlashcard()" ${this.currentFlashcardIdx === 0 ? 'disabled' : ''}>
                            <i class="bi bi-chevron-left me-1"></i> Previous
                        </button>
                        <button class="btn btn-success px-4 rounded-pill" onclick="StudyToolsManager.nextFlashcard()">
                            <i class="bi bi-check2-circle me-1"></i> ${this.currentFlashcardIdx === total - 1 ? 'Finish Deck' : 'Next Card'} <i class="bi bi-chevron-right ms-1"></i>
                        </button>
                    </div>
                </div>
            </div>`;
    }

    static toggleCardFlip() {
        this.isCardFlipped = !this.isCardFlipped;
        const inner = document.querySelector(".flashcard-inner");
        if (inner) {
            inner.classList.toggle("flipped", this.isCardFlipped);
        }
    }

    static nextFlashcard() {
        if (this.currentFlashcardIdx < this.currentFlashcards.length - 1) {
            this.currentFlashcardIdx++;
            this.isCardFlipped = false;
            this.renderFlashcards();
        } else {
            App.showToast("Congratulations! You completed the study flashcard deck 🎉", "success");
            this.currentFlashcardIdx = 0;
            this.isCardFlipped = false;
            this.renderFlashcards();
        }
    }

    static prevFlashcard() {
        if (this.currentFlashcardIdx > 0) {
            this.currentFlashcardIdx--;
            this.isCardFlipped = false;
            this.renderFlashcards();
        }
    }

    // --- 4. Study Notes ---
    static async loadNotes() {
        if (!this.currentDocId) return;
        const container = document.getElementById("notesContainer");
        if (!container) return;

        container.innerHTML = `
            <div class="text-center my-5 py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted fw-medium">Structuring comprehensive study notes...</p>
            </div>`;

        try {
            const data = await ApiClient.getNotes(this.currentDocId);
            container.innerHTML = `
                <div class="card border-0 shadow-sm mb-4">
                    <div class="card-header bg-white py-3 border-0 d-flex align-items-center justify-content-between">
                        <h5 class="fw-bold text-primary mb-0"><i class="bi bi-journal-code me-2"></i>${data.title}</h5>
                        <button class="btn btn-sm btn-primary" onclick="StudyToolsManager.downloadNotes('${data.title}', \`${this.escapeNotes(data.markdown_content)}\`)">
                            <i class="bi bi-download me-1"></i> Export Markdown
                        </button>
                    </div>
                    <div class="card-body p-4">
                        ${data.key_concepts && data.key_concepts.length > 0 ? `
                            <div class="mb-4">
                                <small class="text-muted fw-bold d-block mb-2">KEY CONCEPTS COVERED:</small>
                                <div class="d-flex flex-wrap gap-2">
                                    ${data.key_concepts.map(c => `<span class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 fs-6 rounded-pill">${c}</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                        <div class="markdown-preview p-4 rounded bg-light border text-dark font-monospace" style="white-space: pre-wrap; font-size: 0.95rem;">${data.markdown_content}</div>
                    </div>
                </div>`;
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        }
    }

    static escapeNotes(str) {
        return str ? str.replace(/`/g, "\\`").replace(/\$/g, "\\$") : "";
    }

    static downloadNotes(title, content) {
        const element = document.createElement("a");
        const file = new Blob([content], {type: 'text/markdown'});
        element.href = URL.createObjectURL(file);
        element.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
        App.showToast("Study notes downloaded!", "success");
    }
}
