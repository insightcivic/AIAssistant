import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
from io import BytesIO
import base64
import openai
from mem0 import Mem0
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from typing import List, Dict

class ConversationSystem:
    def __init__(self):
        self.openai = openai
        self.mem0 = Mem0()
        self.qdrant = QdrantClient("localhost", port=6333)
        self.system_prompt = """You are a warm and empathetic AI assistant, inspired by 'Her'.
        Your responses should be caring, understanding, and supportive. Always strive to build
        a personal connection with the user."""
        
        # Initialize Qdrant collection for storing conversations
        self.qdrant.recreate_collection(
            collection_name="conversations",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    def generate_response(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        # Retrieve relevant memories
        relevant_memories = self.mem0.retrieve(user_input)
        
        # Construct the prompt
        prompt = f"{self.system_prompt}\n\n"
        prompt += "Conversation history:\n"
        for message in conversation_history[-5:]:  # Include last 5 messages for context
            prompt += f"{message['role']}: {message['content']}\n"
        prompt += f"\nRelevant memories:\n{relevant_memories}\n"
        prompt += f"\nUser: {user_input}\nAssistant:"

        # Generate response using ChatGPT-4-mini
        response = openai.Completion.create(
            engine="text-davinci-002",  # Replace with actual ChatGPT-4-mini engine when available
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )

        assistant_response = response.choices[0].text.strip()
        
        # Store the conversation in Qdrant
        self.store_conversation(user_input, assistant_response)
        
        # Update Mem0 with the new interaction
        self.mem0.add(f"User: {user_input}\nAssistant: {assistant_response}")

        return assistant_response

    def store_conversation(self, user_input: str, assistant_response: str):
        # Encode the conversation to a vector (simplified for this example)
        vector = openai.Embedding.create(
            input=f"{user_input} {assistant_response}",
            engine="text-embedding-ada-002"
        )['data'][0]['embedding']

        # Store in Qdrant
        self.qdrant.upsert(
            collection_name="conversations",
            points=[PointStruct(
                id=hash(f"{user_input} {assistant_response}"),
                vector=vector,
                payload={"user_input": user_input, "assistant_response": assistant_response}
            )]
        )

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp

def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = r.listen(source)
        st.write("Processing...")
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.write("Could not understand audio")
    except sr.RequestError as e:
        st.write(f"Could not request results; {e}")

def get_audio_html(audio_fp):
    audio_bytes = audio_fp.getvalue()
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'

st.title("AI Assistant")

# Initialize conversation system
conversation_system = ConversationSystem()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
input_mode = st.radio("Choose input mode:", ("Text", "Voice"))

if input_mode == "Text":
    if prompt := st.chat_input("What is your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        response = conversation_system.generate_response(prompt, st.session_state.messages)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Convert response to speech
        audio_fp = text_to_speech(response)
        st.markdown(get_audio_html(audio_fp), unsafe_allow_html=True)

elif input_mode == "Voice":
    if st.button("Start Recording"):
        user_input = speech_to_text()
        if user_input:
            st.write(f"You said: {user_input}")
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Generate AI response
            response = conversation_system.generate_response(user_input, st.session_state.messages)
            
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Convert response to speech
            audio_fp = text_to_speech(response)
            st.markdown(get_audio_html(audio_fp), unsafe_allow_html=True)

# Option to clear chat history
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.experimental_rerun()