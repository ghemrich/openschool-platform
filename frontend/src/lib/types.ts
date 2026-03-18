export interface User {
  id: number;
  github_id: number;
  username: string;
  email: string | null;
  avatar_url: string | null;
  role: 'student' | 'mentor' | 'admin';
  discord_id: string | null;
  created_at: string;
  last_login: string | null;
}

export interface Exercise {
  id: number;
  name: string;
  order: number;
  repo_prefix: string | null;
  classroom_url: string | null;
  required: boolean;
}

export interface Module {
  id: number;
  name: string;
  order: number;
  exercises: Exercise[];
}

export interface Course {
  id: number;
  name: string;
  description: string | null;
  modules: Module[];
}

export interface CourseListItem {
  id: number;
  name: string;
  description: string | null;
}

export interface DashboardCourse {
  course_id: number;
  course_name: string;
  total_exercises: number;
  completed_exercises: number;
  progress_percent: number;
}

export interface ExerciseProgress {
  id: number;
  name: string;
  status: 'not_started' | 'in_progress' | 'completed';
}

export interface ModuleProgress {
  module_id: number;
  module_name: string;
  exercises: ExerciseProgress[];
}

export interface Certificate {
  cert_id: string;
  course_id: number;
  course_name: string;
  issued_at: string;
}

export interface AdminStats {
  users: number;
  courses: number;
  enrollments: number;
  certificates: number;
  exercises: number;
}

export interface PromotionRule {
  id: number;
  name: string;
  description: string | null;
  target_role: 'student' | 'mentor' | 'admin';
  is_active: boolean;
  created_at: string | null;
  course_ids: number[];
}

export interface VerifyResponse {
  name: string;
  course: string;
  issued_at: string;
  cert_id: string;
}
