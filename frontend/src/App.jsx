import { useEffect, useRef, useState } from "react";
import {
  Bot,
  BookOpen,
  Brain,
  FileDown,
  FileText,
  GraduationCap,
  HelpCircle,
  Layers,
  Lightbulb,
  ListChecks,
  MessageSquareX,
  Monitor,
  Moon,
  MoreVertical,
  Paperclip,
  Pencil,
  Plus,
  Presentation,
  RefreshCw,
  RotateCcw,
  SearchCheck,
  Send,
  Sparkles,
  Target,
  TerminalSquare,
  Trash2,
  X,
  Copy,
  ExternalLink,
  LockOpen,
  Quote,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import api from "./api/axios";
import ScholarSearchPanel from "./components/ScholarSearchPanel";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

function App() {
  const [themeMode, setThemeMode] = useState(
    localStorage.getItem("scholarmind-theme") || "system"
  );

  const [systemDark, setSystemDark] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );

  const isDark =
    themeMode === "dark" || (themeMode === "system" && systemDark);

  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [file, setFile] = useState(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [answering, setAnswering] = useState(false);
  const [warmingUp, setWarmingUp] = useState(false);

  const [processingSeconds, setProcessingSeconds] = useState(0);
  const [uploadId, setUploadId] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);

  const [documentAnalysis, setDocumentAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showAnalysisPanel, setShowAnalysisPanel] = useState(false);

  const [relatedPapers, setRelatedPapers] = useState([]);
  const [relatedPapersLoading, setRelatedPapersLoading] = useState(false);
  const [showRelatedPanel, setShowRelatedPanel] = useState(false);
  const [relatedSearchQuery, setRelatedSearchQuery] = useState("");

  const [openPaperMenuId, setOpenPaperMenuId] = useState(null);
  const [managementLoading, setManagementLoading] = useState(null);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeSource, setActiveSource] = useState(null);

  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  const documentTools = [
    {
      title: "Document Summary",
      icon: BookOpen,
      prompt:
        "Summarize this document in an academic but easy-to-understand way. If it is a project report, include main project idea, problem, objectives, system overview, implementation approach, testing/result, future scope, and why it matters. If it is a research paper, include main theme, research problem, objective, methodology, key contribution, limitation or future work.",
    },
    {
      title: "Main Theme",
      icon: Brain,
      prompt:
        "What is the main theme of this document? Explain the central idea, key focus, and why this document matters.",
    },
    {
      title: "Objectives",
      icon: Target,
      prompt:
        "Identify and explain the main objectives of this document. If objectives are not directly stated, infer them only from the provided document context and clearly mention that they are inferred.",
    },
    {
      title: "Problem Statement",
      icon: SearchCheck,
      prompt:
        "Explain the problem statement of this document. Include the issue being addressed, why it is important, and what gap or need the work is trying to solve.",
    },
    {
      title: "Methodology / Approach",
      icon: ListChecks,
      prompt:
        "Explain the methodology or approach used in this document step by step. For a research paper, include research design, data/dataset, method/model, and evaluation. For a project report, include workflow, system process, modules, and implementation approach.",
    },
    {
      title: "System Design",
      icon: Layers,
      prompt:
        "Explain the system design or architecture described in this document. Include modules, data flow, database/design components, diagrams if mentioned, and how the system parts work together.",
    },
    {
      title: "Implementation",
      icon: TerminalSquare,
      prompt:
        "Explain the implementation of this document or project. Include technologies used, frontend/backend/database/API details, important modules, and how the system was built.",
    },
    {
      title: "Testing & Results",
      icon: SearchCheck,
      prompt:
        "Explain the testing, evaluation, and results described in this document. Include test cases, validation, performance, findings, or final outputs if available.",
    },
    {
      title: "Research Gap",
      icon: SearchCheck,
      prompt:
        "Identify the research gap or knowledge gap from this document. Explain the existing problem, what previous work or existing systems failed to solve, and what opportunity remains for future work.",
    },
    {
      title: "Limitations",
      icon: Target,
      prompt:
        "Extract and explain the limitations of this document. If limitations are not directly stated, infer only from the provided context and clearly mention that they are inferred.",
    },
    {
      title: "Future Scope",
      icon: Lightbulb,
      prompt:
        "Find and explain the future scope or future work of this document. Present them as clear improvement opportunities or future research/project directions.",
    },
    {
      title: "Thesis Ideas",
      icon: GraduationCap,
      prompt:
        "Suggest strong thesis or research project ideas based on this document. For each idea, include a title, problem, possible method, and expected contribution.",
    },
    {
      title: "Presentation Points",
      icon: Presentation,
      prompt:
        "Generate presentation points from this document. Organize them slide-wise: Title, Introduction, Problem, Objectives, Methodology/Approach, System Design or Experiment, Implementation, Results, Limitations, Future Scope, and Conclusion.",
    },
    {
      title: "Viva Questions",
      icon: HelpCircle,
      prompt:
        "Generate possible viva or defense questions from this document with short answer hints. Include questions about objective, methodology, system design, implementation, testing, limitations, and future scope.",
    },
  ];

  const progressSteps = [
    {
      title: "Saving PDF",
      threshold: 5,
      description: "Saving the uploaded file to the backend.",
    },
    {
      title: "Extracting text",
      threshold: 15,
      description: "Reading PDF pages. OCR may be used for scanned PDFs.",
    },
    {
      title: "Creating chunks",
      threshold: 35,
      description: "Creating page and line-aware chunks.",
    },
    {
      title: "Saving chunks",
      threshold: 45,
      description: "Saving document chunks into the database.",
    },
    {
      title: "Generating embeddings",
      threshold: 55,
      description: "Generating vector embeddings using sentence-transformers.",
    },
    {
      title: "Indexing vectors",
      threshold: 85,
      description: "Saving vectors and sources into ChromaDB.",
    },
    {
      title: "Building intelligence",
      threshold: 88,
      description: "Creating section summaries and document profile.",
    },
    {
      title: "Completed",
      threshold: 100,
      description: "Document is ready.",
    },
  ];

  const realProgressPercent = uploadProgress?.percent || (uploading ? 1 : 0);
  const realProgressStage =
    uploadProgress?.stage || (uploading ? "Starting" : "Waiting");
  const realProgressDetails =
    uploadProgress?.details ||
    (uploading
      ? "Upload started. Waiting for backend progress..."
      : "No active upload.");
  const realProgressStatus = uploadProgress?.status || "idle";

  const selectedAnalysisStatus =
    documentAnalysis?.status ||
    selectedPaper?.analysis_status ||
    "not_created";

  const selectedDocumentType =
    documentAnalysis?.document_type ||
    selectedPaper?.document_type ||
    "Unknown";

  const analysisReady = selectedAnalysisStatus === "ready";
  const sectionSummaryCount = documentAnalysis?.section_summaries
    ? Object.keys(documentAnalysis.section_summaries).length
    : 0;

  const relatedPapersCount =
    relatedPapers.length || selectedPaper?.related_papers_count || 0;

  const pageClass = isDark
    ? "min-h-screen bg-slate-950 text-white"
    : "min-h-screen bg-gradient-to-br from-blue-50 via-white to-emerald-50 text-slate-950";

  const sidebarClass = isDark
    ? "hidden border-r border-slate-800 bg-slate-950 p-6 xl:flex xl:flex-col"
    : "hidden border-r border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/60 xl:flex xl:flex-col";

  const cardClass = isDark
    ? "border border-slate-800 bg-slate-900 shadow-2xl shadow-black/30"
    : "border border-slate-200 bg-white shadow-2xl shadow-slate-200/80";

  const mutedText = isDark ? "text-slate-300" : "text-slate-700";

  const scrollToBottom = () => {
    setTimeout(() => {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 80);
  };

  const changeTheme = (mode) => {
    setThemeMode(mode);
    localStorage.setItem("scholarmind-theme", mode);
  };

  const getErrorMessage = (err, fallbackMessage) => {
    const backendData = err?.response?.data;

    if (backendData?.details) {
      return `${fallbackMessage}: ${backendData.details}`;
    }

    if (backendData?.error) {
      return `${fallbackMessage}: ${backendData.error}`;
    }

    if (err?.message) {
      return `${fallbackMessage}: ${err.message}`;
    }

    return fallbackMessage;
  };

  const createUploadId = () => {
    return (
      window.crypto?.randomUUID?.() ||
      `upload_${Date.now()}_${Math.random().toString(36).slice(2)}`
    );
  };

  const buildWelcomeMessage = (paperTitle) => ({
    role: "assistant",
    content: `Great. I selected "${paperTitle}". I can help you summarize it, explain the objectives, analyze methodology, system design, implementation, testing, limitations, future scope, or viva questions.`,
    sources: [],
  });

  const clearAlerts = () => {
    setError("");
    setNotice("");
  };

  const isManagingPaper = (paperId, action = null) => {
    if (!managementLoading) return false;

    if (action) {
      return (
        managementLoading.paperId === paperId &&
        managementLoading.action === action
      );
    }

    return managementLoading.paperId === paperId;
  };

  const getSourceBadgeClass = (source) => {
    const label = (source?.relevance_label || "").toLowerCase();

    if (label.includes("very strong")) {
      return isDark
        ? "border-emerald-400/30 bg-emerald-500/15 text-emerald-100"
        : "border-emerald-200 bg-emerald-50 text-emerald-700";
    }

    if (label.includes("strong")) {
      return isDark
        ? "border-blue-400/30 bg-blue-500/15 text-blue-100"
        : "border-blue-200 bg-blue-50 text-blue-700";
    }

    if (label.includes("moderate")) {
      return isDark
        ? "border-amber-400/30 bg-amber-500/15 text-amber-100"
        : "border-amber-200 bg-amber-50 text-amber-700";
    }

    if (label.includes("weak") || label.includes("low")) {
      return isDark
        ? "border-red-400/30 bg-red-500/15 text-red-100"
        : "border-red-200 bg-red-50 text-red-700";
    }

    return isDark
      ? "border-slate-600 bg-slate-800 text-slate-200"
      : "border-slate-200 bg-slate-50 text-slate-700";
  };

  const getSourceBadgeText = (source) => {
    if (source?.relevance_label) {
      return source.relevance_label;
    }

    if (source?.used_in_answer === true) {
      return "Used";
    }

    return "Source";
  };

  const formatSourceScore = (source) => {
    if (
      source?.relevance_score === undefined ||
      source?.relevance_score === null
    ) {
      return "";
    }

    const score = Number(source.relevance_score);

    if (Number.isNaN(score)) {
      return "";
    }

    return ` • ${(score * 100).toFixed(0)}%`;
  };

  const makeSafeFilename = (title, suffix) => {
    const safeTitle = (title || "document")
      .replace(/[^a-z0-9_-]+/gi, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 80);

    return `${safeTitle || "document"}_${suffix}.docx`;
  };

  const downloadBlob = (blobData, filename) => {
    const blob = new Blob([blobData], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const exportPaperChatDocx = async (paper, event) => {
    event.stopPropagation();

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "export-chat" });

      const res = await api.get(`/papers/${paper.id}/export/chat-docx/`, {
        responseType: "blob",
      });

      downloadBlob(res.data, makeSafeFilename(paper.title, "chat_history"));

      setNotice("Chat history DOCX exported successfully.");
      setOpenPaperMenuId(null);
    } catch (err) {
      setError(getErrorMessage(err, "Chat history export failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const exportPaperAnalysisDocx = async (paper, event) => {
    event.stopPropagation();

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "export-analysis" });

      const res = await api.get(`/papers/${paper.id}/export/analysis-docx/`, {
        responseType: "blob",
      });

      downloadBlob(
        res.data,
        makeSafeFilename(paper.title, "document_intelligence")
      );

      setNotice("Document intelligence DOCX exported successfully.");
      setOpenPaperMenuId(null);
    } catch (err) {
      setError(getErrorMessage(err, "Document intelligence export failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const warmupSystem = async () => {
    try {
      setWarmingUp(true);
      await api.get("/system/warmup/");
    } catch (err) {
      console.log("Warmup failed:", err);
    } finally {
      setWarmingUp(false);
    }
  };

  const fetchPapers = async () => {
    try {
      const res = await api.get("/papers/");
      setPapers(res.data);
    } catch (err) {
      console.log(err);
    }
  };

  const fetchDocumentAnalysis = async (paperId, openPanel = false) => {
    if (!paperId) return null;

    try {
      setAnalysisLoading(true);
      const res = await api.get(`/papers/${paperId}/analysis/`);

      setDocumentAnalysis(res.data);

      if (openPanel) {
        setShowAnalysisPanel(true);
      }

      return res.data;
    } catch (err) {
      console.log("Document analysis fetch failed:", err);

      if (openPanel) {
        setError(
          getErrorMessage(
            err,
            "Could not load document intelligence profile"
          )
        );
      }

      setDocumentAnalysis(null);
      return null;
    } finally {
      setAnalysisLoading(false);
    }
  };

  const formatAuthors = (authors) => {
  if (!authors || !Array.isArray(authors) || authors.length === 0) {
    return "Unknown authors";
  }

  return authors.join(", ");
};

const truncateText = (text, maxLength = 520) => {
  if (!text) return "";

  const clean = String(text).replace(/\s+/g, " ").trim();

  if (clean.length <= maxLength) return clean;

  return `${clean.slice(0, maxLength).trim()}...`;
};

const copyRelatedPaperDetails = async (paper) => {
  const lines = [
    paper.title || "Untitled paper",
    `Authors: ${formatAuthors(paper.authors)}`,
    `Year: ${paper.year || "Unknown"}`,
    `Venue: ${paper.venue || "Unknown"}`,
    paper.doi ? `DOI: ${paper.doi}` : "",
    paper.url ? `URL: ${paper.url}` : "",
    paper.why_related ? `Why related: ${paper.why_related}` : "",
    paper.abstract ? `Abstract: ${paper.abstract}` : "",
  ].filter(Boolean);

  try {
    await navigator.clipboard.writeText(lines.join("\n"));
    setNotice("Related paper details copied.");
  } catch {
    setError("Could not copy related paper details.");
  }
};

const fetchRelatedPapers = async (paperId, openPanel = false) => {
  if (!paperId) return null;

  try {
    setRelatedPapersLoading(true);

    const res = await api.get(`/papers/${paperId}/related-papers/`);

    const results = res.data?.results || [];

    setRelatedPapers(results);

    if (results.length > 0) {
      setRelatedSearchQuery(results[0]?.search_query || "");
    } else {
      setRelatedSearchQuery("");
    }

    if (openPanel) {
      setShowRelatedPanel(true);
    }

    return results;
  } catch (err) {
    console.log("Related literature fetch failed:", err);

    if (openPanel) {
      setError(getErrorMessage(err, "Could not load related literature"));
    }

    setRelatedPapers([]);
    setRelatedSearchQuery("");

    return null;
  } finally {
    setRelatedPapersLoading(false);
  }
};

const generateRelatedPapers = async (paper = selectedPaper, event = null) => {
  event?.stopPropagation?.();

  if (!paper) {
    setError("Select or upload a document first.");
    return;
  }

  const confirmed = window.confirm(
    `Generate related published literature for "${paper.title}"?\n\nThis will search global academic sources and save the recommendations.`
  );

  if (!confirmed) return;

  try {
    clearAlerts();
    setRelatedPapersLoading(true);
    setManagementLoading({ paperId: paper.id, action: "related-literature" });

    const res = await api.post(`/papers/${paper.id}/related-papers/generate/`, {
      limit: 10,
      from_year: 2018,
      to_year: new Date().getFullYear(),
      open_access_only: false,
    });

    const results = res.data?.results || [];

    setRelatedPapers(results);
    setRelatedSearchQuery(res.data?.search_query || "");
    setShowRelatedPanel(true);

    if (selectedPaper?.id === paper.id) {
      const detailRes = await api.get(`/papers/${paper.id}/`);
      setSelectedPaper(detailRes.data);
    }

    setNotice("Related literature generated successfully.");
    setOpenPaperMenuId(null);

    await fetchPapers();
  } catch (err) {
    setError(getErrorMessage(err, "Related literature generation failed"));
  } finally {
    setRelatedPapersLoading(false);
    setManagementLoading(null);
  }
};

const clearRelatedPapers = async (paper = selectedPaper, event = null) => {
  event?.stopPropagation?.();

  if (!paper) {
    setError("Select or upload a document first.");
    return;
  }

  const confirmed = window.confirm(
    `Clear saved related literature for "${paper.title}"?`
  );

  if (!confirmed) return;

  try {
    clearAlerts();
    setRelatedPapersLoading(true);
    setManagementLoading({ paperId: paper.id, action: "clear-related" });

    await api.delete(`/papers/${paper.id}/related-papers/clear/`);

    setRelatedPapers([]);
    setRelatedSearchQuery("");
    setShowRelatedPanel(false);

    if (selectedPaper?.id === paper.id) {
      const detailRes = await api.get(`/papers/${paper.id}/`);
      setSelectedPaper(detailRes.data);
    }

    setNotice("Related literature cleared successfully.");
    setOpenPaperMenuId(null);

    await fetchPapers();
  } catch (err) {
    setError(getErrorMessage(err, "Clear related literature failed"));
  } finally {
    setRelatedPapersLoading(false);
    setManagementLoading(null);
  }
};

const openRelatedLiteraturePanel = async () => {
  if (!selectedPaper) {
    setError("Select or upload a document first.");
    return;
  }

  if (relatedPapers.length > 0) {
    setShowRelatedPanel(true);
    return;
  }

  const existing = await fetchRelatedPapers(selectedPaper.id, true);

  if (!existing || existing.length === 0) {
    const confirmed = window.confirm(
      "No saved related literature found for this document. Generate recommendations now?"
    );

    if (confirmed) {
      await generateRelatedPapers(selectedPaper);
    }
  }
};

  const fetchChatHistory = async (paperId, paperTitle) => {
    try {
      const res = await api.get(`/papers/${paperId}/chat-history/`);

      const historyMessages = (res.data || []).map((item) => ({
        role: item.role,
        content: item.message,
        sources: item.sources || [],
      }));

      if (historyMessages.length > 0) {
        setMessages(historyMessages);
      } else {
        setMessages([buildWelcomeMessage(paperTitle)]);
      }
    } catch (err) {
      console.log("Chat history fetch failed:", err);
      setMessages([buildWelcomeMessage(paperTitle)]);
    }
  };

  const selectPaper = async (paper) => {
    try {
      clearAlerts();
      setOpenPaperMenuId(null);

      const res = await api.get(`/papers/${paper.id}/`);

      setSelectedPaper(res.data);
      setFile(null);
      setUploadId(null);
      setUploadProgress(null);
      setDocumentAnalysis(null);
      setShowAnalysisPanel(false);
      setRelatedPapers([]);
      setRelatedSearchQuery("");
      setShowRelatedPanel(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setActiveSource(null);

      await fetchChatHistory(res.data.id, res.data.title);

      if (res.data.analysis_status === "ready") {
        fetchDocumentAnalysis(res.data.id, false);
      }

      if (res.data.related_papers_count > 0) {
        fetchRelatedPapers(res.data.id, false);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Could not select this document"));
      console.log(err);
    }
  };

  const renamePaper = async (paper, event) => {
    event.stopPropagation();

    const currentTitle = paper.title || "";
    const newTitle = window.prompt("Enter new document title:", currentTitle);

    if (!newTitle) {
      setOpenPaperMenuId(null);
      return;
    }

    const cleanTitle = newTitle.trim();

    if (!cleanTitle) {
      setOpenPaperMenuId(null);
      setError("Document title cannot be empty.");
      return;
    }

    if (cleanTitle === currentTitle) {
      setOpenPaperMenuId(null);
      return;
    }

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "rename" });

      const res = await api.patch(`/papers/${paper.id}/rename/`, {
        title: cleanTitle,
      });

      const updatedPaper = res.data.paper;

      setPapers((prev) =>
        prev.map((item) => (item.id === paper.id ? updatedPaper : item))
      );

      if (selectedPaper?.id === paper.id) {
        setSelectedPaper(updatedPaper);
      }

      setNotice("Document renamed successfully.");
      setOpenPaperMenuId(null);
      await fetchPapers();
    } catch (err) {
      setError(getErrorMessage(err, "Rename failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const clearPaperChatHistory = async (paper, event) => {
    event.stopPropagation();

    const confirmed = window.confirm(
      `Clear all chat history for "${paper.title}"? This cannot be undone.`
    );

    if (!confirmed) {
      setOpenPaperMenuId(null);
      return;
    }

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "clear-chat" });

      await api.post(`/papers/${paper.id}/clear-chat/`);

      if (selectedPaper?.id === paper.id) {
        setMessages([buildWelcomeMessage(paper.title)]);
        setActiveSource(null);
      }

      setNotice("Chat history cleared successfully.");
      setOpenPaperMenuId(null);
      await fetchPapers();
    } catch (err) {
      setError(getErrorMessage(err, "Clear chat history failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const reprocessPaperAnalysis = async (paper, event) => {
    event.stopPropagation();

    const confirmed = window.confirm(
      `Rebuild document intelligence for "${paper.title}"? This may take some time.`
    );

    if (!confirmed) {
      setOpenPaperMenuId(null);
      return;
    }

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "reprocess" });

      const res = await api.post(`/papers/${paper.id}/reprocess-analysis/`);

      if (selectedPaper?.id === paper.id) {
        setDocumentAnalysis(res.data.analysis || null);
        setShowAnalysisPanel(Boolean(res.data.analysis));

        const detailRes = await api.get(`/papers/${paper.id}/`);
        setSelectedPaper(detailRes.data);
      }

      setNotice("Document intelligence rebuilt successfully.");
      setOpenPaperMenuId(null);
      await fetchPapers();
    } catch (err) {
      setError(getErrorMessage(err, "Rebuild intelligence failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const deletePaper = async (paper, event) => {
    event.stopPropagation();

    const confirmed = window.confirm(
      `Delete "${paper.title}" permanently?\n\nThis will remove the PDF, chunks, vectors, analysis, and chat history.`
    );

    if (!confirmed) {
      setOpenPaperMenuId(null);
      return;
    }

    try {
      clearAlerts();
      setManagementLoading({ paperId: paper.id, action: "delete" });

      await api.delete(`/papers/${paper.id}/delete/`);

      setPapers((prev) => prev.filter((item) => item.id !== paper.id));

      if (selectedPaper?.id === paper.id) {
        setSelectedPaper(null);
        setFile(null);
        setQuestion("");
        setMessages([]);
        setActiveSource(null);
        setUploadId(null);
        setUploadProgress(null);
        setProcessingSeconds(0);
        setDocumentAnalysis(null);
        setShowAnalysisPanel(false);
        setRelatedPapers([]);
        setRelatedSearchQuery("");
        setShowRelatedPanel(false);

        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }

      setNotice("Document deleted successfully.");
      setOpenPaperMenuId(null);
      await fetchPapers();
    } catch (err) {
      setError(getErrorMessage(err, "Delete failed"));
    } finally {
      setManagementLoading(null);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];

    if (!selectedFile) return;

    const isPdf = selectedFile.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setFile(null);
      setSelectedPaper(null);
      setError("Only PDF files are allowed.");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      return;
    }

    console.log("Selected PDF:", {
      name: selectedFile.name,
      size: selectedFile.size,
      type: selectedFile.type,
    });

    setFile(selectedFile);
    setSelectedPaper(null);
    setUploadId(null);
    setUploadProgress(null);
    setDocumentAnalysis(null);
    setShowAnalysisPanel(false);
    setRelatedPapers([]);
    setRelatedSearchQuery("");
    setShowRelatedPanel(false);
    setError("");
    setNotice("");
    setActiveSource(null);
    setOpenPaperMenuId(null);

    setMessages([
      {
        role: "assistant",
        content: `"${selectedFile.name}" is attached. Now write your question and press send. I will upload, index, and deeply analyze the document first.`,
        sources: [],
      },
    ]);
  };

  const removeAttachedFile = () => {
    setFile(null);
    setUploadId(null);
    setUploadProgress(null);
    setDocumentAnalysis(null);
    setShowAnalysisPanel(false);
    setRelatedPapers([]);
    setRelatedSearchQuery("");
    setShowRelatedPanel(false);
    setError("");
    setNotice("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadPaper = async () => {
    if (!file) {
      setError("Attach a PDF first.");
      return null;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed.");
      return null;
    }

    const newUploadId = createUploadId();

    const formData = new FormData();
    formData.append("title", file.name.replace(/\.pdf$/i, ""));
    formData.append("file", file);
    formData.append("upload_id", newUploadId);

    try {
      setUploading(true);
      setProcessingSeconds(0);
      setUploadId(newUploadId);
      setUploadProgress({
        upload_id: newUploadId,
        status: "processing",
        stage: "Starting",
        percent: 1,
        details: "Upload started. Sending PDF to backend...",
      });

      setError("");
      setNotice("");
      setActiveSource(null);
      setDocumentAnalysis(null);
      setShowAnalysisPanel(false);
      setRelatedPapers([]);
      setRelatedSearchQuery("");
      setShowRelatedPanel(false);

      console.log("Uploading PDF to backend:", {
        name: file.name,
        size: file.size,
        type: file.type,
        upload_id: newUploadId,
      });

      setMessages([
        {
          role: "assistant",
          content:
            "I am preparing your document now. I will extract text, create chunks, build embeddings, and generate a document intelligence profile.",
          sources: [],
        },
      ]);

      const res = await api.post("/papers/upload/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (!res.data?.paper) {
        throw new Error("Backend did not return document data.");
      }

      const uploadedPaper = res.data.paper;

      setUploadProgress((prev) => ({
        ...(prev || {}),
        upload_id: newUploadId,
        status: "completed",
        stage: "Completed",
        percent: 100,
        details:
          "Document is indexed and document intelligence profile is ready.",
      }));

      setSelectedPaper(uploadedPaper);
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await fetchPapers();
      await fetchDocumentAnalysis(uploadedPaper.id, false);
      setMessages([
        {
          role: "assistant",
          content: `"${uploadedPaper.title}" is ready. You can now ask questions, view the intelligence profile, or click “Generate Related Literature” to discover related published studies in a separate research panel.`,
          sources: [],
        },
      ]);

      setNotice("Document uploaded and analyzed successfully.");

      return uploadedPaper;
    } catch (err) {
      console.log("Upload failed:", err);

      setUploadProgress((prev) => ({
        ...(prev || {}),
        upload_id: newUploadId,
        status: "failed",
        stage: "Failed",
        percent: 100,
        details:
          err?.response?.data?.details ||
          err?.response?.data?.error ||
          err?.message ||
          "Upload or processing failed.",
      }));

      setError(
        getErrorMessage(
          err,
          "Upload failed. The file reached the frontend, but backend processing failed"
        )
      );

      setMessages([
        {
          role: "assistant",
          content:
            "Upload failed. Please check the backend terminal error. The PDF may be scanned, corrupted, or backend/Groq/OCR processing may have failed.",
          sources: [],
        },
      ]);

      return null;
    } finally {
      setUploading(false);
    }
  };

  const askQuestion = async (e, suggestedQuestion = null) => {
    e?.preventDefault();

    setError("");
    setNotice("");
    setActiveSource(null);

    const finalQuestion = suggestedQuestion || question.trim();

    if (!finalQuestion) {
      setError("Write a question first.");
      return;
    }

    let paper = selectedPaper;

    if (!paper && file) {
      const uploadedPaper = await uploadPaper();

      if (!uploadedPaper) return;

      paper = uploadedPaper;
    }

    if (!paper && !file) {
      setError("Attach a PDF or select a recent document first.");
      return;
    }

    if (!paper) {
      setError("Document is not ready yet. Please upload or select a document first.");
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: finalQuestion,
        sources: [],
      },
      {
        role: "assistant",
        content: "",
        sources: [],
        typing: true,
      },
    ]);

    setQuestion("");
    setError("");
    setActiveSource(null);
    setAnswering(true);
    scrollToBottom();

    try {
      const response = await fetch(
        `${API_BASE_URL}/papers/${paper.id}/chat-stream/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: finalQuestion,
          }),
        }
      );

      if (!response.ok || !response.body) {
        throw new Error("Streaming request failed.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";

      const updateAssistantMessage = (updater) => {
        setMessages((prev) => {
          const copy = [...prev];
          const lastIndex = copy.length - 1;
          copy[lastIndex] = updater(copy[lastIndex]);
          return copy;
        });
      };

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop();

        for (const event of events) {
          const dataLine = event
            .split("\n")
            .find((line) => line.startsWith("data: "));

          if (!dataLine) continue;

          const data = JSON.parse(dataLine.replace("data: ", ""));

          if (data.type === "sources") {
            updateAssistantMessage((msg) => ({
              ...msg,
              sources: data.sources || [],
            }));
          }

          if (data.type === "token") {
            updateAssistantMessage((msg) => ({
              ...msg,
              content: msg.content + data.token,
            }));

            scrollToBottom();
          }

          if (data.type === "error") {
            setError(data.message || "Streaming failed.");
          }

          if (data.type === "done") {
            updateAssistantMessage((msg) => ({
              ...msg,
              typing: false,
            }));
          }
        }
      }

      updateAssistantMessage((msg) => ({
        ...msg,
        typing: false,
      }));

      await fetchPapers();
    } catch (err) {
      console.log("Answer streaming failed:", err);
      setError(getErrorMessage(err, "Answer streaming failed"));
    } finally {
      setAnswering(false);
      scrollToBottom();
    }
  };

  const runDocumentTool = (tool) => {
    if (!selectedPaper && !file) {
      setQuestion(tool.prompt);
      setError("Attach a PDF or select a recent document first, then run this tool.");
      return;
    }

    askQuestion(null, tool.prompt);
  };

  const openSource = (source, index) => {
    setActiveSource({
      ...source,
      label: source.source_id || `Source ${index + 1}`,
      number: index + 1,
    });
  };

  const openAnalysisPanel = async () => {
    if (!selectedPaper) {
      setError("Select or upload a document first.");
      return;
    }

    if (!documentAnalysis) {
      await fetchDocumentAnalysis(selectedPaper.id, true);
      return;
    }

    setShowAnalysisPanel(true);
  };

  const resetChat = () => {
    setSelectedPaper(null);
    setFile(null);
    setQuestion("");
    setMessages([]);
    setError("");
    setNotice("");
    setActiveSource(null);
    setUploadId(null);
    setUploadProgress(null);
    setProcessingSeconds(0);
    setDocumentAnalysis(null);
    setShowAnalysisPanel(false);
    setRelatedPapers([]);
    setRelatedSearchQuery("");
    setShowRelatedPanel(false);
    setOpenPaperMenuId(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const MarkdownMessage = ({ content, role }) => {
    return (
      <div
        className={`max-w-none ${
          role === "user"
            ? "text-white"
            : isDark
            ? "text-slate-100"
            : "text-slate-900"
        }`}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="mb-3 mt-2 text-2xl font-black leading-tight">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="mb-3 mt-2 text-xl font-black leading-tight">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="mb-2 mt-2 text-lg font-black leading-tight">
                {children}
              </h3>
            ),
            p: ({ children }) => (
              <p className="mb-3 leading-7 last:mb-0">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="mb-3 ml-5 list-disc space-y-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-3 ml-5 list-decimal space-y-1">{children}</ol>
            ),
            li: ({ children }) => <li className="leading-7">{children}</li>,
            strong: ({ children }) => (
              <strong className="font-black">{children}</strong>
            ),
            em: ({ children }) => <em className="italic">{children}</em>,
            blockquote: ({ children }) => (
              <blockquote
                className={`my-3 border-l-4 pl-4 ${
                  isDark
                    ? "border-blue-400 text-slate-200"
                    : "border-blue-500 text-slate-700"
                }`}
              >
                {children}
              </blockquote>
            ),
            code: ({ children }) => (
              <code
                className={`rounded-md px-1.5 py-0.5 text-sm ${
                  isDark
                    ? "bg-slate-950 text-emerald-200"
                    : "bg-slate-200 text-slate-900"
                }`}
              >
                {children}
              </code>
            ),
          }}
        >
          {content || ""}
        </ReactMarkdown>
      </div>
    );
  };

  useEffect(() => {
    warmupSystem();
    fetchPapers();

    const media = window.matchMedia("(prefers-color-scheme: dark)");

    const listener = (event) => {
      setSystemDark(event.matches);
    };

    media.addEventListener("change", listener);

    return () => {
      media.removeEventListener("change", listener);
    };
  }, []);

  useEffect(() => {
    if (!uploading) {
      setProcessingSeconds(0);
      return;
    }

    const secondTimer = setInterval(() => {
      setProcessingSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      clearInterval(secondTimer);
    };
  }, [uploading]);

  useEffect(() => {
    if (!uploading || !uploadId) {
      return;
    }

    let stopped = false;

    const fetchProgress = async () => {
      try {
        const res = await api.get(`/upload-progress/${uploadId}/`);

        if (!stopped) {
          setUploadProgress(res.data);
        }
      } catch (err) {
        console.log("Progress polling failed:", err);
      }
    };

    fetchProgress();

    const timer = setInterval(fetchProgress, 1000);

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [uploading, uploadId]);

  return (
    <div
      className={pageClass}
      onClick={() => {
        if (openPaperMenuId) {
          setOpenPaperMenuId(null);
        }
      }}
    >
      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[330px_1fr]">
        <aside className={sidebarClass}>
          <div className="mb-8 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-emerald-400 font-black text-white shadow-lg shadow-blue-500/20">
              S
            </div>

            <div>
              <h1 className="text-xl font-black tracking-tight">
                ScholarMind
              </h1>
              <p className={`text-sm ${mutedText}`}>Academic companion</p>
            </div>
          </div>

          <div
            className={`mb-5 rounded-3xl p-4 ${
              isDark
                ? "border border-slate-800 bg-slate-900"
                : "border border-slate-200 bg-slate-50"
            }`}
          >
            <div className="mb-3 flex items-center gap-2">
              <GraduationCap size={18} className="text-blue-500" />
              <span className="text-sm font-black">Document Mode</span>
            </div>
            <p className={`text-sm leading-6 ${mutedText}`}>
              “A document becomes easier when you can question it like a
              supervisor.”
            </p>
          </div>

          <button
            onClick={(event) => {
              event.stopPropagation();
              resetChat();
            }}
            className={`mb-5 flex items-center justify-center gap-2 rounded-2xl px-4 py-3 font-bold transition ${
              isDark
                ? "bg-white text-slate-950 hover:bg-blue-50"
                : "bg-slate-950 text-white hover:bg-slate-800"
            }`}
          >
            <Plus size={18} />
            New document
          </button>

          <div
            className={`mb-6 rounded-3xl p-4 ${
              isDark
                ? "border border-slate-800 bg-slate-900"
                : "border border-slate-200 bg-white"
            }`}
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_18px_#34d399]" />
              <span className="text-sm font-bold">Active document</span>
            </div>

            <p className={`line-clamp-3 text-sm leading-6 ${mutedText}`}>
              {selectedPaper ? selectedPaper.title : "No document selected"}
            </p>

            {selectedPaper && (
              <div className="mt-3 space-y-2">
                <div
                  className={`rounded-2xl border px-3 py-2 text-xs font-bold ${
                    relatedPapersCount > 0
                      ? isDark
                        ? "border-purple-400/30 bg-purple-500/10 text-purple-100"
                        : "border-purple-200 bg-purple-50 text-purple-700"
                      : isDark
                      ? "border-slate-700 bg-slate-900 text-slate-300"
                      : "border-slate-200 bg-slate-50 text-slate-600"
                  }`}
                >
                  Related Literature: {relatedPapersCount}
                </div>

                <div
                  className={`rounded-2xl border px-3 py-2 text-xs font-bold ${
                    analysisReady
                      ? isDark
                        ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100"
                        : "border-emerald-200 bg-emerald-50 text-emerald-700"
                      : isDark
                      ? "border-amber-400/30 bg-amber-500/10 text-amber-100"
                      : "border-amber-200 bg-amber-50 text-amber-700"
                  }`}
                >
                  Intelligence: {selectedAnalysisStatus}
                </div>

                <div
                  className={`rounded-2xl border px-3 py-2 text-xs font-bold ${
                    isDark
                      ? "border-blue-400/20 bg-blue-500/10 text-blue-100"
                      : "border-blue-100 bg-blue-50 text-blue-700"
                  }`}
                >
                  Type: {selectedDocumentType}
                </div>
              </div>
            )}
          </div>

          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">
              Recent Documents
            </h2>

            <button
              onClick={(event) => {
                event.stopPropagation();
                fetchPapers();
              }}
              className={`rounded-lg p-1.5 transition ${
                isDark
                  ? "text-slate-400 hover:bg-slate-800 hover:text-white"
                  : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="space-y-2 overflow-y-auto pr-1">
            {papers.length === 0 ? (
              <p className={`text-sm ${mutedText}`}>No documents yet.</p>
            ) : (
              papers.slice(0, 12).map((paper) => {
                const menuOpen = openPaperMenuId === paper.id;
                const managing = isManagingPaper(paper.id);

                return (
                  <div
                    key={paper.id}
                    onClick={() => {
                      if (!managing) {
                        selectPaper(paper);
                      }
                    }}
                    className={`relative w-full cursor-pointer rounded-2xl border p-3 pr-10 text-left transition ${
                      selectedPaper?.id === paper.id
                        ? "border-blue-400 bg-blue-500/15"
                        : isDark
                        ? "border-slate-800 bg-slate-900 hover:border-slate-700 hover:bg-slate-800"
                        : "border-slate-200 bg-white hover:border-blue-200 hover:bg-blue-50"
                    }`}
                  >
                    <div className="mb-1 flex items-start gap-2">
                      <FileText
                        size={16}
                        className="mt-0.5 shrink-0 text-blue-500"
                      />
                      <span className="line-clamp-2 text-sm font-bold">
                        {paper.title}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      <span className={`text-xs capitalize ${mutedText}`}>
                        {paper.status}
                      </span>

                      {paper.analysis_status && (
                        <span className={`text-xs ${mutedText}`}>
                          • AI: {paper.analysis_status}
                        </span>
                      )}

                      {typeof paper.chat_count === "number" && (
                        <span className={`text-xs ${mutedText}`}>
                          • {paper.chat_count} chats
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      disabled={managing}
                      onClick={(event) => {
                        event.stopPropagation();
                        setOpenPaperMenuId(menuOpen ? null : paper.id);
                      }}
                      className={`absolute right-2 top-2 rounded-xl p-1.5 transition disabled:cursor-not-allowed disabled:opacity-60 ${
                        isDark
                          ? "text-slate-300 hover:bg-slate-700 hover:text-white"
                          : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                      }`}
                      title="More options"
                    >
                      {managing ? (
                        <RefreshCw size={17} className="animate-spin" />
                      ) : (
                        <MoreVertical size={17} />
                      )}
                    </button>

                    {menuOpen && (
                      <div
                        onClick={(event) => event.stopPropagation()}
                        className={`absolute right-2 top-10 z-50 w-56 overflow-hidden rounded-2xl border p-2 shadow-2xl ${
                          isDark
                            ? "border-slate-700 bg-slate-950 shadow-black/50"
                            : "border-slate-200 bg-white shadow-slate-300/60"
                        }`}
                      >
                        <button
                          type="button"
                          onClick={(event) => renamePaper(paper, event)}
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <Pencil size={15} />
                          Rename
                        </button>

                        <button
                          type="button"
                          onClick={(event) =>
                            clearPaperChatHistory(paper, event)
                          }
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <MessageSquareX size={15} />
                          Clear chat
                        </button>

                        <button
                          type="button"
                          onClick={(event) =>
                            reprocessPaperAnalysis(paper, event)
                          }
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <RotateCcw size={15} />
                          Rebuild intelligence
                        </button>
                        <button
                          type="button"
                          onClick={(event) => generateRelatedPapers(paper, event)}
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <BookOpen size={15} />
                          Generate related literature
                        </button>

                        <button
                          type="button"
                          onClick={(event) => clearRelatedPapers(paper, event)}
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <MessageSquareX size={15} />
                          Clear related literature
                        </button>
                        <button
                          type="button"
                          onClick={(event) => exportPaperChatDocx(paper, event)}
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <FileDown size={15} />
                          Export chat DOCX
                        </button>

                        <button
                          type="button"
                          onClick={(event) =>
                            exportPaperAnalysisDocx(paper, event)
                          }
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-slate-100 hover:bg-slate-800"
                              : "text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          <FileDown size={15} />
                          Export intelligence DOCX
                        </button>

                        <div
                          className={`my-1 h-px ${
                            isDark ? "bg-slate-800" : "bg-slate-200"
                          }`}
                        />

                        <button
                          type="button"
                          onClick={(event) => deletePaper(paper, event)}
                          disabled={managing}
                          className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-60 ${
                            isDark
                              ? "text-red-300 hover:bg-red-500/10"
                              : "text-red-600 hover:bg-red-50"
                          }`}
                        >
                          <Trash2 size={15} />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </aside>

        <main className="flex min-h-screen flex-col p-4 md:p-6">
          <header className="mx-auto mb-4 flex w-full max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div
                className={`mb-3 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold ${
                  isDark
                    ? "border-slate-700 bg-slate-900 text-blue-200"
                    : "border-blue-100 bg-blue-50 text-blue-700"
                }`}
              >
                <Sparkles size={14} />
                Universal academic workspace
              </div>

              <h2
                className={`text-3xl font-black tracking-tight md:text-5xl ${
                  isDark ? "text-white" : "text-slate-950"
                }`}
              >
                Discover evidence. Understand papers. Build better research.
              </h2>

              <p
                className={`mt-3 max-w-2xl text-sm leading-6 md:text-base ${
                  isDark ? "text-slate-300" : "text-slate-700"
                }`}
              >
                Upload research papers, thesis chapters, systematic review materials, or academic reports. ScholarMind helps you analyze evidence, extract research gaps, compare methodologies, and discover related published studies with DOI, citations, and open-access links.
              </p>

              <div className="mt-4">
                <ScholarSearchPanel
                  isDark={isDark}
                  selectedPaper={selectedPaper}
              />
            </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => changeTheme("dark")}
                className={`flex items-center gap-2 rounded-2xl border px-4 py-3 font-bold transition ${
                  themeMode === "dark"
                    ? "border-blue-500 bg-blue-600 text-white"
                    : isDark
                    ? "border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <Moon size={17} />
                Dark
              </button>

              <button
                onClick={() => changeTheme("system")}
                className={`flex items-center gap-2 rounded-2xl border px-4 py-3 font-bold transition ${
                  themeMode === "system"
                    ? "border-emerald-500 bg-emerald-500 text-white"
                    : isDark
                    ? "border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <Monitor size={17} />
                System
              </button>

              <button
                onClick={resetChat}
                className={`rounded-2xl border px-4 py-3 font-bold transition xl:hidden ${
                  isDark
                    ? "border-slate-700 bg-slate-900 text-white hover:bg-slate-800"
                    : "border-slate-200 bg-white text-slate-900 hover:bg-slate-50"
                }`}
              >
                New document
              </button>
            </div>
          </header>

          {warmingUp && (
            <div
              className={`mx-auto mb-3 w-full max-w-6xl rounded-2xl border px-4 py-3 text-sm font-bold ${
                isDark
                  ? "border-blue-400/30 bg-blue-500/10 text-blue-200"
                  : "border-blue-200 bg-blue-50 text-blue-700"
              }`}
            >
              ScholarMind is warming up the AI services in the background...
            </div>
          )}

          {notice && !uploading && (
            <div
              className={`mx-auto mb-3 w-full max-w-6xl rounded-2xl border px-4 py-3 text-sm font-bold ${
                isDark
                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-200"
                  : "border-emerald-200 bg-emerald-50 text-emerald-700"
              }`}
            >
              {notice}
            </div>
          )}

          <section
            className={`mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col overflow-hidden rounded-[2rem] ${cardClass}`}
          >
            <div className="flex-1 overflow-y-auto p-4 md:p-7">
              {(selectedPaper || file) && (
                <div
                  className={`mb-5 rounded-3xl border p-4 ${
                    isDark
                      ? "border-slate-700 bg-slate-800/70"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Sparkles size={17} className="text-blue-500" />
                      <h3 className="font-black">Document Tools</h3>
                      <span className={`text-sm ${mutedText}`}>
                        One-click academic and project analysis
                      </span>
                    </div>

                    
                  </div>


                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    {documentTools.map((tool) => {
                      const ToolIcon = tool.icon;

                      return (
                        <button
                          key={tool.title}
                          onClick={() => runDocumentTool(tool)}
                          disabled={uploading || answering}
                          className={`flex items-center gap-2 rounded-2xl border px-3 py-2 text-left text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                            isDark
                              ? "border-slate-700 bg-slate-900 text-white hover:bg-slate-700"
                              : "border-slate-200 bg-white text-slate-900 hover:border-blue-200 hover:bg-blue-50"
                          }`}
                        >
                          <ToolIcon
                            size={16}
                            className="shrink-0 text-emerald-500"
                          />
                          <span className="line-clamp-1">{tool.title}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {showAnalysisPanel && documentAnalysis && (
                <div
                  className={`mb-6 rounded-3xl border p-5 ${
                    isDark
                      ? "border-emerald-400/20 bg-emerald-500/10"
                      : "border-emerald-200 bg-emerald-50"
                  }`}
                >
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-black">
                        Document Intelligence Profile
                      </h3>
                      <p className={`mt-1 text-sm ${mutedText}`}>
                        Type: {documentAnalysis.document_type} • Status:{" "}
                        {documentAnalysis.status}
                      </p>
                    </div>

                    <button
                      onClick={() => setShowAnalysisPanel(false)}
                      className={`rounded-xl p-2 transition ${
                        isDark
                          ? "bg-slate-950/70 text-emerald-100 hover:bg-slate-950"
                          : "bg-white text-emerald-900 hover:bg-emerald-100"
                      }`}
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {documentAnalysis.source_coverage && (
                    <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                      <div
                        className={`rounded-2xl border px-4 py-3 ${
                          isDark
                            ? "border-slate-700 bg-slate-900/70"
                            : "border-emerald-100 bg-white"
                        }`}
                      >
                        <p className={`text-xs font-bold ${mutedText}`}>
                          Total Chunks
                        </p>
                        <p className="mt-1 font-black">
                          {documentAnalysis.source_coverage.total_chunks ||
                            "Unknown"}
                        </p>
                      </div>

                      <div
                        className={`rounded-2xl border px-4 py-3 ${
                          isDark
                            ? "border-slate-700 bg-slate-900/70"
                            : "border-emerald-100 bg-white"
                        }`}
                      >
                        <p className={`text-xs font-bold ${mutedText}`}>
                          Sections Detected
                        </p>
                        <p className="mt-1 font-black">
                          {documentAnalysis.source_coverage
                            .total_sections_detected || "Unknown"}
                        </p>
                      </div>

                      <div
                        className={`rounded-2xl border px-4 py-3 ${
                          isDark
                            ? "border-slate-700 bg-slate-900/70"
                            : "border-emerald-100 bg-white"
                        }`}
                      >
                        <p className={`text-xs font-bold ${mutedText}`}>
                          Sections Analyzed
                        </p>
                        <p className="mt-1 font-black">
                          {sectionSummaryCount}
                        </p>
                      </div>
                    </div>
                  )}

                  <div
                    className={`max-h-72 overflow-y-auto rounded-2xl border p-4 ${
                      isDark
                        ? "border-slate-700 bg-slate-950/80"
                        : "border-emerald-100 bg-white"
                    }`}
                  >
                    <MarkdownMessage
                      content={
                        documentAnalysis.profile ||
                        "No profile text available."
                      }
                      role="assistant"
                    />
                  </div>

                  {documentAnalysis.section_summaries &&
                    sectionSummaryCount > 0 && (
                      <div className="mt-4">
                        <h4 className="mb-3 font-black">
                          Section Summaries
                        </h4>

                        <div className="grid gap-3 md:grid-cols-2">
                          {Object.entries(
                            documentAnalysis.section_summaries
                          ).map(([section, summary]) => (
                            <details
                              key={section}
                              className={`rounded-2xl border p-4 ${
                                isDark
                                  ? "border-slate-700 bg-slate-900/70"
                                  : "border-emerald-100 bg-white"
                              }`}
                            >
                              <summary className="cursor-pointer font-black">
                                {section}
                              </summary>

                              <div className="mt-3 max-h-52 overflow-y-auto text-sm leading-6">
                                <MarkdownMessage
                                  content={summary}
                                  role="assistant"
                                />
                              </div>
                            </details>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              )}

              {uploading && (
                <div
                  className={`mb-6 overflow-hidden rounded-3xl border ${
                    isDark
                      ? "border-blue-400/20 bg-blue-500/10"
                      : "border-blue-200 bg-blue-50"
                  }`}
                >
                  <div className="p-5">
                    <div className="mb-4 flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-500/30">
                          <RefreshCw size={22} className="animate-spin" />
                        </div>

                        <div>
                          <h3
                            className={`text-lg font-black ${
                              isDark ? "text-white" : "text-slate-950"
                            }`}
                          >
                            {realProgressStage}
                          </h3>

                          <p className={`mt-1 text-sm leading-6 ${mutedText}`}>
                            {realProgressDetails}
                          </p>

                          {uploadId && (
                            <p className={`mt-1 text-xs ${mutedText}`}>
                              Upload ID: {uploadId}
                            </p>
                          )}
                        </div>
                      </div>

                      <div
                        className={`rounded-2xl px-3 py-2 text-sm font-black ${
                          realProgressStatus === "failed"
                            ? "bg-red-100 text-red-700"
                            : isDark
                            ? "bg-slate-950/70 text-blue-200"
                            : "bg-white text-blue-700"
                        }`}
                      >
                        {realProgressPercent}% • {processingSeconds}s
                      </div>
                    </div>

                    <div
                      className={`mb-4 h-3 overflow-hidden rounded-full ${
                        isDark ? "bg-slate-800" : "bg-white"
                      }`}
                    >
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          realProgressStatus === "failed"
                            ? "bg-red-500"
                            : "bg-gradient-to-r from-blue-500 via-emerald-400 to-blue-500"
                        }`}
                        style={{
                          width: `${Math.max(
                            1,
                            Math.min(100, realProgressPercent)
                          )}%`,
                        }}
                      />
                    </div>

                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                      {progressSteps.map((step) => {
                        const isDone = realProgressPercent >= step.threshold;
                        const isActive =
                          realProgressStage === step.title ||
                          (step.title === "Building intelligence" &&
                            realProgressStage
                              .toLowerCase()
                              .includes("intelligence"));

                        return (
                          <div
                            key={step.title}
                            className={`rounded-2xl border px-4 py-3 transition ${
                              isActive
                                ? isDark
                                  ? "border-blue-400 bg-blue-500/20 text-blue-100"
                                  : "border-blue-300 bg-white text-blue-800"
                                : isDone
                                ? isDark
                                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100"
                                  : "border-emerald-200 bg-emerald-50 text-emerald-800"
                                : isDark
                                ? "border-slate-700 bg-slate-900/60 text-slate-300"
                                : "border-slate-200 bg-white/70 text-slate-600"
                            }`}
                          >
                            <div className="mb-1 flex items-center gap-2">
                              <span
                                className={`h-2.5 w-2.5 rounded-full ${
                                  isActive
                                    ? "bg-blue-500"
                                    : isDone
                                    ? "bg-emerald-500"
                                    : "bg-slate-400"
                                }`}
                              />
                              <p className="text-sm font-black">
                                {step.title}
                              </p>
                            </div>
                            <p className="line-clamp-2 text-xs leading-5 opacity-80">
                              {step.description}
                            </p>
                          </div>
                        );
                      })}
                    </div>

                    <p className={`mt-4 text-xs leading-5 ${mutedText}`}>
                      This is real backend progress from Django. Large PDFs may
                      take time because ScholarMind extracts text, creates
                      chunks, generates embeddings, stores vectors, and builds a
                      document intelligence profile.
                    </p>
                  </div>
                </div>
              )}

              {messages.length === 0 && (
                <div className="grid min-h-[58vh] place-items-center text-center">
                  <div>
                    <div
                      className={`mx-auto mb-5 grid h-24 w-24 place-items-center rounded-[2rem] border text-5xl ${
                        isDark
                          ? "border-slate-800 bg-slate-800"
                          : "border-slate-200 bg-slate-50"
                      }`}
                    >
                      <BookOpen className="text-blue-500" size={44} />
                    </div>

                    <h3
                      className={`text-3xl font-black tracking-tight ${
                        isDark ? "text-white" : "text-slate-950"
                      }`}
                    >
                      Your document, explained clearly.
                    </h3>

                    <p
                      className={`mx-auto mt-3 max-w-xl leading-7 ${mutedText}`}
                    >
                      Attach a PDF, then ask questions. ScholarMind will create
                      source chunks, embeddings, document intelligence, and
                      persistent chat memory.
                    </p>

                    <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {documentTools.slice(0, 8).map((tool) => {
                        const ToolIcon = tool.icon;

                        return (
                          <button
                            key={tool.title}
                            onClick={() => runDocumentTool(tool)}
                            className={`rounded-2xl border px-4 py-3 text-left text-sm font-bold transition ${
                              isDark
                                ? "border-slate-700 bg-slate-800 text-white hover:bg-slate-700"
                                : "border-slate-200 bg-white text-slate-900 hover:border-blue-200 hover:bg-blue-50"
                            }`}
                          >
                            <ToolIcon
                              size={17}
                              className="mb-2 text-emerald-500"
                            />
                            {tool.title}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-6">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "assistant" && (
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-emerald-400 font-black text-slate-950">
                        <Bot size={18} />
                      </div>
                    )}

                    <div
                      className={`max-w-[82%] rounded-3xl px-5 py-4 leading-7 ${
                        msg.role === "user"
                          ? "rounded-tr-md bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                          : isDark
                          ? "rounded-tl-md border border-slate-700 bg-slate-800 text-white"
                          : "rounded-tl-md border border-slate-200 bg-slate-50 text-slate-900"
                      }`}
                    >
                      <MarkdownMessage content={msg.content} role={msg.role} />

                      {msg.typing && (
                        <span className="ml-1 animate-pulse text-blue-500">
                          ▋
                        </span>
                      )}

                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {msg.sources.map((source, sourceIndex) => (
                            <button
                              key={sourceIndex}
                              onClick={() => openSource(source, sourceIndex)}
                              className={`rounded-full border px-3 py-1 text-xs font-black transition ${
                                isDark
                                  ? "border-blue-300/30 bg-blue-400/10 text-blue-200 hover:bg-blue-400/20"
                                  : "border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100"
                              }`}
                            >
                              <span className="flex items-center gap-2">
                                <span>
                                  {source.source_id ||
                                    `Source ${sourceIndex + 1}`}
                                  {source.page_number
                                    ? ` • p.${source.page_number}`
                                    : ""}
                                </span>

                                <span
                                  className={`rounded-full border px-2 py-0.5 text-[10px] font-black ${getSourceBadgeClass(
                                    source
                                  )}`}
                                >
                                  {getSourceBadgeText(source)}
                                  {formatSourceScore(source)}
                                </span>
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {msg.role === "user" && (
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-blue-500 text-xs font-black text-white">
                        You
                      </div>
                    )}
                  </div>
                ))}

                {answering && !messages[messages.length - 1]?.typing && (
                  <div className="flex gap-3">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-emerald-400 font-black text-slate-950">
                      <Bot size={18} />
                    </div>
                    <div
                      className={`flex w-fit gap-2 rounded-3xl rounded-tl-md px-5 py-4 ${
                        isDark
                          ? "border border-slate-700 bg-slate-800"
                          : "border border-slate-200 bg-slate-50"
                      }`}
                    >
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>
            </div>

            {activeSource && (
              <div
                className={`border-t p-4 md:p-5 ${
                  isDark
                    ? "border-amber-300/20 bg-amber-300/10"
                    : "border-amber-200 bg-amber-50"
                }`}
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3
                        className={`font-black ${
                          isDark ? "text-amber-100" : "text-amber-900"
                        }`}
                      >
                        {activeSource.label || `Source ${activeSource.number}`}
                      </h3>

                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] font-black ${getSourceBadgeClass(
                          activeSource
                        )}`}
                      >
                        {getSourceBadgeText(activeSource)}
                        {formatSourceScore(activeSource)}
                      </span>
                    </div>

                    <p
                      className={`mt-1 text-sm ${
                        isDark ? "text-amber-100/70" : "text-amber-800/70"
                      }`}
                    >
                      Page {activeSource.page_number || "Unknown"}
                      {activeSource.start_line && activeSource.end_line
                        ? `, Lines ${activeSource.start_line}–${activeSource.end_line}`
                        : ""}
                      {activeSource.section_title &&
                      activeSource.section_title !== "Unknown"
                        ? ` • ${activeSource.section_title}`
                        : ""}
                    </p>
                  </div>

                  <button
                    onClick={() => setActiveSource(null)}
                    className={`rounded-xl p-2 transition ${
                      isDark
                        ? "bg-slate-950/70 text-amber-100 hover:bg-slate-950"
                        : "bg-white text-amber-900 hover:bg-amber-100"
                    }`}
                  >
                    <X size={18} />
                  </button>
                </div>

                {activeSource.preview && (
                  <p
                    className={`mb-3 rounded-2xl border px-4 py-3 text-sm leading-6 ${
                      isDark
                        ? "border-slate-700 bg-slate-900 text-slate-200"
                        : "border-amber-200 bg-white text-slate-700"
                    }`}
                  >
                    <strong>Preview:</strong> {activeSource.preview}
                  </p>
                )}

                <div className="max-h-44 overflow-y-auto rounded-2xl border border-amber-200 bg-amber-100 px-4 py-3 leading-7 text-slate-950">
                  {activeSource.content}
                </div>
              </div>
            )}

            {error && !uploading && (
              <div className="mx-4 mb-3 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 font-bold text-red-500">
                {error}
              </div>
            )}

            {file && (
              <div
                className={`mx-4 mb-3 flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm ${
                  isDark
                    ? "border-blue-300/20 bg-blue-500/10 text-blue-100"
                    : "border-blue-100 bg-blue-50 text-blue-700"
                }`}
              >
                <span className="line-clamp-1">
                  {uploading ? "Analyzing: " : "Attached: "}
                  {file.name}
                </span>
                <button
                  onClick={removeAttachedFile}
                  disabled={uploading}
                  className={`rounded-lg px-2 py-1 font-bold disabled:cursor-not-allowed disabled:opacity-50 ${
                    isDark
                      ? "bg-blue-950/60 hover:bg-blue-950"
                      : "bg-blue-100 hover:bg-blue-200"
                  }`}
                >
                  Remove
                </button>
              </div>
            )}

            <form
              onSubmit={askQuestion}
              className={`flex items-end gap-3 border-t p-4 ${
                isDark
                  ? "border-slate-800 bg-slate-950"
                  : "border-slate-200 bg-white"
              }`}
            >
              <button
                type="button"
                onClick={() => fileInputRef.current.click()}
                className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl transition ${
                  isDark
                    ? "bg-slate-800 text-blue-200 hover:bg-slate-700"
                    : "bg-slate-100 text-blue-600 hover:bg-blue-50"
                }`}
                title="Attach PDF"
              >
                <Paperclip size={20} />
              </button>

              <input
                ref={fileInputRef}
                hidden
                type="file"
                accept="application/pdf,.pdf"
                onChange={handleFileChange}
              />

              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows="1"
                placeholder={
                  uploading
                    ? "Please wait. ScholarMind is analyzing your document..."
                    : selectedPaper
                    ? "Ask anything about this document..."
                    : file
                    ? "PDF attached. Ask your first question..."
                    : "Attach a PDF or select a recent document, then ask a question..."
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    askQuestion(e);
                  }
                }}
                disabled={uploading}
                className={`max-h-36 min-h-12 flex-1 resize-none rounded-2xl border px-4 py-3 outline-none disabled:cursor-not-allowed disabled:opacity-70 ${
                  isDark
                    ? "border-slate-700 bg-slate-900 text-white placeholder:text-slate-500 focus:border-blue-400 focus:ring-4 focus:ring-blue-500/10"
                    : "border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-blue-300 focus:ring-4 focus:ring-blue-100"
                }`}
              />

              <button
                type="submit"
                disabled={uploading || answering}
                className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:bg-slate-400 disabled:text-slate-100"
              >
                {uploading ? "⏳" : <Send size={20} />}
              </button>
            </form>
          </section>
        </main>
      </div>
      {selectedPaper && (
        <div className="fixed right-4 top-1/2 z-40 hidden -translate-y-1/2 flex-col gap-3 xl:flex">
          <button
            type="button"
            onClick={openRelatedLiteraturePanel}
            disabled={relatedPapersLoading}
            className={`group flex min-w-[170px] items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm font-black shadow-xl transition hover:-translate-x-1 disabled:cursor-not-allowed disabled:opacity-60 ${
              relatedPapersCount > 0
                ? isDark
                  ? "border-purple-400/30 bg-purple-500/20 text-purple-100 hover:bg-purple-500/30"
                  : "border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100"
                : isDark
                ? "border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
                : "border-slate-200 bg-white text-slate-800 hover:bg-slate-50"
            }`}
          >
            <span className="flex items-center gap-2">
              <BookOpen size={17} />
              Related Research Literature
            </span>

            <span
              className={`rounded-full px-2 py-0.5 text-xs font-black ${
                relatedPapersCount > 0
                  ? isDark
                    ? "bg-purple-300 text-slate-950"
                    : "bg-purple-600 text-white"
                  : isDark
                  ? "bg-slate-800 text-slate-300"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {relatedPapersLoading ? "..." : relatedPapersCount}
            </span>
          </button>

          <button
            type="button"
            onClick={openAnalysisPanel}
            disabled={analysisLoading}
            className={`group flex min-w-[170px] items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm font-black shadow-xl transition hover:-translate-x-1 disabled:cursor-not-allowed disabled:opacity-60 ${
              analysisReady
                ? isDark
                  ? "border-emerald-400/30 bg-emerald-500/20 text-emerald-100 hover:bg-emerald-500/30"
                  : "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                : isDark
                ? "border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
                : "border-slate-200 bg-white text-slate-800 hover:bg-slate-50"
            }`}
          >
            <span className="flex items-center gap-2">
              <Brain size={17} />
              Intelligence
            </span>

            <span
              className={`h-2.5 w-2.5 rounded-full ${
                analysisReady ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
          </button>
        </div>
      )}

   {showRelatedPanel && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <button
            type="button"
            aria-label="Close related literature panel"
            onClick={() => setShowRelatedPanel(false)}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          />

          <aside
            className={`relative z-10 flex h-full w-full max-w-[520px] flex-col border-l shadow-2xl ${
              isDark
                ? "border-slate-700 bg-slate-950 text-slate-100"
                : "border-slate-200 bg-white text-slate-950"
            }`}
          >
            <div
              className={`border-b px-5 py-4 ${
                isDark ? "border-slate-800" : "border-slate-200"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-black">
                    Related Research Literature
                  </h3>
                  <p className={`mt-1 text-sm ${mutedText}`}>
                    Related published studies for the selected document.
                  </p>

                  {relatedSearchQuery && (
                    <p className={`mt-2 text-xs font-bold ${mutedText}`}>
                      Search query: “{relatedSearchQuery}”
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setShowRelatedPanel(false)}
                  className={`rounded-xl p-2 transition ${
                    isDark
                      ? "bg-slate-900 text-slate-200 hover:bg-slate-800"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <X size={18} />
                </button>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {selectedPaper && (
                  <button
                    type="button"
                    onClick={() => generateRelatedPapers(selectedPaper)}
                    disabled={relatedPapersLoading}
                    className="rounded-2xl bg-purple-600 px-4 py-2 text-sm font-black text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {relatedPapersLoading ? "Generating..." : "Regenerate"}
                  </button>
                )}

                {selectedPaper && relatedPapers.length > 0 && (
                  <button
                    type="button"
                    onClick={() => clearRelatedPapers(selectedPaper)}
                    disabled={relatedPapersLoading}
                    className={`rounded-2xl border px-4 py-2 text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-60 ${
                      isDark
                        ? "border-slate-700 text-slate-200 hover:bg-slate-800"
                        : "border-slate-200 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {relatedPapersLoading && (
                <div
                  className={`mb-4 rounded-2xl border px-4 py-3 text-sm font-bold ${
                    isDark
                      ? "border-purple-400/20 bg-purple-500/10 text-purple-100"
                      : "border-purple-200 bg-purple-50 text-purple-700"
                  }`}
                >
                  Searching global scholarly sources and saving related literature...
                </div>
              )}

              {!relatedPapersLoading && relatedPapers.length === 0 && (
                <div
                  className={`rounded-3xl border p-6 text-center ${
                    isDark
                      ? "border-slate-700 bg-slate-900"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <BookOpen
                    size={38}
                    className={
                      isDark
                        ? "mx-auto text-purple-300"
                        : "mx-auto text-purple-600"
                    }
                  />

                  <h4 className="mt-3 text-lg font-black">
                    No related literature yet
                  </h4>

                  <p className={`mt-2 text-sm leading-6 ${mutedText}`}>
                    Click generate to discover related studies, DOI links,
                    citation signals, and open-access PDFs.
                  </p>

                  {selectedPaper && (
                    <button
                      type="button"
                      onClick={() => generateRelatedPapers(selectedPaper)}
                      className="mt-4 rounded-2xl bg-purple-600 px-5 py-3 text-sm font-black text-white transition hover:bg-purple-700"
                    >
                      Generate Related Literature
                    </button>
                  )}
                </div>
              )}

              {relatedPapers.length > 0 && (
                <div className="space-y-4">
                  {relatedPapers.map((paper) => (
                    <div
                      key={paper.id}
                      className={`rounded-3xl border p-4 ${
                        isDark
                          ? "border-slate-700 bg-slate-900"
                          : "border-slate-200 bg-slate-50"
                      }`}
                    >
                      <div className="mb-2 flex flex-wrap gap-2">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-black ${
                            isDark
                              ? "bg-blue-500/15 text-blue-200"
                              : "bg-blue-50 text-blue-700"
                          }`}
                        >
                          {paper.source || "OpenAlex"}
                        </span>

                        {paper.open_access && (
                          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700">
                            Open Access
                          </span>
                        )}

                        {paper.work_type && (
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-black ${
                              isDark
                                ? "bg-slate-800 text-slate-300"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {paper.work_type}
                          </span>
                        )}
                      </div>

                      <h4 className="text-base font-black leading-snug">
                        {paper.title || "Untitled related paper"}
                      </h4>

                      <p className={`mt-2 text-sm font-semibold ${mutedText}`}>
                        {formatAuthors(paper.authors)}
                      </p>

                      <div
                        className={`mt-3 flex flex-wrap gap-3 text-xs font-bold ${mutedText}`}
                      >
                        <span className="flex items-center gap-1">
                          <BookOpen size={14} />
                          {paper.venue || "Unknown venue"}
                        </span>

                        <span className="flex items-center gap-1">
                          <LockOpen size={14} />
                          {paper.year || "Unknown year"}
                        </span>

                        <span className="flex items-center gap-1">
                          <Quote size={14} />
                          {paper.cited_by_count || 0} citations
                        </span>
                      </div>

                      {paper.doi && (
                        <p className={`mt-3 text-xs font-bold ${mutedText}`}>
                          DOI: {paper.doi}
                        </p>
                      )}

                      {paper.why_related && (
                        <p
                          className={`mt-4 rounded-2xl border px-4 py-3 text-sm leading-6 ${
                            isDark
                              ? "border-purple-400/20 bg-purple-500/10 text-purple-100"
                              : "border-purple-100 bg-white text-purple-800"
                          }`}
                        >
                          <strong>Why related:</strong> {paper.why_related}
                        </p>
                      )}

                      {paper.abstract && (
                        <p
                          className={`mt-4 rounded-2xl border px-4 py-3 text-sm leading-6 ${
                            isDark
                              ? "border-slate-700 bg-slate-950/70 text-slate-300"
                              : "border-slate-200 bg-white text-slate-700"
                          }`}
                        >
                          {truncateText(paper.abstract)}
                        </p>
                      )}

                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => copyRelatedPaperDetails(paper)}
                          className={`flex items-center gap-2 rounded-2xl border px-4 py-2 text-sm font-black transition ${
                            isDark
                              ? "border-slate-700 text-slate-200 hover:bg-slate-800"
                              : "border-slate-200 text-slate-700 hover:bg-slate-100"
                          }`}
                        >
                          <Copy size={15} />
                          Copy
                        </button>

                        {paper.url && (
                          <button
                            type="button"
                            onClick={() =>
                              window.open(
                                paper.url,
                                "_blank",
                                "noopener,noreferrer"
                              )
                            }
                            className="flex items-center gap-2 rounded-2xl bg-blue-600 px-4 py-2 text-sm font-black text-white transition hover:bg-blue-700"
                          >
                            <ExternalLink size={15} />
                            Open
                          </button>
                        )}

                        {paper.pdf_url && (
                          <button
                            type="button"
                            onClick={() =>
                              window.open(
                                paper.pdf_url,
                                "_blank",
                                "noopener,noreferrer"
                              )
                            }
                            className="flex items-center gap-2 rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-black text-white transition hover:bg-emerald-700"
                          >
                            <FileText size={15} />
                            PDF
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

export default App;