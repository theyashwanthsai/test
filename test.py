from twilio.rest import Client

# Your Account SID and Auth Token from twilio.com/console
account_sid = ''
auth_token = ''  # Replace with your actual auth token
client = Client(account_sid, auth_token)

message = client.messages.create(
    body='Hello! This is a test message from your kidnapping detection system.',
    from_='whatsapp:+14155238886',
    to='whatsapp:+918919567888'
)

print(message.sid)
