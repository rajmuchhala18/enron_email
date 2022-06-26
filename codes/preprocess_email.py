#Email Preprocessing functions
from email.parser import Parser

def email_analyse(email):
    email_body = Parser().parsestr(email)
    if(email_body):
        return email_body.get_payload()

def parse_raw_message(raw_message):
    lines = raw_message.split('\n')
    email = {}
    message = ''
    for line in lines:
        if ':' not in line:
            message += line.strip()
            email['body'] = message
    return email

def parse_into_emails(message):
    email = parse_raw_message(message)
    return email

def get_email(data):
    result = []
    email_body = email_analyse(data)
    final_email = parse_into_emails(email_body)
    result.append(final_email['body'])
    return result
