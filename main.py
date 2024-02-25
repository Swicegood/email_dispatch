from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import subprocess


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
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

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

def get_email_body(email):
    return email['snippet']

def get_email_subject(email):
    for header in email['payload']['headers']:
        if header['name'] == 'Subject':
            return header['value']
    return "No Subject"

import json

def create_email(email):
    subject = get_email_subject(email)
    body = get_email_body(email)
    confidence = email['confidence']
    return f"Subject: {subject}\n\nBody: {body}\n\nConfidence: {confidence}"


if __name__ == "__main__":
    email_matches = grab_emails("ThoughtOfTheDay")
    for email in email_matches:
        print(create_email(email))
        email_str = create_email(email)
        cmd = f'echo "{email_str}" | docker run --rm -i thought_of_the_day'

        subprocess.run(cmd, shell=True)