import React, { useState } from 'react';
import { ZoomIn, ExternalLink, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

interface ImageDisplayProps {
  src: string;
  alt: string;
  caption?: string;
  className?: string;
  showCaption?: boolean;
}

export const ImageDisplay: React.FC<ImageDisplayProps> = ({
  src,
  alt,
  caption,
  className = '',
  showCaption = true,
}) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [showFullsize, setShowFullsize] = useState(false);

  // Try to resolve the image path - for local development, we need to handle relative paths
  const getImageSrc = (originalSrc: string) => {
    // Handle undefined/null/empty strings
    if (!originalSrc || typeof originalSrc !== 'string') {
      return '';
    }
    
    // If it's already a full URL, use it as is
    if (originalSrc.startsWith('http') || originalSrc.startsWith('data:')) {
      return originalSrc;
    }
    
    // For local development with Vite alias
    if (originalSrc.startsWith('output/')) {
      return `/${originalSrc}`;
    }
    
    return originalSrc;
  };

  const handleImageLoad = () => {
    setLoaded(true);
    setError(false);
  };

  const handleImageError = () => {
    setError(true);
    setLoaded(false);
  };

  const openFullsize = () => {
    setShowFullsize(true);
  };

  const closeFullsize = () => {
    setShowFullsize(false);
  };

  return (
    <>
      <div className={`relative group ${className}`}>
        {/* Loading placeholder */}
        {!loaded && !error && (
          <div className="w-full h-32 bg-gray-100 rounded-lg flex items-center justify-center animate-pulse">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="w-full h-32 bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg flex flex-col items-center justify-center text-gray-400">
            <AlertTriangle className="w-6 h-6 mb-2" />
            <span className="text-sm font-medium">Image not accessible</span>
            <span className="text-xs text-gray-500 mt-1 px-2 text-center break-all">
              {getImageSrc(src)}
            </span>
            <button
              onClick={() => window.open(getImageSrc(src), '_blank')}
              className="text-xs text-blue-500 hover:text-blue-700 mt-2 underline"
            >
              Try to open directly
            </button>
          </div>
        )}

        {/* Image */}
        <div className={`relative ${loaded ? 'fade-in' : 'hidden'}`}>
          <img
            src={getImageSrc(src)}
            alt={alt}
            onLoad={handleImageLoad}
            onError={handleImageError}
            className={clsx(
              "w-full rounded-lg shadow-sm hover:shadow-md transition-all duration-200",
              className?.includes('h-') ? "h-full object-cover" : "h-auto"
            )}
          />
          
          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="flex space-x-2">
              <button
                onClick={openFullsize}
                className="bg-white bg-opacity-90 hover:bg-opacity-100 p-2 rounded-full shadow-lg transition-all duration-200"
                title="View fullsize"
              >
                <ZoomIn className="w-4 h-4 text-gray-700" />
              </button>
              <button
                onClick={() => window.open(getImageSrc(src), '_blank')}
                className="bg-white bg-opacity-90 hover:bg-opacity-100 p-2 rounded-full shadow-lg transition-all duration-200"
                title="Open in new tab"
              >
                <ExternalLink className="w-4 h-4 text-gray-700" />
              </button>
            </div>
          </div>
        </div>

        {/* Caption */}
        {showCaption && caption && loaded && (
          <p className="text-sm text-gray-600 mt-2 leading-relaxed">
            {caption}
          </p>
        )}
      </div>

      {/* Fullsize modal */}
      {showFullsize && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={closeFullsize}
        >
          <div
            className="relative max-w-7xl max-h-full"
            onClick={event => event.stopPropagation()}
          >
            <button
              onClick={closeFullsize}
              className="absolute top-4 right-4 text-white bg-black/60 hover:bg-black/80 rounded-full p-2 transition-colors"
              aria-label="Close image preview"
            >
              ✕
            </button>
            <img
              src={getImageSrc(src)}
              alt={alt}
              className="max-w-full max-h-full object-contain rounded-lg"
            />
            {caption && (
              <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white p-4 rounded-b-lg">
                <p className="text-sm">{caption}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
