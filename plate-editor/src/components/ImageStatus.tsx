import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, Loader, X } from 'lucide-react';

export const ImageStatus: React.FC = () => {
  const [imageStatus, setImageStatus] = useState<'checking' | 'available' | 'unavailable'>('checking');
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Test if images are accessible
    const testImage = new Image();
    testImage.onload = () => setImageStatus('available');
    testImage.onerror = () => setImageStatus('unavailable');
    testImage.src = '/output/chess_run/images/img_p1.png';
  }, []);

  if (dismissed) return null;

  return (
    <div className={`
      fixed bottom-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg border transition-all duration-300
      ${imageStatus === 'available' 
        ? 'bg-green-50 border-green-200 text-green-800' 
        : imageStatus === 'unavailable'
        ? 'bg-amber-50 border-amber-200 text-amber-800'
        : 'bg-blue-50 border-blue-200 text-blue-800'
      }
    `}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 pt-0.5">
          {imageStatus === 'checking' && <Loader className="h-5 w-5 animate-spin" />}
          {imageStatus === 'available' && <CheckCircle className="h-5 w-5" />}
          {imageStatus === 'unavailable' && <AlertCircle className="h-5 w-5" />}
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">
            {imageStatus === 'checking' && 'Checking image access...'}
            {imageStatus === 'available' && 'Images are loading correctly!'}
            {imageStatus === 'unavailable' && 'Images may not load properly'}
          </p>
          {imageStatus === 'unavailable' && (
            <p className="text-xs mt-1 opacity-75">
              Make sure the ADT output directory is accessible from the plate editor.
            </p>
          )}
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