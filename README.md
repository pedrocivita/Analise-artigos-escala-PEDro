# PEDro Scale Scientific Article Analyzer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google AI](https://img.shields.io/badge/Google_AI-Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A web-based application that leverages Large Language Models (Google Gemini AI) to automatically assess the methodological quality of clinical trials using the PEDro (Physiotherapy Evidence Database) scale. This tool provides researchers and healthcare professionals with an efficient way to evaluate scientific article reliability.

## Overview

This project was developed as part of the Computer Engineering program at Insper, focusing on the application of artificial intelligence in healthcare research evaluation. The application analyzes uploaded PDF articles and scores them according to the internationally recognized PEDro scale, providing detailed justifications for each criterion.

## Features

- **PDF Text Extraction**: Automatically extracts text content from uploaded scientific articles
- **AI-Powered Analysis**: Utilizes Google's Gemini 1.5 Flash model for intelligent article evaluation
- **PEDro Scale Assessment**: Evaluates articles across 11 standardized criteria
- **Detailed Scoring**: Provides scores from 0-10 with reliability classification (Low/Moderate/High)
- **Comprehensive Justifications**: Offers evidence-based explanations for each criterion assessment
- **User-Friendly Interface**: Clean, intuitive Streamlit web interface
- **Real-time Processing**: Fast analysis and results generation

## PEDro Scale

The PEDro (Physiotherapy Evidence Database) scale is a reliable tool for assessing the methodological quality of clinical trials. It evaluates 11 criteria:

1. **Eligibility Criteria** (not scored)
2. **Random Allocation**
3. **Concealed Allocation**
4. **Baseline Comparability**
5. **Subject Blinding**
6. **Therapist Blinding**
7. **Assessor Blinding**
8. **Adequate Follow-up** (>85%)
9. **Intention-to-Treat Analysis**
10. **Between-Group Statistical Comparisons**
11. **Point Measures and Variability**

**Reliability Classification:**
- 0-3 points: Low reliability
- 4-6 points: Moderate reliability
- 7-10 points: High reliability

## Technologies Used

- **Python 3.8+**: Core programming language
- **Streamlit**: Web application framework
- **PyPDF2**: PDF text extraction
- **Google Gemini AI**: Large Language Model for article analysis
- **Requests**: HTTP library for API communication

## Installation

### Prerequisites

- Python 3.8 or higher
- Google AI Studio API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. Clone the repository:
```bash
git clone https://github.com/pedrocivita/Analise-artigos-escala-PEDro.git
cd Analise-artigos-escala-PEDro
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser and navigate to `http://localhost:8501`

## Usage

1. **Obtain API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) and create a free API key

2. **Launch Application**: Run the Streamlit app using the command above

3. **Configure Settings**:
   - Enter your Google AI Studio API key in the sidebar
   - Upload a scientific article in PDF format

4. **Analyze Article**: Click the "Analisar Artigo" button to begin the evaluation

5. **Review Results**: The application will display:
   - Detailed assessment for each PEDro criterion
   - Individual scores with justifications
   - Final PEDro score (0-10)
   - Reliability classification
   - Summary of clinical applicability

## Project Structure

```
Analise-artigos-escala-PEDro/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── .gitignore           # Git ignore rules
```

## How It Works

1. **Text Extraction**: The application uses PyPDF2 to extract text content from the uploaded PDF (limited to 28,000 characters to comply with API constraints)

2. **Prompt Engineering**: A specialized prompt instructs the Gemini AI model to act as an expert researcher in physiotherapy and dermatology, evaluating the article against all PEDro criteria

3. **API Communication**: The extracted text and prompt are sent to Google's Gemini 1.5 Flash API for processing

4. **Result Presentation**: The AI-generated analysis is formatted in Markdown and displayed in an organized, readable format

## Limitations

- PDF text extraction quality depends on the source document formatting
- Text analysis is limited to 28,000 characters per article
- Requires a valid Google AI Studio API key
- AI analysis accuracy depends on article clarity and information completeness
- Best suited for physiotherapy and rehabilitation clinical trials

## Future Enhancements

- Support for multiple article formats (DOCX, HTML)
- Batch processing capabilities
- Export results to PDF/CSV
- Historical analysis tracking
- Custom prompt templates
- Multi-language support
- Integration with PubMed/PEDro databases

## Academic Context

This project was developed as part of the Computer Engineering curriculum at **Instituto de Ensino e Pesquisa (Insper)**, São Paulo, Brazil. It demonstrates the practical application of artificial intelligence and natural language processing in healthcare research evaluation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for any improvements or bug fixes.

## Contact

**Pedro Civita**

- Email: [pedrocivita@gmail.com](mailto:pedrocivita@gmail.com)
- Email: [pedropc1@al.insper.edu.br](mailto:pedropc1@al.insper.edu.br)
- LinkedIn: [linkedin.com/in/pedro-civita](https://linkedin.com/in/pedro-civita)
- GitHub: [@pedrocivita](https://github.com/pedrocivita)

## License

This project is available under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- **Insper - Instituto de Ensino e Pesquisa** for the academic support
- **Google AI Studio** for providing the Gemini API
- **PEDro Database** for the standardized scale methodology
- The open-source community for the excellent tools and libraries used in this project

---

*Developed as part of the Computer Engineering program at Insper*
