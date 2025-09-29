import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Layout } from './components/Layout';
import { FileUploader } from './components/FileUploader';
import { PlateOverview } from './components/PlateOverview';
import { SectionsList } from './components/SectionsList';
import { CompactSectionCard } from './components/CompactSectionCard';
import { SectionEditor } from './components/SectionEditor';
import { Pagination } from './components/Pagination';
import { VerticalPageNavigation } from './components/VerticalPageNavigation';
import { ChangesPanel } from './components/ChangesPanel';
import { ImageStatus } from './components/ImageStatus';
import { usePlate } from './hooks/usePlate';
import { usePagination } from './hooks/usePagination';
import { usePageNavigation } from './hooks/usePageNavigation';
import { useChangeTracking } from './hooks/useChangeTracking';
import { PlateSection, GlossaryItem, PlatePage } from './types/plate';
import { PageSummaryCard } from './components/PageSummaryCard';
import { SpeechPlayer } from './components/SpeechPlayer';

const getEasyReadIdsForSection = (section: PlateSection): string[] =>
  section.part_ids.map(partId => `${partId}_easy_read`);

const rebuildGlossary = (sections: PlateSection[]): GlossaryItem[] => {
  const glossaryByWord = new Map<string, GlossaryItem>();
  sections.forEach(section => {
    section.glossary.forEach(item => {
      if (!glossaryByWord.has(item.word)) {
        glossaryByWord.set(item.word, item);
      }
    });
  });
  return Array.from(glossaryByWord.values());
};

const rebuildPages = (pages: PlatePage[] = [], sections: PlateSection[]): PlatePage[] => {
  const sectionsByPage = new Map<number, PlateSection[]>();
  sections.forEach(section => {
    const match = section.section_id.match(/sec_p(\d+)_s/);
    if (!match) return;
    const pageNumber = parseInt(match[1], 10);
    if (!sectionsByPage.has(pageNumber)) {
      sectionsByPage.set(pageNumber, []);
    }
    sectionsByPage.get(pageNumber)!.push(section);
  });

  return pages.map(page => {
    const pageSections = sectionsByPage.get(page.page_number) || [];
    return {
      ...page,
      section_ids: pageSections.map(section => section.section_id),
      section_count: pageSections.length,
    };
  });
};

function App() {
  const {
    plate,
    loading,
    error,
    loadPlate,
    savePlate,
    updatePlate,
    audioBasePath,
    audioLanguages,
  } = usePlate();
  const [editingSection, setEditingSection] = useState<PlateSection | null>(null);
  const [previewSection, setPreviewSection] = useState<PlateSection | null>(null);
  const [currentPdfPage, setCurrentPdfPage] = useState(1);
  const [changesPanelOpen, setChangesPanelOpen] = useState(false);
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [deletingSection, setDeletingSection] = useState<PlateSection | null>(null);
  
  // Navigation and change tracking
  const { pageGroups, totalPages: totalPdfPages, getSectionsByPage } = usePageNavigation(plate?.sections || []);
  const changeTracking = useChangeTracking(plate);
  const currentPageData = plate?.pages?.find(page => page.page_number === currentPdfPage) ?? null;

  // Get sections for current PDF page
  const currentPageSections = getSectionsByPage(currentPdfPage);
  
  // Pagination for sections within current page
  const sectionsPerPage = 8; // More sections per page with compact design
  const {
    currentPage: sectionPage,
    totalPages: sectionPages,
    paginatedItems: paginatedSections,
    goToPage: goToSectionPage,
    hasNext,
    hasPrev,
  } = usePagination(currentPageSections, sectionsPerPage);

  const handleSectionReorder = (reorderedSections: PlateSection[]) => {
    if (!plate) return;
    
    // Find the original and new positions for change tracking
    const originalSections = [...currentPageSections];
    const oldIndex = originalSections.findIndex(s => s.section_id === reorderedSections[0].section_id);
    const newIndex = reorderedSections.findIndex(s => s.section_id === reorderedSections[0].section_id);
    
    if (oldIndex !== newIndex) {
      changeTracking.trackSectionReorder(oldIndex, newIndex);
    }
    
    // Update all sections in the plate
    const allSections = [...plate.sections];
    const pageStartIndex = pageGroups.slice(0, currentPdfPage - 1).reduce((acc, p) => acc + p.sectionCount, 0);
    
    // Replace the sections for this page
    reorderedSections.forEach((section, localIndex) => {
      const globalIndex = pageStartIndex + localIndex;
      if (globalIndex < allSections.length) {
        allSections[globalIndex] = section;
      }
    });
    
    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;
      return {
        ...prevPlate,
        sections: allSections,
        pages: rebuildPages(prevPlate.pages || [], allSections),
      };
    });
  };

  const handleSectionEdit = (updatedSection: PlateSection) => {
    if (!plate) return;
    
    const originalSection = plate.sections.find(s => s.section_id === updatedSection.section_id);
    if (originalSection) {
      // Track specific field changes
      const originalExplanation = originalSection.explanation ?? '';
      const updatedExplanation = updatedSection.explanation ?? '';
      if (originalExplanation !== updatedExplanation) {
        changeTracking.trackSectionEdit(updatedSection.section_id, 'explanation', originalExplanation, updatedExplanation);
      }
      const originalEasyRead = originalSection.easy_read ?? '';
      const updatedEasyRead = updatedSection.easy_read ?? '';
      if (originalEasyRead !== updatedEasyRead) {
        changeTracking.trackSectionEdit(updatedSection.section_id, 'easy_read', originalEasyRead, updatedEasyRead);
      }
      if (JSON.stringify(originalSection.glossary) !== JSON.stringify(updatedSection.glossary)) {
        changeTracking.trackSectionEdit(updatedSection.section_id, 'glossary', originalSection.glossary, updatedSection.glossary);
      }
    }

    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;

      const easyReadIds = new Set(getEasyReadIdsForSection(updatedSection));
      const updatedTexts = prevPlate.texts.map(text => {
        if (updatedSection.explanation_id && text.text_id === updatedSection.explanation_id) {
          return { ...text, text: updatedSection.explanation ?? '' };
        }
        if (easyReadIds.has(text.text_id)) {
          return { ...text, text: updatedSection.easy_read ?? '' };
        }
        return text;
      });

      const updatedSections = prevPlate.sections.map(section =>
        section.section_id === updatedSection.section_id ? { ...updatedSection } : section
      );

      return {
        ...prevPlate,
        sections: updatedSections,
        texts: updatedTexts,
        glossary: rebuildGlossary(updatedSections),
        pages: rebuildPages(prevPlate.pages || [], updatedSections),
      };
    });
  };

  const handleTitleUpdate = (title: string) => {
    if (plate && plate.title !== title) {
      changeTracking.trackTitleChange(plate.title, title);
      updatePlate(prevPlate => ({
        ...prevPlate,
        title,
      }));
    }
  };

  const handleLanguageUpdate = (language_code: string) => {
    if (plate && plate.language_code !== language_code) {
      changeTracking.trackLanguageChange(plate.language_code, language_code);
      updatePlate(prevPlate => ({
        ...prevPlate,
        language_code,
      }));
    }
  };

  const handleSaveWithChangeTracking = () => {
    savePlate();
    changeTracking.updateOriginalPlate(plate);
  };

  // Section Management Functions
  const generateSectionId = (pageNumber: number, sectionIndex: number) => {
    return `sec_p${pageNumber}_s${sectionIndex}`;
  };

  const handleDeleteSection = (section: PlateSection) => {
    setDeletingSection(section);
  };

  const confirmDeleteSection = () => {
    if (!plate || !deletingSection) return;
    
    changeTracking.trackSectionDelete(deletingSection.section_id);
    const easyReadIds = new Set(getEasyReadIdsForSection(deletingSection));
    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;

      const remainingSections = prevPlate.sections.filter(s => s.section_id !== deletingSection.section_id);
      return {
        ...prevPlate,
        sections: remainingSections,
        texts: prevPlate.texts.filter(text => {
          if (deletingSection.explanation_id && text.text_id === deletingSection.explanation_id) {
            return false;
          }
          if (easyReadIds.has(text.text_id)) {
            return false;
          }
          return true;
        }),
        glossary: rebuildGlossary(remainingSections),
        pages: rebuildPages(prevPlate.pages || [], remainingSections),
      };
    });
    setDeletingSection(null);
    setSelectedSections(prev => prev.filter(id => id !== deletingSection.section_id));
  };

  const handleDuplicateSection = (section: PlateSection) => {
    if (!plate) return;
    
    const newSectionId = generateSectionId(currentPdfPage, Date.now()); // Use timestamp for uniqueness

    const sourceSection = plate.sections.find(s => s.section_id === section.section_id);
    if (!sourceSection) return;

    const newExplanationId = sourceSection.explanation_id ? `${newSectionId}_eli5` : null;
    const duplicatedSection: PlateSection = {
      ...sourceSection,
      section_id: newSectionId,
      explanation_id: newExplanationId,
      explanation: `${sourceSection.explanation ?? ''} (copy)`,
    };

    const newSections = [...plate.sections];
    const globalIndex = newSections.findIndex(s => s.section_id === section.section_id);
    newSections.splice(globalIndex + 1, 0, duplicatedSection);

    let updatedTexts = [...plate.texts];
    if (newExplanationId) {
      const sourceText = plate.texts.find(text => text.text_id === sourceSection.explanation_id)?.text ?? duplicatedSection.explanation ?? '';
      updatedTexts = [...updatedTexts, { text_id: newExplanationId, text: sourceText, speech: {} }];
    }

    changeTracking.trackSectionAdd(newSectionId, 'duplicate');
    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;
      return {
        ...prevPlate,
        sections: newSections,
        texts: updatedTexts,
        glossary: rebuildGlossary(newSections),
        pages: rebuildPages(prevPlate.pages || [], newSections),
      };
    });
  };

  const handleAddAfter = (section: PlateSection) => {
    if (!plate) return;
    
    const newSectionId = generateSectionId(currentPdfPage, Date.now());
    const newExplanationId = `${newSectionId}_eli5`;
    const newSection: PlateSection = {
      section_id: newSectionId,
      section_type: 'other',
      page_image_upath: section.page_image_upath,
      part_ids: [],
      explanation_id: newExplanationId,
      explanation: 'New section - click to edit',
      easy_read: '',
      glossary: [],
      background_color: section.background_color ?? null,
      text_color: section.text_color ?? null,
      layout_type: section.layout_type ?? null,
    };
    
    const allSections = [...plate.sections];
    const globalIndex = allSections.findIndex(s => s.section_id === section.section_id);
    allSections.splice(globalIndex + 1, 0, newSection);
    const updatedTexts = [...plate.texts, { text_id: newExplanationId, text: newSection.explanation, speech: {} }];

    changeTracking.trackSectionAdd(newSectionId, 'create');
    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;
      return {
        ...prevPlate,
        sections: allSections,
        texts: updatedTexts,
        glossary: rebuildGlossary(allSections),
        pages: rebuildPages(prevPlate.pages || [], allSections),
      };
    });
  };

  const handleMergeWithNext = (section: PlateSection) => {
    if (!plate) return;
    
    const currentPageSections = getSectionsByPage(currentPdfPage);
    const currentIndex = currentPageSections.findIndex(s => s.section_id === section.section_id);
    const nextSection = currentPageSections[currentIndex + 1];
    
    if (!nextSection) return;
    
    const mergedExplanation = [section.explanation ?? '', nextSection.explanation ?? '']
      .filter(Boolean)
      .join('\n\n')
      .trim();

    const mergedEasyRead = [section.easy_read ?? '', nextSection.easy_read ?? '']
      .filter(Boolean)
      .join('\n\n')
      .trim();

    const mergedSection: PlateSection = {
      ...section,
      explanation: mergedExplanation,
      easy_read: mergedEasyRead,
      part_ids: [...section.part_ids, ...nextSection.part_ids],
      glossary: [...section.glossary, ...nextSection.glossary],
    };

    const allSections = [...plate.sections];
    const globalCurrentIndex = allSections.findIndex(s => s.section_id === section.section_id);
    const globalNextIndex = allSections.findIndex(s => s.section_id === nextSection.section_id);

    if (globalCurrentIndex === -1 || globalNextIndex === -1) return;

    // Replace current section with merged version and remove next section
    allSections[globalCurrentIndex] = mergedSection;
    allSections.splice(globalNextIndex, 1);

    const easyReadIds = new Set(getEasyReadIdsForSection(mergedSection));
    const updatedTexts = plate.texts
      .filter(text => !(nextSection.explanation_id && text.text_id === nextSection.explanation_id))
      .map(text => {
        if (mergedSection.explanation_id && text.text_id === mergedSection.explanation_id) {
          return { ...text, text: mergedSection.explanation ?? '' };
        }
        if (easyReadIds.has(text.text_id)) {
          return { ...text, text: mergedSection.easy_read ?? '' };
        }
        return text;
      });

    changeTracking.trackSectionMerge(section.section_id, nextSection.section_id);
    updatePlate(prevPlate => {
      if (!prevPlate) return prevPlate;
      return {
        ...prevPlate,
        sections: allSections,
        texts: updatedTexts,
        glossary: rebuildGlossary(allSections),
        pages: rebuildPages(prevPlate.pages || [], allSections),
      };
    });
  };

  const handleSelectSection = (section: PlateSection) => {
    setSelectedSections(prev => {
      if (prev.includes(section.section_id)) {
        return prev.filter(id => id !== section.section_id);
      } else {
        return [...prev, section.section_id];
      }
    });
  };

  if (error) {
    return (
      <Layout title="Error">
        <div className="text-center py-12">
          <div className="text-red-600 text-lg mb-4">Error loading plate file</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </Layout>
    );
  }

  if (!plate) {
    return (
      <Layout title="Upload Plate File">
        <FileUploader onFileSelect={loadPlate} loading={loading} />
      </Layout>
    );
  }

  return (
    <Layout 
      title={plate.title} 
      onSave={handleSaveWithChangeTracking}
      hasChanges={changeTracking.hasChanges}
    >
      {/* Vertical Page Navigation */}
      <VerticalPageNavigation
        pageGroups={pageGroups}
        currentPage={currentPdfPage}
        onPageChange={setCurrentPdfPage}
        totalSections={plate.sections.length}
      />

      <div className="flex gap-6 pt-6 pl-72">
        {/* Main Content Area - Optimized for editing */}
        <div className="flex-1 min-w-0">
          {/* Sections - Compact Cards for Better Space Utilization */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-6 py-4 border-b bg-gray-50">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Page {currentPdfPage} Sections
                </h2>
                <div className="text-sm text-gray-500">
                  {paginatedSections.length} of {currentPageSections.length} sections
                </div>
              </div>
            </div>
            
            <div className="p-4">
              {paginatedSections.length > 0 ? (
                <SectionsList
                  sections={paginatedSections}
                  images={plate.images}
                  texts={plate.texts}
                  onReorder={handleSectionReorder}
                  onEditSection={setEditingSection}
                  onPreviewSection={setPreviewSection}
                  onDeleteSection={handleDeleteSection}
                  onDuplicateSection={handleDuplicateSection}
                  onMergeWithNext={handleMergeWithNext}
                  onAddAfter={handleAddAfter}
                  onSelectSection={handleSelectSection}
                  useCompactCards={true}
                  changedSectionIds={changeTracking.changes.map(c => c.sectionId).filter(Boolean)}
                  selectedSectionIds={selectedSections}
                  audioBasePath={audioBasePath}
                  audioLanguages={audioLanguages}
                />
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-lg mb-2">📄</div>
                  <p className="text-gray-500">No sections on this page</p>
                </div>
              )}
            </div>

            {/* Section Pagination */}
            {sectionPages > 1 && (
              <div className="border-t">
                <Pagination
                  currentPage={sectionPage}
                  totalPages={sectionPages}
                  onPageChange={goToSectionPage}
                  hasNext={hasNext}
                  hasPrev={hasPrev}
                />
              </div>
            )}
          </div>
        </div>

        {/* Sidebar for Plate Metadata and Quick Actions */}
        <div className="w-80 flex-shrink-0 space-y-4">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Plate Information</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
                <input
                  type="text"
                  value={plate.title}
                  onChange={(e) => handleTitleUpdate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus-ring"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Language</label>
                <input
                  type="text"
                  value={plate.language_code}
                  onChange={(e) => handleLanguageUpdate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus-ring"
                />
              </div>
            </div>
          </div>

          <ChangesPanel
            changes={changeTracking.recentChanges}
            changesSummary={changeTracking.changesSummary}
            onSave={handleSaveWithChangeTracking}
            onClearChanges={changeTracking.clearChanges}
            isOpen={changesPanelOpen}
            onToggle={() => setChangesPanelOpen(!changesPanelOpen)}
            floating={false}
          />

          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Document Stats</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="text-center p-2 bg-blue-50 rounded">
                <div className="font-semibold text-blue-600">{totalPdfPages}</div>
                <div className="text-gray-600">Pages</div>
              </div>
              <div className="text-center p-2 bg-green-50 rounded">
                <div className="font-semibold text-green-600">{plate.sections.length}</div>
                <div className="text-gray-600">Sections</div>
              </div>
              <div className="text-center p-2 bg-purple-50 rounded">
                <div className="font-semibold text-purple-600">{plate.images.length}</div>
                <div className="text-gray-600">Images</div>
              </div>
              <div className="text-center p-2 bg-amber-50 rounded">
                <div className="font-semibold text-amber-600">{plate.texts.length}</div>
                <div className="text-gray-600">Texts</div>
              </div>
            </div>
          </div>

          {currentPageData && (
            <PageSummaryCard page={currentPageData} sections={currentPageSections} />
          )}
        </div>
      </div>

      {/* Section Editor Modal */}
      {editingSection && (
        <SectionEditor
          section={editingSection}
          onSave={handleSectionEdit}
          onClose={() => setEditingSection(null)}
        />
      )}

      {/* Section Preview Modal (placeholder) */}
      {previewSection && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setPreviewSection(null)}
            aria-hidden="true"
          />
          <div className="relative w-full max-w-3xl mx-4 bg-white rounded-lg shadow-lg flex flex-col max-h-[calc(100vh-4rem)] overflow-hidden">
            <div className="flex items-start justify-between border-b px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-900">Section Preview</h3>
              <button
                onClick={() => setPreviewSection(null)}
                className="rounded-full p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white"
                aria-label="Close section preview"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="px-6 py-4 overflow-y-auto">
              <div className="prose max-w-none">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Source Text</h4>
                <ul className="space-y-3 mb-6">
                  {plate.texts
                    .filter(text => previewSection.part_ids.includes(text.text_id))
                    .map(text => (
                      <li key={text.text_id} className="bg-gray-50 border border-gray-200 rounded-md p-3">
                        <div className="text-xs text-gray-500 mb-1 font-mono">{text.text_id}</div>
                        <p className="text-gray-900 whitespace-pre-wrap leading-relaxed">{text.text}</p>
                        <SpeechPlayer
                          textId={text.text_id}
                          audioBasePath={audioBasePath}
                          languages={audioLanguages}
                        />
                      </li>
                    ))}
                </ul>

                <h4 className="text-sm font-medium text-gray-500 mb-2">Explanation</h4>
                <p className="text-gray-900 mb-6">{previewSection.explanation}</p>

                <h4 className="text-sm font-medium text-gray-500 mb-2">Easy Read</h4>
                <p className="text-gray-900 mb-6">{previewSection.easy_read}</p>

                {previewSection.glossary.length > 0 && (
                  <>
                    <h4 className="text-sm font-medium text-gray-500 mb-2">Glossary</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-900">
                      {previewSection.glossary.map((item, index) => (
                        <li key={index}>
                          <strong>{item.word}:</strong> {item.definition}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingSection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4 p-6">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Delete Section</h3>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-700 mb-2">
                Are you sure you want to delete this section? This action cannot be undone.
              </p>
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="text-sm font-medium text-gray-900 mb-1">
                  {deletingSection.section_id} ({deletingSection.section_type})
                </div>
                <div className="text-sm text-gray-600 line-clamp-2">
                  {deletingSection.explanation || 'No explanation'}
                </div>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setDeletingSection(null)}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteSection}
                className="flex-1 px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Delete Section
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Status Notification */}
      {plate && <ImageStatus plate={plate} />}
    </Layout>
  );
}

export default App;
