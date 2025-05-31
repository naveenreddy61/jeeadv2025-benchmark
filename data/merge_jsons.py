import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any

try:
    from datasets import Dataset
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False

def extract_paper_number(filename: str) -> int:
    """
    Extract paper number from filename.
    
    Args:
        filename: The filename to extract number from
    
    Returns:
        int: Extracted paper number, or raises ValueError if not found
    """
    # Try to extract number from filename like "paper_1.json", "paper1.json", "test_paper_2.json", etc.
    filename_stem = Path(filename).stem  # Remove extension
    
    # Look for patterns like "paper_1", "paper1", "1", etc.
    patterns = [
        r'paper[_-]?(\d+)',  # paper_1, paper-1, paper1
        r'(\d+)[_-]?paper',  # 1_paper, 1-paper, 1paper
        r'(?:^|[_-])(\d+)(?:[_-]|$)',  # any number with separators or at boundaries
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename_stem, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # If no pattern matches, try to find any digit sequence
    digits = re.findall(r'\d+', filename_stem)
    if digits:
        return int(digits[0])  # Take the first number found
    
    raise ValueError(f"Could not extract paper number from filename: {filename}")

def merge_question_papers(paper_files: List[str], output_file: str = "all_problems", 
                         create_json: bool = True, create_jsonl: bool = True, 
                         create_hf: bool = True, verbose: bool = True):
    """
    Merge multiple question paper JSON files into a single dataset format.
    Paper numbers are extracted from filenames (e.g., "paper_1.json" -> paper: 1).
    
    Args:
        paper_files: List of input JSON file paths
        output_file: Base output file name (without extension)
        create_json: Whether to create JSON format
        create_jsonl: Whether to create JSONL format  
        create_hf: Whether to create HuggingFace dataset format
        verbose: Whether to print progress information
    
    Returns:
        List[Dict]: Combined list of all questions
    """
    all_questions = []
    
    for paper_file in paper_files:
        paper_path = Path(paper_file)
        
        if not paper_path.exists():
            if verbose:
                print(f"Warning: File {paper_file} not found, skipping...")
            continue
        
        # Extract paper number from filename
        try:
            paper_number = extract_paper_number(paper_file)
        except ValueError as e:
            if verbose:
                print(f"Warning: {e}, using filename as paper identifier")
            paper_number = paper_path.stem  # Use filename without extension as fallback
        
        if verbose:
            print(f"Processing {paper_file} (Paper {paper_number})...")
        
        try:
            # Load the JSON file
            with open(paper_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # Extract questions from all results
            questions_count = 0
            
            # Handle the structure from your batch processing script
            results = paper_data.get('results', [])
            
            for result in results:
                # Skip failed extractions
                if result.get('processing_status') != 'success':
                    continue
                
                questions = result.get('questions', [])
                
                for question in questions:
                    # Create a new question entry with paper information
                    question_entry = {
                        "year": "2025",
                        "subject": question.get("subject"),
                        "question_number": question.get("question_number"),
                        "question_text": question.get("question_text"),
                        "question_figure_description": question.get("question_figure_description"),
                        "answer_text": question.get("answer_text"),
                        "paper": paper_number,
                        "source_file": result.get("file_name")  # Optional: keep track of original image file
                    }
                    
                    all_questions.append(question_entry)
                    questions_count += 1
            
            if verbose:
                print(f"  ✓ Extracted {questions_count} questions from Paper {paper_number}")
        
        except json.JSONDecodeError as e:
            if verbose:
                print(f"  ✗ Error parsing JSON in {paper_file}: {e}")
        except Exception as e:
            if verbose:
                print(f"  ✗ Error processing {paper_file}: {e}")
    
    # Sort questions by paper and then by question number for consistency
    # Handle case where paper might be int or string
    # def sort_key(x):
    #     paper = x.get("paper", 0)
    #     # Convert to int if possible for proper sorting
    #     if isinstance(paper, str) and paper.isdigit():
    #         paper = int(paper)
    #     return (paper, x.get("question_number", 0))
    def sort_key(x):
        paper = x.get("paper", 0)
        # Convert to int if possible for proper sorting
        if isinstance(paper, str) and paper.isdigit():
            paper = int(paper)
        
        # Define custom subject order
        subject_order = {"mathematics": 1, "physics": 2, "chemistry": 3}
        subject = x.get("subject", "")
        subject_sort_value = subject_order.get(subject, 999)  # Unknown subjects go last
        
        question_number = x.get("question_number", 0)
        return (paper, subject_sort_value, question_number)    
    all_questions.sort(key=sort_key)
    
    # Create output files in different formats
    output_path = Path(output_file)
    created_files = []
    
    try:
        # 1. Create JSON format
        if create_json:
            json_file = output_path.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(all_questions, f, indent=2, ensure_ascii=False)
            created_files.append(("JSON", str(json_file.absolute())))
            if verbose:
                print(f"✓ JSON format saved to: {json_file}")
        
        # 2. Create JSONL format
        if create_jsonl:
            jsonl_file = output_path.with_suffix('.jsonl')
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for question in all_questions:
                    json.dump(question, f, ensure_ascii=False)
                    f.write('\n')
            created_files.append(("JSONL", str(jsonl_file.absolute())))
            if verbose:
                print(f"✓ JSONL format saved to: {jsonl_file}")
        
        # 3. Create HuggingFace dataset format
        if create_hf:
            if HF_DATASETS_AVAILABLE:
                hf_dir = output_path.with_suffix('_dataset')
                dataset = Dataset.from_list(all_questions)
                dataset.save_to_disk(str(hf_dir))
                created_files.append(("HuggingFace Dataset", str(hf_dir.absolute())))
                if verbose:
                    print(f"✓ HuggingFace dataset saved to: {hf_dir}")
            else:
                if verbose:
                    print("⚠ HuggingFace datasets library not available. Install with: pip install datasets")
                    print("  Skipping HuggingFace dataset creation.")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Dataset creation complete!")
            print(f"Total questions: {len(all_questions)}")
            
            # Print summary by paper
            paper_counts = {}
            subject_counts = {}
            
            for q in all_questions:
                paper_num = q.get("paper", "unknown")
                subject = q.get("subject", "unknown")
                
                paper_counts[paper_num] = paper_counts.get(paper_num, 0) + 1
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
            
            print(f"\nBreakdown by paper:")
            for paper, count in sorted(paper_counts.items()):
                print(f"  Paper {paper}: {count} questions")
            
            print(f"\nBreakdown by subject:")
            for subject, count in sorted(subject_counts.items()):
                print(f"  {subject.title()}: {count} questions")
            
            print(f"\nFiles created:")
            for format_name, file_path in created_files:
                print(f"  {format_name}: {file_path}")
            
            print(f"{'='*60}")
    
    except Exception as e:
        if verbose:
            print(f"Error saving merged dataset: {e}")
        raise
    
    return all_questions

def create_jsonl_version(questions: List[Dict], output_file: str = "all_problems.jsonl"):
    """
    Create a JSONL version of the dataset (one JSON object per line).
    
    Args:
        questions: List of question dictionaries
        output_file: Output JSONL file name
    """
    output_path = Path(output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for question in questions:
            json.dump(question, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"JSONL version saved to: {output_path.absolute()}")

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Merge multiple question paper JSON files into a single dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python merge_papers.py paper_1.json paper_2.json
  python merge_papers.py paper_1.json paper_2.json -o dataset.json
  python merge_papers.py exam_paper_*.json --jsonl
  
Note: Paper numbers are automatically extracted from filenames
  - "paper_1.json" -> paper: 1
  - "paper_2.json" -> paper: 2
  - "test_paper_3.json" -> paper: 3
        """
    )
    
    parser.add_argument("input_files", nargs="+",
                       help="Input JSON files to merge")
    parser.add_argument("-o", "--output", 
                       default="all_problems.json",
                       help="Output JSON file name (default: all_problems.json)")
    parser.add_argument("--jsonl", action="store_true",
                       help="Also create a JSONL version of the dataset")
    parser.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    try:
        # Merge the papers
        all_questions = merge_question_papers(
            paper_files=args.input_files,
            output_file=args.output,
            verbose=not args.quiet
        )
        
        # Create JSONL version if requested
        if args.jsonl:
            jsonl_file = Path(args.output).with_suffix('.jsonl')
            create_jsonl_version(all_questions, str(jsonl_file))
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

# Quick function for your specific use case
def merge_paper_1_and_2(output_file: str = "all_problems", formats: str = "all"):
    """
    Convenience function to merge paper_1.json and paper_2.json specifically.
    Paper numbers (1 and 2) will be automatically extracted from the filenames.
    
    Args:
        output_file: Base output filename (without extension)
        formats: Which formats to create - "all", "json", "jsonl", "hf", or combination like "json,jsonl"
    
    Returns:
        List[Dict]: Combined questions with paper: 1 and paper: 2 respectively
    """
    # Parse format options
    if formats == "all":
        create_json, create_jsonl, create_hf = True, True, True
    else:
        format_list = [f.strip().lower() for f in formats.split(",")]
        create_json = "json" in format_list
        create_jsonl = "jsonl" in format_list
        create_hf = "hf" in format_list or "huggingface" in format_list
    
    return merge_question_papers(
        paper_files=["paper_1.json", "paper_2.json"],
        output_file=output_file,
        create_json=create_json,
        create_jsonl=create_jsonl,
        create_hf=create_hf,
        verbose=True
    )

if __name__ == "__main__":
    exit(main())

# Additional usage examples and format comparison
"""
USAGE EXAMPLES:

1. Command Line - Create all formats:
   python merge_papers.py paper_1.json paper_2.json

2. Command Line - Create specific formats:
   python merge_papers.py paper_1.json paper_2.json --jsonl-only
   python merge_papers.py paper_1.json paper_2.json --no-hf

3. Python - Quick merge with all formats:
   from merge_papers import merge_paper_1_and_2
   questions = merge_paper_1_and_2("my_dataset")

4. Python - Specific formats:
   questions = merge_paper_1_and_2("my_dataset", "json,jsonl")

5. Inspect created datasets:
   python merge_papers.py paper_1.json paper_2.json --inspect

FORMAT COMPARISON:

📄 JSON (all_problems.json):
   - Human readable with indentation
   - Easy to inspect and debug
   - Must load entire file into memory
   - Good for: Small datasets, exploration, sharing

📝 JSONL (all_problems.jsonl):
   - One question per line
   - Streamable and memory efficient
   - Standard for ML pipelines
   - Good for: Training, large datasets, production

🤗 HuggingFace Dataset (all_problems_dataset/):
   - Optimized columnar format
   - Fast filtering and transformations
   - Rich metadata and features
   - Good for: Advanced ML, research, analysis

LOADING EXAMPLES:

# JSON
import json
with open('all_problems.json', 'r') as f:
    questions = json.load(f)

# JSONL
import json
questions = []
with open('all_problems.jsonl', 'r') as f:
    for line in f:
        questions.append(json.loads(line))

# HuggingFace Dataset
from datasets import Dataset
dataset = Dataset.load_from_disk('all_problems_dataset')
questions = dataset.to_list()  # Convert back to list if needed
"""