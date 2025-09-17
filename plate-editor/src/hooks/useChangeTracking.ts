import { useState, useCallback, useMemo } from 'react';
import { Plate, PlateSection } from '../types/plate';

export interface Change {
  id: string;
  type: 'edit' | 'reorder' | 'title' | 'language' | 'delete' | 'add' | 'merge';
  timestamp: number;
  description: string;
  sectionId?: string;
  field?: string;
  oldValue?: any;
  newValue?: any;
}

export const useChangeTracking = (initialPlate: Plate | null) => {
  const [changes, setChanges] = useState<Change[]>([]);
  const [originalPlate, setOriginalPlate] = useState<Plate | null>(initialPlate);

  const addChange = useCallback((change: Omit<Change, 'id' | 'timestamp'>) => {
    const newChange: Change = {
      ...change,
      id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
    };
    setChanges(prev => [...prev, newChange]);
  }, []);

  const clearChanges = useCallback(() => {
    setChanges([]);
  }, []);

  const trackSectionEdit = useCallback((sectionId: string, field: string, oldValue: any, newValue: any) => {
    if (JSON.stringify(oldValue) === JSON.stringify(newValue)) return;
    
    addChange({
      type: 'edit',
      description: `Modified ${field} in section ${sectionId}`,
      sectionId,
      field,
      oldValue,
      newValue,
    });
  }, [addChange]);

  const trackSectionReorder = useCallback((fromIndex: number, toIndex: number) => {
    addChange({
      type: 'reorder',
      description: `Moved section from position ${fromIndex + 1} to ${toIndex + 1}`,
      oldValue: fromIndex,
      newValue: toIndex,
    });
  }, [addChange]);

  const trackTitleChange = useCallback((oldTitle: string, newTitle: string) => {
    if (oldTitle === newTitle) return;
    
    addChange({
      type: 'title',
      description: `Changed title from "${oldTitle}" to "${newTitle}"`,
      field: 'title',
      oldValue: oldTitle,
      newValue: newTitle,
    });
  }, [addChange]);

  const trackLanguageChange = useCallback((oldLang: string, newLang: string) => {
    if (oldLang === newLang) return;
    
    addChange({
      type: 'language',
      description: `Changed language from "${oldLang}" to "${newLang}"`,
      field: 'language_code',
      oldValue: oldLang,
      newValue: newLang,
    });
  }, [addChange]);

  const trackSectionDelete = useCallback((sectionId: string) => {
    addChange({
      type: 'delete',
      description: `Deleted section ${sectionId}`,
      sectionId,
    });
  }, [addChange]);

  const trackSectionAdd = useCallback((sectionId: string, method: 'create' | 'duplicate') => {
    addChange({
      type: 'add',
      description: method === 'duplicate' 
        ? `Duplicated section to create ${sectionId}`
        : `Created new section ${sectionId}`,
      sectionId,
      newValue: method,
    });
  }, [addChange]);

  const trackSectionMerge = useCallback((sectionId1: string, sectionId2: string) => {
    addChange({
      type: 'merge',
      description: `Merged sections ${sectionId1} and ${sectionId2}`,
      sectionId: sectionId1,
      oldValue: sectionId2,
    });
  }, [addChange]);

  const updateOriginalPlate = useCallback((plate: Plate | null) => {
    setOriginalPlate(plate);
    clearChanges();
  }, [clearChanges]);

  const recentChanges = useMemo(() => {
    return changes
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 10);
  }, [changes]);

  const hasChanges = changes.length > 0;

  const changesSummary = useMemo(() => {
    const summary = {
      total: changes.length,
      edits: changes.filter(c => c.type === 'edit').length,
      reorders: changes.filter(c => c.type === 'reorder').length,
      metadata: changes.filter(c => c.type === 'title' || c.type === 'language').length,
      deletes: changes.filter(c => c.type === 'delete').length,
      adds: changes.filter(c => c.type === 'add').length,
      merges: changes.filter(c => c.type === 'merge').length,
    };
    return summary;
  }, [changes]);

  return {
    changes,
    recentChanges,
    hasChanges,
    changesSummary,
    addChange,
    clearChanges,
    trackSectionEdit,
    trackSectionReorder,
    trackSectionDelete,
    trackSectionAdd,
    trackSectionMerge,
    trackTitleChange,
    trackLanguageChange,
    updateOriginalPlate,
  };
};