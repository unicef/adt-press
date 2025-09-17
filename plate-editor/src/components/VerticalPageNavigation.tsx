import React from 'react';
import { ChevronUp, ChevronDown, FileText } from 'lucide-react';
import { PageGroup } from '../hooks/usePageNavigation';
import { ImageDisplay } from './ImageDisplay';
import clsx from 'clsx';

interface VerticalPageNavigationProps {
  pageGroups: PageGroup[];
  currentPage: number;
  onPageChange: (pageNumber: number) => void;
  totalSections: number;
}

export const VerticalPageNavigation: React.FC<VerticalPageNavigationProps> = ({
  pageGroups,
  currentPage,
  onPageChange,
  totalSections,
}) => {
  const currentPageGroup = pageGroups.find(p => p.pageNumber === currentPage);
  
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < pageGroups.length;

  return (
    <div className="fixed left-4 top-20 z-10 w-64 bg-white rounded-lg shadow-lg border max-h-[calc(100vh-6rem)] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 rounded-t-lg">
        <div className="flex items-center space-x-2 mb-2">
          <FileText className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-semibold text-gray-900">Pages</span>
        </div>
        <div className="text-xs text-gray-600">
          {totalSections} total sections across {pageGroups.length} pages
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-between p-3 border-b">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!canGoPrev}
          className={clsx(
            'p-1 rounded transition-colors',
            canGoPrev
              ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              : 'text-gray-300 cursor-not-allowed'
          )}
          title="Previous page"
        >
          <ChevronUp className="h-4 w-4" />
        </button>
        
        <div className="text-center">
          <div className="text-sm font-medium text-gray-900">Page {currentPage}</div>
          <div className="text-xs text-gray-500">of {pageGroups.length}</div>
        </div>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          className={clsx(
            'p-1 rounded transition-colors',
            canGoNext
              ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              : 'text-gray-300 cursor-not-allowed'
          )}
          title="Next page"
        >
          <ChevronDown className="h-4 w-4" />
        </button>
      </div>

      {/* Current Page Preview */}
      {currentPageGroup && (
        <div className="p-3 border-b bg-blue-50">
          <div className="text-center mb-2">
            <div className="text-lg font-bold text-blue-600">
              {currentPageGroup.sectionCount}
            </div>
            <div className="text-xs text-blue-800">
              sections on this page
            </div>
          </div>
          
          {currentPageGroup.pageImagePath && (
            <div className="relative">
              <div className="w-full h-32 rounded-lg overflow-hidden border border-blue-200 bg-white">
                <ImageDisplay
                  src={currentPageGroup.pageImagePath}
                  alt={`Page ${currentPage} preview`}
                  showCaption={false}
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
                Page {currentPage}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Page List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {pageGroups.map((page) => (
            <button
              key={page.pageId}
              onClick={() => onPageChange(page.pageNumber)}
              className={clsx(
                'w-full text-left p-3 rounded-lg transition-all duration-200 border',
                page.pageNumber === currentPage
                  ? 'bg-blue-100 border-blue-200 text-blue-900'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={clsx(
                    'w-6 h-6 rounded flex items-center justify-center text-xs font-medium',
                    page.pageNumber === currentPage
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  )}>
                    {page.pageNumber}
                  </div>
                  <div>
                    <div className="text-sm font-medium">
                      Page {page.pageNumber}
                    </div>
                    <div className="text-xs text-gray-500">
                      {page.sectionCount} section{page.sectionCount !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
                
                {page.pageNumber === currentPage && (
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                )}
              </div>
              
              {/* Section types preview */}
              <div className="mt-2 flex flex-wrap gap-1">
                {page.sections.slice(0, 3).map((section) => (
                  <span
                    key={section.section_id}
                    className={clsx(
                      'px-1.5 py-0.5 text-xs rounded',
                      page.pageNumber === currentPage
                        ? 'bg-blue-200 text-blue-800'
                        : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    {section.section_type.replace(/_/g, ' ').substring(0, 8)}
                  </span>
                ))}
                {page.sections.length > 3 && (
                  <span className={clsx(
                    'px-1.5 py-0.5 text-xs rounded',
                    page.pageNumber === currentPage
                      ? 'bg-blue-200 text-blue-700'
                      : 'bg-gray-100 text-gray-500'
                  )}>
                    +{page.sections.length - 3}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="p-3 border-t bg-gray-50 rounded-b-lg">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="text-center">
            <div className="font-medium text-gray-900">
              {pageGroups.slice(0, currentPage).reduce((acc, p) => acc + p.sectionCount, 0)}
            </div>
            <div className="text-gray-500">sections before</div>
          </div>
          <div className="text-center">
            <div className="font-medium text-gray-900">
              {pageGroups.slice(currentPage).reduce((acc, p) => acc + p.sectionCount, 0)}
            </div>
            <div className="text-gray-500">sections after</div>
          </div>
        </div>
      </div>
    </div>
  );
};