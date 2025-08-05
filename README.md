# Recapify

<div align="center">

![Recapify Logo](https://img.shields.io/badge/Recapify-AI%20Meeting%20Summarizer-004C3F?style=for-the-badge&logo=shopify)

**Transform your meeting recordings into actionable insights with AI-powered summarization**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/Gradio-Interface-orange.svg)](https://gradio.app/)

</div>

---

## 🚀 Overview

Recapify is a sophisticated AI-powered application that converts audio recordings of meetings into comprehensive transcripts and intelligent summaries. Built with cutting-edge technology including Whisper.cpp for audio-to-text conversion and Ollama for advanced text summarization, Recapify helps you extract key insights, decisions, and action items from your meetings efficiently.

### ✨ Key Features

- **🎤 High-Quality Audio Processing**: Supports multiple audio formats with advanced preprocessing
- **🤖 AI-Powered Transcription**: Uses Whisper.cpp for accurate speech-to-text conversion
- **📝 Intelligent Summarization**: Leverages Ollama models for context-aware summaries
- **🎨 Professional UI**: Clean, modern interface with Shopify-inspired design
- **⚡ Real-time Processing**: Fast and efficient audio processing with GPU acceleration
- **📊 Multiple Model Support**: Choose from various Whisper and LLM models
- **🌍 Multi-language Support**: Automatic language detection and translation
- **💾 Export Capabilities**: Download transcripts and summaries for offline use

---

## 🛠️ Technology Stack

- **Frontend**: Gradio (Python web interface)
- **Audio Processing**: Whisper.cpp (OpenAI's Whisper implementation)
- **AI Summarization**: Ollama (Local LLM inference)
- **Audio Conversion**: FFmpeg
- **Styling**: Custom CSS with Shopify design principles

---

## 📋 Prerequisites

Before running Recapify, ensure you have the following installed:

- **Python 3.8+**
- **FFmpeg** (for audio processing)
- **Ollama** (for AI summarization)
- **Git** (for cloning the repository)

### Installing Ollama

1. **Download Ollama** from [ollama.com](https://ollama.com/)
2. **Install and start** the Ollama server
3. **Download a model** (e.g., Llama 3.2):
   ```bash
   ollama run llama3.2
   ```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/kabir2004/Recapify.git
cd Recapify
```

### 2. Run the Setup Script

The setup script will automatically install all dependencies and configure the environment:

```bash
chmod +x run_meeting_summarizer.sh
./run_meeting_summarizer.sh
```

This script will:
- ✅ Create a Python virtual environment
- ✅ Install required Python packages
- ✅ Install FFmpeg (if not present)
- ✅ Clone and build Whisper.cpp
- ✅ Download the Whisper model
- ✅ Launch the Recapify interface

### 3. Access the Application

Once setup is complete, open your browser and navigate to:
```
http://127.0.0.1:7860
```

---

## 📖 Usage Guide

### Uploading Audio Files

1. **Select Audio File**: Click the upload area and choose your meeting recording
2. **Add Context** (Optional): Provide additional context for better summarization
3. **Choose Models**: Select your preferred Whisper and summarization models
4. **Process**: Click submit to generate your transcript and summary

### Supported Audio Formats

- MP3, WAV, M4A, FLAC, OGG
- Any format supported by FFmpeg
- Recommended: 16kHz sample rate for optimal performance

### Model Selection

**Whisper Models** (Audio-to-Text):
- `base`: Fast, good for short recordings
- `small`: Balanced speed and accuracy (default)
- `medium`: Higher accuracy, slower processing
- `large-V3`: Best accuracy, requires more resources

**Summarization Models** (via Ollama):
- Any model available on your Ollama server
- Popular choices: llama3.2, mistral, codellama

---

## 🎨 Customization

### Changing the Default Whisper Model

Edit the `run_meeting_summarizer.sh` script:

```bash
WHISPER_MODEL="medium"  # Change from "small" to your preferred model
```

### Downloading Additional Whisper Models

```bash
cd whisper.cpp
./models/download-ggml-model.sh base    # For base model
./models/download-ggml-model.sh medium  # For medium model
./models/download-ggml-model.sh large   # For large model
```

### Customizing the UI

The application uses custom CSS for styling. Modify the `custom_css` variable in `main.py` to change colors, fonts, or layout.

---

## 🔧 Manual Installation

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install requests gradio

# Install FFmpeg (macOS)
brew install ffmpeg

# Clone and build Whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make

# Download Whisper model
./models/download-ggml-model.sh small

# Run the application
python main.py
```

---

## 🏗️ Architecture

```
Recapify/
├── main.py                    # Main application logic
├── run_meeting_summarizer.sh  # Setup and installation script
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── LICENSE                   # MIT License
└── whisper.cpp/              # Whisper.cpp installation
    ├── build/                # Compiled binaries
    └── models/               # Downloaded Whisper models
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Whisper.cpp** by Georgi Gerganov for efficient audio-to-text conversion
- **Gradio** for the intuitive web interface framework
- **Ollama** for providing local LLM inference capabilities
- **OpenAI** for the original Whisper model

---

## 📞 Support

If you encounter any issues or have questions:

- 📧 Create an issue on GitHub
- 🔧 Check the troubleshooting section below
- 📚 Review the documentation

---

## 🔍 Troubleshooting

### Common Issues

**Ollama Connection Error**
- Ensure Ollama server is running: `ollama serve`
- Check if models are downloaded: `ollama list`

**Audio Processing Issues**
- Verify FFmpeg is installed: `ffmpeg -version`
- Check audio file format compatibility

**Whisper Model Errors**
- Ensure models are downloaded in `whisper.cpp/models/`
- Check available models: `ls whisper.cpp/models/`

**Memory Issues**
- Use smaller Whisper models for long recordings
- Close other applications to free up RAM

---

<div align="center">

**Built with ❤️ by [Your Name]**

[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?style=social&logo=github)](https://github.com/kabir2004)

</div>
