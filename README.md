# AWS Intelligent WhatsApp Assistant

Serverless, AI-powered WhatsApp chatbot built with AWS services.

## Features
- 💬 Natural language conversations (AWS Bedrock - Claude)
- 🎤 Voice message transcription (AWS Transcribe)
- 📸 Image analysis and description (AWS Rekognition)
- ⏰ Smart reminder system (EventBridge + DynamoDB)
- 💾 Conversation history and context management

## Architecture
- **API Gateway**: Webhook endpoint for Twilio
- **Lambda**: 4 serverless functions
- **DynamoDB**: NoSQL database for chat history and reminders
- **S3**: Media file storage
- **Bedrock**: Claude AI for natural language processing
- **Transcribe**: Speech-to-text conversion
- **Rekognition**: Computer vision for image analysis
- **EventBridge**: Scheduler for reminders

## Cost
100% FREE with AWS Free Tier

## Tech Stack
Python 3.11 | AWS Lambda | DynamoDB | S3 | Bedrock | Transcribe | Rekognition
