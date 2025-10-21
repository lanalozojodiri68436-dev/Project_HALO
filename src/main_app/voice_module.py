# -*- coding: utf-8 -*-
"""
Voice Module for HALO
=====================

Handles Speech-to-Text (STT) and Text-to-Speech (TTS) functionalities.
"""
import speech_recognition as sr
import pyttsx3
from loguru import logger

class VoiceModule:
    """Manages all voice-related interactions for HALO."""

    def __init__(self):
        """Initializes the TTS and STT engines."""
        logger.info("Initializing VoiceModule...")
        try:
            # Initialize TTS Engine (pyttsx3)
            self.tts_engine = pyttsx3.init()
            
            # Initialize STT Recognizer (SpeechRecognition)
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            logger.info("TTS and STT engines initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize voice engines: {e}")
            self.tts_engine = None
            self.recognizer = None

    def speak(self, text: str):
        """
        Converts text to speech and plays it.

        Args:
            text (str): The text to be spoken.
        """
        if self.tts_engine:
            logger.info(f"Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            logger.error("TTS engine is not available.")

    def listen(self) -> str | None:
        """
        Listens for voice input from the microphone and converts it to text.

        Returns:
            str | None: The recognized text, or None if recognition fails.
        """
        if not self.recognizer or not self.microphone:
            logger.error("STT engine is not available.")
            return None
            
        with self.microphone as source:
            logger.info("Listening for command...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        
        try:
            logger.info("Recognizing speech...")
            text = self.recognizer.recognize_google(audio, language="zh-CN")
            logger.info(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None