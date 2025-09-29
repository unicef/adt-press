import React, { useState, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Plate } from '../types/plate';

interface ImageStatusProps {
  plate: Plate;
}

const resolveImageSrc = (originalSrc: string) => {
  if (!originalSrc || typeof originalSrc !== 'string') {
    return '';
  }

  if (originalSrc.startsWith('http') || originalSrc.startsWith('data:')) {
    return originalSrc;
  }

  if (originalSrc.startsWith('/')) {
    return originalSrc;
  }

  if (originalSrc.startsWith('output/')) {
    return `/${originalSrc}`;
  }

  return originalSrc;
};

export const ImageStatus: React.FC<ImageStatusProps> = ({ plate }) => {
  const [imageStatus, setImageStatus] = useState<'checking' | 'available' | 'unavailable'>('checking');
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const candidatePaths = [
      ...(plate.sections?.map(section => section.page_image_upath) ?? []),
      ...(plate.images?.map(image => image.upath) ?? []),
    ]
      .filter((path): path is string => Boolean(path))
      .map(path => resolveImageSrc(path));

    if (candidatePaths.length === 0) {
      setImageStatus('available');
      return;
    }

    setImageStatus('checking');

    const checkPath = (index: number) => {
      if (cancelled) return;
      if (index >= candidatePaths.length) {
        setImageStatus('unavailable');
        return;
      }

      const img = new Image();
      img.onload = () => {
        if (!cancelled) {
          setImageStatus('available');
        }
      };
      img.onerror = () => {
        if (!cancelled) {
          checkPath(index + 1);
        }
      };
      img.src = candidatePaths[index];
    };

    checkPath(0);

    return () => {
      cancelled = true;
    };
  }, [plate]);

  if (dismissed || imageStatus !== 'unavailable') return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg border transition-all duration-300 bg-amber-50 border-amber-200 text-amber-800">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 pt-0.5">
          <AlertCircle className="h-5 w-5" />
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">Images may not load properly</p>
          <p className="text-xs mt-1 opacity-75">
            Make sure the ADT output directory is accessible from the plate editor.
          </p>
        </div>
        
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 p-1 hover:bg-black hover:bg-opacity-10 rounded"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
