import dspy
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    """Result for a single question"""

    question_number: int
    subject: str
    paper: int
    question_text: str
    predicted_answer: str
    ground_truth: str
    marks_awarded: int
    is_correct: bool
    reasoning: str
    question_figure_description: str
    model_name: str
    temperature: float


# Signature for answering JEE questions
class JEEQuestionSolver(dspy.Signature):
    """Answer a JEE question following the given instructions."""

    question_instruction: str = dspy.InputField(
        desc="Instructions for answering this question"
    )
    question_text: str = dspy.InputField(desc="The question to be answered")
    question_figure_description: str = dspy.InputField(
        desc="Description of any figure in the question", default=""
    ) 

    final_answer: str = dspy.OutputField(
        desc="Final answer following the instruction format"
    )


# Signature for grading answers
class JEEAnswerGrader(dspy.Signature):
    """Grade a JEE answer based on instructions, predicted answer, and ground truth."""

    question_instruction: str = dspy.InputField(desc="Original question instructions")
    question_text: str = dspy.InputField(desc="The original question")
    predicted_answer: str = dspy.InputField(desc="Answer given by the model")
    ground_truth_answer: str = dspy.InputField(desc="Correct answer")

    marks_awarded: int = dspy.OutputField(
        desc="Marks awarded based on the marking scheme"
    )
    is_correct: bool = dspy.OutputField(desc="Whether the answer is correct")


class Solver(dspy.Module):
    def __init__(self):
        self.solver = dspy.ChainOfThought(JEEQuestionSolver)

    def forward(self, question):
        solution = self.solver(
            question_instruction=question["question_instruction"],
            question_text=question["question_text"],
            question_figure_description=question.get("question_figure_description", ""),
        )
        return solution


class Grader(dspy.Module):
    def __init__(self):
        self.grader = dspy.Predict(JEEAnswerGrader)

    def forward(self, question, solution):
        grade = self.grader(
            question_instruction=question["question_instruction"],
            question_text=question["question_text"],
            predicted_answer=solution.final_answer,
            ground_truth_answer=question["answer_text"],
        )
        return grade
