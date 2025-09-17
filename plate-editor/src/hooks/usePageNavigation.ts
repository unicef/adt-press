import { useMemo } from 'react';
import { PlateSection } from '../types/plate';

export interface PageGroup {
  pageNumber: number;
  pageId: string;
  pageImagePath: string;
  sections: PlateSection[];
  sectionCount: number;
}

export const usePageNavigation = (sections: PlateSection[]) => {
  const pageGroups = useMemo(() => {
    const groups = new Map<string, PageGroup>();
    
    sections.forEach((section, index) => {
      // Extract page number from section ID (e.g., "sec_p1_s0" -> page 1)
      const pageMatch = section.section_id.match(/sec_p(\d+)_s\d+/);
      const pageNumber = pageMatch ? parseInt(pageMatch[1], 10) : 1;
      const pageId = `page_${pageNumber}`;
      
      if (!groups.has(pageId)) {
        groups.set(pageId, {
          pageNumber,
          pageId,
          pageImagePath: section.page_image_upath,
          sections: [],
          sectionCount: 0,
        });
      }
      
      const group = groups.get(pageId)!;
      group.sections.push(section);
      group.sectionCount++;
    });
    
    // Convert to array and sort by page number
    return Array.from(groups.values()).sort((a, b) => a.pageNumber - b.pageNumber);
  }, [sections]);

  const totalPages = pageGroups.length;
  
  const getPageBySectionId = (sectionId: string): PageGroup | null => {
    return pageGroups.find(page => 
      page.sections.some(section => section.section_id === sectionId)
    ) || null;
  };

  const getSectionsByPage = (pageNumber: number): PlateSection[] => {
    const page = pageGroups.find(p => p.pageNumber === pageNumber);
    return page ? page.sections : [];
  };

  return {
    pageGroups,
    totalPages,
    getPageBySectionId,
    getSectionsByPage,
  };
};