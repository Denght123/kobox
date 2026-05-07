export type LocaleCode = 'zh-CN' | 'zh-TW' | 'en' | 'ja' | 'ko'

export type CollectionStatus =
  | 'completed'
  | 'watching'
  | 'plan_to_watch'
  | 'on_hold'
  | 'dropped'

export interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiErrorBody {
  code: string
  message: string
  details?: unknown
}

export interface AnimeSummary {
  id: number
  source_id?: string | null
  title: string
  summary: string
  year: number
  season: string | null
  genres: string[]
  cover_url: string
  source_cover_url?: string | null
}

export interface UserProfile {
  id: number
  username: string
  public_slug: string
  display_name: string
  avatar_url: string | null
  background_image_url: string | null
  birthday: string | null
  bio: string | null
  is_public: boolean
}

export interface UserSettings {
  language: LocaleCode
  show_dynamic_background: boolean
  show_public_rank: boolean
}

export interface UserDashboard {
  profile: UserProfile
  settings: UserSettings
  collections: ListResponse<CollectionItem>
  favorites: ListResponse<FavoriteRankItem>
}

export interface CollectionItem {
  id: number
  user_id: number
  anime: AnimeSummary
  collection_status: CollectionStatus
  added_at: string
  updated_at: string
}

export interface FavoriteRankItem {
  id: number
  user_id: number
  anime: AnimeSummary
  rank_order: number
  created_at: string
  updated_at: string
}

export interface LoginPayload {
  account: string
  password: string
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
  display_name?: string
}

export interface PasswordResetRequestPayload {
  email: string
}

export interface PasswordResetConfirmPayload {
  token: string
  password: string
}

export interface PasswordResetRequestResponse {
  message: string
  dev_reset_token?: string | null
}

export interface AuthSession {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  user: UserProfile
  dashboard?: UserDashboard | null
}

export interface SearchAnimeParams {
  q: string
  page?: number
  page_size?: number
}

export interface AnimeSuggestion {
  id: number
  title: string
}

export interface AddCollectionPayload {
  anime_id?: number
  source_id?: string
  collection_status: CollectionStatus
}

export interface UpdateCollectionPayload {
  collection_status: CollectionStatus
}

export interface UpdateFavoriteRankPayload {
  items: Array<{
    anime_id: number
    rank_order: number
  }>
}

export interface UpdateProfilePayload {
  display_name: string
  birthday: string | null
  bio: string
  avatar_url?: string
  background_image_url?: string
}
