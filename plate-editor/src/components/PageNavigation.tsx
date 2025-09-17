import React from 'react';
import { ChevronLeft, ChevronRight, FileText, Image as ImageIcon } from 'lucide-react';
import { PageGroup } from '../hooks/usePageNavigation';
import { ImageDisplay } from './ImageDisplay';
import clsx from 'clsx';

interface PageNavigationProps {
  pageGroups: PageGroup[];
  currentPage: number;
  onPageChange: (pageNumber: number) => void;
  totalSections: number;
}

export const PageNavigation: React.FC<PageNavigationProps> = ({
  pageGroups,
  currentPage,
  onPageChange,
  totalSections,
}) => {
  const currentPageGroup = pageGroups.find(p => p.pageNumber === currentPage);
  
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < pageGroups.length;

  return (
    <div className="bg-white border-b border-gray-200 sticky top-16 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Page Info */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-900">
                Page {currentPage} of {pageGroups.length}
              </span>
            </div>
            
            {currentPageGroup && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>{currentPageGroup.sectionCount} sections</span>
                <span>•</span>
                <span>Section {pageGroups.slice(0, currentPage - 1).reduce((acc, p) => acc + p.sectionCount, 0) + 1}-{pageGroups.slice(0, currentPage).reduce((acc, p) => acc + p.sectionCount, 0)} of {totalSections}</span>
              </div>
            )}
          </div>

          {/* Page Navigation Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!canGoPrev}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                canGoPrev
                  ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  : 'text-gray-300 cursor-not-allowed'
              )}
              title="Previous page"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>

            {/* Page thumbnails/numbers */}
            <div className="flex items-center space-x-1">
              {pageGroups.map((page) => (
                <button
                  key={page.pageId}
                  onClick={() => onPageChange(page.pageNumber)}
                  className={clsx(
                    'relative px-3 py-2 text-sm rounded-lg transition-all duration-200',
                    page.pageNumber === currentPage
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  )}
                  title={`Page ${page.pageNumber} (${page.sectionCount} sections)`}
                >
                  <span className="relative z-10">{page.pageNumber}</span>
                  {page.pageNumber === currentPage && (
                    <div className="absolute inset-0 bg-blue-600 rounded-lg animate-pulse opacity-20"></div>
                  )}
                </button>
              ))}
            </div>

            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!canGoNext}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                canGoNext
                  ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  : 'text-gray-300 cursor-not-allowed'
              )}
              title="Next page"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Page Preview */}
        {currentPageGroup && currentPageGroup.pageImagePath && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-24 h-32 rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
                  <ImageDisplay
                    src={currentPageGroup.pageImagePath}
                    alt={`Page ${currentPage} preview`}
                    showCaption={false}
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-900 mb-1">
                  Page {currentPage} Content
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  {currentPageGroup.sectionCount} sections on this page
                </p>
                <div className="flex flex-wrap gap-1">
                  {currentPageGroup.sections.slice(0, 3).map((section) => (
                    <span
                      key={section.section_id}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      {section.section_type.replace(/_/g, ' ')}
                    </span>
                  ))}
                  {currentPageGroup.sections.length > 3 && (
                    <span className="px-2 py-1 text-xs text-gray-500">
                      +{currentPageGroup.sections.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};