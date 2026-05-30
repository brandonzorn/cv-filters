export interface DragonflyResponse {
  id: number;
  species_name: string;
  gender: string | null;
  created_at: string;
}

export interface ImageResponse {
  id: number;
  original_url: string;
  processed_url: string;
  thumbnail_url: string;
  filter_type: string;
  created_at: string;
  dragonfly: DragonflyResponse;
}