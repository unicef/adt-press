const QUIZ_SECTION_SELECTOR = 'section[role="activity"][data-section-type="activity_quiz"]';
const CORRECT_ANSWERS_SCRIPT_ID = 'quiz-correct-answers';
const EXPLANATIONS_SCRIPT_ID = 'quiz-explanations';

const ensureValidationLiveRegion = () => {
  if (document.getElementById('validation-results-announcement')) {
    return;
  }

  const announcement = document.createElement('div');
  announcement.id = 'validation-results-announcement';
  announcement.className = 'sr-only';
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  document.body.appendChild(announcement);
};

const applyQuizBackground = () => {
  document.body.style.backgroundColor = '#FFFAF5';
};

const parseJsonScriptContent = (elementId) => {
  const scriptElement = document.getElementById(elementId);

  if (!scriptElement || !scriptElement.textContent) {
    return null;
  }

  try {
    return JSON.parse(scriptElement.textContent);
  } catch (error) {
    console.warn(`activity_quiz: unable to parse JSON for ${elementId}`, error);
    return null;
  }
};

const mergeIntoWindow = (targetKey, data) => {
  if (!data || typeof data !== 'object') {
    return;
  }

  const existing = window[targetKey] || {};
  window[targetKey] = { ...existing, ...data };
};

const hydrateQuizData = () => {
  const correctAnswers = parseJsonScriptContent(CORRECT_ANSWERS_SCRIPT_ID);
  mergeIntoWindow('correctAnswers', correctAnswers);

  const explanations = parseJsonScriptContent(EXPLANATIONS_SCRIPT_ID);
  mergeIntoWindow('multipleChoiceExplanations', explanations);
};

export const initializeQuizActivity = () => {
  const quizSection = document.querySelector(QUIZ_SECTION_SELECTOR);

  if (!quizSection) {
    console.warn('activity_quiz: quiz activity section not found.');
    return;
  }

  applyQuizBackground();
  ensureValidationLiveRegion();
  hydrateQuizData();
};

export default {
  initializeQuizActivity,
};
