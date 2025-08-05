import subprocess
import os
import streamlit as st
import requests
import json
import tempfile
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Recapify",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Shopify-style design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .main-header {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        color: #004C3F;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -0.025em;
    }
    
    .description {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 400;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stButton > button {
        background-color: #004C3F;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #003d32;
    }
</style>
""", unsafe_allow_html=True)

OLLAMA_SERVER_URL = os.environ.get("OLLAMA_SERVER_URL", "http://localhost:11434")
WHISPER_MODEL_DIR = "./whisper.cpp/models"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_available_models():
    """Get available models from Ollama server"""
    try:
        response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()["models"]
            return [model["model"] for model in models]
        else:
            st.warning(f"Failed to retrieve models from Ollama server: {response.text}")
            return ["ollama-not-available"]
    except requests.exceptions.RequestException as e:
        st.warning(f"Cannot connect to Ollama server at {OLLAMA_SERVER_URL}: {e}")
        return ["ollama-not-available"]

@st.cache_data
def get_available_whisper_models():
    """Get available Whisper models"""
    valid_models = ["base", "small", "medium", "large", "large-V3"]
    
    # For Streamlit deployment, we'll assume small model is available
    # In a real deployment, you'd check the actual model directory
    if os.path.exists(WHISPER_MODEL_DIR):
        try:
            model_files = [f for f in os.listdir(WHISPER_MODEL_DIR) if f.endswith(".bin")]
            whisper_models = [
                os.path.splitext(f)[0].replace("ggml-", "")
                for f in model_files
                if any(valid_model in f for valid_model in valid_models) and "test" not in f
            ]
            return list(set(whisper_models)) if whisper_models else ["small"]
        except:
            return ["small"]
    else:
        return ["small"]

def summarize_with_model(llm_model_name: str, context: str, text: str) -> str:
    """Summarize text using Ollama model"""
    if llm_model_name == "ollama-not-available":
        return f"""❌ **Ollama Service Unavailable**

This deployment cannot connect to an Ollama server for AI summarization.

📝 **Raw Transcript Available**: You can download the full transcript below.

🔧 **To enable AI summarization**:
1. Deploy your own Ollama server
2. Set the OLLAMA_SERVER_URL environment variable
3. Redeploy this application

**Context provided**: {context if context else 'None'}

**Transcript preview** (first 500 characters):
{text[:500]}{'...' if len(text) > 500 else ''}"""

    prompt = f"""You are given a transcript from a meeting, along with some optional context.
    
    Context: {context if context else 'No additional context provided.'}
    
    The transcript is as follows:
    
    {text}
    
    Please summarize the transcript."""

    headers = {"Content-Type": "application/json"}
    data = {"model": llm_model_name, "prompt": prompt}

    try:
        response = requests.post(
            f"{OLLAMA_SERVER_URL}/api/generate", 
            json=data, 
            headers=headers, 
            stream=True, 
            timeout=60
        )

        if response.status_code == 200:
            full_response = ""
            try:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        json_line = json.loads(decoded_line)
                        full_response += json_line.get("response", "")
                        if json_line.get("done", False):
                            break
                return full_response
            except json.JSONDecodeError:
                return f"Failed to parse the response from the server. Raw response: {response.text}"
        else:
            return f"❌ Error: Failed to summarize with model {llm_model_name}. Server returned: {response.text}\n\nTranscript is still available for download below."
    except requests.exceptions.RequestException as e:
        return f"❌ Error: Cannot connect to Ollama server: {e}\n\nTranscript is still available for download below."

def preprocess_audio_file(audio_file_path: str) -> str:
    """Convert audio file to WAV format"""
    output_wav_file = f"{os.path.splitext(audio_file_path)[0]}_converted.wav"
    cmd = f'ffmpeg -y -i "{audio_file_path}" -ar 16000 -ac 1 "{output_wav_file}"'
    
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return output_wav_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error converting audio file: {e}")
        return None

def transcribe_audio(audio_file_path: str, whisper_model_name: str) -> str:
    """Transcribe audio using whisper.cpp"""
    output_file = "output.txt"
    
    # Convert audio file
    audio_file_wav = preprocess_audio_file(audio_file_path)
    if not audio_file_wav:
        return None
    
    try:
        # For Streamlit deployment, we'll use a simpler approach
        # In production, you'd build whisper.cpp properly
        whisper_command = f'./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-{whisper_model_name}.bin -f "{audio_file_wav}" > {output_file}'
        
        # Try to run whisper, but handle gracefully if not available
        try:
            subprocess.run(whisper_command, shell=True, check=True, capture_output=True)
            
            with open(output_file, "r") as f:
                transcript = f.read()
            
            # Clean up
            os.remove(audio_file_wav)
            os.remove(output_file)
            
            return transcript
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: return a message that whisper.cpp is not available
            return f"""🔧 **Whisper.cpp Not Available in This Deployment**

This Streamlit deployment doesn't have whisper.cpp compiled. 

**To enable transcription:**
1. Deploy with a custom Docker container that builds whisper.cpp
2. Use OpenAI Whisper API instead
3. Use a pre-built whisper service

**Audio file received:** {os.path.basename(audio_file_path)}
**Model requested:** {whisper_model_name}

For a working demo, try the Railway deployment with Docker."""
            
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">Recapify</h1>', unsafe_allow_html=True)
    st.markdown('<p class="description">Upload an audio file of a meeting and get a summary of the key concepts discussed.</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Get available models
    ollama_models = get_available_models()
    whisper_models = get_available_whisper_models()
    
    # Model selection
    whisper_model = st.sidebar.selectbox(
        "Select Whisper Model",
        whisper_models,
        index=0,
        help="Choose the Whisper model for audio-to-text conversion"
    )
    
    llm_model = st.sidebar.selectbox(
        "Select Summarization Model", 
        ollama_models,
        index=0,
        help="Choose the model for text summarization"
    )
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Upload Audio File")
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'mp4', 'm4a', 'ogg', 'flac'],
            help="Upload your meeting audio file in any supported format"
        )
        
        st.subheader("📝 Context (Optional)")
        context = st.text_area(
            "Provide additional context",
            placeholder="e.g., Meeting about AI and Ethics, Q3 Planning Session, etc.",
            help="Optional context to help improve the summary quality"
        )
    
    with col2:
        st.subheader("📊 Results")
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            if st.button("🚀 Process Audio", type="primary"):
                with st.spinner("Processing audio file..."):
                    # Transcribe audio
                    transcript = transcribe_audio(tmp_file_path, whisper_model)
                    
                    if transcript:
                        # Save transcript for download
                        transcript_file = "transcript.txt"
                        with open(transcript_file, "w") as f:
                            f.write(transcript)
                        
                        # Generate summary
                        with st.spinner("Generating summary..."):
                            summary = summarize_with_model(llm_model, context, transcript)
                        
                        # Display results
                        st.subheader("📋 Summary")
                        st.markdown(summary)
                        
                        # Download buttons
                        st.subheader("💾 Downloads")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📄 Download Transcript",
                                data=transcript,
                                file_name="transcript.txt",
                                mime="text/plain"
                            )
                        
                        with col2:
                            st.download_button(
                                label="📊 Download Summary", 
                                data=summary,
                                file_name="summary.txt",
                                mime="text/plain"
                            )
                        
                        # Clean up
                        try:
                            os.unlink(tmp_file_path)
                            if os.path.exists(transcript_file):
                                os.unlink(transcript_file)
                        except:
                            pass
                    else:
                        st.error("Failed to transcribe audio file.")
        else:
            st.info("👆 Upload an audio file to get started!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #6B7280; font-size: 0.9rem;'>
            Built with ❤️ using Streamlit • Powered by whisper.cpp and Ollama
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()