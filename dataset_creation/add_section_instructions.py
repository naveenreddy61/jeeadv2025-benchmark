import json
import argparse
from pathlib import Path
from typing import Dict, List

# Define section instructions mapping
section_instructions= {
1 : '''
Each question has FOUR options (A), (B), (C) and (D). ONLY ONE of these four options is the correct answer.
For each question, choose the option corresponding to the correct answer.
Answer to each question will be evaluated according to the following marking scheme:
Full Marks: +3 If ONLY the correct option is chosen;
Zero Marks: 0 If none of the options is chosen (i.e. the question is unanswered);
Negative Marks: -1 In all other cases.
''',
2 :'''
Each question has FOUR options (A), (B), (C) and (D). ONE OR MORE THAN ONE of these four option(s) is(are) correct answer(s).
For each question, choose the option(s) corresponding to the all) the correct answer(s).
Answer to each question will be evaluated according to the following marking scheme:
Full Marks: +4 If ONLY the all correct option(s) is(are) chosen;
Partial Marks: +3 If three or four options are correct but ONLY three options are chosen;
Partial Marks: +2 If three or four options are correct but ONLY two options are chosen, both of which are correct;
Partial Marks: +1 If two or more options are correct but ONLY one option is chosen and it is a correct option;
Zero Marks: 0 If none of the options is chosen (i.e. the question is unanswered);
Negative Marks: -2 In all other cases.
For example in a question, if (A), (B) and (D) are the ONLY three options corresponding to correct answers, then
choosing ONLY (A), (B) and (D) will get +4 marks;
choosing ONLY (A) and (B) will get +2 marks;
choosing ONLY (A) and (D) will get +2 marks;
choosing ONLY (B) and (D) will get +2 marks;
choosing ONLY (A) will get +1 mark;
choosing ONLY (B) will get +1 mark;
choosing ONLY (D) will get +1 mark;
choosing no option (i.e. the question is unanswered) will get 0 marks; and
choosing any other combination of options will get -2 marks.
''',
3:'''
The answer to each question is a NUMERICAL VALUE.
For each question, enter the correct numerical value of the answer using the mouse and the on-screen virtual numeric keypad in the place designated to enter the answer.
If the numerical value has more than two decimal places, truncate/round-off the value to TWO decimal places.
Answer to each question will be evaluated according to the following marking scheme:
Full Marks: +4 If ONLY the correct numerical value is entered in the designated place;
Zero Marks: 0 In all other cases.
''',
4:'''
Multiple Choice Matching List Sets.
Each set has ONE Multiple Choice Question.
Each set has TWO lists: List-I and List-II.
List-I has Four entries (P), (Q), (R) and (S) and List-II has Five entries (1), (2), (3), (4) and (5).
FOUR options are given in each Multiple Choice Question based on List-I and List-II and ONLY ONE of these four options satisfies the condition asked in the Multiple Choice Question.
Answer to each question will be evaluated according to the following marking scheme:
Full Marks : +4 ONLY if the option corresponding to the correct combination is chosen;
Zero Marks : 0 If none of the options is chosen (i.e. the question is unanswered);
Negative Marks : -1 In all other cases.
'''

}

def get_question_instruction(paper: int, question_number: int) -> str:
    """
    Get the instruction for a question based on paper and question number.
    
    Paper 1: Q1-4→format1, Q5-7→format2, Q8-13→format3, Q14-16→format4
    Paper 2: Q1-4→format1, Q5-8→format2, Q9-16→format3
    
    Args:
        paper: Paper number (1 or 2)
        question_number: Question number
    
    Returns:
        str: The instruction text for this question
    """
    if paper == 1:
        if 1 <= question_number <= 4:
            return section_instructions[1]
        elif 5 <= question_number <= 7:
            return section_instructions[2]
        elif 8 <= question_number <= 13:
            return section_instructions[3]
        elif 14 <= question_number <= 16:
            return section_instructions[4]
    elif paper == 2:
        if 1 <= question_number <= 4:
            return section_instructions[1]
        elif 5 <= question_number <= 8:
            return section_instructions[2]
        elif 9 <= question_number <= 16:
            return section_instructions[3]
    
    # Fallback for unknown ranges
    return section_instructions.get(1, "")

def enhance_dataset(input_file: str, output_base: str = "enhanced_problems", 
                   create_json: bool = True, create_jsonl: bool = True, 
                   verbose: bool = True) -> List[Dict]:
    """
    Enhance existing dataset by adding question_instruction field.
    
    Args:
        input_file: Path to input JSON file
        output_base: Base name for output files (without extension)
        create_json: Whether to create JSON output
        create_jsonl: Whether to create JSONL output
        verbose: Whether to print progress
    
    Returns:
        List[Dict]: Enhanced questions list
    """
    if verbose:
        print(f"{'='*60}")
        print(f"DATASET ENHANCEMENT")
        print(f"{'='*60}")
        print(f"Input file: {input_file}")
    
    # Load existing dataset
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {input_file}: {e}")
    
    if verbose:
        print(f"Loaded {len(questions)} questions")
    
    # Enhance each question with instruction
    enhanced_questions = []
    instruction_stats = {}
    
    for question in questions:
        paper = question.get("paper")
        question_number = question.get("question_number")
        
        # Get the appropriate instruction
        instruction = get_question_instruction(paper, question_number)
        
        # Create enhanced question
        enhanced_question = question.copy()
        enhanced_question["question_instruction"] = instruction
        enhanced_questions.append(enhanced_question)
        
        # Track instruction usage for stats
        key = f"Paper {paper}, Q{question_number}"
        if instruction in instruction_stats:
            instruction_stats[instruction] += 1
        else:
            instruction_stats[instruction] = 1
    
    if verbose:
        print(f"Enhanced {len(enhanced_questions)} questions")
        print(f"\nInstruction usage statistics:")
        for instruction, count in instruction_stats.items():
            preview = (instruction[:50] + "...") if len(instruction) > 50 else instruction
            print(f"  '{preview}': {count} questions")
    
    # Save enhanced dataset
    output_path = Path(output_base)
    created_files = []
    
    try:
        # Create JSON format
        if create_json:
            json_file = output_path.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_questions, f, indent=2, ensure_ascii=False)
            created_files.append(("JSON", str(json_file.absolute())))
            if verbose:
                print(f"✓ Enhanced JSON saved to: {json_file}")
        
        # Create JSONL format
        if create_jsonl:
            jsonl_file = output_path.with_suffix('.jsonl')
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for question in enhanced_questions:
                    json.dump(question, f, ensure_ascii=False)
                    f.write('\n')
            created_files.append(("JSONL", str(jsonl_file.absolute())))
            if verbose:
                print(f"✓ Enhanced JSONL saved to: {jsonl_file}")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"ENHANCEMENT COMPLETE")
            print(f"{'='*60}")
            print(f"Files created:")
            for format_name, file_path in created_files:
                print(f"  {format_name}: {file_path}")
            print(f"{'='*60}")
    
    except Exception as e:
        if verbose:
            print(f"Error saving enhanced dataset: {e}")
        raise
    
    return enhanced_questions

def enhance_jsonl_dataset(input_file: str, output_base: str = "enhanced_problems", 
                         verbose: bool = True) -> List[Dict]:
    """
    Enhance JSONL dataset by adding question_instruction field.
    
    Args:
        input_file: Path to input JSONL file
        output_base: Base name for output files
        verbose: Whether to print progress
    
    Returns:
        List[Dict]: Enhanced questions list
    """
    if verbose:
        print(f"Loading JSONL dataset: {input_file}")
    
    # Load JSONL dataset
    questions = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        question = json.loads(line)
                        questions.append(question)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"JSONL file not found: {input_file}")
    
    # Convert to JSON format temporarily and use existing enhancement
    temp_json_file = "temp_enhance.json"
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    try:
        enhanced_questions = enhance_dataset(temp_json_file, output_base, 
                                           create_json=True, create_jsonl=True, 
                                           verbose=verbose)
        Path(temp_json_file).unlink()  # Clean up temp file
        return enhanced_questions
    except Exception as e:
        Path(temp_json_file).unlink(missing_ok=True)  # Clean up temp file
        raise e

def validate_instruction_mapping(input_file: str, verbose: bool = True) -> Dict:
    """
    Validate that the instruction mapping covers all questions in the dataset.
    
    Args:
        input_file: Path to input JSON file
        verbose: Whether to print detailed results
    
    Returns:
        Dict: Validation results
    """
    if verbose:
        print(f"{'='*60}")
        print(f"INSTRUCTION MAPPING VALIDATION")
        print(f"{'='*60}")
    
    # Load dataset
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except Exception as e:
        raise ValueError(f"Error loading dataset: {e}")
    
    # Check each question
    unmapped_questions = []
    paper_question_ranges = {}
    
    for question in questions:
        paper = question.get("paper")
        question_number = question.get("question_number")
        subject = question.get("subject")
        
        # Track question ranges per paper
        if paper not in paper_question_ranges:
            paper_question_ranges[paper] = {"min": question_number, "max": question_number}
        else:
            paper_question_ranges[paper]["min"] = min(paper_question_ranges[paper]["min"], question_number)
            paper_question_ranges[paper]["max"] = max(paper_question_ranges[paper]["max"], question_number)
        
        # Check if instruction mapping exists
        instruction = get_question_instruction(paper, question_number)
        if instruction == section_instructions.get(1, ""):  # Fallback was used
            if not (paper == 1 and 1 <= question_number <= 4) and not (paper == 2 and 1 <= question_number <= 4):
                unmapped_questions.append({
                    "paper": paper,
                    "subject": subject,
                    "question_number": question_number
                })
    
    if verbose:
        print(f"Question ranges found:")
        for paper, ranges in paper_question_ranges.items():
            print(f"  Paper {paper}: Q{ranges['min']} to Q{ranges['max']}")
        
        if unmapped_questions:
            print(f"\n❌ UNMAPPED QUESTIONS FOUND:")
            for q in unmapped_questions:
                print(f"  Paper {q['paper']}, {q['subject']}, Q{q['question_number']}")
        else:
            print(f"\n✅ ALL QUESTIONS HAVE INSTRUCTION MAPPINGS")
    
    return {
        "all_mapped": len(unmapped_questions) == 0,
        "unmapped_questions": unmapped_questions,
        "paper_ranges": paper_question_ranges
    }

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Enhance question dataset by adding question_instruction field",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhance_dataset.py all_problems.json
  python enhance_dataset.py all_problems.jsonl --jsonl
  python enhance_dataset.py dataset.json -o enhanced_dataset
  python enhance_dataset.py all_problems.json --validate-only
  
Instruction Mapping:
  Paper 1: Q1-4→format1, Q5-7→format2, Q8-13→format3, Q14-16→format4
  Paper 2: Q1-4→format1, Q5-8→format2, Q9-16→format3
        """
    )
    
    parser.add_argument("input_file", 
                       help="Path to input dataset file (JSON or JSONL)")
    parser.add_argument("-o", "--output", 
                       default="enhanced_problems",
                       help="Base output filename without extension (default: enhanced_problems)")
    parser.add_argument("--jsonl", action="store_true",
                       help="Input file is in JSONL format")
    parser.add_argument("--json-only", action="store_true",
                       help="Create only JSON output")
    parser.add_argument("--jsonl-only", action="store_true",
                       help="Create only JSONL output")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate instruction mapping, don't enhance dataset")
    parser.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    try:
        # Validate instruction mapping first
        if args.validate_only:
            validation = validate_instruction_mapping(args.input_file, verbose=not args.quiet)
            return 0 if validation["all_mapped"] else 1
        
        # Determine output formats
        if args.json_only:
            create_json, create_jsonl = True, False
        elif args.jsonl_only:
            create_json, create_jsonl = False, True
        else:
            create_json, create_jsonl = True, True
        
        # Enhance dataset
        if args.jsonl:
            enhanced_questions = enhance_jsonl_dataset(
                args.input_file, args.output, verbose=not args.quiet
            )
        else:
            enhanced_questions = enhance_dataset(
                args.input_file, args.output, 
                create_json=create_json, create_jsonl=create_jsonl,
                verbose=not args.quiet
            )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

# Quick enhancement function
def quick_enhance(input_file: str = "all_problems.json", 
                 output_base: str = "enhanced_problems") -> List[Dict]:
    """
    Quick enhancement function for interactive use.
    
    Args:
        input_file: Input dataset file
        output_base: Base name for output files
    
    Returns:
        List[Dict]: Enhanced questions
    """
    return enhance_dataset(input_file, output_base, verbose=True)

if __name__ == "__main__":
    exit(main())