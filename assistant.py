import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
from io import BytesIO
import base64
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance
from typing import List, Dict
from dotenv import load_dotenv
import uuid
import time
import traceback

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ConversationSystem:
    def __init__(self):
        st.write("Initializing ConversationSystem...")
        
        # Initialize Qdrant client with in-memory storage
        self.qdrant = QdrantClient(":memory:")
        
        self.system_prompt = """You are a warm and empathetic AI assistant, inspired by 'Her'.
        Your responses should be caring, understanding, and supportive. Always strive to build
        a personal connection with the user."""
        
        # Initialize Qdrant collection for storing conversations
        self.init_qdrant_collection()
        st.write("ConversationSystem initialized successfully.")

    def init_qdrant_collection(self):
        st.write("Initializing Qdrant collection...")
        try:
            self.qdrant.get_collection("conversations")
            st.write("Qdrant collection already exists.")
        except Exception:
            st.write("Creating new Qdrant collection...")
            self.qdrant.create_collection(
                collection_name="conversations",
                vectors_config=models.VectorParams(size=1536, distance=Distance.COSINE),
            )
            st.write("Qdrant collection created successfully.")

    def generate_response(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        prompt = self.construct_prompt(user_input, conversation_history)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )

            assistant_response = response.choices[0].message.content.strip()
        
            self.store_conversation(user_input, assistant_response)

            return assistant_response
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "I'm sorry, but I encountered an error while trying to generate a response. Please try again."

    def construct_prompt(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        prompt = f"{self.system_prompt}\n\n"
        prompt += "Conversation history:\n"
        for message in conversation_history[-5:]:  # Include last 5 messages for context
            prompt += f"{message['role']}: {message['content']}\n"
        prompt += f"\nUser: {user_input}\nAssistant:"
        return prompt

    def store_conversation(self, user_input: str, assistant_response: str):
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=f"{user_input} {assistant_response}"
            )
            vector = response.data[0].embedding

            self.qdrant.upsert(
                collection_name="conversations",
                points=[models.PointStruct(
                    id=hash(f"{user_input} {assistant_response}"),
                    vector=vector,
                    payload={"user_input": user_input, "assistant_response": assistant_response}
                )]
            )
        except Exception as e:
            st.warning(f"Error storing conversation: {str(e)}")

    def update_memories(self, user_input: str, assistant_response: str):
        try:
            self.mem0.add(f"User: {user_input}\nAssistant: {assistant_response}", user_id="user", metadata={"conversation": "history"})
        except Exception as e:
            st.warning(f"Error adding memory: {str(e)}")

def text_to_speech(text: str) -> BytesIO:
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)  # Rewind the file pointer to the beginning
    return fp

def speech_to_text() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = r.listen(source)
        st.write("Processing...")
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        st.write("Could not understand audio")
    except sr.RequestError as e:
        st.write(f"Could not request results; {e}")
    return ""

def get_audio_html(audio_fp: BytesIO) -> str:
    audio_bytes = audio_fp.getvalue()
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'

st.title("AI Assistant")

st.write("Initializing application...")

try:
    conversation_system = ConversationSystem()
    st.write("ConversationSystem initialized successfully.")
except Exception as e:
    st.error("Failed to initialize ConversationSystem")
    st.write(f"Error: {str(e)}")
    st.write(traceback.format_exc())
    conversation_system = None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

input_mode = st.radio("Choose input mode:", ("Text", "Voice"))

if conversation_system:
    if input_mode == "Text":
        if prompt := st.chat_input("What is your message?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            response = conversation_system.generate_response(prompt, st.session_state.messages)
            
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            audio_fp = text_to_speech(response)
            st.markdown(get_audio_html(audio_fp), unsafe_allow_html=True)

    elif input_mode == "Voice":
        if st.button("Start Recording"):
            user_input = speech_to_text()
            if user_input:
                st.write(f"You said: {user_input}")
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                response = conversation_system.generate_response(user_input, st.session_state.messages)
                
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                audio_fp = text_to_speech(response)
                st.markdown(get_audio_html(audio_fp), unsafe_allow_html=True)

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()
else:
    st.error("ConversationSystem is not initialized. Please check the error messages above and try restarting the application.")

st.write("Application initialization complete.")