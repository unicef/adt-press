import React from 'react';
import { PlatePage, PlateSection } from '../types/plate';
import { ImageDisplay } from './ImageDisplay';
import { FileText, Image as ImageIcon, ListOrdered } from 'lucide-react';

interface PageSummaryCardProps {
  page: PlatePage;
  sections: PlateSection[];
}

export const PageSummaryCard: React.FC<PageSummaryCardProps> = ({ page, sections }) => {
  const visibleSections = sections.slice(0, 5);
  const additionalSections = Math.max(0, sections.length - visibleSections.length);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Page {page.page_number} Overview</h3>
        <span className="text-xs text-gray-500">{page.page_id}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs mb-4">
        <div className="flex items-center gap-2 bg-blue-50 text-blue-700 px-2 py-1 rounded">
          <ListOrdered className="h-4 w-4" />
          <span>{page.section_count} section{page.section_count === 1 ? '' : 's'}</span>
        </div>
        <div className="flex items-center gap-2 bg-purple-50 text-purple-700 px-2 py-1 rounded">
          <FileText className="h-4 w-4" />
          <span>{page.text_count} text{page.text_count === 1 ? '' : 's'}</span>
        </div>
        <div className="flex items-center gap-2 bg-green-50 text-green-700 px-2 py-1 rounded">
          <ImageIcon className="h-4 w-4" />
          <span>{page.image_count} image{page.image_count === 1 ? '' : 's'}</span>
        </div>
      </div>

      {page.image_upath && (
        <div className="mb-4">
          <ImageDisplay
            src={page.image_upath}
            alt={`Page ${page.page_number} preview`}
            className="rounded border"
            showCaption={false}
          />
        </div>
      )}

      <div>
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Sections on this page</h4>
        <ul className="space-y-1">
          {visibleSections.map(section => (
            <li
              key={section.section_id}
              className="flex items-center justify-between text-xs bg-gray-50 rounded px-2 py-1"
            >
              <span className="font-medium text-gray-700">{section.section_id}</span>
              <span className="text-gray-500">{section.section_type}</span>
            </li>
          ))}
        </ul>
        {additionalSections > 0 && (
          <div className="text-xs text-gray-500 mt-2">
            +{additionalSections} more section{additionalSections === 1 ? '' : 's'} on this page
          </div>
        )}
      </div>
    </div>
  );
};

