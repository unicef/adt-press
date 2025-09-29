import React, { useState } from 'react';
import { History, X, RotateCcw, Save, ChevronDown, ChevronRight } from 'lucide-react';
import { Change } from '../hooks/useChangeTracking';
import clsx from 'clsx';

interface ChangesPanelProps {
  changes: Change[];
  changesSummary: {
    total: number;
    edits: number;
    reorders: number;
    metadata: number;
  };
  onSave: () => void;
  onClearChanges: () => void;
  isOpen: boolean;
  onToggle: () => void;
  floating?: boolean;
}

const getChangeIcon = (type: string) => {
  const icons = {
    edit: '✏️',
    reorder: '🔄',
    title: '📝',
    language: '🌐',
    delete: '🗑️',
    add: '➕',
    merge: '🔗',
  };
  return icons[type as keyof typeof icons] || '📝';
};

const formatTime = (timestamp: number) => {
  const now = Date.now();
  const diff = now - timestamp;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return new Date(timestamp).toLocaleDateString();
};

export const ChangesPanel: React.FC<ChangesPanelProps> = ({
  changes,
  changesSummary,
  onSave,
  onClearChanges,
  isOpen,
  onToggle,
  floating = true,
}) => {
  const [showAllChanges, setShowAllChanges] = useState(false);
  
  const displayedChanges = showAllChanges ? changes : changes.slice(0, 5);
  const hasChanges = changesSummary.total > 0;

  return (
    <div className={floating ? 'fixed right-4 top-20 z-20 w-80' : 'w-full'}>
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className={clsx(
          'flex items-center justify-between w-full p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition-all duration-200',
          hasChanges && 'border-amber-200 bg-amber-50',
          isOpen && 'rounded-b-none border-b-0'
        )}
      >
        <div className="flex items-center space-x-2">
          <History className={clsx('h-4 w-4', hasChanges ? 'text-amber-600' : 'text-gray-400')} />
          <span className={clsx('text-sm font-medium', hasChanges ? 'text-amber-900' : 'text-gray-700')}>
            Changes ({changesSummary.total})
          </span>
          {hasChanges && (
            <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
          )}
        </div>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>

      {/* Panel Content */}
      {isOpen && (
        <div className="bg-white border border-t-0 rounded-b-lg shadow-lg max-h-96 flex flex-col">
          {hasChanges ? (
            <>
              {/* Summary */}
              <div className="p-3 border-b bg-gray-50">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Edits:</span>
                    <span className="font-medium">{changesSummary.edits}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Reorders:</span>
                    <span className="font-medium">{changesSummary.reorders}</span>
                  </div>
                </div>
              </div>

              {/* Changes List */}
              <div className="flex-1 overflow-y-auto max-h-48">
                {displayedChanges.map((change) => (
                  <div
                    key={change.id}
                    className="p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-sm flex-shrink-0 mt-0.5">
                        {getChangeIcon(change.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 line-clamp-2">
                          {change.description}
                        </p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-gray-500">
                            {formatTime(change.timestamp)}
                          </span>
                          {change.sectionId && (
                            <span className="text-xs text-blue-600 font-mono">
                              {change.sectionId}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {changes.length > 5 && (
                  <button
                    onClick={() => setShowAllChanges(!showAllChanges)}
                    className="w-full p-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 transition-colors"
                  >
                    {showAllChanges ? 'Show less' : `Show ${changes.length - 5} more changes`}
                  </button>
                )}
              </div>

              {/* Actions */}
              <div className="p-3 border-t bg-gray-50 flex space-x-2">
                <button
                  onClick={onSave}
                  className="flex-1 btn-primary text-xs py-2 px-3"
                >
                  <Save className="h-3 w-3 mr-1" />
                  Export Changes
                </button>
                <button
                  onClick={onClearChanges}
                  className="btn-secondary text-xs py-2 px-3"
                  title="Clear change history"
                >
                  <RotateCcw className="h-3 w-3" />
                </button>
              </div>
            </>
          ) : (
            <div className="p-6 text-center">
              <History className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-1">No changes yet</p>
              <p className="text-xs text-gray-400">
                Edits will be tracked here
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
