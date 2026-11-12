export type Role = "CITIZEN" | "ADMIN" | "MAINTENANCE";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  first_name: string;
  last_name: string;
}

export interface Issue {
  public_id: string;
  title: string;
  description?: string;
  category: string;
  severity: string;
  status: string;
  priority: string;
  priority_score: number;
  support_count: number;
  latitude: string;
  longitude: string;
  address: string;
  reporter_name?: string;
  assigned_team_name?: string | null;
  reporter?: User;
  assigned_team?: Team | null;
  resolution_notes?: string;
  images?: IssueImage[];
  status_history?: StatusHistory[];
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface IssueImage {
  id: number;
  image: string;
  kind: string;
  created_at: string;
}

export interface StatusHistory {
  id: number;
  previous_status: string;
  new_status: string;
  actor: User | null;
  comment: string;
  created_at: string;
}

export interface Team {
  id: number;
  name: string;
  description: string;
  specialization: string;
  is_active: boolean;
  member_count?: number;
}

export interface DuplicateSuggestion {
  public_id: string;
  title: string;
  status: string;
  category: string;
  address: string;
  support_count: number;
  score: number;
  distance_meters: number;
  text_similarity: number;
}

export interface NotificationItem {
  id: number;
  kind: string;
  title: string;
  message: string;
  issue_public_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_issues: number;
  pending_verification: number;
  high_priority_open: number;
  resolved_issues: number;
  resolution_rate_percent: number;
  average_resolution_hours: number | null;
  by_category: { category: string; count: number }[];
  by_status: { status: string; count: number }[];
  by_priority: { priority: string; count: number }[];
  reported_over_time: { day: string; count: number }[];
  duplicate_candidates_detected: number;
  generated_at: string;
  cache_source?: string;
  cache_counters?: Record<string, number | number[]>;
}
