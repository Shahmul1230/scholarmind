import { useState } from "react";
import axios from "axios";
import {
  BookOpen,
  Calendar,
  Copy,
  ExternalLink,
  FileText,
  Globe2,
  Loader2,
  LockOpen,
  Quote,
  Search,
  Sparkles,
  X,
} from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const truncateText = (text, maxLength = 420) => {
  if (!text) return "";

  const clean = String(text).replace(/\s+/g, " ").trim();

  if (clean.length <= maxLength) return clean;

  return `${clean.slice(0, maxLength).trim()}...`;
};

const formatAuthors = (authors) => {
  if (!authors || !Array.isArray(authors) || authors.length === 0) {
    return "Unknown authors";
  }

  return authors.join(", ");
};

const buildSelectedPaperQuery = (selectedPaper) => {
  if (!selectedPaper) return "";

  const title = selectedPaper.title || "";
  const documentType = selectedPaper.document_type || "";

  return `${title} ${documentType}`.replace(/\s+/g, " ").trim();
};

export default function ScholarSearchPanel({
  isDark = false,
  selectedPaper = null,
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [fromYear, setFromYear] = useState(2020);
  const [toYear, setToYear] = useState(new Date().getFullYear());
  const [openAccessOnly, setOpenAccessOnly] = useState(false);

  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const selectedPaperQuery = buildSelectedPaperQuery(selectedPaper);

  const panelClass = isDark
    ? "border-slate-700 bg-slate-950 text-slate-100"
    : "border-slate-200 bg-white text-slate-950";

  const inputClass = isDark
    ? "border-slate-700 bg-slate-900 text-slate-100 placeholder:text-slate-500 focus:border-blue-400"
    : "border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:border-blue-500";

  const cardClass = isDark
    ? "border-slate-800 bg-slate-900/80"
    : "border-slate-200 bg-slate-50";

  const mutedText = isDark ? "text-slate-400" : "text-slate-500";

  const clearMessages = () => {
    setError("");
    setCopiedIndex(null);
  };

  const searchPapers = async (customQuery = null) => {
    const finalQuery = String(customQuery ?? query).trim();

    if (!finalQuery) {
      setError("Search query is required.");
      return;
    }

    try {
      clearMessages();
      setLoading(true);
      setSearched(true);

      const payload = {
        query: finalQuery,
        limit: Number(limit) || 10,
        from_year: fromYear ? Number(fromYear) : null,
        to_year: toYear ? Number(toYear) : null,
        open_access_only: openAccessOnly,
      };

      const res = await axios.post(`${API_BASE_URL}/scholar/search/`, payload);

      setResults(res.data?.results || []);
    } catch (err) {
      const backendError =
        err?.response?.data?.details ||
        err?.response?.data?.error ||
        err?.message;

      setError(backendError || "Scholar search failed.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const searchSelectedPaper = async () => {
    if (!selectedPaperQuery) {
      setError("No selected document found.");
      return;
    }

    setQuery(selectedPaperQuery);
    await searchPapers(selectedPaperQuery);
  };

  const copyPaperDetails = async (paper, index) => {
    const lines = [
      paper.title || "Untitled paper",
      `Authors: ${formatAuthors(paper.authors)}`,
      `Year: ${paper.year || "Unknown"}`,
      `Venue: ${paper.venue || "Unknown"}`,
      paper.doi ? `DOI: ${paper.doi}` : "",
      paper.url ? `URL: ${paper.url}` : "",
      paper.abstract ? `Abstract: ${paper.abstract}` : "",
    ].filter(Boolean);

    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopiedIndex(index);

      setTimeout(() => {
        setCopiedIndex(null);
      }, 1600);
    } catch {
      setError("Could not copy paper details.");
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`flex w-full max-w-[360px] items-center gap-3 rounded-2xl border px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg ${
          isDark
            ? "border-blue-400/30 bg-blue-500/15 text-blue-100 hover:bg-blue-500/25"
            : "border-blue-200 bg-blue-50 text-blue-800 hover:border-blue-300 hover:bg-blue-100"
        }`}
      >
        <div
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${
            isDark ? "bg-blue-400 text-slate-950" : "bg-blue-600 text-white"
          }`}
        >
          <Search size={21} />
        </div>

        <div className="leading-tight">
          <p className="text-sm font-black">Find Published Papers</p>
          <p
            className={`mt-0.5 text-xs font-bold ${
              isDark ? "text-blue-100/70" : "text-blue-700/70"
            }`}
          >
            Search global research papers
          </p>
        </div>
      </button>

      {open && (
        <div className="fixed inset-0 z-50">
          <button
            type="button"
            aria-label="Close scholar search overlay"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/45 backdrop-blur-sm"
          />

          <div
            className={`absolute bottom-4 right-4 top-4 flex w-[min(1120px,calc(100vw-2rem))] flex-col overflow-hidden rounded-3xl border shadow-2xl ${panelClass}`}
          >
            <div
              className={`flex items-center justify-between border-b px-5 py-4 ${
                isDark ? "border-slate-800" : "border-slate-200"
              }`}
            >
              <div>
                <div className="flex items-center gap-2">
                  <div
                    className={`rounded-2xl p-2 ${
                      isDark
                        ? "bg-blue-500/15 text-blue-200"
                        : "bg-blue-50 text-blue-700"
                    }`}
                  >
                    <Globe2 size={20} />
                  </div>

                  <div>
                    <h2 className="text-lg font-black">
                      Global Published Paper Search
                    </h2>
                    <p className={`text-xs font-semibold ${mutedText}`}>
                      Search related papers from global academic sources.
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setOpen(false)}
                className={`rounded-2xl p-2 transition ${
                  isDark
                    ? "text-slate-300 hover:bg-slate-800"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <X size={20} />
              </button>
            </div>

            <div
              className={`border-b px-5 py-4 ${
                isDark ? "border-slate-800" : "border-slate-200"
              }`}
            >
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  searchPapers();
                }}
                className="space-y-4"
              >
                <div className="flex flex-col gap-3 lg:flex-row">
                  <div className="flex-1">
                    <label className="mb-2 block text-xs font-black uppercase tracking-wide">
                      Search query
                    </label>

                    <div className="relative">
                      <Search
                        size={18}
                        className={`absolute left-4 top-1/2 -translate-y-1/2 ${mutedText}`}
                      />

                      <input
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="Example: large language model cyber threat intelligence"
                        className={`w-full rounded-2xl border py-3 pl-11 pr-4 text-sm font-semibold outline-none transition ${inputClass}`}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 lg:w-[360px]">
                    <div>
                      <label className="mb-2 block text-xs font-black uppercase tracking-wide">
                        Limit
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="25"
                        value={limit}
                        onChange={(event) => setLimit(event.target.value)}
                        className={`w-full rounded-2xl border px-4 py-3 text-sm font-bold outline-none ${inputClass}`}
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-xs font-black uppercase tracking-wide">
                        From
                      </label>
                      <input
                        type="number"
                        value={fromYear}
                        onChange={(event) => setFromYear(event.target.value)}
                        className={`w-full rounded-2xl border px-4 py-3 text-sm font-bold outline-none ${inputClass}`}
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-xs font-black uppercase tracking-wide">
                        To
                      </label>
                      <input
                        type="number"
                        value={toYear}
                        onChange={(event) => setToYear(event.target.value)}
                        className={`w-full rounded-2xl border px-4 py-3 text-sm font-bold outline-none ${inputClass}`}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center gap-2 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-black text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loading ? (
                      <Loader2 size={17} className="animate-spin" />
                    ) : (
                      <Search size={17} />
                    )}
                    {loading ? "Searching..." : "Search Papers"}
                  </button>

                  <button
                    type="button"
                    onClick={() => setOpenAccessOnly(!openAccessOnly)}
                    className={`flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-black transition ${
                      openAccessOnly
                        ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                        : isDark
                        ? "border-slate-700 text-slate-200 hover:bg-slate-800"
                        : "border-slate-200 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    <LockOpen size={16} />
                    Open Access Only: {openAccessOnly ? "On" : "Off"}
                  </button>

                  <button
                    type="button"
                    onClick={searchSelectedPaper}
                    disabled={!selectedPaperQuery || loading}
                    className={`flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-50 ${
                      isDark
                        ? "border-purple-400/30 bg-purple-500/10 text-purple-100 hover:bg-purple-500/20"
                        : "border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100"
                    }`}
                  >
                    <Sparkles size={16} />
                    Search Related to Selected Document
                  </button>
                </div>
              </form>

              {error && (
                <div
                  className={`mt-4 rounded-2xl border px-4 py-3 text-sm font-bold ${
                    isDark
                      ? "border-red-400/30 bg-red-500/10 text-red-100"
                      : "border-red-200 bg-red-50 text-red-700"
                  }`}
                >
                  {error}
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5">
              {!searched && (
                <div
                  className={`flex h-full min-h-[360px] flex-col items-center justify-center rounded-3xl border border-dashed p-8 text-center ${
                    isDark
                      ? "border-slate-800 bg-slate-900/40"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <BookOpen
                    size={44}
                    className={isDark ? "text-blue-300" : "text-blue-600"}
                  />
                  <h3 className="mt-4 text-xl font-black">
                    Search global published papers
                  </h3>
                  <p className={`mt-2 max-w-xl text-sm leading-6 ${mutedText}`}>
                    Enter a topic, project title, methodology, or research area.
                    Results will show title, authors, year, venue, DOI, open
                    access status, citation count, and abstract preview.
                  </p>
                </div>
              )}

              {searched && !loading && results.length === 0 && !error && (
                <div
                  className={`rounded-3xl border p-8 text-center ${cardClass}`}
                >
                  <FileText
                    size={38}
                    className={
                      isDark
                        ? "mx-auto text-slate-500"
                        : "mx-auto text-slate-400"
                    }
                  />
                  <h3 className="mt-3 text-lg font-black">No papers found</h3>
                  <p className={`mt-2 text-sm ${mutedText}`}>
                    Try a shorter query or remove year/open access filters.
                  </p>
                </div>
              )}

              <div className="space-y-4">
                {results.map((paper, index) => (
                  <div
                    key={`${paper.openalex_id || paper.title || index}-${index}`}
                    className={`rounded-3xl border p-5 shadow-sm ${cardClass}`}
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
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

                          {paper.type && (
                            <span
                              className={`rounded-full px-3 py-1 text-xs font-black ${
                                isDark
                                  ? "bg-slate-800 text-slate-300"
                                  : "bg-slate-100 text-slate-600"
                              }`}
                            >
                              {paper.type}
                            </span>
                          )}
                        </div>

                        <h3 className="text-lg font-black leading-snug">
                          {paper.title || "Untitled paper"}
                        </h3>

                        <p className={`mt-2 text-sm font-semibold ${mutedText}`}>
                          {formatAuthors(paper.authors)}
                        </p>

                        <div
                          className={`mt-3 flex flex-wrap gap-3 text-xs font-bold ${mutedText}`}
                        >
                          <span className="flex items-center gap-1">
                            <Calendar size={14} />
                            {paper.year || "Unknown year"}
                          </span>

                          <span className="flex items-center gap-1">
                            <BookOpen size={14} />
                            {paper.venue || "Unknown venue"}
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

                        {paper.abstract && (
                          <p
                            className={`mt-4 rounded-2xl border px-4 py-3 text-sm leading-6 ${
                              isDark
                                ? "border-slate-800 bg-slate-950/50 text-slate-300"
                                : "border-slate-200 bg-white text-slate-700"
                            }`}
                          >
                            {truncateText(paper.abstract)}
                          </p>
                        )}

                        {paper.concepts && paper.concepts.length > 0 && (
                          <div className="mt-4 flex flex-wrap gap-2">
                            {paper.concepts.map((concept) => (
                              <span
                                key={concept}
                                className={`rounded-full border px-3 py-1 text-xs font-bold ${
                                  isDark
                                    ? "border-slate-700 text-slate-300"
                                    : "border-slate-200 text-slate-600"
                                }`}
                              >
                                {concept}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex shrink-0 flex-row gap-2 lg:flex-col">
                        <button
                          type="button"
                          onClick={() => copyPaperDetails(paper, index)}
                          className={`flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-sm font-black transition ${
                            isDark
                              ? "border-slate-700 text-slate-200 hover:bg-slate-800"
                              : "border-slate-200 text-slate-700 hover:bg-slate-100"
                          }`}
                        >
                          <Copy size={15} />
                          {copiedIndex === index ? "Copied" : "Copy"}
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
                            className="flex items-center justify-center gap-2 rounded-2xl bg-blue-600 px-4 py-2 text-sm font-black text-white transition hover:bg-blue-700"
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
                            className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-black text-white transition hover:bg-emerald-700"
                          >
                            <FileText size={15} />
                            PDF
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div
              className={`border-t px-5 py-3 text-xs font-semibold ${mutedText} ${
                isDark ? "border-slate-800" : "border-slate-200"
              }`}
            >
              Backend endpoint used:{" "}
              <span className="font-black">POST /api/scholar/search/</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}