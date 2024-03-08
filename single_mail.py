import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER") # Outlook SMTP server
port = 587  # For STARTTLS
sender_email = os.getenv("SENDER_EMAIL")
password = os.getenv("SENDER_PASSWORD")

context = ssl.create_default_context()
server = None

try:
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)

    receiver_email = "whomyouwant@send.com"
    subject = "Subject: Hi there"
    body = "This message is sent from Python."

    message = f"{subject}\n\n{body}"

    server.sendmail(sender_email, receiver_email, message)
    print("Email sent successfully!")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if server:
        server.quit()
