import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { getBugReport, submitBugReport } from "./api";
import type {
  AnalysisStatus,
  BugAnalysisResult,
  BugReportResponse,
} from "./types";

import "./App.css";


interface ResultListProps {
  title: string;
  items: string[];
  numbered?: boolean;
}


function ResultList({
  title,
  items,
  numbered = false,
}: ResultListProps) {
  return (
    <section className="result-section">
      <h3>{title}</h3>

      {items.length > 0 ? (
        <ul className={numbered ? "result-list numbered" : "result-list"}>
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="empty-message">No findings reported.</p>
      )}
    </section>
  );
}


function formatStatus(status: AnalysisStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}


function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred.";
}


function AnalysisResult({
  analysis,
}: {
  analysis: BugAnalysisResult;
}) {
  return (
    <div className="analysis-content">
      <section className="summary-card">
        <div>
          <p className="section-label">AI diagnosis</p>
          <h2>{analysis.summary}</h2>
        </div>

        <div className="analysis-labels">
          <span className={`severity severity-${analysis.severity}`}>
            Severity: {analysis.severity}
          </span>

          <span className="confidence">
            Confidence: {analysis.confidence}
          </span>
        </div>
      </section>

      <div className="result-grid">
        <ResultList
          title="Detected errors"
          items={analysis.detected_errors}
        />

        <ResultList
          title="Likely root causes"
          items={analysis.likely_root_causes}
          numbered
        />

        <ResultList
          title="Screenshot observations"
          items={analysis.screenshot_observations}
        />

        <ResultList
          title="Supporting-file findings"
          items={analysis.supporting_file_findings}
        />

        <ResultList
          title="Evidence"
          items={analysis.evidence}
        />

        <ResultList
          title="Recommended fixes"
          items={analysis.recommended_fixes}
          numbered
        />

        <ResultList
          title="Verification steps"
          items={analysis.verification_steps}
          numbered
        />

        <ResultList
          title="Missing information"
          items={analysis.missing_information}
        />
      </div>
    </div>
  );
}


function App() {
  const [description, setDescription] = useState("");
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [supportingFile, setSupportingFile] = useState<File | null>(null);

  const [report, setReport] = useState<BugReportResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const reportId = report?.id;
  const reportStatus = report?.status;

  // Keep checking the backend while Ollama is processing the report.
  useEffect(() => {
    if (
      reportId === undefined ||
      (reportStatus !== "queued" && reportStatus !== "analyzing")
    ) {
      return;
    }

    let isCancelled = false;

    async function refreshReport() {
      try {
        const updatedReport = await getBugReport(reportId as number);

        if (!isCancelled) {
          setReport(updatedReport);
          setErrorMessage("");
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(getErrorMessage(error));
        }
      }
    }

    const pollingTimer = window.setInterval(refreshReport, 3000);

    return () => {
      isCancelled = true;
      window.clearInterval(pollingTimer);
    };
  }, [reportId, reportStatus]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanedDescription = description.trim();

    if (cleanedDescription.length < 10) {
      setErrorMessage(
        "Description must contain at least 10 characters.",
      );
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setReport(null);

    try {
      // First save the report and obtain its database ID.
      const submission = await submitBugReport(
        cleanedDescription,
        screenshot,
        supportingFile,
      );

      // Retrieve the saved report so polling can begin.
      const createdReport = await getBugReport(
        submission.bug_report_id,
      );

      setReport(createdReport);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const isProcessing =
    report?.status === "queued" || report?.status === "analyzing";

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="brand">
          <div className="brand-mark">TL</div>

          <div>
            <h1>TraceLens</h1>
            <p>Multimodal software bug investigation</p>
          </div>
        </div>

        <span className="local-badge">Local AI</span>
      </header>

      <main className="page-content">
        <section className="hero">
          <p className="eyebrow">AI-powered debugging assistant</p>

          <h2>Turn scattered bug evidence into an actionable diagnosis.</h2>

          <p>
            Submit a description, screenshot, and supporting file.
            TraceLens analyzes the evidence together and recommends
            practical fixes.
          </p>
        </section>

        <div className="workspace-grid">
          <section className="panel submission-panel">
            <div className="panel-heading">
              <div>
                <p className="step-number">01</p>
                <h2>Submit bug evidence</h2>
              </div>

              <p>Screenshot and supporting file are optional.</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-field">
                <label htmlFor="description">
                  Bug description
                  <span aria-hidden="true"> *</span>
                </label>

                <textarea
                  id="description"
                  value={description}
                  onChange={(event) => {
                    setDescription(event.target.value);
                  }}
                  placeholder="Describe what happened, what you expected, and how to reproduce it."
                  rows={7}
                  required
                />

                <div className="field-help">
                  <span>Minimum 10 characters</span>
                  <span>{description.trim().length} characters</span>
                </div>
              </div>

              <div className="file-grid">
                <div className="form-field">
                  <label htmlFor="screenshot">Error screenshot</label>

                  <input
                    id="screenshot"
                    type="file"
                    accept=".png,.jpg,.jpeg,.webp"
                    onChange={(event) => {
                      setScreenshot(event.target.files?.[0] ?? null);
                    }}
                  />

                  <p className="field-help">
                    PNG, JPG, JPEG or WebP · Maximum 5 MB
                  </p>
                </div>

                <div className="form-field">
                  <label htmlFor="supporting-file">
                    Supporting file
                  </label>

                  <input
                    id="supporting-file"
                    type="file"
                    accept=".log,.txt,.csv,.json,.pdf,.doc,.docx"
                    onChange={(event) => {
                      setSupportingFile(event.target.files?.[0] ?? null);
                    }}
                  />

                  <p className="field-help">
                    LOG, TXT, CSV, JSON, PDF, DOC or DOCX · Maximum 10 MB
                  </p>
                </div>
              </div>

              {errorMessage && (
                <div className="error-message" role="alert">
                  {errorMessage}
                </div>
              )}

              <button
                className="submit-button"
                type="submit"
                disabled={isSubmitting || isProcessing}
              >
                {isSubmitting
                  ? "Submitting report..."
                  : isProcessing
                    ? "Analysis in progress..."
                    : "Analyze bug"}
              </button>
            </form>
          </section>

          <section className="panel report-panel">
            <div className="panel-heading">
              <div>
                <p className="step-number">02</p>
                <h2>Investigation report</h2>
              </div>

              {report && (
                <span className={`status status-${report.status}`}>
                  {formatStatus(report.status)}
                </span>
              )}
            </div>

            {!report && (
              <div className="empty-state">
                <div className="empty-state-icon">TL</div>
                <h3>No report submitted yet</h3>
                <p>
                  Your structured diagnosis will appear here after
                  submitting the available evidence.
                </p>
              </div>
            )}

            {isProcessing && report && (
              <div className="processing-state">
                <div className="spinner" aria-hidden="true" />

                <div>
                  <h3>Analyzing report #{report.id}</h3>
                  <p>
                    Ollama is examining the description and uploaded
                    evidence. This page updates automatically.
                  </p>
                </div>
              </div>
            )}

            {report?.status === "failed" && (
              <div className="failed-state">
                <h3>Analysis failed</h3>
                <p>
                  TraceLens saved the report, but the AI analysis could
                  not be completed. Check that Ollama is running and try
                  again.
                </p>
              </div>
            )}

            {report?.status === "completed" &&
              report.analysis_result && (
                <AnalysisResult analysis={report.analysis_result} />
              )}
          </section>
        </div>
      </main>
    </div>
  );
}


export default App;