export interface GlossaryItem {
  word: string;
  variants: string[];
  definition: string;
  emojis: string[];
}

export type SectionType = 
  | 'separator'
  | 'other'
  | 'text_and_images'
  | 'activity_multiple_choice'
  | 'activity_fill_in_the_blank'
  | 'activity_true_false'
  | 'activity_matching'
  | 'activity_short_answer'
  | 'activity_essay'
  | 'back_cover'
  | 'credits';

export interface PlateText {
  text_id: string;
  text: string;
}

export interface PlateImage {
  image_id: string;
  upath: string;
  caption_id?: string | null;
  caption?: string | null;
}

export interface PlateSection {
  section_id: string;
  section_type: SectionType;
  page_image_upath: string;
  part_ids: string[];
  explanation_id?: string | null;
  explanation?: string;
  easy_read?: string;
  glossary: GlossaryItem[];
  background_color?: string | null;
  text_color?: string | null;
  layout_type?: string | null;
}

export interface Plate {
  title: string;
  language_code: string;
  sections: PlateSection[];
  images: PlateImage[];
  texts: PlateText[];
  glossary?: GlossaryItem[];
  pages?: PlatePage[];
}

export interface PlatePage {
  page_id: string;
  page_number: number;
  image_upath: string;
  section_ids: string[];
  section_count: number;
  text_count: number;
  image_count: number;
}
