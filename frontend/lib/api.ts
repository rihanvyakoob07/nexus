import type { AdminAssessment, AdminTeam, Application, ATSResult, DemandResponse, Engineer, EngineerDashboard, EngineerPassport, LeadershipAnalytics, Opportunity, Resume } from "@/types/api";
import type { Role } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window === "undefined" ? null : window.localStorage.getItem("nexus_token");
  const isMultipart = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const headers = new Headers(init?.headers);
  if (!isMultipart && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...Object.fromEntries(headers.entries()),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem("nexus_token");
    }
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // Keep the HTTP status when the API does not return JSON.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export async function login(email: string, password: string) {
  const result = await apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  window.localStorage.setItem("nexus_token", result.access_token);
  return result;
}

export function logout() {
  window.localStorage.removeItem("nexus_token");
}

export function isAuthenticated() {
  return typeof window !== "undefined" && Boolean(window.localStorage.getItem("nexus_token"));
}

export function getRole(): Role | null {
  if (typeof window === "undefined") return null;
  const token = window.localStorage.getItem("nexus_token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as { role?: Role };
    return payload.role ?? null;
  } catch {
    return null;
  }
}

export function hasRole(...roles: Role[]) {
  const role = getRole();
  return role !== null && roles.includes(role);
}

export async function uploadResume(file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<Resume>("/engineers/me/resume", { method: "POST", headers: {}, body: form });
}

export function getResume() {
  return apiFetch<Resume>("/engineers/me/resume");
}

export function getResumeATS() {
  return apiFetch<ATSResult>("/engineers/me/resume/ats");
}

export function getOpportunities() {
  return apiFetch<Opportunity[]>("/opportunities");
}

export function applyToOpportunity(jdId: number, coverNote?: string) {
  return apiFetch<Application>(`/opportunities/${jdId}/apply`, { method: "POST", body: JSON.stringify({ cover_note: coverNote }) });
}

export function getMyApplications() {
  return apiFetch<Application[]>("/engineers/me/applications");
}

export function getMyProfile() { return apiFetch<EngineerDashboard>("/dashboard/engineer").then((dashboard) => apiFetch<EngineerPassport>(`/engineers/${dashboard.engineer_id}`)); }
export function updateMyProfile(payload: { name?: string; seniority?: string; bio?: string }) { return apiFetch<Engineer>("/engineers/me", { method: "PATCH", body: JSON.stringify(payload) }); }
export function getAdminAssessments() { return apiFetch<AdminAssessment[]>("/dashboard/admin/assessments"); }
export function getAdminTeams() { return apiFetch<AdminTeam[]>("/dashboard/admin/teams"); }
export function getLeadershipAnalytics() { return apiFetch<LeadershipAnalytics>("/dashboard/analytics"); }
export function getLeadershipDemand() { return apiFetch<DemandResponse>("/dashboard/demand"); }
export function publishJd(id: number) { return apiFetch(`/jds/${id}/publish`, { method: "PATCH" }); }
export function closeJd(id: number) { return apiFetch(`/jds/${id}/close`, { method: "PATCH" }); }
