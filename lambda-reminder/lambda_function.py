import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
reminders_table = dynamodb.Table('Reminders')

TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_WHATSAPP_NUMBER = os.environ['TWILIO_WHATSAPP_NUMBER']

def lambda_handler(event, context):
    try:
        print("Hatırlatıcı kontrolü başladı")
        
        # Şu anki zaman (son 60 saniyeyi kapsayacak şekilde)
        current_time = int(datetime.now().timestamp())
        
        # Son 1 dakika içindeki tüm hatırlatıcıları kontrol et
        sent_count = 0
        for i in range(60):
            check_time = current_time - i
            
            try:
                response = reminders_table.query(
                    IndexName='RemindAtIndex',
                    KeyConditionExpression='remind_at = :time',
                    ExpressionAttributeValues={':time': check_time}
                )
                
                # Her hatırlatıcı için
                for reminder in response['Items']:
                    phone_number = reminder['phone_number']
                    message = reminder['message']
                    
                    print(f"Hatırlatıcı gönderiliyor: {phone_number} - {message}")
                    
                    # WhatsApp mesajı gönder
                    send_whatsapp_message(
                        phone_number,
                        f"🔔 Hatırlatma: {message}"
                    )
                    
                    # Hatırlatıcıyı sil
                    reminders_table.delete_item(
                        Key={'reminder_id': reminder['reminder_id']}
                    )
                    
                    sent_count += 1
                    
            except Exception as e:
                print(f"Zaman {check_time} kontrol hatası: {str(e)}")
                continue
        
        print(f"{sent_count} hatırlatıcı gönderildi")
        return {
            'statusCode': 200,
            'body': json.dumps(f"{sent_count} hatırlatıcı gönderildi")
        }
        
    except Exception as e:
        print(f"Hatırlatıcı ana hatası: {str(e)}")
        return {'statusCode': 500}

def send_whatsapp_message(to_number, message):
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
        print(f"Mesaj gönderildi: {to_number}")
    except Exception as e:
        print(f"Twilio hatası: {str(e)}")
