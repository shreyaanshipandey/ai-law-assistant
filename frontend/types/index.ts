export type UserRole = "admin" | "user";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface BNSSectionHit {
  section_number: string;
  section_title: string;
  description: string;
  punishment: string;
  imprisonment_term: string;
  bailable: string;
  cognizable: string;
  relevance_score: number;
}

export interface BNSPredictionResult {
  applicable_sections: BNSSectionHit[];
  overall_severity: "Low" | "Moderate" | "High" | "Severe";
  severity_explanation: string;
  recommended_next_steps: string[];
  disclaimer: string;
}

export interface CaseAnalysisOut {
  id: string;
  case_summary: string;
  case_category: string | null;
  predicted_sections: BNSPredictionResult;
  created_at: string;
}

export interface PetitionScanIssue {
  category: string;
  severity: string;
  description: string;
  suggestion: string;
}

export interface PetitionScanResult {
  validity_score: number;
  summary: string;
  issues: PetitionScanIssue[];
  missing_sections_detected: string[];
  strengths: string[];
}

export interface PetitionOut {
  id: string;
  title: string;
  source_type: "generated" | "uploaded";
  content_text: string;
  file_path: string | null;
  scan_result: PetitionScanResult | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  ts: string;
}

export interface ChatSessionOut {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface Helpline {
  name: string;
  number: string;
  category: string;
  description: string;
  available: string;
}
export type CaseStatus =
  | "Pending"
  | "Adjourned"
  | "Reserved for Orders"
  | "Disposed"
  | "Dismissed";

export interface CaseRecord {
  id: string;
  case_number: string;
  title: string;
  status: CaseStatus;
  filing_date: string;
  next_hearing_date: string | null;
  court: string | null;
  court: string;
  description: string | null;
  is_ongoing: boolean;
  created_at: string;
  updated_at: string;
}