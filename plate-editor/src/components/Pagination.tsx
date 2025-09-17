import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  hasNext: boolean;
  hasPrev: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  hasNext,
  hasPrev,
}) => {
  const getVisiblePages = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];

    for (
      let i = Math.max(2, currentPage - delta);
      i <= Math.min(totalPages - 1, currentPage + delta);
      i++
    ) {
      range.push(i);
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else if (totalPages > 1) {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  };

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center space-x-2 py-4">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={!hasPrev}
        className={clsx(
          'p-2 rounded-md',
          hasPrev
            ? 'text-gray-700 hover:bg-gray-100'
            : 'text-gray-400 cursor-not-allowed'
        )}
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {getVisiblePages().map((page, index) => (
        <button
          key={index}
          onClick={() => typeof page === 'number' && onPageChange(page - 1)}
          disabled={typeof page !== 'number'}
          className={clsx(
            'px-3 py-2 text-sm rounded-md',
            typeof page === 'number' && page === currentPage + 1
              ? 'bg-blue-600 text-white'
              : typeof page === 'number'
              ? 'text-gray-700 hover:bg-gray-100'
              : 'text-gray-400 cursor-default'
          )}
        >
          {page}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={!hasNext}
        className={clsx(
          'p-2 rounded-md',
          hasNext
            ? 'text-gray-700 hover:bg-gray-100'
            : 'text-gray-400 cursor-not-allowed'
        )}
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
};