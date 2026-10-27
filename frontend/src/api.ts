import type {
  AnalyzeSubmissionResponse,
  BugReportResponse,
} from "./types";

// Address of the FastAPI backend during local development.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

// Extract a readable message from an unsuccessful API response.
async function getApiErrorMessage(response: Response): Promise<string> {
  try {
    const responseData = (await response.json()) as {
      detail?: string | {
        message?: string;
      };
    };

    if (typeof responseData.detail === "string") {
      return responseData.detail;
    }

    if (
      typeof responseData.detail === "object" &&
      responseData.detail?.message
    ) {
      return responseData.detail.message;
    }
  } catch {
    // Use the fallback message when the server did not return JSON.
  }

  return `Request failed with status ${response.status}.`;
}

// Send the description and optional files to POST /analyze.
export async function submitBugReport(
  description: string,
  screenshot: File | null,
  supportingFile: File | null,
): Promise<AnalyzeSubmissionResponse> {
  const formData = new FormData();

  formData.append("description", description);

  if (screenshot) {
    formData.append("screenshot", screenshot);
  }

  if (supportingFile) {
    formData.append("supporting_file", supportingFile);
  }

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response));
  }

  return (await response.json()) as AnalyzeSubmissionResponse;
}

// Retrieve the latest status and result for one saved report.
export async function getBugReport(
  reportId: number,
): Promise<BugReportResponse> {
  const response = await fetch(
    `${API_BASE_URL}/bug-reports/${reportId}`,
  );

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response));
  }

  return (await response.json()) as BugReportResponse;
}