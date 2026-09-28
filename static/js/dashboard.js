// ==========================================
// LexiGuard Dashboard
// ==========================================


// ==========================================
// DOM Elements
// ==========================================

const uploadButton =
    document.getElementById("uploadButton");

const documentInput =
    document.getElementById("documentInput");

function getDocumentsContainer() {
    return document.getElementById("documentsContainer") ||
           document.getElementById("recentDocumentsContainer");
}

const documentCount =
    document.getElementById("documentCount");

const refreshDocuments =
    document.getElementById("refreshDocuments");

const analysisToolCards =
    document.querySelectorAll(
        ".tool-card"
    );


// ==========================================
// Selected Document
// ==========================================

let selectedDocument = null;


// ==========================================
// Analysis Tool Cards
// ==========================================

analysisToolCards.forEach(
    function (card) {

        card.addEventListener(
            "click",
            function (event) {

                const analysisType =
                    card.dataset.analysisType;

                if (!analysisType) {
                    return;
                }

                event.preventDefault();

                handleAnalysisTool(
                    analysisType
                );
            }
        );
    }
);


// ==========================================
// Upload Button
// ==========================================

if (uploadButton && documentInput) {

    uploadButton.addEventListener(
        "click",
        function () {
            documentInput.click();
        }
    );
}


// ==========================================
// File Selection
// ==========================================

if (documentInput) {

    documentInput.addEventListener(
        "change",
        async function () {

            const file =
                documentInput.files[0];

            if (!file) {
                return;
            }

            if (
                !file.name
                    .toLowerCase()
                    .endsWith(".pdf")
            ) {

                alert(
                    "Please select a PDF file."
                );

                documentInput.value = "";

                return;
            }

            await uploadDocument(file);

            documentInput.value = "";
        }
    );
}


// ==========================================
// Upload Document
// ==========================================

async function uploadDocument(file) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    if (uploadButton) {

        uploadButton.disabled = true;

        uploadButton.textContent =
            "Uploading...";
    }

    try {

        const response =
            await fetch(
                "/api/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to upload document."
            );
        }

        if (window.LexiGuard && window.LexiGuard.showToast) {
            window.LexiGuard.showToast("Document uploaded successfully.", "success");
        } else {
            alert("Document uploaded successfully.");
        }

        await loadDocuments();

    } catch (error) {

        console.error(
            "Upload error:",
            error
        );

        alert(
            error.message
        );

    } finally {

        if (uploadButton) {

            uploadButton.disabled = false;

            uploadButton.textContent =
                "Upload Document";
        }
    }
}


// ==========================================
// Load Documents
// ==========================================

let lexiguardDocsCachePromise = null;

async function loadDocuments(forceRefresh) {

    const container = getDocumentsContainer();

    if (forceRefresh) {
        lexiguardDocsCachePromise = null;
    }

    try {

        if (container) {

            container.innerHTML = `
                <div class="empty-state">

                    <div class="empty-icon">
                        ◫
                    </div>

                    <h4>
                        Loading documents...
                    </h4>

                    <p>
                        Fetching your stored documents.
                    </p>

                </div>
            `;
        }

        if (!lexiguardDocsCachePromise) {
            lexiguardDocsCachePromise = (async function () {
                const response = await fetch("/api/documents");
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || "Unable to load documents.");
                }
                const rawDocuments = result.documents || [];
                return rawDocuments.filter(function (doc) {
                    return doc && doc.document_id && !String(doc.document_id).startsWith("USER#");
                });
            })();
        }

        const documents = await lexiguardDocsCachePromise;

        if (documentCount) {

            documentCount.textContent =
                documents.length;
        }

        const currentContainer = getDocumentsContainer();
        if (currentContainer) {

            renderDocuments(
                documents
            );
        }

        if (documents.length > 0 && !selectedDocument) {
            selectedDocument = {
                documentId: documents[0].document_id,
                documentName: documents[0].filename
            };
            updateSelectedDocument();
        }

        populateDocumentDropdowns(
            documents
        );
        attachAskAnalysisButtonListener();

    } catch (error) {

        lexiguardDocsCachePromise = null;

        console.error(
            "Document loading error:",
            error
        );

        if (documentCount) {

            documentCount.textContent =
                "—";
        }

        const errContainer = getDocumentsContainer();
        if (errContainer) {

            errContainer.innerHTML = `
                <div class="empty-state">

                    <div class="empty-icon">
                        !
                    </div>

                    <h4>
                        Unable to load documents
                    </h4>

                    <p>
                        Please refresh and try again.
                    </p>

                </div>
            `;
        }
    }
}


// ==========================================
// Load User Statistics
// ==========================================

async function loadUserStats() {
    try {
        const response = await fetch("/api/user/stats");
        if (!response.ok) return;
        const stats = await response.json();

        const documentCountEl = document.getElementById("documentCount");
        const analysisCountEl = document.getElementById("analysisCount");
        const comparisonCountEl = document.getElementById("comparisonCount");
        const chatCountEl = document.getElementById("chatCount");

        if (documentCountEl && stats.total_documents !== undefined) {
            documentCountEl.textContent = stats.total_documents;
        }
        if (analysisCountEl && stats.total_analyses !== undefined) {
            analysisCountEl.textContent = stats.total_analyses;
        }
        if (comparisonCountEl && stats.total_comparisons !== undefined) {
            comparisonCountEl.textContent = stats.total_comparisons;
        }
        if (chatCountEl && stats.total_chats !== undefined) {
            chatCountEl.textContent = stats.total_chats;
        }
    } catch (error) {
        console.error("User stats loading error:", error);
    }
}


// ==========================================
// Render Documents
// ==========================================

function renderDocuments(documents) {

    const container = getDocumentsContainer();
    if (!container) {
        return;
    }

    const rawFiltered = (documents || []).filter(function (doc) {
        return doc &&
               doc.document_id &&
               !String(doc.document_id).startsWith("USER#");
    });

    const validDocuments =
        (window.LexiGuard &&
         window.LexiGuard.formatDocumentDisplayLabels)
            ? window.LexiGuard.formatDocumentDisplayLabels(rawFiltered)
            : rawFiltered;

    if (validDocuments.length === 0) {

        container.innerHTML = `
            <div class="recent-documents-empty">
                <div class="recent-empty-icon">▤</div>
                <h4>No documents uploaded</h4>
                <p>Upload a PDF to begin analyzing legal documents.</p>
                <a href="/documents" class="recent-empty-button">
                    Upload Document
                </a>
            </div>
        `;

        return;
    }

    const isDashboard = !!document.getElementById("recentDocumentsContainer");
    const docsToRender = isDashboard ? validDocuments.slice(0, 5) : validDocuments;

    container.innerHTML = docsToRender
        .map(function (documentItem) {

            const documentId =
                escapeHtml(documentItem.document_id);

            const filename =
                escapeHtml(
                    documentItem.display_filename ||
                    documentItem.filename ||
                    "Untitled Document"
                );

            const rawFilename =
                escapeHtml(
                    documentItem.filename ||
                    "Untitled Document"
                );

            const pageCount =
                escapeHtml(
                    documentItem.page_count ?? "—"
                );

            const fileSize =
                formatFileSize(
                    documentItem.file_size_bytes
                );

            return `
                <div class="recent-document-card"
                     data-document-id="${documentId}">

                    <div class="recent-document-main">

                        <div class="recent-document-icon">
                            <span>PDF</span>
                        </div>

                        <div class="recent-document-details">

                            <div class="recent-document-title"
                                 title="${rawFilename}">
                                ${filename}
                            </div>

                            <div class="recent-document-meta">
                                <span>
                                    ${pageCount} pages
                                </span>

                                <span class="meta-separator">•</span>

                                <span>
                                    ${escapeHtml(fileSize)}
                                </span>
                            </div>

                        </div>

                    </div>

                    <div class="recent-document-actions">

                        <button
                            type="button"
                            class="recent-action-button view-pdf-button"
                            data-document-id="${documentId}"
                            data-document-name="${rawFilename}">
                            <span>↗</span>
                            View PDF
                        </button>

                        <button
                            type="button"
                            class="recent-action-button primary analyze-button"
                            data-document-id="${documentId}"
                            data-document-name="${rawFilename}">
                            <span>✦</span>
                            Analyze
                        </button>

                        <button
                            type="button"
                            class="recent-delete-button delete-document-button"
                            data-document-id="${documentId}"
                            data-document-name="${rawFilename}"
                            aria-label="Delete document">
                            Delete
                        </button>

                    </div>

                </div>
            `;
        })
        .join("");

    attachAnalyzeButtons();
}
// ==========================================
// Attach Analyze & Document Action Buttons
// ==========================================

function attachAnalyzeButtons() {

    const viewPdfButtons =
        document.querySelectorAll(
            ".view-pdf-button"
        );

    viewPdfButtons.forEach(
        function (button) {
            button.addEventListener(
                "click",
                function (event) {
                    event.stopPropagation();
                    const documentId =
                        button.dataset.documentId;
                    window.open(
                        `/documents/${documentId}/view`,
                        "_blank"
                    );
                }
            );
        }
    );

    const analyzeButtons =
        document.querySelectorAll(
            ".analyze-button"
        );

    analyzeButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();

                    const documentId =
                        button.dataset.documentId;

                    if (documentId) {
                        window.location.href = `/analyze?document_id=${encodeURIComponent(documentId)}`;
                    }
                }
            );
        }
    );

    const deleteButtons =
        document.querySelectorAll(
            ".delete-document-button"
        );

    deleteButtons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                (event) => {

                    event.stopPropagation();

                    const documentId =
                        button.dataset.documentId;

                    const documentName =
                        button.dataset.documentName;

                    deleteDocument(
                        documentId,
                        documentName
                    );
                }
            );
        }
    );
}

async function analyzeDocumentRow(button, documentId, documentName) {
    if (isAskingDashboardQuestion) {
        return;
    }

    selectDocument(documentId, documentName);

    const resultContainer = document.getElementById("analysisResult");
    if (!resultContainer) {
        return;
    }

    const questionInput = document.getElementById("analysisQuestion");
    const userPrompt = questionInput ? questionInput.value.trim() : "";
    const promptText = userPrompt || "Summarize this legal document";

    isAskingDashboardQuestion = true;
    button.disabled = true;
    const originalButtonText = button.textContent;
    button.textContent = "Analyzing...";

    resultContainer.innerHTML = `
        <div class="analysis-placeholder">
            <div class="empty-icon">✦</div>
            <h4>Running document analysis...</h4>
            <p>LexiGuard is processing the document and generating analysis.</p>
        </div>
    `;

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                document_id: documentId,
                question: promptText
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to analyze document.");
        }

        renderAnalysisResult(result);
        loadAnalysisHistory(documentId);

    } catch (error) {
        console.error("Analysis error:", error);
        resultContainer.innerHTML = `
            <div class="analysis-error">
                <h4>Analysis failed</h4>
                <p>${escapeHtml(error.message || "Unable to analyze document.")}</p>
            </div>
        `;
    } finally {
        isAskingDashboardQuestion = false;
        button.disabled = false;
        button.textContent = originalButtonText;
    }
}


// ==========================================
// Select Document
// ==========================================
function selectDocument(
    documentId,
    documentName
) {

    selectedDocument = {

        documentId:
            documentId,

        documentName:
            documentName
    };

    showAnalysisPanel();


    loadAnalysisHistory(
        documentId
    );


    loadChatHistory(
        documentId
    );


    const questionInput =
        document.getElementById(
            "analysisQuestion"
        );


    if (questionInput) {

        questionInput.focus();
    }
}


// ==========================================
// Delete Document
// ==========================================
async function deleteDocument(documentId, documentName) {
    /*
     * Delete a document after user confirmation.
     */

    if (!documentId) {
        alert("Document ID is required.");
        return;
    }

    const confirmed = confirm(
        `Are you sure you want to delete "${documentName}"?\n\n` +
        "This will permanently remove the document " +
        "and its analysis and chat history."
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `/api/documents/${encodeURIComponent(documentId)}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error ||
                "Unable to delete the document."
            );
        }

        if (window.LexiGuard && window.LexiGuard.showToast) {
            window.LexiGuard.showToast("Document deleted successfully.", "success");
        } else {
            alert("Document deleted successfully.");
        }

        // Clear the selected document if
        // the deleted document was selected.
        if (
            selectedDocument &&
            selectedDocument.documentId === documentId
        ) {
            selectedDocument = null;

            const analysisPanel =
                document.getElementById(
                    "analysisPanel"
                );

            if (analysisPanel) {
                analysisPanel.innerHTML = "";
                analysisPanel.style.display =
                    "none";
            }
        }

        // Refresh the document list.
        await loadDocuments();

    } catch (error) {

        console.error(
            "Document deletion failed:",
            error
        );

        alert(
            error.message ||
            "Unable to delete the document."
        );
    }
}
// ==========================================
// Handle Analysis Tool
// ==========================================

function handleAnalysisTool(
    analysisType
) {

    if (!selectedDocument) {

        alert(
            "Please select a document first."
        );

        return;
    }


    // Comparison is a separate
    // two-document workflow.

    if (
        analysisType === "comparison"
    ) {

        showComparisonPanel();

        return;
    }


    showAnalysisPanel();


    const questionInput =
        document.getElementById(
            "analysisQuestion"
        );

    const analysisHeading =
        document.getElementById(
            "analysisHeading"
        );

    const analysisLabel =
        document.getElementById(
            "analysisLabel"
        );

    const analysisButton =
        document.getElementById(
            "askAnalysisButton"
        );

    const analysisPlaceholder =
        document.getElementById(
            "analysisPlaceholderText"
        );


    if (!questionInput) {
        return;
    }


    const analysisConfig = {

        qa: {

            label:
                "AI ANALYSIS",

            heading:
                "Ask LexiGuard",

            question:
                "",

            placeholder:
                "Example: What are the payment terms?",

            buttonText:
                "Ask LexiGuard",

            placeholderText:
                "Ask a question about the selected legal document."
        },


        summary: {

            label:
                "DOCUMENT SUMMARY",

            heading:
                "Document Summary",

            question:
                "Summarize this legal document.",

            placeholder:
                "Generate a structured summary of this document.",

            buttonText:
                "Generate Summary",

            placeholderText:
                "Generate a structured summary of the selected legal document."
        },


        risk: {

            label:
                "RISK ANALYSIS",

            heading:
                "Potential Risks",

            question:
                "Analyze this document for potential risks and clauses requiring review.",

            placeholder:
                "Analyze the document for potential risks and clauses requiring review.",

            buttonText:
                "Analyze Risks",

            placeholderText:
                "Identify potential risks and clauses requiring review."
        }
    };


    const config =
        analysisConfig[analysisType] ||
        analysisConfig.qa;


    if (analysisLabel) {

        analysisLabel.textContent =
            config.label;
    }


    if (analysisHeading) {

        analysisHeading.textContent =
            config.heading;
    }


    questionInput.value =
        config.question;


    questionInput.placeholder =
        config.placeholder;


    if (analysisButton) {

        analysisButton.textContent =
            config.buttonText;
    }


    if (analysisPlaceholder) {

        analysisPlaceholder.textContent =
            config.placeholderText;
    }


    questionInput.focus();
}


function attachAskAnalysisButtonListener() {
    const askButton = document.getElementById("askAnalysisButton");
    if (askButton) {
        askButton.removeEventListener("click", askQuestion);
        askButton.addEventListener("click", askQuestion);
    }

    const sumBtn = document.getElementById("summarizeDocumentButton");
    if (sumBtn) {
        sumBtn.removeEventListener("click", summarizeDocument);
        sumBtn.addEventListener("click", summarizeDocument);
    }

    const riskBtn = document.getElementById("riskAnalysisButton");
    if (riskBtn) {
        riskBtn.removeEventListener("click", analyzeRisks);
        riskBtn.addEventListener("click", analyzeRisks);
    }

    const clauseBtn = document.getElementById("clauseExtractionButton");
    if (clauseBtn) {
        clauseBtn.removeEventListener("click", extractClauses);
        clauseBtn.addEventListener("click", extractClauses);
    }

    const questionInput = document.getElementById("analysisQuestion");
    if (questionInput && !questionInput.dataset.enterListenerAttached) {
        questionInput.dataset.enterListenerAttached = "true";
        questionInput.addEventListener("keydown", function(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    }

    const chipButtons = document.querySelectorAll(".chip-button");
    chipButtons.forEach(function(chip) {
        if (!chip.dataset.listenerAttached) {
            chip.dataset.listenerAttached = "true";
            chip.addEventListener("click", function() {
                const question = chip.dataset.question;
                if (questionInput && question) {
                    questionInput.value = question;
                    askQuestion();
                }
            });
        }
    });

    const clearBtn = document.getElementById("clearChatButton");
    if (clearBtn && !clearBtn.dataset.listenerAttached) {
        clearBtn.dataset.listenerAttached = "true";
        clearBtn.addEventListener("click", function() {
            const resultContainer = document.getElementById("analysisResult");
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="empty-response" style="text-align: center; padding: 30px 20px;">
                        <div class="response-symbol" style="font-size: 24px; margin-bottom: 8px; color: var(--navy-700);">✦</div>
                        <h4 style="color: var(--navy-900);">Your AI analysis will appear here</h4>
                        <p style="color: var(--text-muted); font-size: 12px; margin-top: 4px;">Click "Analyze" on a document above and ask a question.</p>
                    </div>
                `;
            }
        });
    }
}

async function executeDocumentAnalysisAction(promptText, buttonId, loadingText) {
    if (isAskingDashboardQuestion) {
        return;
    }

    if (!selectedDocument) {
        alert("Please select a document first.");
        return;
    }

    const resultContainer = document.getElementById("analysisResult");
    const targetButton = document.getElementById(buttonId);

    if (!resultContainer || !targetButton) {
        return;
    }

    isAskingDashboardQuestion = true;
    targetButton.disabled = true;
    const originalButtonText = targetButton.textContent;
    targetButton.textContent = loadingText;

    resultContainer.innerHTML = `
        <div class="typing-indicator" style="margin: 20px 0;">
            <span>✦ LexiGuard is analyzing document...</span>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                document_id: selectedDocument.documentId,
                question: promptText
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to analyze document.");
        }

        renderAnalysisResult(result);

    } catch (error) {
        console.error("Analysis error:", error);
        resultContainer.innerHTML = `
            <div class="analysis-error">
                <h4>Analysis failed</h4>
                <p>${escapeHtml(error.message || "Unable to analyze document.")}</p>
            </div>
        `;
    } finally {
        isAskingDashboardQuestion = false;
        targetButton.disabled = false;
        targetButton.textContent = originalButtonText;
    }
}

function summarizeDocument() {
    executeDocumentAnalysisAction(
        "Summarize this legal document",
        "summarizeDocumentButton",
        "Summarizing..."
    );
}

function analyzeRisks() {
    executeDocumentAnalysisAction(
        "Identify potential risks in this legal document",
        "riskAnalysisButton",
        "Analyzing Risks..."
    );
}

function extractClauses() {
    executeDocumentAnalysisAction(
        "Extract important legal clauses from this document",
        "clauseExtractionButton",
        "Extracting..."
    );
}


// ==========================================
// Show Analysis Panel
// ==========================================

function showAnalysisPanel() {

    let panel =
        document.getElementById(
            "analysisPanel"
        );


    if (panel) {

        panel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        updateSelectedDocument();
        attachAskAnalysisButtonListener();

        return;
    }


    panel =
        document.createElement(
            "section"
        );


    panel.id =
        "analysisPanel";


    panel.className =
        "analysis-panel";


    panel.innerHTML = `
        <div class="section-heading">

            <div>

                <p
                    class="section-label"
                    id="analysisLabel"
                >
                    AI ANALYSIS
                </p>

                <h3 id="analysisHeading">
                    Ask LexiGuard
                </h3>

            </div>

        </div>


        <div class="selected-document">

            <div class="document-icon">
                PDF
            </div>

            <div>

                <strong
                    id="selectedDocumentName"
                >
                    —
                </strong>

                <small>
                    Selected document
                </small>

            </div>

        </div>


        <div class="question-area">

            <label
                for="analysisQuestion"
            >
                Analysis Request
            </label>

            <textarea
                id="analysisQuestion"
                rows="4"
                placeholder="Example: What are the payment terms?"
            ></textarea>

            <button
                type="button"
                class="primary-button"
                id="askAnalysisButton"
            >
                Ask LexiGuard
            </button>

        </div>


        <div
            id="analysisResult"
            class="analysis-result"
        >

            <div class="analysis-placeholder">

                <div class="empty-icon">
                    ✦
                </div>

                <h4>
                    Your AI analysis will appear here
                </h4>

                <p id="analysisPlaceholderText">
                    Ask a question about the selected
                    legal document.
                </p>

            </div>

        </div>
    `;


    const mainContent =
        document.querySelector(
            ".content-body"
        );

    const disclaimer =
        document.querySelector(
            ".disclaimer-bar"
        );


    if (!mainContent) {
        return;
    }


    if (disclaimer) {

        mainContent.insertBefore(
            panel,
            disclaimer
        );

    } else {

        mainContent.appendChild(
            panel
        );
    }


    updateSelectedDocument();
    attachAskAnalysisButtonListener();


    panel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ==========================================
// Update Selected Document
// ==========================================

function updateSelectedDocument() {

    const selectedDocumentName =
        document.getElementById(
            "selectedDocumentName"
        );

    if (
        selectedDocumentName &&
        selectedDocument
    ) {

        selectedDocumentName.textContent =
            selectedDocument.documentName;
    }
}


// ==========================================
// Ask Question
// ==========================================

let isAskingDashboardQuestion = false;

async function askQuestion() {

    if (isAskingDashboardQuestion) {
        return;
    }

    if (!selectedDocument) {

        alert(
            "Please select a document first."
        );

        return;
    }


    const questionInput =
        document.getElementById(
            "analysisQuestion"
        );

    const resultContainer =
        document.getElementById(
            "analysisResult"
        );

    const askButton =
        document.getElementById(
            "askAnalysisButton"
        );


    if (
        !questionInput ||
        !resultContainer ||
        !askButton
    ) {
        return;
    }


    const question =
        questionInput.value.trim();


    if (!question) {

        alert(
            "Please enter a question."
        );

        questionInput.focus();

        return;
    }

    isAskingDashboardQuestion = true;

    askButton.disabled = true;


    const originalButtonText =
        askButton.textContent;


    askButton.textContent =
        "Analyzing...";


    resultContainer.innerHTML = `
        <div class="analysis-placeholder">

            <div class="empty-icon">
                ✦
            </div>

            <h4>
                Analyzing document...
            </h4>

            <p>
                LexiGuard is retrieving relevant
                document content.
            </p>

        </div>
    `;


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        document_id:
                            selectedDocument.documentId,

                        question:
                            question
                    })
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to analyze document."
            );
        }

        console.log("QA response:", result);
        console.log("Answer:", result.response || result.answer);

        renderAnalysisResult(
            result
        );


    } catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        resultContainer.innerHTML = `
            <div class="analysis-error">

                <h4>
                    Analysis failed
                </h4>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Unable to analyze document."
                    )}
                </p>

            </div>
        `;


    } finally {

        isAskingDashboardQuestion = false;

        askButton.disabled = false;

        askButton.textContent =
            originalButtonText;
    }
}


// ==========================================
// Render Analysis Result
// ==========================================

function renderAnalysisResult(
    result
) {

    const resultContainer =
        document.getElementById(
            "analysisResult"
        );


    if (!resultContainer) {
        return;
    }


    const sources =
        result.sources || [];


    let sourcesHtml =
        "";


    if (sources.length > 0) {

        sourcesHtml = `
            <div class="analysis-sources">

                <h4>
                    Sources
                </h4>

                <div class="source-list">

                    ${sources.map(
                        function (source) {

                            const documentLabel =
                                source.document
                                    ? `Document ${escapeHtml(
                                        source.document
                                    )} · `
                                    : "";


                            return `
                                <span
                                    class="source-tag"
                                >

                                    ${documentLabel}

                                    Page
                                    ${escapeHtml(
                                        source.page_number
                                    )}

                                    ·

                                    Chunk
                                    ${escapeHtml(
                                        source.chunk_number
                                    )}

                                </span>
                            `;
                        }
                    ).join("")}

                </div>

            </div>
        `;

    } else {

        sourcesHtml = `
            <div class="analysis-sources">

                <h4>
                    Sources
                </h4>

                <p>
                    No source references returned.
                </p>

            </div>
        `;
    }


    const intent =
        result.intent || "qa";


    const responseHeading =
        getResponseHeading(
            intent
        );


    const reportBtnHtml = (selectedDocument && selectedDocument.documentId)
        ? `<a href="/api/reports/analysis/${selectedDocument.documentId}" target="_blank" class="secondary-button" style="text-decoration: none; padding: 4px 12px; font-size: 12px; font-weight: 600; float: right;">📥 Download PDF Report</a>`
        : "";

    resultContainer.innerHTML = `
        <div class="analysis-answer">

            <div class="answer-header" style="overflow: hidden;">

                <span class="answer-label">
                    ${escapeHtml(
                        responseHeading
                    )}
                </span>

                <span class="intent-tag">
                    ${escapeHtml(
                        intent
                    )}
                </span>

                ${reportBtnHtml}

            </div>


            <div class="answer-content">

                ${formatResponse(
                    result.response || result.answer
                )}

            </div>


            ${sourcesHtml}

        </div>
    `;
}


// ==========================================
// Response Heading
// ==========================================

function getResponseHeading(
    intent
) {

    const headings = {

        qa:
            "LexiGuard Response",

        summary:
            "Document Summary",

        clause:
            "Clause Extraction",

        risk:
            "Potential Risks",

        comparison:
            "Document Comparison"
    };


    return (
        headings[intent] ||
        "LexiGuard Response"
    );
}


// ==========================================
// Format AI Response
// ==========================================

function formatResponse(
    response
) {

    if (!response) {

        return `
            <p>
                No response was returned.
            </p>
        `;
    }


    if (
        typeof response !== "string"
    ) {

        return `
            <p>
                ${escapeHtml(
                    JSON.stringify(
                        response,
                        null,
                        2
                    )
                )}
            </p>
        `;
    }


    return response
        .split("\n")
        .map(
            function (line) {

                const trimmedLine =
                    line.trim();


                if (!trimmedLine) {
                    return "";
                }


                return `
                    <p>
                        ${escapeHtml(
                            trimmedLine
                        )}
                    </p>
                `;
            }
        )
        .join("");
}


// ==========================================
// Show Comparison Panel
// ==========================================

async function showComparisonPanel() {

    let panel =
        document.getElementById(
            "comparisonPanel"
        );


    if (panel) {

        await loadComparisonDocuments();

        panel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        return;
    }


    panel =
        document.createElement(
            "section"
        );


    panel.id =
        "comparisonPanel";


    panel.className =
        "analysis-panel";


    panel.innerHTML = `
        <div class="section-heading">

            <div>

                <p class="section-label">
                    DOCUMENT COMPARISON
                </p>

                <h3>
                    Compare Legal Documents
                </h3>

            </div>

        </div>


        <div class="comparison-description">

            <p>
                Select two legal documents to compare
                their important contractual terms.
            </p>

        </div>


        <div class="comparison-selection">

            <div class="comparison-field">

                <label
                    for="documentASelect"
                >
                    Document A
                </label>

                <select
                    id="documentASelect"
                >

                    <option value="">
                        Select Document A
                    </option>

                </select>

            </div>


            <div class="comparison-field">

                <label
                    for="documentBSelect"
                >
                    Document B
                </label>

                <select
                    id="documentBSelect"
                >

                    <option value="">
                        Select Document B
                    </option>

                </select>

            </div>

        </div>


        <button
            type="button"
            class="primary-button"
            id="compareDocumentsButton"
        >
            Compare Documents
        </button>


        <div
            id="comparisonResult"
            class="analysis-result"
        >

            <div class="analysis-placeholder">

                <div class="empty-icon">
                    ⇄
                </div>

                <h4>
                    Comparison results will appear here
                </h4>

                <p>
                    Select two documents and compare
                    their contractual terms.
                </p>

            </div>

        </div>
    `;


    const mainContent =
        document.querySelector(
            ".content-body"
        );


    const disclaimer =
        document.querySelector(
            ".disclaimer-bar"
        );


    if (!mainContent) {
        return;
    }


    if (disclaimer) {

        mainContent.insertBefore(
            panel,
            disclaimer
        );

    } else {

        mainContent.appendChild(
            panel
        );
    }


    await loadComparisonDocuments();


    const compareButton =
        document.getElementById(
            "compareDocumentsButton"
        );


    if (compareButton) {

        compareButton.addEventListener(
            "click",
            compareDocuments
        );
    }


    panel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ==========================================
// Load Comparison Documents
// ==========================================

async function loadComparisonDocuments() {

    const documentASelect =
        document.getElementById(
            "documentASelect"
        );


    const documentBSelect =
        document.getElementById(
            "documentBSelect"
        );


    if (
        !documentASelect ||
        !documentBSelect
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/documents"
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to load documents."
            );
        }


        const documents =
            result.documents || [];


        // Clear old options
        // before adding current documents.

        documentASelect.innerHTML = `
            <option value="">
                Select Document A
            </option>
        `;


        documentBSelect.innerHTML = `
            <option value="">
                Select Document B
            </option>
        `;


        documents.forEach(
            function (documentItem) {

                const optionA =
                    document.createElement(
                        "option"
                    );


                optionA.value =
                    documentItem.document_id;


                optionA.textContent =
                    documentItem.filename;


                documentASelect.appendChild(
                    optionA
                );


                const optionB =
                    document.createElement(
                        "option"
                    );


                optionB.value =
                    documentItem.document_id;


                optionB.textContent =
                    documentItem.filename;


                documentBSelect.appendChild(
                    optionB
                );
            }
        );


    } catch (error) {

        console.error(
            "Comparison document loading error:",
            error
        );


        alert(
            "Unable to load documents for comparison."
        );
    }
}


// ==========================================
// Compare Documents
// ==========================================

async function compareDocuments() {

    const documentASelect =
        document.getElementById(
            "documentASelect"
        );


    const documentBSelect =
        document.getElementById(
            "documentBSelect"
        );


    const resultContainer =
        document.getElementById(
            "comparisonResult"
        );


    const compareButton =
        document.getElementById(
            "compareDocumentsButton"
        );


    if (
        !documentASelect ||
        !documentBSelect ||
        !resultContainer ||
        !compareButton
    ) {
        return;
    }


    const documentAId =
        documentASelect.value;


    const documentBId =
        documentBSelect.value;


    if (!documentAId) {

        alert(
            "Please select Document A."
        );

        return;
    }


    if (!documentBId) {

        alert(
            "Please select Document B."
        );

        return;
    }


    if (
        documentAId === documentBId
    ) {

        alert(
            "Document A and Document B must be different."
        );

        return;
    }


    compareButton.disabled = true;


    compareButton.textContent =
        "Comparing...";


    resultContainer.innerHTML = `
        <div class="analysis-placeholder">

            <div class="empty-icon">
                ⇄
            </div>

            <h4>
                Comparing documents...
            </h4>

            <p>
                LexiGuard is analyzing the contractual
                differences between both documents.
            </p>

        </div>
    `;


    try {

        const response =
            await fetch(
                "/api/compare",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        document_a_id:
                            documentAId,

                        document_b_id:
                            documentBId
                    })
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to compare documents."
            );
        }


        // IMPORTANT:
        // The backend now returns a structured
        // JSON comparison object.
        //
        // Therefore we use the dedicated
        // comparison renderer.

        renderComparisonResult(
            result
        );


    } catch (error) {

        console.error(
            "Comparison error:",
            error
        );


        resultContainer.innerHTML = `
            <div class="analysis-error">

                <h4>
                    Comparison failed
                </h4>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Unable to compare documents."
                    )}
                </p>

            </div>
        `;


    } finally {

        compareButton.disabled = false;


        compareButton.textContent =
            "Compare Documents";
    }
}


// ==========================================
// Render Comparison Result
// ==========================================

function renderComparisonResult(
    result
) {

    const comparisonResult =
        document.getElementById(
            "comparisonResult"
        );


    if (!comparisonResult) {
        return;
    }


    const comparisonData =
        result.response;


    // Validate the structured
    // comparison response.

    if (
        !comparisonData ||
        typeof comparisonData !== "object" ||
        !Array.isArray(
            comparisonData.comparison
        )
    ) {

        comparisonResult.innerHTML = `
            <div class="analysis-error">

                <h4>
                    Unable to display comparison
                </h4>

                <p>
                    The comparison response
                    has an unexpected format.
                </p>

            </div>
        `;

        return;
    }


    let html = `

        <div class="comparison-results">

            <div class="comparison-header">

                <div>

                    <span class="result-label">
                        DOCUMENT COMPARISON
                    </span>

                    <h3>
                        Comparison Analysis
                    </h3>

                    <p>
                        The following sections show
                        the information identified in
                        each document and the differences
                        between them.
                    </p>

                </div>

            </div>


            <div class="comparison-grid">
    `;


    comparisonData.comparison.forEach(
        function (item) {

            // Make sure item is an object.

            if (
                !item ||
                typeof item !== "object"
            ) {
                return;
            }


            html += `

                <div class="comparison-card">

                    <div class="comparison-card-header">

                        <h4>
                            ${escapeHtml(
                                item.category ||
                                "Comparison"
                            )}
                        </h4>

                    </div>


                    <div class="comparison-card-body">


                        <div class="comparison-column">

                            <span class="comparison-label">
                                DOCUMENT A
                            </span>

                            <p>
                                ${escapeHtml(
                                    item.document_a ||
                                    "Not found in the document."
                                )}
                            </p>

                        </div>


                        <div class="comparison-column">

                            <span class="comparison-label">
                                DOCUMENT B
                            </span>

                            <p>
                                ${escapeHtml(
                                    item.document_b ||
                                    "Not found in the document."
                                )}
                            </p>

                        </div>


                        <div class="comparison-difference">

                            <span class="comparison-label">
                                DIFFERENCE
                            </span>

                            <p>
                                ${escapeHtml(
                                    item.difference ||
                                    "No material difference identified."
                                )}
                            </p>

                        </div>


                        <div class="comparison-source">

                            <span class="comparison-label">
                                SOURCE
                            </span>

                            <p>
                                ${escapeHtml(
                                    item.source ||
                                    "Source reference not available."
                                )}
                            </p>

                        </div>


                    </div>

                </div>
            `;
        }
    );


    html += `

            </div>
    `;


    // Overall differences

    if (
        comparisonData.overall_differences
    ) {

        html += `

            <div class="comparison-overall">

                <span class="comparison-label">
                    OVERALL DIFFERENCES
                </span>

                <p>
                    ${escapeHtml(
                        comparisonData.overall_differences
                    )}
                </p>

            </div>
        `;
    }


    // Disclaimer

    html += `

            <div class="comparison-disclaimer">

                <strong>
                    Disclaimer:
                </strong>

                ${escapeHtml(
                    comparisonData.disclaimer ||
                    "LexiGuard provides AI-assisted document analysis and is not a substitute for professional legal advice."
                )}

            </div>

        </div>
    `;


    comparisonResult.innerHTML =
        html;
}

// ==========================================
// Analysis History
// ==========================================

const historyContainer =
    document.getElementById(
        "historyContainer"
    );

const refreshHistory =
    document.getElementById(
        "refreshHistory"
    );


async function loadAnalysisHistory(
    documentId
) {

    if (
        !historyContainer ||
        !documentId
    ) {
        return;
    }


    historyContainer.innerHTML = `
        <div class="empty-state">

            <div class="empty-icon">
                ◷
            </div>

            <h4>
                Loading analysis history...
            </h4>

            <p>
                Fetching previous AI analyses.
            </p>

        </div>
    `;


    try {

        const response =
            await fetch(
                `/api/documents/${encodeURIComponent(
                    documentId
                )}/history`
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to load analysis history."
            );
        }


        renderAnalysisHistory(
            result
        );


    } catch (error) {

        console.error(
            "Analysis history error:",
            error
        );


        historyContainer.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    !
                </div>

                <h4>
                    Unable to load history
                </h4>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Unable to retrieve analysis history."
                    )}
                </p>

            </div>
        `;
    }
}


function getAnalysisTypeBadge(typeStr) {
    const type = (typeStr || "analysis").toString().toLowerCase().trim();

    if (type.includes("summary") || type.includes("overview")) {
        return `<span class="history-type-badge badge-type-summary"><span class="badge-icon">📋</span> SUMMARY</span>`;
    }
    if (type.includes("qa") || type.includes("question") || type.includes("chat")) {
        return `<span class="history-type-badge badge-type-qna"><span class="badge-icon">💬</span> Q&A</span>`;
    }
    if (type.includes("risk")) {
        return `<span class="history-type-badge badge-type-risk"><span class="badge-icon">⚠️</span> RISK ASSESSMENT</span>`;
    }
    if (type.includes("clause")) {
        return `<span class="history-type-badge badge-type-clause"><span class="badge-icon">📜</span> CLAUSE EXTRACTION</span>`;
    }
    if (type.includes("compare") || type.includes("comparison")) {
        return `<span class="history-type-badge badge-type-compare"><span class="badge-icon">⚖️</span> COMPARISON</span>`;
    }

    const displayLabel = escapeHtml(type.toUpperCase());
    return `<span class="history-type-badge badge-type-default"><span class="badge-icon">🔍</span> ${displayLabel}</span>`;
}

function formatHistoryTimestamp(timestamp) {
    if (!timestamp) {
        return "Date unavailable";
    }

    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return timestamp;
    }

    const day = date.getDate();
    const month = date.toLocaleString("en-US", { month: "short" });
    const year = date.getFullYear();
    const time = date.toLocaleString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });

    return `${day} ${month} ${year} · ${time}`;
}

function renderAnalysisHistory(result) {
    if (!historyContainer) {
        return;
    }

    const history = result.history || [];

    if (history.length === 0) {
        historyContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">◷</div>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text-main);">No analysis history</h4>
                <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Previous AI analyses for this document will appear here.</p>
            </div>
        `;
        return;
    }

    // Determine document name fallback
    let defaultDocName = result.filename || "";
    if (!defaultDocName && typeof historyDocSelect !== "undefined" && historyDocSelect && historyDocSelect.selectedIndex >= 0) {
        const selectedOpt = historyDocSelect.options[historyDocSelect.selectedIndex];
        if (selectedOpt && selectedOpt.value) {
            defaultDocName = selectedOpt.text;
        }
    }

    const historyItems = [...history].reverse();

    historyContainer.innerHTML = historyItems.map(function (entry) {
        const analysisType = entry.analysis_type || "analysis";
        const question = entry.question || "Document Analysis Request";
        const response = entry.response || "No response available.";
        const timestamp = formatHistoryTimestamp(entry.timestamp);
        const itemDocName = entry.filename || defaultDocName || "Selected Document";
        const sources = entry.sources || [];

        const typeBadgeHtml = getAnalysisTypeBadge(analysisType);

        const sourcesHtml = sources.length > 0
            ? `
                <div class="history-card-section">
                    <div class="history-section-label">SOURCES & CITATIONS</div>
                    <div class="history-sources-list">
                        ${sources.map(function (source) {
                            return `
                                <span class="source-badge">
                                    <span class="source-badge-icon">📌</span>
                                    Page ${escapeHtml(source.page_number || '1')} · Chunk ${escapeHtml(source.chunk_number || '1')}
                                </span>
                            `;
                        }).join("")}
                    </div>
                </div>
            `
            : "";

        return `
            <article class="history-card">
                <!-- 1. ANALYSIS TYPE + DATE -->
                <div class="history-card-header">
                    <div class="history-card-meta-left">
                        ${typeBadgeHtml}
                    </div>
                    <div class="history-card-timestamp">
                        <span>🕒</span> ${escapeHtml(timestamp)}
                    </div>
                </div>

                <!-- 2. QUESTION -->
                <div class="history-card-section">
                    <div class="history-section-label">QUESTION / REQUEST</div>
                    <div class="history-question-box">
                        <div class="history-question-text">${escapeHtml(question)}</div>
                    </div>
                </div>

                <!-- 3. DOCUMENT -->
                <div class="history-card-section">
                    <div class="history-section-label">DOCUMENT</div>
                    <div class="history-document-info">
                        <span>📄</span> ${escapeHtml(itemDocName)}
                    </div>
                </div>

                <!-- 4. AI RESPONSE -->
                <div class="history-card-section">
                    <div class="history-section-label">AI ANALYSIS RESPONSE</div>
                    <div class="history-response-box">
                        ${formatResponse(response)}
                    </div>
                </div>

                <!-- 5. SOURCES -->
                ${sourcesHtml}
            </article>
        `;
    }).join("");
}


if (refreshHistory) {

    refreshHistory.addEventListener(
        "click",
        function () {

            if (!selectedDocument) {

                alert(
                    "Please select a document first."
                );

                return;
            }


            loadAnalysisHistory(
                selectedDocument.documentId
            );
        }
    );
}
// ==========================================
// Chat History
// ==========================================

const chatHistoryContainer =
    document.getElementById(
        "chatHistoryContainer"
    );

const refreshChatHistory =
    document.getElementById(
        "refreshChatHistory"
    );


async function loadChatHistory(
    documentId
) {

    if (
        !chatHistoryContainer ||
        !documentId
    ) {
        return;
    }


    chatHistoryContainer.innerHTML = `
        <div class="empty-state">

            <div class="empty-icon">
                ◷
            </div>

            <h4>
                Loading chat history...
            </h4>

            <p>
                Fetching previous conversations.
            </p>

        </div>
    `;


    try {

        const response =
            await fetch(
                `/api/documents/${encodeURIComponent(
                    documentId
                )}/chat-history`
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                "Unable to load chat history."
            );
        }


        renderChatHistory(
            result
        );


    } catch (error) {

        console.error(
            "Chat history error:",
            error
        );


        chatHistoryContainer.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    !
                </div>

                <h4>
                    Unable to load chat history
                </h4>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Unable to retrieve chat history."
                    )}
                </p>

            </div>
        `;
    }
}


function renderChatHistory(
    result
) {

    if (!chatHistoryContainer) {
        return;
    }


    const history =
        result.chat_history || [];


    if (history.length === 0) {

        chatHistoryContainer.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    ◷
                </div>

                <h4>
                    No chat history
                </h4>

                <p>
                    Previous conversations for
                    this document will appear here.
                </p>

            </div>
        `;

        return;
    }


    const historyItems =
        [...history].reverse();


    chatHistoryContainer.innerHTML =
        historyItems.map(
            function (entry) {

                const userMessage =
                    entry.user_message ||
                    "User message unavailable.";


                const assistantResponse =
                    entry.assistant_response ||
                    "Response unavailable.";


                const timestamp =
                    formatHistoryTimestamp(
                        entry.timestamp
                    );


                const sources =
                    entry.sources || [];


                const sourcesHtml =
                    sources.length > 0
                        ? `
                            <div
                                class="analysis-sources"
                            >

                                <h4>
                                    Sources
                                </h4>

                                <div
                                    class="source-list"
                                >

                                    ${sources.map(
                                        function (
                                            source
                                        ) {

                                            return `
                                                <span
                                                    class="source-tag"
                                                >
                                                    Page
                                                    ${escapeHtml(
                                                        source.page_number
                                                    )}
                                                    ·
                                                    Chunk
                                                    ${escapeHtml(
                                                        source.chunk_number
                                                    )}
                                                </span>
                                            `;
                                        }
                                    ).join("")}

                                </div>

                            </div>
                        `
                        : "";


                return `
                    <article
                        class="history-card"
                    >

                        <div
                            class="history-card-header"
                        >

                            <div>

                                <span
                                    class="history-type"
                                >
                                    You
                                </span>

                                <h4>
                                    ${escapeHtml(
                                        userMessage
                                    )}
                                </h4>

                            </div>

                            <span
                                class="history-date"
                            >
                                ${escapeHtml(
                                    timestamp
                                )}
                            </span>

                        </div>


                        <div
                            class="history-response"
                        >

                            <strong>
                                LexiGuard
                            </strong>

                            ${formatResponse(
                                assistantResponse
                            )}

                        </div>


                        ${sourcesHtml}

                    </article>
                `;
            }
        ).join("");
}


if (refreshChatHistory) {

    refreshChatHistory.addEventListener(
        "click",
        function () {

            if (!selectedDocument) {

                alert(
                    "Please select a document first."
                );

                return;
            }


            loadChatHistory(
                selectedDocument.documentId
            );
        }
    );
}
// ==========================================
// Format File Size
// ==========================================

function formatFileSize(
    bytes
) {

    if (
        bytes === null ||
        bytes === undefined ||
        isNaN(bytes)
    ) {

        return "—";
    }


    if (
        bytes < 1024
    ) {

        return `${bytes} B`;
    }


    if (
        bytes <
        1024 * 1024
    ) {

        return `${(
            bytes / 1024
        ).toFixed(1)} KB`;
    }


    return `${(
        bytes /
        (1024 * 1024)
    ).toFixed(1)} MB`;
}


// ==========================================
// Basic HTML Escaping
// ==========================================

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value ?? "";


    return div.innerHTML;
}


// ==========================================
// Refresh Documents
// ==========================================

if (refreshDocuments) {

    refreshDocuments.addEventListener(
        "click",
        loadDocuments
    );
}


// ==========================================
// Initial Dashboard Load
// ==========================================

function initPage() {
    loadDocuments();
    loadUserStats();
    attachAskAnalysisButtonListener();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPage);
} else {
    initPage();
}


// ==========================================
// Populate Document Dropdowns across Pages
// ==========================================
function populateDocumentDropdowns(documents) {
    const compareA = document.getElementById("compareDocASelect");
    const compareB = document.getElementById("compareDocBSelect");
    const historySelect = document.getElementById("historyDocSelect");
    const chatSelect = document.getElementById("chatDocSelect");
    const analysisSelect = document.getElementById("analysisDocSelect");
    const comparisonDocSelect = document.getElementById("comparisonDocSelect");

    const rawFiltered = (documents || []).filter(function (doc) {
        return doc && doc.document_id && !String(doc.document_id).startsWith("USER#");
    });

    const validDocuments = (window.LexiGuard && window.LexiGuard.formatDocumentDisplayLabels)
        ? window.LexiGuard.formatDocumentDisplayLabels(rawFiltered)
        : rawFiltered;

    [compareA, compareB, historySelect, chatSelect, analysisSelect, comparisonDocSelect].forEach(function (selectEl) {
        if (selectEl) {
            const currentVal = selectEl.value;
            let placeholderText = "Select document...";
            if (selectEl.id === "compareDocASelect") placeholderText = "Select Document A...";
            if (selectEl.id === "compareDocBSelect") placeholderText = "Select Document B...";
            if (selectEl.id === "historyDocSelect") placeholderText = "Select a document to load history...";
            if (selectEl.id === "chatDocSelect") placeholderText = "Select a document to load chat history...";
            if (selectEl.id === "analysisDocSelect") placeholderText = "Select a document to analyze...";
            if (selectEl.id === "comparisonDocSelect") placeholderText = "All Documents";

            let html = `<option value="">${placeholderText}</option>`;
            validDocuments.forEach(function (doc) {
                const labelText = doc.display_filename || doc.filename;
                html += `<option value="${escapeHtml(doc.document_id)}" title="${escapeHtml(doc.filename)}" aria-label="${escapeHtml(doc.filename)}">${escapeHtml(labelText)}</option>`;
            });
            selectEl.innerHTML = html;

            // Retain valid current value or auto-select first available document for instant first-load responsiveness
            if (currentVal && Array.from(selectEl.options).some(function (opt) { return opt.value === currentVal; })) {
                selectEl.value = currentVal;
            } else if (validDocuments.length > 0) {
                if (selectEl.id === "compareDocASelect") {
                    selectEl.value = validDocuments[0].document_id;
                } else if (selectEl.id === "compareDocBSelect" && validDocuments.length > 1) {
                    selectEl.value = validDocuments[1].document_id;
                } else if (selectEl.id === "historyDocSelect") {
                    selectEl.value = validDocuments[0].document_id;
                    if (typeof loadAnalysisHistory === "function") {
                        loadAnalysisHistory(validDocuments[0].document_id);
                    }
                } else if (selectEl.id === "chatDocSelect") {
                    selectEl.value = validDocuments[0].document_id;
                    if (typeof loadChatHistory === "function") {
                        loadChatHistory(validDocuments[0].document_id);
                    }
                } else if (selectEl.id === "analysisDocSelect") {
                    selectEl.value = validDocuments[0].document_id;
                }
            }
        }
    });
}

// ==========================================
// Comparison History Handlers
// ==========================================

const comparisonHistoryContainer = document.getElementById("comparisonHistoryContainer");
const refreshComparisonHistory = document.getElementById("refreshComparisonHistory");
const comparisonDocSelectEl = document.getElementById("comparisonDocSelect");

async function loadComparisonHistory(documentId) {
    if (!comparisonHistoryContainer) {
        return;
    }

    comparisonHistoryContainer.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">⇄</div>
            <h4>Loading comparison history...</h4>
            <p>Fetching previous document comparisons.</p>
        </div>
    `;

    try {
        let url = "/api/comparison-history";
        if (documentId) {
            url = `/api/documents/${encodeURIComponent(documentId)}/comparison-history`;
        }

        const response = await fetch(url);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to load comparison history.");
        }

        renderComparisonHistory(result.comparison_history || []);
    } catch (error) {
        console.error("Comparison history error:", error);
        comparisonHistoryContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">!</div>
                <h4>Unable to load comparison history</h4>
                <p>${escapeHtml(error.message || "Unable to retrieve comparison history.")}</p>
            </div>
        `;
    }
}

function renderComparisonHistory(history) {
    if (!comparisonHistoryContainer) return;

    if (!history || history.length === 0) {
        comparisonHistoryContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚖️</div>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text-main);">No comparison history yet</h4>
                <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Your completed document comparisons will appear here.</p>
            </div>
        `;
        return;
    }

    const historyItems = [...history].reverse();

    let html = "";
    historyItems.forEach(function (entry) {
        const timestamp = formatHistoryTimestamp(entry.timestamp);
        const docAName = (entry.document_a && entry.document_a.filename) || "Document A";
        const docBName = (entry.document_b && entry.document_b.filename) || "Document B";

        let responseData = entry.response;
        if (typeof responseData === "string") {
            try { responseData = JSON.parse(responseData); } catch (e) {}
        }

        const items = (responseData && Array.isArray(responseData.comparison)) ? responseData.comparison : [];
        const compId = entry.comparison_id;

        const downloadBtnHtml = compId
            ? `<a href="/api/reports/comparison/${escapeHtml(compId)}" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none; padding: 5px 12px; font-size: 11.5px; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">📥 Download PDF Report</a>`
            : "";

        html += `
            <article class="comparison-history-card">
                <!-- 1. COMPARISON HEADER -->
                <div class="comparison-history-header">
                    <div class="comparison-header-left">
                        <span class="comparison-header-badge">⚖️ DOCUMENT COMPARISON</span>
                        <div class="comparison-docs-title">
                            <span class="doc-pill" title="${escapeHtml(docAName)}">📄 ${escapeHtml(docAName)}</span>
                            <span class="doc-vs-label">VS</span>
                            <span class="doc-pill" title="${escapeHtml(docBName)}">📄 ${escapeHtml(docBName)}</span>
                        </div>
                    </div>
                    <div class="comparison-header-right">
                        ${downloadBtnHtml}
                        <div class="comparison-date-text">
                            <span>🕒</span> ${escapeHtml(timestamp)}
                        </div>
                    </div>
                </div>
        `;

        if (items.length > 0) {
            html += `
                <!-- 2. 4-COLUMN COMPARISON MATRIX TABLE -->
                <div class="comparison-table-wrapper">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th class="col-category">CATEGORY / CLAUSE</th>
                                <th class="col-doc-a" title="${escapeHtml(docAName)}">${escapeHtml(docAName)}</th>
                                <th class="col-doc-b" title="${escapeHtml(docBName)}">${escapeHtml(docBName)}</th>
                                <th class="col-difference">KEY DIFFERENCE</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            items.forEach(function (item) {
                const category = item.category || item.clause || "Clause / Section";
                const valA = item.document_a || "Not specified";
                const valB = item.document_b || "Not specified";
                const diff = item.difference || "No material difference identified.";

                html += `
                    <tr>
                        <td class="category-name">${escapeHtml(category)}</td>
                        <td>${escapeHtml(valA)}</td>
                        <td>${escapeHtml(valB)}</td>
                        <td class="difference-cell">${escapeHtml(diff)}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html += `
                <div style="padding: 16px; background: var(--bg-subtle); border-radius: var(--radius-sm); font-size: 13px; color: var(--text-muted); font-style: italic;">
                    Detailed comparison matrix items not available for this record.
                </div>
            `;
        }

        html += `</article>`;
    });

    comparisonHistoryContainer.innerHTML = html;
}

if (refreshComparisonHistory) {
    refreshComparisonHistory.addEventListener("click", function () {
        const docId = comparisonDocSelectEl ? comparisonDocSelectEl.value : null;
        loadComparisonHistory(docId);
    });
}

if (comparisonDocSelectEl) {
    comparisonDocSelectEl.addEventListener("change", function () {
        const docId = comparisonDocSelectEl.value;
        loadComparisonHistory(docId);
    });
}

if (comparisonHistoryContainer) {
    loadComparisonHistory();
}

// ==========================================
// Comparison Page Handler & Validation
// ==========================================
function validateComparisonSelection() {
    const docASelect = document.getElementById("compareDocASelect");
    const docBSelect = document.getElementById("compareDocBSelect");
    const startBtn = document.getElementById("startCompareBtn");
    const errContainer = document.getElementById("compareValidationError");

    if (!docASelect || !docBSelect) return true;

    const valA = docASelect.value;
    const valB = docBSelect.value;

    if (valA && valB && valA === valB) {
        if (errContainer) {
            errContainer.style.display = "flex";
        }
        if (startBtn) {
            startBtn.disabled = true;
        }
        return false;
    } else {
        if (errContainer) {
            errContainer.style.display = "none";
        }
        if (startBtn) {
            startBtn.disabled = false;
        }
        return true;
    }
}

const docASelectEl = document.getElementById("compareDocASelect");
const docBSelectEl = document.getElementById("compareDocBSelect");
if (docASelectEl) docASelectEl.addEventListener("change", validateComparisonSelection);
if (docBSelectEl) docBSelectEl.addEventListener("change", validateComparisonSelection);

const startCompareBtn = document.getElementById("startCompareBtn");
if (startCompareBtn) {
    startCompareBtn.addEventListener("click", async function () {
        const docASelect = document.getElementById("compareDocASelect");
        const docBSelect = document.getElementById("compareDocBSelect");
        const docAId = docASelect ? docASelect.value : "";
        const docBId = docBSelect ? docBSelect.value : "";

        if (!docAId || !docBId) {
            if (window.LexiGuard && window.LexiGuard.showToast) {
                window.LexiGuard.showToast("Please select both Document A and Document B to compare.", "error");
            } else {
                alert("Please select both Document A and Document B to compare.");
            }
            return;
        }

        if (!validateComparisonSelection()) {
            if (window.LexiGuard && window.LexiGuard.showToast) {
                window.LexiGuard.showToast("Please select two different documents to compare.", "error");
            }
            return;
        }

        const resultsSection = document.getElementById("comparisonResultsSection");
        const resultsContainer = document.getElementById("comparisonResultsContainer");

        if (resultsSection && resultsContainer) {
            resultsSection.style.display = "block";
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon" style="color: var(--accent-blue);">✦</div>
                    <h4 id="compareStatusHeader" style="font-size: 15px; font-weight: 700; color: var(--text-main);">Comparing documents with AI...</h4>
                    <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Please wait while LexiGuard analyzes terms, obligations, and clause differences.</p>
                </div>
            `;
        }

        let compareTracker = null;
        const compareStatusHeader = document.getElementById("compareStatusHeader");
        if (compareStatusHeader && window.LexiGuard && window.LexiGuard.createProgressTracker) {
            compareTracker = window.LexiGuard.createProgressTracker(compareStatusHeader, [
                "Preparing Document A and Document B...",
                "Extracting clause comparison matrices...",
                "Evaluating obligation & liability diffs...",
                "Generating side-by-side comparison report..."
            ], 1500);
        }

        startCompareBtn.disabled = true;
        startCompareBtn.textContent = "Comparing...";

        try {
            const response = await fetch("/api/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ document_a_id: docAId, document_b_id: docBId })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Unable to compare documents.");
            }

            if (compareTracker) {
                compareTracker.complete("Comparison complete");
            }

            renderComparisonResults(data);
            if (window.LexiGuard && window.LexiGuard.showToast) {
                window.LexiGuard.showToast("Comparison analysis complete.", "success");
            }
        } catch (err) {
            if (compareTracker) {
                compareTracker.error(err.message || "Unable to compare documents.");
            }
            if (window.LexiGuard && window.LexiGuard.showToast) {
                window.LexiGuard.showToast(err.message || "Unable to compare documents.", "error");
            }
            if (resultsContainer) {
                resultsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <div>
                            <strong>Comparison Failed</strong>
                            <p style="font-size: 13px; margin-top: 4px;">${escapeHtml(err.message)}</p>
                        </div>
                    </div>
                `;
            }
        } finally {
            startCompareBtn.disabled = false;
            startCompareBtn.textContent = "Compare Agreements";
        }
    });
}

function renderComparisonResults(data) {
    const container = document.getElementById("comparisonResultsContainer");
    if (!container) return;

    let responseData = data.response;
    if (typeof responseData === "string") {
        let cleaned = responseData.trim();
        if (cleaned.startsWith("```")) {
            const lines = cleaned.split("\n");
            cleaned = lines.slice(1, -1).join("\n");
        }
        try {
            responseData = JSON.parse(cleaned);
        } catch (e) {
            // fallback
        }
    }

    const items = (responseData && responseData.comparison) ? responseData.comparison : [];
    const docAName = (data.document_a && data.document_a.filename) || "Document A";
    const docBName = (data.document_b && data.document_b.filename) || "Document B";
    const compId = data.comparison_id;

    let downloadHtml = "";
    if (compId) {
        downloadHtml = `
            <a href="/api/reports/comparison/${compId}" target="_blank" class="btn btn-outline btn-sm">
                <span>📥</span> Download Comparison Report (PDF)
            </a>
        `;
    }

    let html = `
        <div class="comparison-results-wrapper">
            <!-- Documents Compared Header Banner -->
            <div class="comparison-header-banner" style="margin-bottom: 24px; padding: 20px; background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md);">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
                    <div>
                        <span class="badge badge-info" style="margin-bottom: 4px;">DOCUMENTS COMPARED</span>
                        <h4 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0;">Side-by-Side Agreement Comparison</h4>
                    </div>
                    ${downloadHtml}
                </div>

                <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: center;">
                    <!-- Document A Header -->
                    <div style="padding: 12px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); display: flex; align-items: center; gap: 12px; min-width: 0;">
                        <div style="width: 32px; height: 36px; background: var(--primary-light); border: 1px solid var(--primary-border); border-radius: 6px; color: var(--primary); font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">PDF</div>
                        <div style="min-width: 0;">
                            <div style="font-size: 10px; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px;">Document A</div>
                            <div style="font-size: 13.5px; font-weight: 650; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(docAName)}">${escapeHtml(docAName)}</div>
                        </div>
                    </div>

                    <!-- VS Badge -->
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--navy-header); color: #FFFFFF; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: var(--shadow-sm);">
                        VS
                    </div>

                    <!-- Document B Header -->
                    <div style="padding: 12px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); display: flex; align-items: center; gap: 12px; min-width: 0;">
                        <div style="width: 32px; height: 36px; background: var(--bg-subtle); border: 1px solid var(--border-dark); border-radius: 6px; color: var(--text-secondary); font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">PDF</div>
                        <div style="min-width: 0;">
                            <div style="font-size: 10px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">Document B</div>
                            <div style="font-size: 13.5px; font-weight: 650; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(docBName)}">${escapeHtml(docBName)}</div>
                        </div>
                    </div>
                </div>
            </div>
    `;

    if (!items || items.length === 0) {
        html += `
            <div class="empty-state" style="padding: 30px; text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);">
                <div style="font-size: 32px; color: var(--text-muted); margin-bottom: 8px;">⇄</div>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text-primary);">No clause differences detected</h4>
                <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">The comparison returned no distinct clause variations between the selected documents.</p>
            </div>
        `;
    } else {
        html += `
            <div class="comparison-table-wrapper" style="overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface); box-shadow: var(--shadow-sm);">
                <table class="comparison-table" style="width: 100%; min-width: 800px; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="background: var(--navy-header); color: #FFFFFF;">
                            <th style="padding: 14px 16px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; width: 18%; border-right: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; background: var(--navy-header); z-index: 2;">
                                Category / Clause
                            </th>
                            <th style="padding: 14px 16px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; width: 30%; border-right: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; background: var(--navy-header); z-index: 2;" title="${escapeHtml(docAName)}">
                                <div style="font-size: 10px; opacity: 0.8; font-weight: 600;">DOCUMENT A</div>
                                <div style="font-size: 12.5px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;">${escapeHtml(docAName)}</div>
                            </th>
                            <th style="padding: 14px 16px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; width: 30%; border-right: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; background: var(--navy-header); z-index: 2;" title="${escapeHtml(docBName)}">
                                <div style="font-size: 10px; opacity: 0.8; font-weight: 600;">DOCUMENT B</div>
                                <div style="font-size: 12.5px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;">${escapeHtml(docBName)}</div>
                            </th>
                            <th style="padding: 14px 16px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; width: 22%; position: sticky; top: 0; background: var(--navy-header); z-index: 2;">
                                Key Difference
                            </th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        items.forEach(function (item, idx) {
            const categoryName = item.category || "General Provision";
            const docAText = item.document_a || "Not specified in Document A.";
            const docBText = item.document_b || "Not specified in Document B.";
            const diffText = item.difference || "No material difference identified.";
            const rowBg = idx % 2 === 0 ? "var(--surface)" : "var(--bg-main)";

            html += `
                <tr style="border-bottom: 1px solid var(--border); background: ${rowBg};">
                    <td style="padding: 16px; font-size: 13px; font-weight: 700; color: var(--text-primary); vertical-align: top; background: var(--bg-subtle); border-right: 1px solid var(--border);">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="color: var(--primary); font-size: 13px;">📋</span>
                            <span>${escapeHtml(categoryName)}</span>
                        </div>
                    </td>
                    <td style="padding: 16px; font-size: 13px; color: var(--text-primary); line-height: 1.55; vertical-align: top; border-right: 1px solid var(--border); white-space: pre-wrap;">
                        ${escapeHtml(docAText)}
                    </td>
                    <td style="padding: 16px; font-size: 13px; color: var(--text-primary); line-height: 1.55; vertical-align: top; border-right: 1px solid var(--border); white-space: pre-wrap;">
                        ${escapeHtml(docBText)}
                    </td>
                    <td style="padding: 16px; font-size: 12.5px; color: var(--text-primary); line-height: 1.5; vertical-align: top; background: var(--primary-light); border-left: 2px solid var(--primary);">
                        <div style="font-size: 10.5px; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                            ✦ Key Difference
                        </div>
                        <div style="font-weight: 500;">
                            ${escapeHtml(diffText)}
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    html += `</div>`;
    container.innerHTML = html;
}

// ==========================================
// History State & Pagination Manager (BUG-01 Fix)
// ==========================================
window.historyState = window.historyState || {
    currentPage: 1,
    type: "all",
    documentId: "",
    filter: "",
    dateRange: ""
};

window.resetHistoryPagination = function () {
    if (window.historyState) {
        window.historyState.currentPage = 1;
    }
};

const historyDocSelect = document.getElementById("historyDocSelect");
if (historyDocSelect) {
    historyDocSelect.addEventListener("change", function () {
        window.resetHistoryPagination();
        const docId = historyDocSelect.value;
        if (docId && typeof loadAnalysisHistory === "function") {
            loadAnalysisHistory(docId);
        }
    });
}

["historyTypeFilter", "historyDateFilter", "historySearchInput", "historyFilterSelect", "docCategoryFilter"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener("change", window.resetHistoryPagination);
        el.addEventListener("input", window.resetHistoryPagination);
    }
});

const chatDocSelect = document.getElementById("chatDocSelect");
if (chatDocSelect) {
    chatDocSelect.addEventListener("change", function () {
        window.resetHistoryPagination();
        const docId = chatDocSelect.value;
        if (docId && typeof loadChatHistory === "function") {
            loadChatHistory(docId);
        }
    });
}