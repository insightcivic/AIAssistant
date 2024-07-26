import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
from io import BytesIO
import base64

# Import your ConversationSystem here
# from conversation_system import ConversationSystem

# Initialize conversation system
# conversation_system = ConversationSystem()

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
        # response = conversation_system.generate_response(prompt, st.session_state.messages)
        response = "This is a placeholder response. Implement your AI logic here."
        
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
            # response = conversation_system.generate_response(user_input, st.session_state.messages)
            response = "This is a placeholder response. Implement your AI logic here."
            
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