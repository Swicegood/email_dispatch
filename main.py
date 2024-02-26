from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import subprocess
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def grab_emails(search_str):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('./token/token.json'):
        creds = Credentials.from_authorized_user_file('./token/token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                os.remove('token.json')  # Remove the invalid token
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_console()
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_console()

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().messages().list(userId='me', q=search_str, maxResults=10).execute()
    messages = results.get('messages', [])
    emailmatches = []    

    if not messages:
        print('No messages found.')
    else:
        print('Messages:')
        for message in messages:
            emailmatches.append(service.users().messages().get(userId='me', id=message['id']).execute())
            emailmatches[-1]['confidence'] = 7
            print(emailmatches[-1]['snippet'])

    return emailmatches


def create_email(email):
# Create a MIMEMultipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = next(header['value'] for header in email['payload']['headers'] if header['name'] == 'Subject')
    msg['From'] = next(header['value'] for header in email['payload']['headers'] if header['name'] == 'From')
    msg['To'] = next(header['value'] for header in email['payload']['headers'] if header['name'] == 'To')

    # Add the plain and HTML parts
    for part in email['payload']['parts']:
        part_data = base64.urlsafe_b64decode(part['body']['data'].encode('ASCII')).decode('utf-8')
        if part['mimeType'] == 'text/plain':
            msg.attach(MIMEText(part_data, 'plain'))
        elif part['mimeType'] == 'text/html':
            msg.attach(MIMEText(part_data, 'html'))

    # Convert the multipart message to a string
    return  msg.as_string()


if __name__ == "__main__":
    email_matches = grab_emails("ThoughtOfTheDay")
    for email in email_matches:
        print(create_email(email))
        email_str = create_email(email)
        cmd = f"echo '{email_str}' | docker run --rm -i thought_of_the_day"

        subprocess.run(cmd, shell=True)