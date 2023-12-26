import customtkinter as ctk
import tkinter as tk
from google.cloud import speech
import sounddevice as sd
import numpy as np
import threading
import queue
import sys
import time
import json
from itertools import cycle
import openai

# Constants
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16
BUFFER_DURATION = 5.0
RESPONSE_MAX_TOKENS = 300
OPENAI_API_KEY = "YOUR API KEY"
GOOGLE_APPLICATION_CREDENTIALS = "GOGLE JSON FILE HERE"
COLORS = cycle(["dark blue", "green", "purple", "orange", "brown"])
EXCLUDED_PHRASES = ["great answer", "thank you for that answer", "we do appreciate it"]
DATABASE_FILE = "database.json"

# Initialize OpenAI GPT model
openai.api_key = OPENAI_API_KEY

# Configure Google Cloud Speech client
client = speech.SpeechClient.from_service_account_json(GOOGLE_APPLICATION_CREDENTIALS)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=SAMPLE_RATE,
    language_code="en-US",
    model="default",
)
streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

# Audio queue
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("Status:", status, file=sys.stderr)
    audio_queue.put(indata.copy())

audio_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback)

class TranscriptionApp(ctk.CTk):
    BACKGROUND_INFO = "I have customer service skills, strong management & IT Skills"
    def __init__(self):
        super().__init__()
        self.chat_history = [{"role": "system", "content": self.BACKGROUND_INFO}]
        self.title("Enhanced Real-Time Transcription and Response Assistant v1.0")
        self.geometry("800x800")
        self.setup_frames()
        self.setup_text_widgets()
        self.setup_buttons()
        self.is_listening = False
        self.paused = False
        self.sentence_counter = 1
        self.current_color = next(COLORS)
        self.transcription = ""
        self.chat_history = []

    def setup_frames(self):
        self.transcription_frame = ctk.CTkFrame(self, width=400, height=800)
        self.transcription_frame.pack(side="left", fill="both", expand=True)

        self.response_frame = ctk.CTkFrame(self, width=400, height=800)
        self.response_frame.pack(side="right", fill="both", expand=True)

    def setup_text_widgets(self):
        self.transcription_scroll = ctk.CTkScrollbar(self.transcription_frame)
        self.transcription_scroll.pack(side="right", fill="y")

        self.response_scroll = ctk.CTkScrollbar(self.response_frame)
        self.response_scroll.pack(side="right", fill="y")

        self.transcription_text = tk.Text(self.transcription_frame, bg="lightgrey",
                                          yscrollcommand=self.transcription_scroll.set, wrap="word")
        self.transcription_text.pack(fill="both", expand=True)
        self.transcription_scroll.configure(command=self.transcription_text.yview)

        self.response_text = tk.Text(self.response_frame, bg="white", yscrollcommand=self.response_scroll.set,
                                     wrap="word", font=("Arial", 14))
        self.response_text.pack(fill="both", expand=True)
        self.response_scroll.configure(command=self.response_text.yview)

    def setup_buttons(self):
        self.listen_button = ctk.CTkButton(self, text="Listen", command=self.toggle_listening)
        self.listen_button.pack(pady=10)

        self.pause_button = ctk.CTkButton(self, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(pady=10)

        self.clear_button = ctk.CTkButton(self, text="Clear", command=self.clear_texts)
        self.clear_button.pack(pady=10)

    def toggle_listening(self):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.configure(text="Resume" if self.paused else "Pause")

    def start_listening(self):
        self.is_listening = True
        self.listen_button.configure(text="Stop")
        try:
            audio_stream.start()
            threading.Thread(target=self.process_audio_stream, daemon=True).start()
        except Exception as e:
            print(f"Error starting audio stream: {e}", file=sys.stderr)
            self.is_listening = False

    def stop_listening(self):
        self.is_listening = False
        self.listen_button.configure(text="Listen")
        try:
            audio_stream.stop()
        except Exception as e:
            print(f"Error stopping audio stream: {e}", file=sys.stderr)
        audio_queue.queue.clear()

    def process_audio_stream(self):
        with audio_stream:
            while self.is_listening:
                if self.paused:
                    continue
                audio_buffer = np.empty((0, CHANNELS), dtype=DTYPE)
                start_time = time.time()

                while time.time() - start_time < BUFFER_DURATION:
                    try:
                        data = audio_queue.get(timeout=BUFFER_DURATION)
                        audio_buffer = np.append(audio_buffer, data, axis=0)
                    except queue.Empty:
                        print("Queue is empty. Waiting for more data.")

                if audio_buffer.size > 0:
                    self.process_transcription(audio_buffer)

    def process_transcription(self, audio_buffer):
        requests = (speech.StreamingRecognizeRequest(audio_content=audio_buffer.tobytes()),)
        responses = client.streaming_recognize(streaming_config, requests)

        for response in responses:
            if response.results:
                transcription = response.results[0].alternatives[0].transcript.lower()
                is_final = response.results[0].is_final
                if is_final and not any(phrase in transcription for phrase in EXCLUDED_PHRASES):
                    self.handle_transcription(transcription)

    def handle_transcription(self, transcription):
        similar_answer = self.find_similar_question(transcription)
        if similar_answer:
            self.display_response(similar_answer, "Answer from database")
        else:
            self.transcription += transcription + " "
            self.chat_history.append({"role": "user", "content": transcription})
            self.transcription_text.insert("end", f"{self.sentence_counter}. Q: " + self.transcription + "\n\n",
                                           str(self.sentence_counter))
            self.transcription_text.tag_configure(str(self.sentence_counter), foreground=self.current_color)
            self.generate_response()
            self.transcription = ""
            self.sentence_counter += 1
            self.current_color = next(COLORS)

    def generate_response(self):
        try:
            # Make the API call with the formatted chat history
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.chat_history,
                max_tokens=RESPONSE_MAX_TOKENS
            )
            response_text = response.choices[0].message['content'].strip()

            # Append the assistant's response to the chat history
            self.chat_history.append({"role": "assistant", "content": response_text})

            # Display the response
            self.display_response(response_text, "Generated by AI")
        except openai.error.OpenAIError as e:
            print(f"Error in generating response: {e}", file=sys.stderr)

    def display_response(self, response_text, reasoning):
        self.response_text.insert("end", f"{self.sentence_counter}. A: " + response_text + "\n",
                                  str(self.sentence_counter))
        self.response_text.insert("end", reasoning + "\n\n", "reasoning")
        self.response_text.tag_configure(str(self.sentence_counter), foreground=self.current_color)
        self.response_text.tag_configure("reasoning", font=("Arial", 12, "italic"))

    def clear_texts(self):
        self.transcription_text.delete("1.0", "end")
        self.response_text.delete("1.0", "end")
        self.sentence_counter = 1
        self.current_color = next(COLORS)
        self.chat_history.clear()

    def load_database(self):
        try:
            with open(DATABASE_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_to_database(self, question, answer):
        database = self.load_database()
        database[question] = answer
        with open(DATABASE_FILE, 'w') as file:
            json.dump(database, file, indent=4)

    def find_similar_question(self, question):
        database = self.load_database()
        # Implement similarity check here
        # For now, we're using a direct match
        return database.get(question)

if __name__ == "__main__":
    app = TranscriptionApp()
    app.mainloop()
