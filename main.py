import subprocess
import os
import gradio as gr
import requests
import json

OLLAMA_SERVER_URL = os.environ.get("OLLAMA_SERVER_URL", "http://localhost:11434")  # Use env var or default
WHISPER_MODEL_DIR = "./whisper.cpp/models"  # Directory where whisper models are stored


def get_available_models() -> list[str]:
    """
    Retrieves a list of all available models from the Ollama server and extracts the model names.

    Returns:
        A list of model names available on the Ollama server.
    """
    try:
        response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()["models"]
            llm_model_names = [model["model"] for model in models]  # Extract model names
            return llm_model_names
        else:
            print(f"Warning: Failed to retrieve models from Ollama server: {response.text}")
            return ["ollama-not-available"]
    except requests.exceptions.RequestException as e:
        print(f"Warning: Cannot connect to Ollama server at {OLLAMA_SERVER_URL}: {e}")
        return ["ollama-not-available"]


def get_available_whisper_models() -> list[str]:
    """
    Retrieves a list of available Whisper models based on downloaded .bin files in the whisper.cpp/models directory.
    Filters out test models and only includes official Whisper models (e.g., base, small, medium, large).

    Returns:
        A list of available Whisper model names (e.g., 'base', 'small', 'medium', 'large-V3').
    """
    # List of acceptable official Whisper models
    valid_models = ["base", "small", "medium", "large", "large-V3"]

    # Get the list of model files in the models directory
    model_files = [f for f in os.listdir(WHISPER_MODEL_DIR) if f.endswith(".bin")]

    # Filter out test models and models that aren't in the valid list
    whisper_models = [
        os.path.splitext(f)[0].replace("ggml-", "")
        for f in model_files
        if any(valid_model in f for valid_model in valid_models) and "test" not in f
    ]

    # Remove any potential duplicates
    whisper_models = list(set(whisper_models))

    return whisper_models


def summarize_with_model(llm_model_name: str, context: str, text: str) -> str:
    """
    Uses a specified model on the Ollama server to generate a summary.
    Handles streaming responses by processing each line of the response.

    Args:
        llm_model_name (str): The name of the model to use for summarization.
        context (str): Optional context for the summary, provided by the user.
        text (str): The transcript text to summarize.

    Returns:
        str: The generated summary text from the model.
    """
    # Check if Ollama is not available
    if llm_model_name == "ollama-not-available":
        return f"""❌ Ollama Service Unavailable

This deployment cannot connect to an Ollama server for AI summarization.

📝 **Raw Transcript Available**: You can still download the full transcript below.

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
            f"{OLLAMA_SERVER_URL}/api/generate", json=data, headers=headers, stream=True, timeout=60
        )

        if response.status_code == 200:
            full_response = ""
            try:
                # Process the streaming response line by line
                for line in response.iter_lines():
                    if line:
                        # Decode each line and parse it as a JSON object
                        decoded_line = line.decode("utf-8")
                        json_line = json.loads(decoded_line)
                        # Extract the "response" part from each JSON object
                        full_response += json_line.get("response", "")
                        # If "done" is True, break the loop
                        if json_line.get("done", False):
                            break
                return full_response
            except json.JSONDecodeError:
                print("Error: Response contains invalid JSON data.")
                return f"Failed to parse the response from the server. Raw response: {response.text}"
        else:
            return f"❌ Error: Failed to summarize with model {llm_model_name}. Server returned: {response.text}\n\nTranscript is still available for download below."
    except requests.exceptions.RequestException as e:
        return f"❌ Error: Cannot connect to Ollama server: {e}\n\nTranscript is still available for download below."


def preprocess_audio_file(audio_file_path: str) -> str:
    """
    Converts the input audio file to a WAV format with 16kHz sample rate and mono channel.

    Args:
        audio_file_path (str): Path to the input audio file.

    Returns:
        str: The path to the preprocessed WAV file.
    """
    output_wav_file = f"{os.path.splitext(audio_file_path)[0]}_converted.wav"

    # Ensure ffmpeg converts to 16kHz sample rate and mono channel
    cmd = f'ffmpeg -y -i "{audio_file_path}" -ar 16000 -ac 1 "{output_wav_file}"'
    subprocess.run(cmd, shell=True, check=True)

    return output_wav_file


def translate_and_summarize(
    audio_file_path: str, context: str, whisper_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Translates the audio file into text using the whisper.cpp model and generates a summary using Ollama.
    Also provides the transcript file for download.

    Args:
        audio_file_path (str): Path to the input audio file.
        context (str): Optional context to include in the summary.
        whisper_model_name (str): Whisper model to use for audio-to-text conversion.
        llm_model_name (str): Model to use for summarizing the transcript.

    Returns:
        tuple[str, str]: A tuple containing the summary and the path to the transcript file for download.
    """
    output_file = "output.txt"

    print("Processing audio file:", audio_file_path)

    # Convert the input file to WAV format if necessary
    audio_file_wav = preprocess_audio_file(audio_file_path)

    print("Audio preprocessed:", audio_file_wav)

    # Call the whisper.cpp binary
    whisper_command = f'./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-{whisper_model_name}.bin -f "{audio_file_wav}" > {output_file}'
    subprocess.run(whisper_command, shell=True, check=True)

    print("Whisper.cpp executed successfully")

    # Read the output from the transcript
    with open(output_file, "r") as f:
        transcript = f.read()

    # Save the transcript to a downloadable file
    transcript_file = "transcript.txt"
    with open(transcript_file, "w") as transcript_f:
        transcript_f.write(transcript)

    # Generate summary from the transcript using Ollama's model
    summary = summarize_with_model(llm_model_name, context, transcript)

    # Clean up temporary files
    os.remove(audio_file_wav)
    os.remove(output_file)

    # Return the downloadable link for the transcript and the summary text
    return summary, transcript_file


# Gradio interface
def gradio_app(
    audio, context: str, whisper_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Gradio application to handle file upload, model selection, and summary generation.

    Args:
        audio: The uploaded audio file.
        context (str): Optional context provided by the user.
        whisper_model_name (str): The selected Whisper model name.
        llm_model_name (str): The selected language model for summarization.

    Returns:
        tuple[str, str]: A tuple containing the summary text and a downloadable transcript file.
    """
    return translate_and_summarize(audio, context, whisper_model_name, llm_model_name)


# Main function to launch the Gradio interface
if __name__ == "__main__":
    # Retrieve available models for Gradio dropdown input
    ollama_models = get_available_models()  # Retrieve models from Ollama server
    whisper_models = (
        get_available_whisper_models()
    )  # Dynamically detect downloaded Whisper models

    # Custom CSS for Shopify font styling
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .gradio-container h1 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        color: #004C3F;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -0.025em;
    }
    
    .gradio-container .description {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 400;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    """
    
    # Ensure the first model is selected by default
    iface = gr.Interface(
        fn=gradio_app,
        inputs=[
            gr.Audio(type="filepath", label="Upload an audio file"),
            gr.Textbox(
                label="Context (optional)",
                placeholder="Provide any additional context for the summary",
            ),
            gr.Dropdown(
                choices=whisper_models,
                label="Select a Whisper model for audio-to-text conversion",
                value=whisper_models[0],
            ),
            gr.Dropdown(
                choices=ollama_models,
                label="Select a model for summarization",
                value=ollama_models[0] if ollama_models else None,
            ),
        ],
        outputs=[
            gr.Textbox(
                label="Summary",
                show_copy_button=True,
            ),  # Display the summary generated by the Ollama model
            gr.File(
                label="Download Transcript"
            ),  # Provide the transcript as a downloadable file
        ],
        analytics_enabled=False,
        title="Recapify",
        description="Upload an audio file of a meeting and get a summary of the key concepts discussed.",
        css=custom_css,
    )

    # Get port from environment variable (for Railway)
    port = int(os.environ.get("PORT", 7860))
    
    iface.launch(
        server_name="0.0.0.0",
        server_port=port,
        debug=False,
        share=False,
        show_error=True,
        quiet=False
    )
