from typing import NewType

PageID = NewType("PageID", str)
SectionID = NewType("SectionID", str)
ImageID = NewType("ImageID", str)
TextID = NewType("TextID", str)
TextGroupID = NewType("TextGroupID", str)
SpeechID = NewType("SpeechID", str)
ChapterID = NewType("ChapterID", str)

OutputTextID = NewType("OutputTextID", str)

QuizID = NewType("QuizID", str)
QuizQuestionID = NewType("QuizQuestionID", str)
QuizExplanationID = NewType("QuizExplanationID", str)
QuizOptionID = NewType("QuizOptionID", str)