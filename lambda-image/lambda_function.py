import json
import boto3
import os
import urllib.request
import uuid
from datetime import datetime

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

S3_BUCKET = os.environ['S3_BUCKET']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_WHATSAPP_NUMBER = os.environ['TWILIO_WHATSAPP_NUMBER']

chat_table = dynamodb.Table('ChatHistory')

def lambda_handler(event, context):
    try:
        phone_number = event['phone_number']
        image_url = event['image_url']
        
        print(f"Görüntü işleniyor: {phone_number} - {image_url}")
        
        # Görüntüyü indir
        image_key = f"images/{uuid.uuid4()}.jpg"
        urllib.request.urlretrieve(image_url, '/tmp/image.jpg')
        s3_client.upload_file('/tmp/image.jpg', S3_BUCKET, image_key)
        
        # Rekognition ile analiz
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': S3_BUCKET, 'Name': image_key}},
            MaxLabels=10,
            MinConfidence=70
        )
        
        # Etiketleri topla
        labels = [label['Name'] for label in response['Labels']]
        labels_text = ", ".join(labels)
        
        print(f"Tespit edilen: {labels_text}")
        
        # AI ile açıklama
        prompt = f"Bu fotoğrafta şunlar var: {labels_text}. Kullanıcıya bu fotoğrafı 2-3 cümle ile kısa ve dostça açıkla. Türkçe konuş."
        ai_description = get_ai_description(prompt)
        
        # Kullanıcıya gönder
        message = f"📸 Fotoğrafını inceledim!\n\n{ai_description}\n\n🔍 Gördüklerim: {labels_text}"
        send_whatsapp_message(phone_number, message)
        
        # Kaydet
        save_chat(phone_number, "[Fotoğraf gönderildi]", 'user')
        save_chat(phone_number, message, 'assistant')
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Image hatası: {str(e)}")
        try:
            send_whatsapp_message(event['phone_number'], "Fotoğrafı analiz edemedim!")
        except:
            pass
        return {'statusCode': 500}

def get_ai_description(prompt):
    try:
        payload = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 500,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    except Exception as e:
        print(f"AI hatası: {str(e)}")
        return "Açıklama yapamadım."

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

def send_whatsapp_message(to_number, message):
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
    except Exception as e:
        print(f"Twilio hatası: {str(e)}")
