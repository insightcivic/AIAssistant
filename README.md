# AIAssistant
AI Assistant

## Prep

Keep your API keys safe by using a .env file.

1. `pip install python-dotenv`

2. Create a file named `.env` and store the following:

```python
QDRANT_API_KEY=your-api-key-here
```
3. Add `.env` to your `.gitignore` file.

4. When deploying your Streamlit app, make sure to set the environment variable in your deployment environment. For example, if you're using Streamlit Cloud, you can set environment variables in the app settings.
## Requirements

`pip install streamlit gtts SpeechRecognition Pyaudio`



## Running

`streamlit run aiassistant.py`


