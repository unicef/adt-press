import React from 'react';
import { PlateSection, PlateImage, PlateText } from '../types/plate';
import { GripVertical, Image, Type, Edit, Eye } from 'lucide-react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import clsx from 'clsx';
import { ImageDisplay } from './ImageDisplay';

interface SectionCardProps {
  section: PlateSection;
  images: PlateImage[];
  texts: PlateText[];
  onEdit: () => void;
  onPreview: () => void;
}

const getSectionTypeColor = (type: string) => {
  const colors = {
    separator: 'bg-gray-100 text-gray-800',
    text_and_images: 'bg-blue-100 text-blue-800',
    activity_multiple_choice: 'bg-green-100 text-green-800',
    activity_fill_in_the_blank: 'bg-yellow-100 text-yellow-800',
    other: 'bg-purple-100 text-purple-800',
  };
  return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
};

export const SectionCard: React.FC<SectionCardProps> = ({
  section,
  images,
  texts,
  onEdit,
  onPreview,
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

  // Get images and texts for this section
  const sectionImages = images.filter(img => section.part_ids.includes(img.image_id));
  const sectionTexts = texts.filter(txt => section.part_ids.includes(txt.text_id));
  const hasPageImage = section.page_image_upath;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={clsx(
        'bg-white rounded-xl shadow-sm border border-gray-100 p-6 card-hover',
        isDragging && 'opacity-50 drag-overlay'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          {/* Drag Handle */}
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
            title="Drag to reorder"
          >
            <GripVertical className="h-5 w-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <span
                className={clsx(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  getSectionTypeColor(section.section_type)
                )}
              >
                {section.section_type}
              </span>
              <span className="text-xs text-gray-500">
                {section.section_id}
              </span>
            </div>

            {/* Content Layout */}
            <div className="space-y-4">
              {/* Page Image Preview */}
              {hasPageImage && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">
                    Page Context
                  </h4>
                  <ImageDisplay
                    src={section.page_image_upath}
                    alt={`Page context for ${section.section_id}`}
                    className="max-w-xs"
                    showCaption={false}
                  />
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column - Text Content */}
                <div className="space-y-4">
                  {/* Explanation Preview */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Explanation
                    </h4>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-sm text-gray-700 line-clamp-3 leading-relaxed">
                        {section.explanation || 'No explanation provided'}
                      </p>
                    </div>
                  </div>

                  {/* Easy Read Preview */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Easy Read
                    </h4>
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-sm text-blue-900 line-clamp-3 leading-relaxed">
                        {section.easy_read || 'No easy read version provided'}
                      </p>
                    </div>
                  </div>

                  {/* Text Content Preview */}
                  {sectionTexts.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        Text Content ({sectionTexts.length})
                      </h4>
                      <div className="space-y-2">
                        {sectionTexts.slice(0, 2).map((text) => (
                          <div key={text.text_id} className="bg-green-50 rounded p-2">
                            <p className="text-xs text-green-800 line-clamp-2">
                              {text.text}
                            </p>
                          </div>
                        ))}
                        {sectionTexts.length > 2 && (
                          <p className="text-xs text-gray-500">
                            +{sectionTexts.length - 2} more text blocks
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Column - Images and Parts */}
                <div className="space-y-4">
                  {/* Section Images */}
                  {sectionImages.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        Images ({sectionImages.length})
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        {sectionImages.slice(0, 4).map((image) => (
                          <div key={image.image_id} className="relative">
                            <ImageDisplay
                              src={image.upath}
                              alt={image.caption || `Image ${image.image_id}`}
                              caption={image.caption}
                              showCaption={false}
                            />
                            {image.caption && (
                              <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white p-1 rounded-b text-xs line-clamp-1">
                                {image.caption}
                              </div>
                            )}
                          </div>
                        ))}
                        {sectionImages.length > 4 && (
                          <div className="flex items-center justify-center bg-gray-100 rounded-lg aspect-square text-xs text-gray-500">
                            +{sectionImages.length - 4} more
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Parts Summary */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Parts Summary
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between bg-gray-50 rounded p-2">
                        <div className="flex items-center space-x-2">
                          <Image className="h-4 w-4 text-gray-600" />
                          <span className="text-sm text-gray-700">Images</span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {sectionImages.length}
                        </span>
                      </div>
                      <div className="flex items-center justify-between bg-gray-50 rounded p-2">
                        <div className="flex items-center space-x-2">
                          <Type className="h-4 w-4 text-gray-600" />
                          <span className="text-sm text-gray-700">Text Blocks</span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {sectionTexts.length}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Glossary indicator */}
            {section.glossary.length > 0 && (
              <div className="mt-2">
                <span className="text-xs text-blue-600">
                  {section.glossary.length} glossary term{section.glossary.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={onPreview}
            className="btn-ghost"
            title="Preview section"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={onEdit}
            className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all duration-200"
            title="Edit section"
          >
            <Edit className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};