from pydantic import BaseModel, model_validator

from adt_press.models.ids import QuizExplanationID, QuizID, QuizOptionID, QuizQuestionID, SectionID


class SectionQuiz(BaseModel):
    quiz_id: QuizID
    section_id: SectionID
    question: str
    question_id: QuizQuestionID = ""
    options: list[str]
    option_ids: list[QuizOptionID] = []
    explanations: list[str]
    explanation_ids: list[QuizExplanationID] = []
    answer_index: int
    reasoning: str

    @model_validator(mode="after")
    def populate_ids(self):
        """Automatically populate question_id, option_ids, and explanation_ids based on quiz_id."""
        if not self.question_id:
            self.question_id = f"{self.quiz_id}_que"

        if not self.option_ids:
            self.option_ids = [f"{self.quiz_id}_opt_{idx}" for idx in range(len(self.options))]

        if not self.explanation_ids:
            self.explanation_ids = [f"{self.quiz_id}_exp_{idx}" for idx in range(len(self.explanations))]

        return self
