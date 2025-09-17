import React from 'react';
import { Plate } from '../types/plate';
import { FileText, Image, Type, Globe } from 'lucide-react';

interface PlateOverviewProps {
  plate: Plate;
  onUpdateTitle: (title: string) => void;
  onUpdateLanguage: (language: string) => void;
}

export const PlateOverview: React.FC<PlateOverviewProps> = ({
  plate,
  onUpdateTitle,
  onUpdateLanguage,
}) => {
  const stats = {
    sections: plate.sections.length,
    images: plate.images.length,
    texts: plate.texts.length,
    glossaryTerms: plate.sections.reduce((acc, section) => acc + section.glossary.length, 0),
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Document Information
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title
              </label>
              <input
                type="text"
                value={plate.title}
                onChange={(e) => onUpdateTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language Code
              </label>
              <input
                type="text"
                value={plate.language_code}
                onChange={(e) => onUpdateLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., en, es, fr"
              />
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Content Statistics
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-blue-900">Sections</p>
                <p className="text-lg font-semibold text-blue-900">{stats.sections}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
              <div className="flex-shrink-0">
                <Image className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-green-900">Images</p>
                <p className="text-lg font-semibold text-green-900">{stats.images}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
              <div className="flex-shrink-0">
                <Type className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-purple-900">Text Blocks</p>
                <p className="text-lg font-semibold text-purple-900">{stats.texts}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-amber-50 rounded-lg">
              <div className="flex-shrink-0">
                <Globe className="h-6 w-6 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-amber-900">Glossary Terms</p>
                <p className="text-lg font-semibold text-amber-900">{stats.glossaryTerms}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};