import json
import boto3
import os
from datetime import datetime
import urllib.parse
import re

# AWS İstemcileri
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda')

# Tablolar
users_table = dynamodb.Table('WhatsAppUsers')
chat_table = dynamodb.Table('ChatHistory')
reminders_table = dynamodb.Table('Reminders')

# Ortam değişkenleri
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_WHATSAPP_NUMBER = os.environ['TWILIO_WHATSAPP_NUMBER']
S3_BUCKET = os.environ['S3_BUCKET']

def lambda_handler(event, context):
    try:
        print(f"Event alındı: {json.dumps(event)}")
        
        # Webhook'tan gelen veriyi parse et
        body = event.get('body', '')
        params = urllib.parse.parse_qs(body)
        
        from_number = params.get('From', [''])[0]
        message_body = params.get('Body', [''])[0]
        media_url = params.get('MediaUrl0', [''])[0]
        media_type = params.get('MediaContentType0', [''])[0]
        
        print(f"Mesaj: {from_number} - {message_body} - Media: {media_url}")
        
        # Kullanıcıyı kaydet
        save_user(from_number)
        
        # Sohbet geçmişine kaydet
        save_chat(from_number, message_body if message_body else "[Medya gönderildi]", 'user')
        
        # Yanıt oluştur
        if media_url:
            if 'audio' in media_type:
                response = invoke_transcribe_lambda(from_number, media_url)
            elif 'image' in media_type:
                response = invoke_image_lambda(from_number, media_url)
            else:
                response = "Bu medya türünü desteklemiyorum. Ses veya görüntü gönder!"
        else:
            if 'hatırlat' in message_body.lower():
                response = handle_reminder(from_number, message_body)
            else:
                response = get_ai_response(from_number, message_body)
        
        # Yanıtı kaydet
        save_chat(from_number, response, 'assistant')
        
        # Twilio'ya XML yanıt
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/xml'},
            'body': f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response}</Message></Response>'
        }
        
    except Exception as e:
        print(f"HATA: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/xml'},
            'body': '<?xml version="1.0" encoding="UTF-8"?><Response><Message>Bir hata oluştu, tekrar dene!</Message></Response>'
        }

def save_user(phone_number):
    try:
        users_table.put_item(Item={
            'phone_number': phone_number,
            'last_interaction': int(datetime.now().timestamp()),
            'created_at': int(datetime.now().timestamp())
        })
    except Exception as e:
        print(f"User kaydetme hatası: {str(e)}")

def save_chat(phone_number, message, role):
    try:
        chat_table.put_item(Item={
            'phone_number': phone_number,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'role': role,
            'message': message
        })
    except Exception as e:
        print(f"Chat kaydetme hatası: {str(e)}")

def get_chat_history(phone_number, limit=6):
    try:
        response = chat_table.query(
            KeyConditionExpression='phone_number = :phone',
            ExpressionAttributeValues={':phone': phone_number},
            ScanIndexForward=False,
            Limit=limit
        )
        return list(reversed(response['Items']))
    except Exception as e:
        print(f"History alma hatası: {str(e)}")
        return []

def get_ai_response(phone_number, message):
    try:
        # Sohbet geçmişi al
        history = get_chat_history(phone_number)
        
        # Claude formatına çevir
        conversation = []
        for item in history[:-1]:
            conversation.append({
                'role': 'user' if item['role'] == 'user' else 'assistant',
                'content': item['message']
            })
        
        # Yeni mesajı ekle
        conversation.append({'role': 'user', 'content': message})
        
        # Bedrock API çağrısı
        payload = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': conversation,
            'system': 'Sen yardımcı bir WhatsApp asistanısın. Kısa, öz ve dostça yanıtlar ver. Her zaman Türkçe konuş.'
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
        
    except Exception as e:
        print(f"AI hatası: {str(e)}")
        return "Şu an yanıt veremiyorum, biraz sonra tekrar dene!"

def handle_reminder(phone_number, message):
    try:
        # Süre çıkar
        minutes_match = re.search(r'(\d+)\s*(dakika|dk)', message.lower())
        hours_match = re.search(r'(\d+)\s*(saat|sa)', message.lower())
        
        if minutes_match:
            minutes = int(minutes_match.group(1))
            remind_time = int(datetime.now().timestamp()) + (minutes * 60)
        elif hours_match:
            hours = int(hours_match.group(1))
            remind_time = int(datetime.now().timestamp()) + (hours * 3600)
        else:
            return "Süre belirt! Örnek: '30 dakika sonra toplantı hatırlat'"
        
        # Mesajı temizle
        reminder_text = re.sub(r'\d+\s*(dakika|dk|saat|sa)\s*sonra\s*', '', message, flags=re.IGNORECASE)
        reminder_text = reminder_text.replace('hatırlat', '').strip()
        
        # DynamoDB'ye kaydet
        reminder_id = f"{phone_number}_{remind_time}"
        reminders_table.put_item(Item={
            'reminder_id': reminder_id,
            'phone_number': phone_number,
            'remind_at': remind_time,
            'message': reminder_text,
            'created_at': int(datetime.now().timestamp())
        })
        
        return f"✅ Tamam! '{reminder_text}' konusunu sana hatırlatacağım."
        
    except Exception as e:
        print(f"Reminder hatası: {str(e)}")
        return "Hatırlatıcı oluştururken sorun çıktı!"

def invoke_transcribe_lambda(phone_number, audio_url):
    try:
        payload = {
            'phone_number': phone_number,
            'audio_url': audio_url
        }
        lambda_client.invoke(
            FunctionName='whatsapp-bot-transcribe',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        return "🎤 Ses mesajını dinliyorum, biraz bekle..."
    except Exception as e:
        print(f"Transcribe invoke hatası: {str(e)}")
        return "Ses mesajını işleyemedim!"

def invoke_image_lambda(phone_number, image_url):
    try:
        payload = {
            'phone_number': phone_number,
            'image_url': image_url
        }
        lambda_client.invoke(
            FunctionName='whatsapp-bot-image',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        return "📸 Fotoğrafa bakıyorum, hemen sonuç göndereceğim..."
    except Exception as e:
        print(f"Image invoke hatası: {str(e)}")
        return "Fotoğrafı işleyemedim!"
