import React, { useCallback, useState } from 'react';
import { Upload, FileText, Sparkles } from 'lucide-react';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  loading?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onFileSelect, loading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => prev + 1);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => prev - 1);
    if (dragCounter === 1) {
      setIsDragOver(false);
    }
  }, [dragCounter]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setDragCounter(0);
    
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/json' || file.name.endsWith('.json'))) {
      onFileSelect(file);
    } else {
      alert('Please upload a JSON file (.json)');
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[500px] p-8">
      {/* Hero Section */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <div className="relative">
            <FileText className="h-16 w-16 text-blue-600" />
            <Sparkles className="h-6 w-6 text-yellow-500 absolute -top-1 -right-1 animate-pulse" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          ADT Plate Editor
        </h2>
        <p className="text-lg text-gray-600 max-w-md">
          Transform your ADT plate files with an intuitive visual editor. 
          Drag, drop, edit, and perfect your content.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={`
          w-full max-w-lg p-12 border-2 border-dashed rounded-2xl text-center transition-all-smooth cursor-pointer
          ${isDragOver 
            ? 'border-blue-500 bg-blue-50 scale-105 shadow-lg' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/30'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onClick={() => !loading && document.getElementById('file-upload')?.click()}
      >
        <div className={`transition-all-smooth ${isDragOver ? 'scale-110' : ''}`}>
          <Upload className={`
            mx-auto h-16 w-16 mb-6 transition-all-smooth
            ${isDragOver ? 'text-blue-600 animate-bounce' : 'text-gray-400'}
          `} />
          
          <h3 className="text-xl font-semibold text-gray-900 mb-3">
            {isDragOver ? 'Drop your plate file here' : 'Upload Plate File'}
          </h3>
          
          <p className="text-gray-500 mb-6 leading-relaxed">
            {isDragOver 
              ? 'Release to load your file'
              : 'Drag and drop a plate.json file here, or click to browse'
            }
          </p>
          
          <input
            type="file"
            accept=".json,application/json"
            onChange={handleFileInput}
            className="hidden"
            id="file-upload"
            disabled={loading}
          />
          
          <div className="space-y-3">
            <button
              type="button"
              disabled={loading}
              className={`
                btn-primary inline-flex items-center space-x-2 text-base px-6 py-3
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {loading ? (
                <>
                  <div className="animate-spin-slow h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  <span>Loading...</span>
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  <span>Choose File</span>
                </>
              )}
            </button>
            
            <p className="text-xs text-gray-400">
              Supports: .json files from ADT processing
            </p>
          </div>
        </div>
      </div>

      {/* Features Preview */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
        <div className="text-center p-4">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <span className="text-xl">🎯</span>
          </div>
          <h4 className="font-medium text-gray-900 mb-1">Visual Editing</h4>
          <p className="text-sm text-gray-600">Edit content with intuitive forms and live previews</p>
        </div>
        
        <div className="text-center p-4">
          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <span className="text-xl">🔄</span>
          </div>
          <h4 className="font-medium text-gray-900 mb-1">Drag & Drop</h4>
          <p className="text-sm text-gray-600">Reorder sections effortlessly with drag and drop</p>
        </div>
        
        <div className="text-center p-4">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <span className="text-xl">📊</span>
          </div>
          <h4 className="font-medium text-gray-900 mb-1">Smart Pagination</h4>
          <p className="text-sm text-gray-600">Navigate large documents with ease</p>
        </div>
      </div>
    </div>
  );
};