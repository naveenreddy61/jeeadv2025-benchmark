# JEE Advanced 2025 AI Benchmark

This repository contains a comprehensive benchmark for evaluating Large Language Models (LLMs) on the Joint Entrance Examination (JEE) Advanced 2025, India's premier engineering entrance exam.

## About JEE Advanced 2025

JEE Advanced is one of the world's most challenging undergraduate entrance examinations, serving as the gateway to India's prestigious Indian Institutes of Technology (IITs). The 2025 exam featured several key characteristics:

- **Structure**: Two mandatory papers (Paper 1 & Paper 2), each 3 hours long
- **Subjects**: Physics, Chemistry, and Mathematics (equal weightage)
- **Total Questions**: 96 questions across both papers
- **Total Marks**: 360 marks (180 per paper, 60 per subject)
- **Question Types**: Multiple Choice (single/multiple correct), Numerical Answer Type, Match the Following

## Benchmark Results

Benchmark applied on all 96 questions from JEE Advanced 2025:

## Benchmark Results

Benchmark applied on all 96 questions from JEE Advanced 2025:

| Model | Questions Correct | Accuracy | Total Marks |
|-------|------------------|----------|-------------|
| **Gemini 2.5 Pro** | **87/96** | **90.6%** | **319/360** |
| Gemini 2.5 Flash | 83/96 | 86.5% | 302/360 |
| OpenAI o4-mini | 81/96 | 84.4% | 300/360 |
| DeepSeek R1 | 78/96 | 81.2%| 282/360 |
| Grok 3 Mini | 78/96 | 81.2% | 284/360 |
| Gemini 2.0 Flash | 70/96 | 72.9% | 238/360 |
| GPT-4o Mini | 38/96 | 39.6% | 111/360 |

### Subject-wise Performance

| Model | Mathematics | Physics | Chemistry |
|-------|-------------|---------|-----------|
| **Gemini 2.5 Pro** | **32/32 (100%)** | **29/32 (90.6%)** | 26/32 (81.2%) |
| Gemini 2.5 Flash | **32/32 (100%)** | 24/32 (75.0%) | **27/32 (84.4%)** |
| **DeepSeek R1** | **32/32 (100%)** | 23/32 (71.9%) | 23/32 (71.9%) |
| OpenAI o4-mini | 30/32 (93.8%) | 24/32 (75.0%) | **27/32 (84.4%)** |
| Grok 3 Mini | 30/32 (93.8%) | 23/32 (71.9%) | 25/32 (78.1%) |
| Gemini 2.0 Flash | 26/32 (81.2%) | 23/32 (71.9%) | 21/32 (65.6%) |
| GPT-4o Mini | 13/32 (40.6%) | 14/32 (43.8%) | 11/32 (34.4%) |

### Paper-wise Performance

| Paper | Gemini 2.0 Flash | Gemini 2.5 Flash | Gemini 2.5 Pro | OpenAI o4-mini | DeepSeek R1 | Grok 3 Mini | GPT-4o Mini |
|-------|------------------|-------------------|-----------------|----------------|-------------|-------------|-------------|
| **Paper 1** | 34/48 (70.8%) | 44/48 (91.7%) | **45/48 (93.8%)** | 40/48 (83.3%) | 39/48 (81.2%) | 39/48 (81.2%) | 23/48 (47.9%) |
| **Paper 2** | 36/48 (75.0%) | 39/48 (81.2%) | **42/48 (87.5%)** | 41/48 (85.4%) | 39/48 (81.2%) | 39/48 (81.2%) | 15/48 (31.2%) |

## Key Findings

- **Perfect Mathematical Reasoning**: Both Gemini 2.5 models and latest DeepSeek R1 achieved 100% accuracy on mathematics questions
- **Strong Physics Performance**: Gemini 2.5 Pro solved 90.6% of physics problems correctly
- **Chemistry Challenges**: All models found chemistry most difficult, highlighting the complexity of factual scientific knowledge
- **Consistent Improvement**: Clear performance scaling from 2.0 Flash → 2.5 Flash → 2.5 Pro

## Methodology

- **Evaluation Type**: Pass@1 (single attempt per question)
- **Temperature**: 0.3 for all models
- **Output Limits**: 2.0 Flash (8K tokens), 2.5 Flash (16K tokens), 2.5 Pro (32K tokens), R1 (32K tokens), Grok 3 Mini (8K tokens), OpenAI o4-mini (20K tokens), OpenAI 4o Mini (8K tokens)
- **Question Format**: Text-only with LLM-generated descriptions for diagrams/figures
- **Framework**: DSPy for structured prompting and evaluation

## Installation & Setup

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- API access to Google Gemini models

### Clone the Repository

```bash
git clone https://github.com/yourusername/jee-advanced-2025-benchmark.git
cd jee-advanced-2025-benchmark
```

### Install Dependencies

```bash
uv sync
```

This will create a virtual environment and install all dependencies from `pyproject.toml`.

### Environment Setup

1. Create a `.env` file with your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

2. Update the `.env` file path in `config/config.yaml`:
```yaml
dotenv_filepath: "/path/to/your/.env"  # Update with your actual path
```

## Usage

### Quick Start

Run the benchmark with default settings:

```bash
uv run benchmark.py
```

### Custom Configuration

Modify `config/config_my_fav_llm.yaml` to customize:

```yaml
input_filepath: "jeeadv2025-bench.json"
output_filepath: "./results/jeeadv2025_benchmark_results_custom.json"
dbfilepath: "db/benchmark_results.db"
dotenv_filepath: "/path/to/your/.env"  # Update with your .env file path
max_questions: null  # Set to a number to limit questions for testing

solver_model_params:
  model: "gemini/gemini-2.5-pro"  # Change model as needed. Refer to litellm for model naming
  temperature: 0.3
  max_tokens: 32000
  num_retries: 1

grader_model_params:
  model: "gemini/gemini-2.0-flash-lite"
  temperature: 0.1
  num_retries: 2
```

Then run:

```bash
uv run benchmark.py --config config/config_my_fav_llm.yaml
```

### Evaluating Specific Subjects or Papers

The dataset includes metadata for filtering:

```python
# Filter by subject
questions = [q for q in questions if q['subject'] == 'mathematics']

# Filter by paper  
questions = [q for q in questions if q['paper'] == 1]
```

## Dataset Structure

The benchmark dataset (`jeeadv2025-bench.json`) contains:

```json
{
  "question_number": 1,
  "subject": "mathematics",
  "paper": 1,
  "question_text": "The question content...",
  "question_instruction": "Choose the correct option(s)...",
  "question_figure_description": "Description of any diagrams...",
  "answer_text": "Correct answer",
  "marking_scheme": "Scoring details..."
}
```

## Results Analysis

The benchmark generates:

1. **Console Output**: Real-time progress and summary statistics
2. **JSON Results**: Detailed results saved to `output_filepath`
3. **SQLite Database**: All results stored in `dbfilepath` for analysis

### Sample Analysis

```python
import sqlite3
import pandas as pd

# Load results from database
conn = sqlite3.connect('db/benchmark_results.db')
df = pd.read_sql_query("SELECT * FROM benchmark_results", conn)

# Analyze by subject
subject_analysis = df.groupby('subject').agg({
    'is_correct': ['count', 'sum', 'mean'],
    'marks_awarded': 'mean'
}).round(3)
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Limitations & Caveats

- **Text-Only Questions**: Diagrams are described via LLM-generated text, not actual visual reasoning
- **Single Language**: Currently supports English questions only
- **Model Access**: Requires API access to tested models
- **Grading**: Automated grading may not capture all nuances of partial credit

## Future Work

- [ ] Add support for more model providers (OpenAI, Anthropic, etc.)
- [ ] Include visual reasoning with actual diagram processing
- [ ] Expand to other competitive exams (NEET, SAT, etc.)
- [ ] Add few-shot prompting strategies
- [ ] Add retrieval-based question answering using previous questions and answers

## Citation

If you use this benchmark in your research, please cite:

```bibtex
@misc{jeeadvanced2025benchmark,
  title={JEE Advanced 2025 AI Benchmark: Evaluating Large Language Models on India's Premier Engineering Entrance Exam},
  author={Naveen Reddy},
  year={2025},
  url={https://github.com/naveenreddy61/jeeadv2025-benchmark}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Indian Institute of Technology (IIT) Kanpur for conducting JEE Advanced 2025
- Google for providing access to Gemini models
- DSPy framework for structured LLM evaluation
- The broader AI research community for advancing language model capabilities

---

**Disclaimer**: This benchmark is for research and educational purposes only. It does not represent official JEE Advanced scoring or evaluation methods.