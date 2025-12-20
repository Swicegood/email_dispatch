from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError
import os
import subprocess
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import tempfile
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists('./token/token.json'):
        creds = Credentials.from_authorized_user_file('./token/token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print(f"Token refresh failed: {e}")
                print("Removing invalid token and re-authenticating...")
                os.remove('./token/token.json')  # Remove the invalid token
                creds = None
        
        if not creds or not creds.valid:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Select your project (or create a new one)\n"
                    "3. Enable Gmail API\n"
                    "4. Go to 'Credentials' > 'Create Credentials' > 'OAuth client ID'\n"
                    "5. Choose 'Desktop app' and download the JSON file\n"
                    "6. Save it as 'credentials.json' in this directory"
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_console()
            except Exception as e:
                error_msg = str(e)
                if 'deleted_client' in error_msg or '401' in error_msg:
                    raise ValueError(
                        "OAuth client has been deleted. Please create a new OAuth client:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Navigate to 'APIs & Services' > 'Credentials'\n"
                        "3. Create a new OAuth 2.0 Client ID (Desktop app)\n"
                        "4. Download the credentials and save as 'credentials.json'\n"
                        "5. Delete the old token.json file if it exists"
                    )
                else:
                    raise

        # Save the credentials for the next run
        os.makedirs('./token', exist_ok=True)
        with open('./token/token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def grab_emails(search_str):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    service = get_gmail_service()

    # Call the Gmail API
    results = service.users().messages().list(userId='me', q=search_str, maxResults=10).execute()
    messages = results.get('messages', [])
    emailmatches = []    

    if not messages:
        print('No messages found.')
    else:
        for message in messages:
            emailmatches.append(service.users().messages().get(userId='me', id=message['id']).execute())
            emailmatches[-1]['confidence'] = 7

    return emailmatches

def unread_emails(emails):
    unread = []
    for email in emails:
        if 'UNREAD' in email.get('labelIds', []):
            unread.append(email)
    return unread

def mark_as_read(email):
    service = get_gmail_service()
    service.users().messages().modify(userId='me', id=email['id'], body={'removeLabelIds': ['UNREAD']}).execute()

def archive_email(email):
    service = get_gmail_service()
    service.users().messages().modify(userId='me', id=email['id'], body={'removeLabelIds': ['INBOX']}).execute()

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
    unread = unread_emails(email_matches)
    if not unread:
        print("No unread Thought Of The Day emails")
        exit(0)
    for email in unread:
        print(create_email(email))
        email_str = create_email(email)
        # Create a temporary file
        with tempfile.NamedTemporaryFile('w', delete=False) as temp:
            temp.write(email_str)
            temp.close()

        # Create the Docker command
        cmd = f'cat {temp.name} | docker run --rm -i thought_of_the_day'
        print(cmd)
        # Run the command
        subprocess.run(cmd, shell=True)
        mark_as_read(email)
        archive_email(email)

    print("Done")







