from dotenv import load_dotenv
load_dotenv("C:\\API_KEYS\\.env")

import dspy
import json
import os
from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import argparse
from tqdm import tqdm
from datetime import datetime

# Configure DSPy
lm = dspy.LM("gemini/gemini-2.0-flash")
# Alternative models (uncomment as needed):
# lm = dspy.LM('openai/gpt-4o-mini')
# lm = dspy.LM("gemini/gemini-2.5-flash-preview-05-20")

dspy.settings.configure(lm=lm, max_tokens = 8000, temperature = 0.2)
dspy.settings.configure(track_usage=True)

# Define the same models and signature from your original script
class ImageInstructionsOutput(BaseModel):
    rules: Optional[str] = Field(
        None,
        description="OCR and repeat the text of any section instructions detected in the image, or None if no such are present",
    )
    section: Optional[int] = Field(
        None,
        description="The section number of the instructions detected in the image, or None if no section headers are found",
    )

class QuestionAnswerOutput(BaseModel):
    subject: Literal["mathematics", "physics", "chemistry"] = Field(
        ...,
        description="The subject of the questions in the image, one of 'mathematics', 'physics', or 'chemistry'",
    )
    question_number: int = Field(
        ..., description="The number of the question in the image"
    )
    question_text: str = Field(
        ...,
        description="""OCR the text of the question as it is. use latex for symbols and equations
                       Include the options. Do not include the answer which is below the corresponding question.
                       whenever required to output something in LaTeX.""",
    )
    question_figure_description: Optional[str] = Field(
        None,
        description="""If the question or options of the question contain any figures or diagrams as part of the question,
                       describe the corresponding figure or diagram in detail in text
                       whenever required to output something in LaTeX.""",
    )
    answer_text: str = Field(
        ...,
        description="The text of the answer to the question, as extracted from the image that comes after Answer:",
    )

class FilePDFSignature2(dspy.Signature):
    document: dspy.Image = dspy.InputField(
        desc="Image from a pdf document which contains exam questions and answers"
    )
    section_instructions: ImageInstructionsOutput = dspy.OutputField()
    questions: List[QuestionAnswerOutput] = dspy.OutputField(
        desc="List of questions and answers extracted from the image"
    )

def process_folder(input_folder: str, output_file: str = "extracted_questions.json", verbose: bool = True):
    """
    Process all images in the input folder and extract questions/answers
    
    Args:
        input_folder: Path to folder containing images
        output_file: Output JSON file name
        verbose: Whether to print detailed progress
    
    Returns:
        dict: Combined results with metadata
    """
    predictor = dspy.Predict(FilePDFSignature2)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder {input_folder} does not exist")
    
    image_files = [f for f in input_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    # Sort files for consistent processing order
    image_files.sort(key=lambda x: x.name)
    
    if not image_files:
        print(f"No image files found in {input_folder}")
        return None
    
    if verbose:
        print(f"Found {len(image_files)} image files to process")
        print(f"Supported extensions: {', '.join(image_extensions)}")
    
    # Process each image
    all_results = []
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    successful_count = 0
    failed_count = 0
    
    # Use tqdm for progress bar
    for img_file in tqdm(image_files, desc="Processing images", disable=not verbose):
        try:
            if verbose:
                print(f"Processing: {img_file.name}")
            
            # Load image
            pdf_image = dspy.Image.from_file(str(img_file))
            
            # Get prediction
            result = predictor(document=pdf_image)
            
            # Get usage info
            usage = result.get_lm_usage() if hasattr(result, 'get_lm_usage') else None
            if usage:
                for key in total_usage:
                    if key in usage:
                        total_usage[key] += usage[key]
            
            # Store result with metadata
            result_data = {
                "file_name": img_file.name,
                "file_path": str(img_file.relative_to(input_path)),
                "processing_status": "success",
                "section_instructions": {
                    "rules": result.section_instructions.rules,
                    "section": result.section_instructions.section
                } if result.section_instructions else None,
                "questions": [
                    {
                        "subject": q.subject,
                        "question_number": q.question_number,
                        "question_text": q.question_text,
                        "question_figure_description": q.question_figure_description,
                        "answer_text": q.answer_text
                    }
                    for q in (result.questions if result.questions else [])
                ],
                "questions_count": len(result.questions) if result.questions else 0,
                "usage": usage,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            all_results.append(result_data)
            successful_count += 1
            
            if verbose:
                print(f"  ✓ Extracted {len(result.questions) if result.questions else 0} questions")
            
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            if verbose:
                print(f"  ✗ Error processing {img_file.name}: {error_msg}")
            
            # Store error info
            error_data = {
                "file_name": img_file.name,
                "file_path": str(img_file.relative_to(input_path)),
                "processing_status": "failed",
                "error": error_msg,
                "section_instructions": None,
                "questions": [],
                "questions_count": 0,
                "usage": None,
                "processing_timestamp": datetime.now().isoformat()
            }
            all_results.append(error_data)
    
    # Calculate summary statistics
    total_questions = sum(r.get("questions_count", 0) for r in all_results if r.get("processing_status") == "success")
    
    # Combine all results
    combined_results = {
        "metadata": {
            "total_files_processed": len(image_files),
            "successful_extractions": successful_count,
            "failed_extractions": failed_count,
            "total_questions_extracted": total_questions,
            "total_usage": total_usage,
            "input_folder": str(input_path.absolute()),
            "output_file": str(Path(output_file).absolute()),
            "processing_timestamp": datetime.now().isoformat(),
            "model_used": str(lm.model) if hasattr(lm, 'model') else "gemini/gemini-2.0-flash",
            "supported_extensions": list(image_extensions)
        },
        "results": all_results
    }
    
    # Save to JSON
    output_path = Path(output_file)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"Processing complete!")
            print(f"Results saved to: {output_path.absolute()}")
            print(f"Total files processed: {len(image_files)}")
            print(f"Successful extractions: {successful_count}")
            print(f"Failed extractions: {failed_count}")
            print(f"Total questions extracted: {total_questions}")
            print(f"Total token usage: {total_usage}")
            print(f"{'='*50}")
    
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")
        raise
    
    return combined_results

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Extract questions and answers from exam paper images using DSPy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py ./question-paper/
  python script.py ./images/ -o results.json
  python script.py ./exam_images/ -o output/exam_results.json --quiet
        """
    )
    
    parser.add_argument("input_folder", 
                       help="Path to folder containing image files")
    parser.add_argument("-o", "--output", 
                       
                       help="Output JSON file name")
    parser.add_argument("-q", "--quiet", 
                       action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    try:
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process the folder
        results = process_folder(
            input_folder=args.input_folder, 
            output_file=args.output,
            verbose=not args.quiet
        )
        
        if results is None:
            print("No files to process.")
            return 1
            
        # Return 0 for success, 1 if there were any failures
        return 0 if results["metadata"]["failed_extractions"] == 0 else 1
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

# Interactive usage function
def process_interactive(input_folder: str, output_file: str = None):
    """
    Interactive function for use in notebooks or scripts
    
    Args:
        input_folder: Path to folder containing images
        output_file: Optional output file name
    
    Returns:
        dict: Processing results
    """
    if output_file is None:
        folder_name = Path(input_folder).name
        output_file = f"extracted_questions_{folder_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return process_folder(input_folder, output_file, verbose=True)

if __name__ == "__main__":
    exit(main())