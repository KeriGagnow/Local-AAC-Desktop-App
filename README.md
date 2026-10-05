_# Local AAC Desktop App
A Augmentative and Alternative Communication desktop application that utilizes Local RAG AI and ChromaDB to predict short hand text and using TTS to announce full sentences. 

## Purpose
This project has been a big dream of mine since middle school and inspired me to study and pursue Computer Science. This application is built to assist non-verbal and mute autistic children & adults with addressing needs and holding conversations. 

## How it works
The application is built using Python to store a local database, creating the desktop app interface and the Text-to-Speech function. The AI model is Phi3, created by Microsoft. The model is downloaded and called from Ollama, which makes the AI model 100% offline and doesn't share any data outside of your local computer, perfect for AI-Privacy first. 
The database comes with sample sentences, but you can train the local AI over time to add new shorthand phrases to its database and it can predict what you want to speak with 80% accuracy.

## How to setup
You'll need to setup Python(Recommend downloading it from Python.org and installing the latest version)
You can use any IDE(I prefer Visual Studio Code) to run the code.
For this project, you will need to pip install from Windows Command Prompt the following:
  *customtkiner
  *ollama
  *pyttx3
  *chromadb
You will also need to download the Ollama application and run *ollama pull phi3* on Windows Command Prompt to install the AI model 

## What can run this:
Currently have not been able to benchmark other hardware that can run this program, so will appreciate additional help to find what hardware can run this.
This is my hardware that I coded and tested the program on:
Dell Latitude 7430 laptop (Intel Core i7 12th gen, 32GB ram, Intel Iris Xe graphics, Windows 11 26h2 Pro)

## Keri's To Dos:
-Creating embedded command prompts to copy and paste into Windows
-Expand on potentially customizing the AI voice's various pitches
-Expand button functionalities
-Expand to website platform for lightweight or ChromeOS platforms
