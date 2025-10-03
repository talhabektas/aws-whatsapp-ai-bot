# 🤖 AWS Intelligent WhatsApp Assistant

Serverless, AI-powered WhatsApp chatbot built entirely with AWS services. Features natural language conversations, voice transcription, image analysis, and smart reminders.

![AWS](https://img.shields.io/badge/AWS-Lambda-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **💬 AI Conversations**: Natural language chat powered by Claude 3 Haiku (AWS Bedrock)
- **🎤 Voice Transcription**: Converts voice messages to text (AWS Transcribe)
- **📸 Image Analysis**: Analyzes and describes photos (AWS Recognition)
- **⏰ Smart Reminders**: Time-based reminder system (EventBridge + DynamoDB)
- **💾 Context Management**: Maintains conversation history for contextual responses

## 🏗️ Architecture

```
WhatsApp → Twilio → API Gateway → Lambda Functions
                                        ↓
                ┌───────────────────────┼───────────────────────┐
                ↓                       ↓                       ↓
            DynamoDB                    S3                  Bedrock
        (Chat/Reminders)              (Media)             (Claude AI)
                ↓                       ↓                       ↓
            Transcribe              Recognition           EventBridge
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| **Lambda** | 4 serverless functions for message processing |
| **API Gateway** | REST API webhook for Twilio |
| **DynamoDB** | NoSQL database for chat history and reminders |
| **S3** | Media file storage |
| **Bedrock** | Claude AI for natural language processing |
| **Transcribe** | Speech-to-text conversion |
| **Recognition** | Computer vision for image analysis |
| **EventBridge** | Scheduler for timed reminders |

## 💰 Cost

**100% FREE** with AWS Free Tier:
- Lambda: 1M requests/month
- DynamoDB: 25 GB storage
- S3: 5 GB storage
- Transcribe: 60 minutes/month
- Recognition: 5,000 images/month

Estimated monthly cost after free tier: **< $5** for moderate usage

## 🚀 Deployment

### Prerequisites
- AWS Account
- Twilio Account (free sandbox)
- Python 3.11+
- AWS CLI configured

### Setup Instructions

#### 1. Clone the repository
```bash
git clone https://github.com/talhabektas/aws-whatsapp-ai-bot.git
cd aws-whatsapp-ai-bot
```

#### 2. Create IAM Role
- Go to AWS IAM → Roles → Create role
- Add policies: Lambda, DynamoDB, S3, Bedrock, Transcribe, Recognition
- Name: `WhatsAppBotLambdaRole`

#### 3. Create DynamoDB Tables

```bash
# WhatsAppUsers
aws dynamodb create-table --table-name WhatsAppUsers \
  --attribute-definitions AttributeName=phone_number,AttributeType=S \
  --key-schema AttributeName=phone_number,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region eu-central-1

# ChatHistory
aws dynamodb create-table --table-name ChatHistory \
  --attribute-definitions AttributeName=phone_number,AttributeType=S AttributeName=timestamp,AttributeType=N \
  --key-schema AttributeName=phone_number,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST --region eu-central-1

# Reminders
aws dynamodb create-table --table-name Reminders \
  --attribute-definitions AttributeName=reminder_id,AttributeType=S AttributeName=remind_at,AttributeType=N \
  --key-schema AttributeName=reminder_id,KeyType=HASH \
  --global-secondary-indexes '[{"IndexName":"RemindAtIndex","KeySchema":[{"AttributeName":"remind_at","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST --region eu-central-1
```

#### 4. Create S3 Bucket

```bash
aws s3 mb s3://your-bucket-name --region eu-central-1
```

#### 5. Deploy Lambda Functions

```bash
cd lambda-main
pip install -r requirements.txt -t .
zip -r ../lambda-main.zip .
cd ..

aws lambda create-function \
  --function-name whatsapp-bot-main \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/WhatsAppBotLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-main.zip \
  --timeout 60 --memory-size 512 \
  --region eu-central-1 \
  --environment Variables="{TWILIO_ACCOUNT_SID=xxx,TWILIO_AUTH_TOKEN=xxx,TWILIO_WHATSAPP_NUMBER=xxx,S3_BUCKET=xxx}"
```

*Repeat for other Lambda functions: `transcribe`, `image`, `reminder`*

#### 6. Setup API Gateway
- Create REST API
- Create `/webhook` resource with POST method
- Configure Lambda proxy integration
- Deploy to `prod` stage

#### 7. Configure EventBridge

```bash
aws events put-rule --name whatsapp-bot-reminder-check \
  --schedule-expression "rate(1 minute)" --state ENABLED --region eu-central-1
```

#### 8. Enable Bedrock Models
- Go to AWS Bedrock → Model access
- Enable Claude 3 Haiku

#### 9. Configure Twilio
- Add API Gateway webhook URL to Twilio WhatsApp sandbox

## 📝 Usage Examples

### Text Chat:
```
User: Merhaba!
Bot: Merhaba! Nasıl yardımcı olabilirim?
```

### Voice Message:
```
User: [Sends voice message]
Bot: 🎤 Duyduğum: [transcribed text]
     [AI response]
```

### Image Analysis:
```
User: [Sends photo]
Bot: 📸 Fotoğrafını inceledim!
     [Description of image]
     🔍 Gördüklerim: [detected objects]
```

### Reminders:
```
User: 30 dakika sonra toplantı hatırlat
Bot: ✅ Tamam! 'toplantı' konusunu sana hatırlatacağım.

[After 30 minutes]
Bot: 🔔 Hatırlatma: toplantı
```

## 🛠️ Tech Stack

- **Language**: Python 3.11
- **Infrastructure**: AWS Lambda (Serverless)
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku), Transcribe, Recognition
- **Database**: DynamoDB (NoSQL)
- **Storage**: S3
- **API**: Twilio WhatsApp, API Gateway
- **Scheduler**: EventBridge

## 📊 Performance

- **Response Time**: < 3 seconds for text messages
- **Scalability**: Auto-scales to handle unlimited concurrent users
- **Availability**: 99.9% uptime (AWS SLA)

## 🔐 Security

- IAM role-based access control
- Encryption at rest (S3, DynamoDB)
- No hardcoded credentials
- Environment variables for sensitive data

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use this project for learning or commercial purposes.

## 👤 Author

**Talha Bektaş**

- GitHub: [@talhabektas](https://github.com/talhabektas)
- LinkedIn: [Talha Bektaş](https://www.linkedin.com/in/mehmettalha6116)

## 🙏 Acknowledgments

- AWS for the amazing serverless platform
- Anthropic for Claude AI
- Twilio for WhatsApp API integration

## 🔒 Security Best Practices

### Before Deployment:
1. **Never commit credentials** to version control
2. Use **AWS Secrets Manager** for sensitive data:
```bash
   aws secretsmanager create-secret --name whatsapp-bot/twilio \
     --secret-string '{"account_sid":"xxx","auth_token":"xxx"}'
```
---
 ⭐ **If you found this project helpful, please give it a star!**  
