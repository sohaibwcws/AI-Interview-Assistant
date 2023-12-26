# AI-Interview-AssistantReal-Time Transcription and Response Assistant Script

# Real-Time Transcription and Response Assistant

## Overview
This script creates an application using `customtkinter` and `tkinter` for real-time transcription and response generation. It utilizes Google Cloud Speech for transcription and OpenAI's GPT model for generating responses.

## Features
- Real-time audio transcription using Google Cloud Speech.
- Interaction with OpenAI's GPT model to generate responses based on transcriptions.
- GUI for displaying transcriptions and responses.
- Ability to toggle listening and manually input transcriptions.
- Storage of transcriptions and responses in a local database.

## Requirements
- Python 3.x
- `customtkinter`
- `tkinter`
- `google-cloud-speech`
- `sounddevice`
- `numpy`
- `openai`

## Installation
1. Install Python 3.x from [Python's official website](https://www.python.org/downloads/).
2. Install the required packages using pip:


## Configuration
- Set your OpenAI API key in the `OPENAI_API_KEY` variable.
- Set your Google Cloud credentials JSON file in `GOOGLE_APPLICATION_CREDENTIALS`.

## Usage
1. Run the script using Python:


2. Click the "Listen" button to start real-time transcription.
3. Transcriptions and AI-generated responses will be displayed in the GUI.
4. Use the "Pause," "Clear," and "Submit Transcription" buttons as needed.

## Note
Ensure you have the necessary credentials and API keys for Google Cloud Speech and OpenAI services. Store your Google Cloud credentials JSON file in the project directory and replace the placeholder path in the script with the actual path to your JSON file.

## Disclaimer
- The script requires an internet connection to access Google Cloud Speech and OpenAI services.
- Usage of these services may incur charges; please check the respective service providers for pricing details.

## Contributing
Contributions, issues, and feature requests are welcome. Feel free to check the issues page if you want to contribute.

## License
This project is [MIT licensed](https://opensource.org/licenses/MIT).
