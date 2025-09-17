import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { PlateSection, PlateImage, PlateText } from '../types/plate';
import { SectionCard } from './SectionCard';
import { CompactSectionCard } from './CompactSectionCard';

interface SectionsListProps {
  sections: PlateSection[];
  images: PlateImage[];
  texts: PlateText[];
  onReorder: (sections: PlateSection[]) => void;
  onEditSection: (section: PlateSection) => void;
  onPreviewSection: (section: PlateSection) => void;
  onDeleteSection?: (section: PlateSection) => void;
  onDuplicateSection?: (section: PlateSection) => void;
  onMergeWithNext?: (section: PlateSection) => void;
  onAddAfter?: (section: PlateSection) => void;
  useCompactCards?: boolean;
  changedSectionIds?: string[];
  selectedSectionIds?: string[];
  onSelectSection?: (section: PlateSection) => void;
}

export const SectionsList: React.FC<SectionsListProps> = ({
  sections,
  images,
  texts,
  onReorder,
  onEditSection,
  onPreviewSection,
  onDeleteSection,
  onDuplicateSection,
  onMergeWithNext,
  onAddAfter,
  useCompactCards = false,
  changedSectionIds = [],
  selectedSectionIds = [],
  onSelectSection,
}) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = sections.findIndex(section => section.section_id === active.id);
      const newIndex = sections.findIndex(section => section.section_id === over?.id);
      onReorder(arrayMove(sections, oldIndex, newIndex));
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={sections.map(s => s.section_id)}
        strategy={verticalListSortingStrategy}
      >
        <div className={useCompactCards ? "space-y-3" : "space-y-4"}>
          {sections.map((section, index) => {
            const hasChanges = changedSectionIds.includes(section.section_id);
            const isSelected = selectedSectionIds.includes(section.section_id);
            const canMergeWithNext = index < sections.length - 1;
            
            return useCompactCards ? (
              <CompactSectionCard
                key={section.section_id}
                section={section}
                images={images}
                texts={texts}
                onEdit={() => onEditSection(section)}
                onPreview={() => onPreviewSection(section)}
                onDelete={onDeleteSection ? () => onDeleteSection(section) : undefined}
                onDuplicate={onDuplicateSection ? () => onDuplicateSection(section) : undefined}
                onMergeWithNext={onMergeWithNext && canMergeWithNext ? () => onMergeWithNext(section) : undefined}
                onAddAfter={onAddAfter ? () => onAddAfter(section) : undefined}
                onSelect={onSelectSection ? () => onSelectSection(section) : undefined}
                hasChanges={hasChanges}
                isSelected={isSelected}
                canMergeWithNext={canMergeWithNext}
              />
            ) : (
              <SectionCard
                key={section.section_id}
                section={section}
                images={images}
                texts={texts}
                onEdit={() => onEditSection(section)}
                onPreview={() => onPreviewSection(section)}
              />
            );
          })}
        </div>
      </SortableContext>
    </DndContext>
  );
};