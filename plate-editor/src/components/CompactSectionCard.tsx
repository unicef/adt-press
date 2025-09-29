import React from 'react';
import { PlateSection, PlateImage, PlateText } from '../types/plate';
import { GripVertical, Edit, Eye, Image, Type, AlertCircle, Trash2, Copy, Plus, Merge } from 'lucide-react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import clsx from 'clsx';
import { ImageDisplay } from './ImageDisplay';
import { SpeechPlayer } from './SpeechPlayer';

interface CompactSectionCardProps {
  section: PlateSection;
  images: PlateImage[];
  texts: PlateText[];
  onEdit: () => void;
  onPreview: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onMergeWithNext?: () => void;
  onAddAfter?: () => void;
  hasChanges?: boolean;
  canMergeWithNext?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
  audioBasePath: string | null;
  audioLanguages: string[];
}

const getSectionTypeColor = (type: string) => {
  const colors = {
    separator: 'bg-gray-100 text-gray-700 border-gray-200',
    text_and_images: 'bg-blue-50 text-blue-700 border-blue-200',
    activity_multiple_choice: 'bg-green-50 text-green-700 border-green-200',
    activity_fill_in_the_blank: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    other: 'bg-purple-50 text-purple-700 border-purple-200',
  };
  return colors[type as keyof typeof colors] || 'bg-gray-50 text-gray-700 border-gray-200';
};

export const CompactSectionCard: React.FC<CompactSectionCardProps> = ({
  section,
  images,
  texts,
  onEdit,
  onPreview,
  onDelete,
  onDuplicate,
  onMergeWithNext,
  onAddAfter,
  hasChanges = false,
  canMergeWithNext = false,
  isSelected = false,
  onSelect,
  audioBasePath,
  audioLanguages,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.section_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Get content for this section
  const sectionImages = images.filter(img => section.part_ids.includes(img.image_id));
  const sectionTexts = texts.filter(txt => section.part_ids.includes(txt.text_id));

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={clsx(
        'bg-white border rounded-lg shadow-sm hover:shadow-md transition-all duration-200 relative',
        isDragging && 'opacity-60 shadow-lg scale-105',
        hasChanges && 'ring-2 ring-amber-200 border-amber-300',
        isSelected && 'ring-2 ring-blue-300 border-blue-300 bg-blue-50'
      )}
    >
      {/* Change indicator */}
      {hasChanges && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full animate-pulse z-10"></div>
      )}

      <div className="p-4">
        <div 
          className="flex items-start gap-3"
          onClick={onSelect}
        >
          {/* Drag Handle */}
          <div
            {...attributes}
            {...listeners}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing rounded hover:bg-gray-100 transition-colors"
            title="Drag to reorder"
          >
            <GripVertical className="h-4 w-4" />
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={clsx(
                  'px-2 py-1 text-xs font-medium rounded-full border',
                  getSectionTypeColor(section.section_type)
                )}>
                  {section.section_type.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-gray-500 font-mono">
                  {section.section_id}
                </span>
              </div>
              
              {/* Content indicators */}
              <div className="flex items-center gap-1">
                {sectionImages.length > 0 && (
                  <div className="flex items-center text-xs text-gray-500">
                    <Image className="h-3 w-3 mr-1" />
                    {sectionImages.length}
                  </div>
                )}
                {sectionTexts.length > 0 && (
                  <div className="flex items-center text-xs text-gray-500">
                    <Type className="h-3 w-3 mr-1" />
                    {sectionTexts.length}
                  </div>
                )}
                {section.glossary.length > 0 && (
                  <div className="flex items-center text-xs text-blue-600">
                    📖 {section.glossary.length}
                  </div>
                )}
              </div>
            </div>

            {/* Editable Content Preview - Main Focus */}
            <div className="space-y-3">
              {/* Source Text - show original extracted content */}
              {sectionTexts.length > 0 && (
                <div className="border rounded-lg p-3 bg-gray-50 border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Type className="h-4 w-4 text-gray-500" />
                      <span>Source Text</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {sectionTexts.length} block{sectionTexts.length === 1 ? '' : 's'}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {sectionTexts.slice(0, 2).map(text => (
                      <div key={text.text_id} className="bg-white border border-gray-200 rounded-md p-2">
                        <div className="text-[11px] text-gray-500 font-mono mb-1">
                          {text.text_id}
                        </div>
                    <p className="text-sm text-gray-800 line-clamp-3 whitespace-pre-line">
                      {text.text}
                    </p>
                        <SpeechPlayer
                          textId={text.text_id}
                          audioBasePath={audioBasePath}
                          languages={audioLanguages}
                        />
                      </div>
                    ))}
                    {sectionTexts.length > 2 && (
                      <p className="text-xs text-gray-500">+{sectionTexts.length - 2} more text block{sectionTexts.length - 2 === 1 ? '' : 's'}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Explanation - Primary editable content */}
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-sm font-medium text-blue-900">Explanation</h4>
                  <button
                    onClick={onEdit}
                    className="text-blue-600 hover:text-blue-700 p-1 rounded hover:bg-blue-100 transition-colors"
                    title="Edit explanation"
                  >
                    <Edit className="h-3 w-3" />
                  </button>
                </div>
                <p className="text-sm text-blue-800 line-clamp-2 leading-relaxed">
                  {section.explanation || 'No explanation provided - click to add'}
                </p>
              </div>

              {/* Easy Read - Secondary editable content */}
              <div className="bg-green-50 rounded-lg p-3 border border-green-100">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-sm font-medium text-green-900">Easy Read</h4>
                  <button
                    onClick={onEdit}
                    className="text-green-600 hover:text-green-700 p-1 rounded hover:bg-green-100 transition-colors"
                    title="Edit easy read"
                  >
                    <Edit className="h-3 w-3" />
                  </button>
                </div>
                <p className="text-sm text-green-800 line-clamp-2 leading-relaxed">
                  {section.easy_read || 'No easy read version - click to add'}
                </p>
              </div>

              {/* Images - Show first few images in compact format */}
              {sectionImages.length > 0 && (
                <div className="border rounded-lg p-2 bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <Image className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">
                      Images ({sectionImages.length})
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {sectionImages.slice(0, 2).map((img) => (
                      <div key={img.image_id} className="relative h-32 overflow-hidden rounded border bg-white flex items-center justify-center">
                        <ImageDisplay
                          src={img.upath || ''}
                          alt={img.image_id || 'Section image'}
                          showCaption={false}
                          className="w-full h-32 object-contain"
                        />
                        {sectionImages.length > 2 && sectionImages.indexOf(img) === 1 && (
                          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded text-white text-xs font-medium">
                            +{sectionImages.length - 2} more
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex-shrink-0 flex flex-col gap-1">
            {/* Primary Actions */}
            <button
              onClick={onPreview}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Preview section"
            >
              <Eye className="h-4 w-4" />
            </button>
            <button
              onClick={onEdit}
              className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200 hover:border-blue-300"
              title="Edit section"
            >
              <Edit className="h-4 w-4" />
            </button>
            
            {/* Section Management Actions */}
            <div className="border-t pt-1 mt-1 space-y-1">
              {onDuplicate && (
                <button
                  onClick={onDuplicate}
                  className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                  title="Duplicate section"
                >
                  <Copy className="h-3 w-3" />
                </button>
              )}
              {onAddAfter && (
                <button
                  onClick={onAddAfter}
                  className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                  title="Add section after this one"
                >
                  <Plus className="h-3 w-3" />
                </button>
              )}
              {onMergeWithNext && canMergeWithNext && (
                <button
                  onClick={onMergeWithNext}
                  className="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition-colors"
                  title="Merge with next section"
                >
                  <Merge className="h-3 w-3" />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Delete section"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
