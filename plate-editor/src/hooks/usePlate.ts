import { useState, useCallback } from 'react';
import { Plate, PlateImage, PlateSection } from '../types/plate';

const buildAudioPath = (basePath: string, language: string, textId: string) => {
  const normalizedLanguage = language.toLowerCase();
  const prefix = basePath.startsWith('/') ? basePath : `/${basePath}`;
  return `${prefix}/audio/${normalizedLanguage}/${textId}_${normalizedLanguage}.mp3`;
};

const deriveAssetBasePath = (plate: Plate): string | null => {
  const candidates = [
    plate.pages?.[0]?.image_upath,
    plate.sections?.[0]?.page_image_upath,
    plate.images?.[0]?.upath,
  ];

  for (const candidate of candidates) {
    if (!candidate) continue;
    const normalized = candidate.replace(/\\/g, '/');
    const imagesIndex = normalized.indexOf('/images/');
    if (imagesIndex !== -1) {
      return normalized.slice(0, imagesIndex);
    }
  }

  return null;
};

const parseOutputLanguages = (configText: string): string[] => {
  const inlineMatch = configText.match(/output_languages:\s*\[([^\]]*)\]/);
  if (inlineMatch) {
    return inlineMatch[1]
      .split(',')
      .map(entry => entry.trim().replace(/^['"]|['"]$/g, ''))
      .filter(Boolean);
  }

  const lines = configText.split(/\r?\n/);
  const languages: string[] = [];
  let capturing = false;
  for (const line of lines) {
    if (!capturing && line.trim().startsWith('output_languages:')) {
      const remainder = line.split(':')[1]?.trim();
      if (remainder && remainder.startsWith('[')) {
        // already handled inline case
        continue;
      }
      capturing = true;
      continue;
    }

    if (capturing) {
      const trimmed = line.trim();
      if (trimmed.startsWith('-')) {
        languages.push(trimmed.slice(1).trim().replace(/^['"]|['"]$/g, ''));
      } else if (trimmed === '' || trimmed.startsWith('#')) {
        continue;
      } else if (!line.startsWith(' ')) {
        break;
      }
    }
  }

  return languages.filter(Boolean);
};

const normalizeSection = (section: PlateSection): PlateSection => ({
  ...section,
  explanation: section.explanation ?? '',
  easy_read: section.easy_read ?? '',
  glossary: section.glossary ?? [],
});

const normalizeImage = (image: PlateImage): PlateImage => ({
  ...image,
  caption: image.caption ?? '',
});

const normalizePlateData = (plate: Plate): Plate => ({
  ...plate,
  sections: plate.sections.map(normalizeSection),
  images: plate.images.map(normalizeImage),
  glossary: plate.glossary ?? [],
  pages: plate.pages ?? [],
});

export const usePlate = () => {
  const [plate, setPlate] = useState<Plate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioBasePath, setAudioBasePath] = useState<string | null>(null);
  const [audioLanguages, setAudioLanguages] = useState<string[]>([]);

  const detectAudioLanguages = useCallback(
    async (normalizedPlate: Plate) => {
      const basePath = deriveAssetBasePath(normalizedPlate);
      if (!basePath) {
        setAudioBasePath(null);
        setAudioLanguages([]);
        return;
      }

      setAudioBasePath(basePath);

      const sampleTextId = normalizedPlate.texts?.[0]?.text_id;
      const configPath = `${basePath.startsWith('/') ? basePath : `/${basePath}`}/config.yaml`;
      let languages: string[] = [];

      try {
        const response = await fetch(configPath);
        if (response.ok) {
          const configText = await response.text();
          languages = parseOutputLanguages(configText);
        }
      } catch (err) {
        // ignore fetch errors; we'll fallback to plate language
      }

      if (languages.length === 0 && normalizedPlate.language_code) {
        languages = [normalizedPlate.language_code];
      }

      languages = Array.from(new Set(languages.filter(Boolean)));

      if (!sampleTextId) {
        setAudioLanguages(languages);
        return;
      }

      const verified: string[] = [];
      await Promise.all(
        languages.map(async language => {
          const audioSrc = buildAudioPath(basePath, language, sampleTextId);
          try {
            const response = await fetch(audioSrc, { method: 'HEAD' });
            if (response.ok) {
              verified.push(language);
            }
          } catch (err) {
            // ignore network errors
          }
        })
      );

      setAudioLanguages(verified.length > 0 ? verified : languages);
    },
    []
  );

  const loadPlate = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      const text = await file.text();
      const plateData = JSON.parse(text) as Plate;
      const normalized = normalizePlateData(plateData);
      setPlate(normalized);
      detectAudioLanguages(normalized);
    } catch (err) {
      setError('Failed to parse plate file: ' + (err as Error).message);
      setAudioBasePath(null);
      setAudioLanguages([]);
    } finally {
      setLoading(false);
    }
  }, [detectAudioLanguages]);

  const savePlate = useCallback(() => {
    if (!plate) return;
    
    const dataStr = JSON.stringify(plate, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `${plate.title}-edited.json`;
    link.click();
  }, [plate]);

  const updatePlate = useCallback((updater: (plate: Plate) => Plate) => {
    setPlate(prev => prev ? updater(prev) : null);
  }, []);

  return {
    plate,
    loading,
    error,
    loadPlate,
    savePlate,
    updatePlate,
    setPlate,
    audioBasePath,
    audioLanguages,
  };
};
