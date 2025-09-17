import React from 'react';
import { Save, FileText, Settings } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
  onSave?: () => void;
  hasChanges?: boolean;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  title, 
  onSave, 
  hasChanges 
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50/30">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-white/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="relative">
                <FileText className="h-8 w-8 text-blue-600 mr-3" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  ADT Plate Editor
                </h1>
                <p className="text-sm text-gray-600 font-medium">{title}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              {hasChanges && (
                <div className="flex items-center space-x-2 text-amber-600">
                  <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Unsaved changes</span>
                </div>
              )}
              {onSave && (
                <button
                  onClick={onSave}
                  className="btn-primary inline-flex items-center space-x-2"
                >
                  <Save className="h-4 w-4" />
                  <span>Export Changes</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="transition-all-smooth">
          {children}
        </div>
      </main>
    </div>
  );
};