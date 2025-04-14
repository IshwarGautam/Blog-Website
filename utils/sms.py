import os
from twilio.rest import Client


def send_otp_sms(to, message):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    message = client.messages.create(body=message, from_=from_number, to=to)
    return message.sid
