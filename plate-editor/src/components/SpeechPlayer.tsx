import React, { useMemo, useState, useEffect } from 'react';
import { Volume2 } from 'lucide-react';

interface SpeechPlayerProps {
  textId: string;
  audioBasePath: string | null;
  languages: string[];
}

const buildAudioSrc = (audioBasePath: string, language: string, textId: string) => {
  const normalizedLanguage = language.toLowerCase();
  const prefix = audioBasePath.startsWith('/') ? audioBasePath : `/${audioBasePath}`;
  return `${prefix}/audio/${normalizedLanguage}/${textId}_${normalizedLanguage}.mp3`;
};

export const SpeechPlayer: React.FC<SpeechPlayerProps> = ({ textId, audioBasePath, languages }) => {
  const validLanguages = useMemo(
    () => languages.filter(Boolean),
    [languages]
  );

  const [failedLanguages, setFailedLanguages] = useState<string[]>([]);

  const playableLanguages = useMemo(
    () => validLanguages.filter(language => !failedLanguages.includes(language)),
    [failedLanguages, validLanguages]
  );

  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(
    playableLanguages.length > 0 ? playableLanguages[0] : null
  );

  useEffect(() => {
    if (playableLanguages.length === 0) {
      setSelectedLanguage(null);
      return;
    }
    if (!selectedLanguage || !playableLanguages.includes(selectedLanguage)) {
      setSelectedLanguage(playableLanguages[0]);
    }
  }, [playableLanguages, selectedLanguage]);

  if (!audioBasePath || playableLanguages.length === 0 || !selectedLanguage) {
    return null;
  }

  const audioSrc = buildAudioSrc(audioBasePath, selectedLanguage, textId);

  const handlePlaybackError = () => {
    setFailedLanguages(prev => (prev.includes(selectedLanguage) ? prev : [...prev, selectedLanguage]));
  };

  return (
    <div className="mt-2 space-y-2">
      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center gap-1 font-medium text-gray-700">
          <Volume2 className="h-3.5 w-3.5" />
          <span>Listen</span>
        </div>
        {playableLanguages.length > 1 && (
          <select
            value={selectedLanguage}
            onChange={event => setSelectedLanguage(event.target.value)}
            className="text-xs border border-gray-300 rounded px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            aria-label={`Select TTS language for ${textId}`}
          >
            {playableLanguages.map(language => (
              <option key={language} value={language}>
                {language.toUpperCase()}
              </option>
            ))}
          </select>
        )}
      </div>
      <audio
        key={`${textId}-${selectedLanguage}`}
        controls
        className="w-full"
        src={audioSrc}
        onError={handlePlaybackError}
      >
        Your browser does not support the audio element.
      </audio>
    </div>
  );
};
