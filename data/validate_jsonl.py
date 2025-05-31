import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter

def validate_dataset(file_path: str, verbose: bool = True) -> Dict:
    """
    Comprehensive validation of the question dataset.
    
    Args:
        file_path: Path to the JSON file containing questions
        verbose: Whether to print detailed validation results
    
    Returns:
        Dict: Validation results with all checks
    """
    if verbose:
        print(f"{'='*60}")
        print(f"DATASET VALIDATION")
        print(f"{'='*60}")
        print(f"Validating: {file_path}")
    
    # Load the dataset
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    
    if verbose:
        print(f"Loaded {len(questions)} questions")
    
    # Initialize validation results
    validation_results = {
        "total_questions": len(questions),
        "papers": {},
        "subjects": set(),
        "validation_passed": True,
        "errors": [],
        "warnings": []
    }
    
    # Organize data by paper and subject
    paper_data = defaultdict(lambda: defaultdict(list))
    subject_counts = defaultdict(lambda: defaultdict(int))
    
    for i, question in enumerate(questions):
        paper = question.get("paper")
        subject = question.get("subject")
        question_number = question.get("question_number")
        
        if paper is None:
            validation_results["errors"].append(f"Question {i}: Missing 'paper' field")
            validation_results["validation_passed"] = False
            continue
            
        if subject is None:
            validation_results["errors"].append(f"Question {i}: Missing 'subject' field")
            validation_results["validation_passed"] = False
            continue
            
        paper_data[paper][subject].append(question)
        subject_counts[paper][subject] += 1
        validation_results["subjects"].add(subject)
    
    # Store paper information
    for paper in paper_data:
        validation_results["papers"][paper] = {
            "total_questions": sum(len(questions) for questions in paper_data[paper].values()),
            "subjects": dict(subject_counts[paper])
        }
    
    if verbose:
        print(f"\nDataset Overview:")
        print(f"Papers found: {sorted(validation_results['papers'].keys())}")
        print(f"Subjects found: {sorted(validation_results['subjects'])}")
        for paper, info in validation_results["papers"].items():
            print(f"Paper {paper}: {info['total_questions']} questions")
            for subject, count in info["subjects"].items():
                print(f"  {subject}: {count} questions")
    
    # VALIDATION 1: Equal number of questions between papers
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION 1: Equal questions per paper")
        print(f"{'='*60}")
    
    paper_question_counts = [info["total_questions"] for info in validation_results["papers"].values()]
    if len(set(paper_question_counts)) > 1:
        validation_results["errors"].append(
            f"Unequal number of questions between papers: {dict(zip(validation_results['papers'].keys(), paper_question_counts))}"
        )
        validation_results["validation_passed"] = False
        if verbose:
            print(f"❌ FAILED: Unequal questions per paper")
            for paper, count in zip(validation_results["papers"].keys(), paper_question_counts):
                print(f"  Paper {paper}: {count} questions")
    else:
        if verbose:
            print(f"✅ PASSED: All papers have equal questions ({paper_question_counts[0]} each)")
    
    # VALIDATION 2: Equal questions per subject within each paper
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION 2: Equal questions per subject within each paper")
        print(f"{'='*60}")
    
    for paper, subjects in subject_counts.items():
        subject_question_counts = list(subjects.values())
        if len(set(subject_question_counts)) > 1:
            validation_results["errors"].append(
                f"Paper {paper}: Unequal questions per subject: {dict(subjects)}"
            )
            validation_results["validation_passed"] = False
            if verbose:
                print(f"❌ Paper {paper} FAILED: Unequal questions per subject")
                for subject, count in subjects.items():
                    print(f"  {subject}: {count} questions")
        else:
            if verbose:
                print(f"✅ Paper {paper} PASSED: All subjects have equal questions ({subject_question_counts[0]} each)")
    
    # VALIDATION 3: No missing question numbers
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION 3: No missing question numbers")
        print(f"{'='*60}")
    
    for paper in paper_data:
        for subject in paper_data[paper]:
            questions_in_subject = paper_data[paper][subject]
            question_numbers = [q.get("question_number") for q in questions_in_subject]
            
            # Remove None values and convert to int
            valid_numbers = []
            for i, num in enumerate(question_numbers):
                if num is None:
                    validation_results["errors"].append(
                        f"Paper {paper}, {subject}: Question {i} has missing question_number"
                    )
                    validation_results["validation_passed"] = False
                else:
                    try:
                        valid_numbers.append(int(num))
                    except (ValueError, TypeError):
                        validation_results["errors"].append(
                            f"Paper {paper}, {subject}: Invalid question_number '{num}'"
                        )
                        validation_results["validation_passed"] = False
            
            if valid_numbers:
                expected_range = set(range(1, len(valid_numbers) + 1))
                actual_numbers = set(valid_numbers)
                
                missing_numbers = expected_range - actual_numbers
                duplicate_numbers = [num for num, count in Counter(valid_numbers).items() if count > 1]
                extra_numbers = actual_numbers - expected_range
                
                if missing_numbers:
                    validation_results["errors"].append(
                        f"Paper {paper}, {subject}: Missing question numbers: {sorted(missing_numbers)}"
                    )
                    validation_results["validation_passed"] = False
                
                if duplicate_numbers:
                    validation_results["errors"].append(
                        f"Paper {paper}, {subject}: Duplicate question numbers: {sorted(duplicate_numbers)}"
                    )
                    validation_results["validation_passed"] = False
                
                if extra_numbers:
                    validation_results["warnings"].append(
                        f"Paper {paper}, {subject}: Unexpected question numbers: {sorted(extra_numbers)}"
                    )
                
                if verbose:
                    if missing_numbers or duplicate_numbers:
                        print(f"❌ Paper {paper}, {subject}: Issues found")
                        if missing_numbers:
                            print(f"  Missing: {sorted(missing_numbers)}")
                        if duplicate_numbers:
                            print(f"  Duplicates: {sorted(duplicate_numbers)}")
                        if extra_numbers:
                            print(f"  Extra: {sorted(extra_numbers)}")
                    else:
                        print(f"✅ Paper {paper}, {subject}: All question numbers 1-{len(valid_numbers)} present")
    
    # VALIDATION 4: No null/empty question text
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION 4: No null/empty question text")
        print(f"{'='*60}")
    
    null_question_count = 0
    for i, question in enumerate(questions):
        question_text = question.get("question_text")
        if question_text is None or (isinstance(question_text, str) and question_text.strip() == ""):
            paper = question.get("paper", "unknown")
            subject = question.get("subject", "unknown")
            q_num = question.get("question_number", "unknown")
            validation_results["errors"].append(
                f"Paper {paper}, {subject}, Q{q_num}: Null/empty question_text"
            )
            validation_results["validation_passed"] = False
            null_question_count += 1
    
    if verbose:
        if null_question_count > 0:
            print(f"❌ FAILED: {null_question_count} questions with null/empty question_text")
        else:
            print(f"✅ PASSED: All questions have non-empty question_text")
    
    # VALIDATION 5: No null/empty answer text
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION 5: No null/empty answer text")
        print(f"{'='*60}")
    
    null_answer_count = 0
    for i, question in enumerate(questions):
        answer_text = question.get("answer_text")
        if answer_text is None or (isinstance(answer_text, str) and answer_text.strip() == ""):
            paper = question.get("paper", "unknown")
            subject = question.get("subject", "unknown")
            q_num = question.get("question_number", "unknown")
            validation_results["errors"].append(
                f"Paper {paper}, {subject}, Q{q_num}: Null/empty answer_text"
            )
            validation_results["validation_passed"] = False
            null_answer_count += 1
    
    if verbose:
        if null_answer_count > 0:
            print(f"❌ FAILED: {null_answer_count} questions with null/empty answer_text")
        else:
            print(f"✅ PASSED: All questions have non-empty answer_text")
    
    # FINAL SUMMARY
    if verbose:
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        if validation_results["validation_passed"]:
            print(f"🎉 ALL VALIDATIONS PASSED!")
            print(f"Dataset is consistent and ready for use.")
        else:
            print(f"❌ VALIDATION FAILED")
            print(f"Total errors: {len(validation_results['errors'])}")
            print(f"Total warnings: {len(validation_results['warnings'])}")
        
        if validation_results["errors"]:
            print(f"\nERRORS:")
            for error in validation_results["errors"]:
                print(f"  - {error}")
        
        if validation_results["warnings"]:
            print(f"\nWARNINGS:")
            for warning in validation_results["warnings"]:
                print(f"  - {warning}")
        
        print(f"\n{'='*60}")
    
    return validation_results

def validate_jsonl_dataset(file_path: str, verbose: bool = True) -> Dict:
    """
    Validate a JSONL format dataset.
    
    Args:
        file_path: Path to the JSONL file
        verbose: Whether to print detailed results
    
    Returns:
        Dict: Validation results
    """
    if verbose:
        print(f"Loading JSONL dataset: {file_path}")
    
    questions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        question = json.loads(line)
                        questions.append(question)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    # Convert to JSON format and use existing validation
    temp_json_file = "temp_validation.json"
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    try:
        results = validate_dataset(temp_json_file, verbose)
        Path(temp_json_file).unlink()  # Clean up temp file
        return results
    except Exception as e:
        Path(temp_json_file).unlink(missing_ok=True)  # Clean up temp file
        raise e

def main():
    """Command line interface for dataset validation"""
    parser = argparse.ArgumentParser(
        description="Validate question dataset for consistency and completeness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_dataset.py all_problems.json
  python validate_dataset.py all_problems.jsonl --jsonl
  python validate_dataset.py dataset.json --quiet
  
Validation Checks:
  1. Equal number of questions between papers
  2. Equal number of questions per subject within each paper
  3. No missing question numbers (1, 2, 3, ... n)
  4. No null/empty question text
  5. No null/empty answer text
        """
    )
    
    parser.add_argument("file_path", 
                       help="Path to the dataset file (JSON or JSONL)")
    parser.add_argument("--jsonl", action="store_true",
                       help="Input file is in JSONL format")
    parser.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress detailed output, only show final result")
    
    args = parser.parse_args()
    
    try:
        if args.jsonl:
            results = validate_jsonl_dataset(args.file_path, verbose=not args.quiet)
        else:
            results = validate_dataset(args.file_path, verbose=not args.quiet)
        
        # Return appropriate exit code
        if results["validation_passed"]:
            if args.quiet:
                print("✅ Dataset validation PASSED")
            return 0
        else:
            if args.quiet:
                print("❌ Dataset validation FAILED")
                print(f"Errors: {len(results['errors'])}")
                for error in results["errors"]:
                    print(f"  - {error}")
            return 1
            
    except Exception as e:
        print(f"Error during validation: {e}")
        return 1

# Quick validation function for your specific use case
def quick_validate(file_path: str = "all_problems.json") -> bool:
    """
    Quick validation function that returns True if dataset is valid.
    
    Args:
        file_path: Path to the dataset file
    
    Returns:
        bool: True if all validations pass, False otherwise
    """
    try:
        results = validate_dataset(file_path, verbose=False)
        return results["validation_passed"]
    except Exception as e:
        print(f"Validation error: {e}")
        return False

if __name__ == "__main__":
    exit(main())