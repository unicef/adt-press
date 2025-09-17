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
  caption: string;
}

export interface PlateSection {
  section_id: string;
  section_type: SectionType;
  page_image_upath: string;
  part_ids: string[];
  explanation: string;
  easy_read: string;
  glossary: GlossaryItem[];
}

export interface Plate {
  title: string;
  language_code: string;
  sections: PlateSection[];
  images: PlateImage[];
  texts: PlateText[];
}