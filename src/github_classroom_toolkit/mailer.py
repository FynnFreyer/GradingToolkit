from contextlib import contextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imaplib import IMAP4_SSL, Time2Internaldate
from time import time


@contextmanager
def imap_connection(server: str, email_account: str, password: str):
    # Establish the IMAP connection
    mail = IMAP4_SSL(server)
    mail.login(email_account, password)
    try:
        yield mail  # Yield the connection object
    finally:
        # Logout and close the connection when done
        mail.logout()


def create_msg(sender: str, recipient: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    return msg


def create_draft(msg: MIMEMultipart, server: str, email_account: str, password: str):
    with imap_connection(server, email_account, password) as mail:
        mail.select('"Drafts"')

        # Create a draft by appending the message
        status, response = mail.append(
            '"Drafts"',
            "\\Draft",
            Time2Internaldate(time()),
            msg.as_string().encode("utf-8"),
        )

        # Check if the draft was created successfully
        if status != "OK":
            raise Exception("Couldn't create draft")
