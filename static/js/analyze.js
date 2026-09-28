// ==========================================
// LexiGuard Live AI Conversational Chat Engine
// ==========================================

const urlParams = new URLSearchParams(window.location.search);
let activeDocumentId = urlParams.get("document_id");
let isAnalyzing = false;

// DOM Elements
const documentName = document.getElementById("documentName");
const documentMetadata = document.getElementById("documentMetadata");
const analysisDocSelect = document.getElementById("analysisDocSelect");
const questionInput = document.getElementById("questionInput") || document.getElementById("analysisQuestion");
const askButton = document.getElementById("askButton") || document.getElementById("askAnalysisButton");
const questionStatus = document.getElementById("questionStatus");
const chatMessagesContainer = document.getElementById("chatMessagesContainer");
const sourcesContainer = document.getElementById("sourcesContainer");
const analysisIntent = document.getElementById("analysisIntent");

// Load analysis document list
async function loadAnalysisDocumentList() {
    try {
        const response = await fetch("/api/documents");
        const result = await response.json();
        if (!response.ok) return;

        const rawDocs = (result.documents || []).filter(function (doc) {
            return doc && doc.document_id && !String(doc.document_id).startsWith("USER#");
        });

        const documents = (window.LexiGuard && window.LexiGuard.formatDocumentDisplayLabels)
            ? window.LexiGuard.formatDocumentDisplayLabels(rawDocs)
            : rawDocs;

        const currentUrlParams = new URLSearchParams(window.location.search);
        const urlDocId = currentUrlParams.get("document_id");
        if (urlDocId) {
            activeDocumentId = urlDocId;
        }

        const docSelectEl = document.getElementById("analysisDocSelect") || analysisDocSelect;

        if (docSelectEl) {
            let html = '<option value="">Select a document to analyze...</option>';
            documents.forEach(function (doc) {
                const labelText = doc.display_filename || doc.filename;
                html += `<option value="${escapeHtml(doc.document_id)}" title="${escapeHtml(doc.filename)}">${escapeHtml(labelText)}</option>`;
            });
            docSelectEl.innerHTML = html;

            if (activeDocumentId) {
                docSelectEl.value = activeDocumentId;
                await loadDocument(activeDocumentId);
            } else if (documents.length > 0) {
                activeDocumentId = documents[0].document_id;
                docSelectEl.value = activeDocumentId;
                await loadDocument(activeDocumentId);
            } else {
                const docNameEl = document.getElementById("documentName") || documentName;
                const docMetaEl = document.getElementById("documentMetadata") || documentMetadata;
                const askBtnEl = document.getElementById("askButton") || askButton;
                if (docNameEl) docNameEl.textContent = "No documents available";
                if (docMetaEl) docMetaEl.textContent = "Please upload a document to begin AI analysis.";
                if (askBtnEl) askBtnEl.disabled = true;
            }
        }
    } catch (error) {
        console.error("Error loading document list for analysis:", error);
    }
}

if (analysisDocSelect) {
    analysisDocSelect.addEventListener("change", function () {
        const selectedId = analysisDocSelect.value;
        if (selectedId) {
            activeDocumentId = selectedId;
            const askBtnEl = document.getElementById("askButton") || askButton;
            if (askBtnEl) askBtnEl.disabled = false;
            loadDocument(selectedId);
        } else {
            activeDocumentId = null;
            const docNameEl = document.getElementById("documentName") || documentName;
            const docMetaEl = document.getElementById("documentMetadata") || documentMetadata;
            const askBtnEl = document.getElementById("askButton") || askButton;
            if (docNameEl) docNameEl.textContent = "No document selected";
            if (docMetaEl) docMetaEl.textContent = "Select a document from the dropdown above.";
            if (askBtnEl) askBtnEl.disabled = true;
        }
    });
}

async function loadDocument(targetDocId) {
    const targetId = targetDocId || activeDocumentId;
    if (!targetId) return;

    const docNameEl = document.getElementById("documentName") || documentName;
    const docMetaEl = document.getElementById("documentMetadata") || documentMetadata;
    const askBtnEl = document.getElementById("askButton") || askButton;

    try {
        const response = await fetch(`/api/documents/${encodeURIComponent(targetId)}`);
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Unable to load document.");

        const documentItem = result.document;
        if (docNameEl) docNameEl.textContent = documentItem.filename;

        const selectedDocNameEl = document.getElementById("selectedDocumentName");
        if (selectedDocNameEl) selectedDocNameEl.textContent = documentItem.filename;

        if (docMetaEl) {
            docMetaEl.textContent =
                `${documentItem.page_count} pages · ` +
                `${formatFileSize(documentItem.file_size_bytes)} · ` +
                `${documentItem.processing_status.toUpperCase()}`;
        }

        if (askBtnEl) askBtnEl.disabled = false;

        const downloadReportBtn = document.getElementById("downloadReportBtn");
        if (downloadReportBtn) {
            downloadReportBtn.href = `/api/reports/analysis/${documentItem.document_id}`;
            downloadReportBtn.style.display = "inline-flex";
        }
    } catch (error) {
        console.error("Document loading error:", error);
        if (docNameEl) docNameEl.textContent = "Unable to load document";
        if (docMetaEl) docMetaEl.textContent = error.message;
        if (askBtnEl) askBtnEl.disabled = true;
    }
}

// Live Conversational Message Handlers
function appendUserMessage(text) {
    if (!chatMessagesContainer) return;

    const userDiv = document.createElement("div");
    userDiv.className = "chat-message chat-message-user";
    userDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-content">${escapeHtml(text)}</div>
        </div>
    `;
    chatMessagesContainer.appendChild(userDiv);
    scrollChatToBottom();
}

function appendTypingIndicator() {
    if (!chatMessagesContainer) return null;

    const id = "typing_" + Date.now();
    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-message chat-message-ai";
    typingDiv.id = id;
    typingDiv.innerHTML = `
        <div class="message-avatar">✦</div>
        <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span style="font-size: 13px; color: #475569; margin-left: 6px; font-weight: 500;">LexiGuard is analyzing...</span>
        </div>
    `;
    chatMessagesContainer.appendChild(typingDiv);
    scrollChatToBottom();
    return id;
}

function removeTypingIndicator(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendAiMessage(text, intent, sources) {
    if (!chatMessagesContainer) return;

    const aiDiv = document.createElement("div");
    aiDiv.className = "chat-message chat-message-ai";

    let sourcesHtml = "";
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">SOURCES & CITATIONS:</span>
                ${sources.map(function(s) {
                    if (s.article || s.part) {
                        return `<span class="source-badge">📜 Constitution · ${escapeHtml(s.article || '')}</span>`;
                    }
                    return `<span class="source-badge">Page ${s.page_number} · Chunk ${s.chunk_number}</span>`;
                }).join(" ")}
            </div>
        `;
    }

    const intentLabel = (intent || "ANALYSIS").toUpperCase();

    aiDiv.innerHTML = `
        <div class="message-avatar">✦</div>
        <div class="message-bubble">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <span class="badge badge-info" style="font-size: 10px;">${escapeHtml(intentLabel)}</span>
                <span style="font-size: 11px; color: #64748B;">Grounded Response</span>
            </div>
            <div class="message-content">${escapeHtml(text)}</div>
            ${sourcesHtml}
        </div>
    `;

    chatMessagesContainer.appendChild(aiDiv);
    scrollChatToBottom();
}

function appendErrorMessage(errorMessage, origQuestion) {
    if (!chatMessagesContainer) return;

    const errDiv = document.createElement("div");
    errDiv.className = "chat-message chat-message-ai";
    errDiv.innerHTML = `
        <div class="message-avatar" style="background: #B91C1C;">✕</div>
        <div class="message-bubble" style="border-color: rgba(185, 28, 28, 0.3); background: #FEF2F2;">
            <div style="font-size: 13.5px; font-weight: 600; color: #B91C1C; margin-bottom: 4px;">Unable to complete request</div>
            <div class="message-content" style="color: #7F1D1D; font-size: 13px;">${escapeHtml(errorMessage)}</div>
            <div style="margin-top: 10px;">
                <button type="button" class="btn btn-sm btn-outline" style="border-color: rgba(185, 28, 28, 0.4); color: #B91C1C;" onclick="retryQuestion('${escapeHtml(origQuestion)}')">
                    <span>↻</span> Try Again
                </button>
            </div>
        </div>
    `;
    chatMessagesContainer.appendChild(errDiv);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    if (chatMessagesContainer) {
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }
}

function retryQuestion(prompt) {
    if (prompt) askQuestion(prompt);
}

// Ask Question Engine
async function askQuestion(overridePrompt) {
    if (isAnalyzing) return;

    const questionText = overridePrompt || (questionInput ? questionInput.value.trim() : "");
    if (!questionText) {
        if (window.LexiGuard && window.LexiGuard.showToast) {
            window.LexiGuard.showToast("Please enter a question or prompt.", "info");
        }
        if (questionInput) questionInput.focus();
        return;
    }

    const isConstitutionMode = window.location.pathname.startsWith("/constitution") || !document.getElementById("analysisDocSelect");

    if (!isConstitutionMode) {
        if (!activeDocumentId && analysisDocSelect) {
            const firstValidOption = analysisDocSelect.querySelector('option[value]:not([value=""])');
            if (firstValidOption) activeDocumentId = firstValidOption.value;
        }
        if (!activeDocumentId) {
            if (window.LexiGuard && window.LexiGuard.showToast) {
                window.LexiGuard.showToast("Please select a document to analyze first.", "error");
            }
            return;
        }
    }

    // Clear input field if sent from composer
    if (questionInput && !overridePrompt) {
        questionInput.value = "";
        questionInput.style.height = "auto";
    }

    isAnalyzing = true;
    if (askButton) {
        askButton.disabled = true;
        askButton.textContent = "Analyzing...";
    }
    if (analysisIntent) analysisIntent.textContent = "PROCESSING";
    if (questionStatus) questionStatus.textContent = isConstitutionMode ? "Searching Constitution knowledge base..." : "Analyzing document...";

    // Append User Message & Typing Indicator
    appendUserMessage(questionText);
    const typingId = appendTypingIndicator();

    try {
        const fetchUrl = isConstitutionMode ? "/api/constitution" : "/api/analyze";
        const fetchBody = isConstitutionMode
            ? JSON.stringify({ question: questionText })
            : JSON.stringify({ document_id: activeDocumentId, question: questionText });

        const response = await fetch(fetchUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: fetchBody
        });

        const result = await response.json();
        removeTypingIndicator(typingId);

        if (!response.ok) {
            throw new Error(result.error || (isConstitutionMode ? "Unable to access the Constitution knowledge base. Please try again." : "Unable to analyze document."));
        }

        const answerText = result.response || result.answer || "No response text returned.";
        appendAiMessage(answerText, result.intent, result.sources);

        if (analysisIntent) analysisIntent.textContent = (result.intent || "READY").toUpperCase();
        if (questionStatus) questionStatus.textContent = "Response generated";

    } catch (error) {
        console.error("Analysis error:", error);
        removeTypingIndicator(typingId);
        appendErrorMessage(error.message || "An unexpected error occurred.", questionText);
        if (analysisIntent) analysisIntent.textContent = "ERROR";
        if (questionStatus) questionStatus.textContent = "Error occurred";
    } finally {
        isAnalyzing = false;
        if (askButton) {
            askButton.disabled = false;
            askButton.textContent = "Send";
        }
    }
}

// Attach Event Listeners
document.addEventListener("DOMContentLoaded", function () {
    const sumBtn = document.getElementById("summarizeDocumentButton");
    if (sumBtn) {
        sumBtn.addEventListener("click", function () {
            askQuestion("Summarize this legal document.");
        });
    }

    const riskBtn = document.getElementById("riskAnalysisButton");
    if (riskBtn) {
        riskBtn.addEventListener("click", function () {
            askQuestion("Analyze this document for potential risks and clauses requiring review.");
        });
    }

    const clauseBtn = document.getElementById("clauseExtractionButton");
    if (clauseBtn) {
        clauseBtn.addEventListener("click", function () {
            askQuestion("Extract important legal clauses from this document.");
        });
    }

    const clearBtn = document.getElementById("clearChatButton");
    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            if (chatMessagesContainer) {
                const welcomeCard = document.getElementById("chatWelcomeCard");
                chatMessagesContainer.innerHTML = "";
                if (welcomeCard) chatMessagesContainer.appendChild(welcomeCard);
            }
            if (questionStatus) questionStatus.textContent = "Ready";
            if (analysisIntent) analysisIntent.textContent = "READY";
        });
    }

    // Suggested Prompts
    document.querySelectorAll(".suggestion-button, .chip-button").forEach(function (button) {
        button.addEventListener("click", function () {
            const q = button.dataset.question;
            if (q) askQuestion(q);
        });
    });

    // Auto-expanding textarea & keyboard shortcuts
    if (questionInput) {
        questionInput.addEventListener("input", function () {
            this.style.height = "auto";
            this.style.height = Math.min(this.scrollHeight, 120) + "px";
        });

        questionInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                askQuestion();
            }
        });
    }

    if (askButton) {
        askButton.addEventListener("click", function () {
            askQuestion();
        });
    }
});

function formatFileSize(bytes) {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

loadAnalysisDocumentList();