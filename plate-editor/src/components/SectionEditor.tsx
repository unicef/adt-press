import React, { useState, useEffect } from 'react';
import { PlateSection, GlossaryItem } from '../types/plate';
import { X, Plus, Trash2 } from 'lucide-react';

interface SectionEditorProps {
  section: PlateSection;
  onSave: (section: PlateSection) => void;
  onClose: () => void;
}

export const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  onSave,
  onClose,
}) => {
  const [editedSection, setEditedSection] = useState<PlateSection>(section);

  useEffect(() => {
    setEditedSection(section);
  }, [section]);

  const handleSave = () => {
    onSave(editedSection);
    onClose();
  };

  const addGlossaryItem = () => {
    setEditedSection(prev => ({
      ...prev,
      glossary: [
        ...prev.glossary,
        {
          word: '',
          variants: [],
          definition: '',
          emojis: [],
        },
      ],
    }));
  };

  const updateGlossaryItem = (index: number, item: GlossaryItem) => {
    setEditedSection(prev => ({
      ...prev,
      glossary: prev.glossary.map((g, i) => i === index ? item : g),
    }));
  };

  const removeGlossaryItem = (index: number) => {
    setEditedSection(prev => ({
      ...prev,
      glossary: prev.glossary.filter((_, i) => i !== index),
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold">Edit Section</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="p-6 space-y-6">
            {/* Section Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Section ID
                </label>
                <input
                  type="text"
                  value={editedSection.section_id}
                  onChange={(e) => setEditedSection(prev => ({
                    ...prev,
                    section_id: e.target.value
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Section Type
                </label>
                <select
                  value={editedSection.section_type}
                  onChange={(e) => setEditedSection(prev => ({
                    ...prev,
                    section_type: e.target.value as any
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="separator">Separator</option>
                  <option value="text_and_images">Text and Images</option>
                  <option value="activity_multiple_choice">Multiple Choice</option>
                  <option value="activity_fill_in_the_blank">Fill in the Blank</option>
                  <option value="activity_true_false">True/False</option>
                  <option value="activity_matching">Matching</option>
                  <option value="activity_short_answer">Short Answer</option>
                  <option value="activity_essay">Essay</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Explanation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Explanation
              </label>
              <textarea
                value={editedSection.explanation}
                onChange={(e) => setEditedSection(prev => ({
                  ...prev,
                  explanation: e.target.value
                }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Easy Read */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Easy Read
              </label>
              <textarea
                value={editedSection.easy_read}
                onChange={(e) => setEditedSection(prev => ({
                  ...prev,
                  easy_read: e.target.value
                }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Part IDs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Part IDs (comma-separated)
              </label>
              <input
                type="text"
                value={editedSection.part_ids.join(', ')}
                onChange={(e) => setEditedSection(prev => ({
                  ...prev,
                  part_ids: e.target.value.split(',').map(id => id.trim()).filter(Boolean)
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Glossary */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-medium text-gray-700">
                  Glossary
                </label>
                <button
                  onClick={addGlossaryItem}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Term
                </button>
              </div>

              <div className="space-y-4">
                {editedSection.glossary.map((item, index) => (
                  <div key={index} className="border border-gray-200 rounded-md p-4">
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-sm font-medium text-gray-900">
                        Term {index + 1}
                      </h4>
                      <button
                        onClick={() => removeGlossaryItem(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Word
                        </label>
                        <input
                          type="text"
                          value={item.word}
                          onChange={(e) => updateGlossaryItem(index, {
                            ...item,
                            word: e.target.value
                          })}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Variants (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={item.variants.join(', ')}
                          onChange={(e) => updateGlossaryItem(index, {
                            ...item,
                            variants: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                          })}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                    
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Definition
                      </label>
                      <textarea
                        value={item.definition}
                        onChange={(e) => updateGlossaryItem(index, {
                          ...item,
                          definition: e.target.value
                        })}
                        rows={2}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Emojis (comma-separated)
                      </label>
                      <input
                        type="text"
                        value={item.emojis.join(', ')}
                        onChange={(e) => updateGlossaryItem(index, {
                          ...item,
                          emojis: e.target.value.split(',').map(e => e.trim()).filter(Boolean)
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 p-6 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};