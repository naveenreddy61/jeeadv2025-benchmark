#!/usr/bin/env python3
"""
JEE 2025 Benchmark - Simple LLM Evaluation System
Evaluates LLM performance on JEE questions across subjects, papers of 2025.
"""

import yaml
from dotenv import load_dotenv
import argparse
import json
import dspy
from typing import Dict, List, Any, Optional
import os
import sqlite3
from dspy_solver import Solver, Grader, BenchmarkResult


# Load config
def load_config(config_path: str):
    """Load YAML config from the given path."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class JEEBenchmark:
    """Simple JEE benchmark system"""

    def __init__(
        self,
        solver_model_params: Dict[str, Any],
        grader_model_params: Dict[str, Any],
        max_questions: int,
        input_filepath: str,
        output_filepath: str,
        dbfilepath: str,
    ):
        self.solver_module = Solver()
        self.solver_module.set_lm(dspy.LM(**solver_model_params))
        self.grader_module = Grader()
        self.grader_module.set_lm(dspy.LM(**grader_model_params))
        self.results: List[BenchmarkResult] = []
        self.model_name = solver_model_params.get("model", "")
        self.temperature = solver_model_params.get("temperature", 0.0)
        self.max_questions = max_questions
        self.input_filepath = input_filepath
        self.output_filepath = output_filepath
        self.dbfilepath = dbfilepath
        self._init_db()

    def _init_db(self):
        """Initialize SQLite DB and table."""
        db_dir = os.path.dirname(self.dbfilepath)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.dbfilepath)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_number INTEGER,
                subject TEXT,
                paper INTEGER,
                question_text TEXT,
                predicted_answer TEXT,
                ground_truth TEXT,
                marks_awarded INTEGER,
                is_correct BOOLEAN,
                reasoning TEXT,
                question_figure_description TEXT,
                model_name TEXT,
                temperature REAL
            )
        """
        )
        self.conn.commit()

    def _insert_result_db(self, result: BenchmarkResult):
        """Insert a BenchmarkResult into the SQLite DB."""
        self.cursor.execute(
            """
            INSERT INTO benchmark_results (
                question_number, subject, paper, question_text,
                predicted_answer, ground_truth, marks_awarded, is_correct,
                reasoning, question_figure_description, model_name, temperature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.question_number,
                result.subject,
                result.paper,
                result.question_text,
                result.predicted_answer,
                result.ground_truth,
                result.marks_awarded,
                int(result.is_correct),
                result.reasoning,
                result.question_figure_description,
                result.model_name,
                result.temperature,
            ),
        )
        self.conn.commit()

    def run_benchmark(
        self, max_questions: Optional[int] = None
    ) -> List[BenchmarkResult]:
        """Run benchmark on JEE questions"""

        try:
            with open(self.input_filepath, "r", encoding="utf-8") as f:
                questions = json.load(f)
        except FileNotFoundError:
            print(f"File {self.input_filepath} not found!")
            return []

        if max_questions is None:
            max_questions = self.max_questions
        if max_questions:
            questions = questions[:max_questions]

        print(f"Running JEE Benchmark on {len(questions)} questions...")
        print("=" * 60)

        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}/{len(questions)}")
            print(
                f"Subject: {question.get('subject', 'N/A')} | "
                f"Paper: {question.get('paper', 'N/A')}"
            )
            try:
                solution = self.solver_module(question)
            except Exception as e:
                print(f"Error solving question {i}: {e}")
                solution = dspy.Prediction(reasoning=f"error occurred {e}", final_answer="unable to solve")
            try:
                grading = self.grader_module(question, solution)
            except Exception as e:
                print(f"Error grading question {i}: {e}")
                grading = dspy.Prediction(marks_awarded=0, is_correct=False)
            result = BenchmarkResult(
                question_number=question.get("question_number", i),
                subject=question.get("subject", "Unknown"),
                paper=question.get("paper", 0),
                question_text=question.get("question_text", ""),
                question_figure_description=question.get("question_figure_description"),
                predicted_answer=solution.final_answer,
                ground_truth=question.get("answer_text", ""),
                marks_awarded=grading.marks_awarded,
                is_correct=grading.is_correct,
                reasoning=solution.reasoning,
                model_name=self.model_name,
                temperature=self.temperature,
            )

            self.results.append(result)
            self._insert_result_db(result)

            status = "✓" if result.is_correct else "✗"
            print(
                f"Answer: {result.predicted_answer} | "
                f"Correct: {result.ground_truth} | "
                f"Status: {status} | "
                f"Marks: {result.marks_awarded}"
            )

        return self.results

    def print_detailed_results(self):
        """Print comprehensive benchmark results"""

        if not self.results:
            print("No results to display!")
            return

        print("\n" + "=" * 80)
        print("DETAILED BENCHMARK RESULTS")
        print("=" * 80)

        total_questions = len(self.results)
        if total_questions == 0:
            print("No questions were processed to show results.")
            return

        correct_answers = sum(1 for r in self.results if r.is_correct)
        total_marks = sum(r.marks_awarded for r in self.results)
        accuracy = correct_answers / total_questions * 100 if total_questions > 0 else 0

        print("\nOVERALL PERFORMANCE:")
        print(f"Total Questions: {total_questions}")
        print(f"Correct Answers: {correct_answers}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"Total Marks: {total_marks}")
        print(
            f"Average Marks per Question: {total_marks/total_questions:.2f}"
            if total_questions > 0
            else "N/A"
        )

        subjects = {}
        for result in self.results:
            if result.subject not in subjects:
                subjects[result.subject] = {"total": 0, "correct": 0, "marks": 0}
            subjects[result.subject]["total"] += 1
            subjects[result.subject]["correct"] += 1 if result.is_correct else 0
            subjects[result.subject]["marks"] += result.marks_awarded

        print("\nPERFORMANCE BY SUBJECT:")
        for subject, stats in subjects.items():
            acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            avg_marks = stats["marks"] / stats["total"] if stats["total"] > 0 else 0
            print(
                f"{subject}: {stats['correct']}/{stats['total']} ({acc:.1f}%) | Avg Marks: {avg_marks:.2f}"
            )

        papers = {}
        for result in self.results:
            paper_key = f"Paper {result.paper}"  # Use a consistent key
            if paper_key not in papers:
                papers[paper_key] = {"total": 0, "correct": 0, "marks": 0}
            papers[paper_key]["total"] += 1
            papers[paper_key]["correct"] += 1 if result.is_correct else 0
            papers[paper_key]["marks"] += result.marks_awarded

        print("\nPERFORMANCE BY PAPER:")
        for paper, stats in papers.items():
            acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            avg_marks = stats["marks"] / stats["total"] if stats["total"] > 0 else 0
            print(
                f"{paper}: {stats['correct']}/{stats['total']} ({acc:.1f}%) | Avg Marks: {avg_marks:.2f}"
            )

    def save_results(self):
        """Save results to JSON file"""
        if not self.results:
            print("No results to save.")
            return

        total_questions = len(self.results)
        correct_answers = sum(1 for r in self.results if r.is_correct)
        accuracy_val = (
            correct_answers / total_questions * 100 if total_questions > 0 else 0
        )

        results_data = {
            "summary": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "total_marks": sum(r.marks_awarded for r in self.results),
                "accuracy": accuracy_val,
            },
            "detailed_results": [
                {
                    "question_number": r.question_number,
                    "subject": r.subject,
                    "paper": r.paper,
                    "question_text": r.question_text,
                    "predicted_answer": r.predicted_answer,
                    "ground_truth": r.ground_truth,
                    "marks_awarded": r.marks_awarded,
                    "is_correct": r.is_correct,
                    "reasoning": r.reasoning
                }
                for r in self.results
            ],
        }

        filename = self.output_filepath
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """Main function to run the benchmark"""
    parser = argparse.ArgumentParser(
        description="JEE 2025 Benchmark - Simple LLM Evaluation System"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to the YAML configuration file (default: config/config.yaml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    load_dotenv(config["dotenv_filepath"])
    benchmark = JEEBenchmark(
        solver_model_params=config["solver_model_params"],
        grader_model_params=config["grader_model_params"],
        max_questions=config["max_questions"],
        input_filepath=config["input_filepath"],
        output_filepath=config["output_filepath"],
        dbfilepath=config["dbfilepath"],
    )

    results = benchmark.run_benchmark()

    if results:
        benchmark.print_detailed_results()
        benchmark.save_results()
        print(f"\nBenchmark completed! Processed {len(results)} questions.")
        benchmark.conn.close()
    else:
        print(
            f"No questions processed. Check your JSON file path ('{config['input_filepath']}') or its content."
        )


if __name__ == "__main__":
    main()
