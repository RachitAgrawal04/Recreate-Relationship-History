// Core types matching the normalized data schema

export type Platform = 'whatsapp' | 'instagram';
export type SenderId = 'person-a' | 'person-b';
export type MessageKind =
  | 'text'
  | 'photo'
  | 'video'
  | 'audio'
  | 'sticker'
  | 'share'
  | 'call';

export type EmotionalWeatherMood =
  | 'neutral'
  | 'joyful'
  | 'tender'
  | 'playful'
  | 'tense'
  | 'latenight'
  | 'morning'
  | 'missing';

export interface Reaction {
  emoji: string;
  count: number;
  reactors: string[];
}

export interface Attachment {
  uri: string;
  media_type: 'photo' | 'video' | 'audio' | 'sticker' | 'gif';
  mime_type?: string;
  width?: number;
  height?: number;
  duration_seconds?: number;
  is_sensitive?: boolean;
}

export interface ShareContent {
  link?: string;
  share_text?: string;
  original_content_owner?: string;
}

export interface Message {
  event_id: string;
  platform: Platform;
  sender_id: SenderId;
  sender_display: string;
  timestamp_parsed: string; // ISO 8601
  text_display: string;
  kind: MessageKind;
  reactions: Reaction[];
  attachments: Attachment[];
  turn_id: string;
  is_sensitive?: boolean;
  mood?: EmotionalWeatherMood;
  share?: ShareContent;
  call_duration_seconds?: number;
  // Annotation overlays (not part of raw data)
  ai_annotation?: string;
  human_note?: string;
}

export interface DayGroup {
  date: string; // ISO date string YYYY-MM-DD
  display_date: string; // "Thursday, August 20, 2026"
  messages: Message[];
  dominant_mood: EmotionalWeatherMood;
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  date_start: string;
  date_end: string;
  date_range_display: string;
  excerpt: string;
  mood: EmotionalWeatherMood;
  message_count: number;
  platforms: Platform[];
  cover_color: string; // fallback bg colour
}

export interface TimelineMonth {
  month_key: string; // "2026-08"
  month_display: string; // "August 2026"
  message_count: number;
  dominant_mood: EmotionalWeatherMood;
  platforms: Platform[];
  events: TimelineEvent[];
}

export interface TimelineEvent {
  id: string;
  date: string;
  label: string;
  kind: 'milestone' | 'media' | 'intensity' | 'silence';
  mood?: EmotionalWeatherMood;
}

export interface MediaItem {
  event_id: string;
  platform: Platform;
  sender_id: SenderId;
  timestamp_parsed: string;
  kind: 'photo' | 'video' | 'audio' | 'sticker';
  uri: string;
  thumbnail_uri?: string;
  is_sensitive: boolean;
  width?: number;
  height?: number;
  duration_seconds?: number;
  caption?: string;
}

export interface InsightCard {
  id: string;
  title: string;
  icon: string; // emoji or icon name
  content: string;
  expanded_content?: string;
  category: 'communication' | 'language' | 'emotion' | 'pattern' | 'temporal';
}

export interface SearchResult {
  event_id: string;
  message: Message;
  score: number;
  highlight_start: number;
  highlight_end: number;
  context_before?: string;
  context_after?: string;
}

export interface ArchiveStats {
  total_messages: number;
  whatsapp_messages: number;
  instagram_messages: number;
  total_days: number;
  media_items: number;
  date_start: string;
  date_end: string;
  person_a_display: string;
  person_b_display: string;
}
