from mailersend import emails

# Initialize the MailerSend client with your API key
mailer = emails.NewEmail('mlsn.094d41e56139cd0ee0319e031a5f0b05ac7dfc5add91762caea5a8752262817d')

# Define email details
mail_body = {}
mail_from = {
    "name": "Karatube",
    "email": "karatube@hendrikx.com.br",
}
recipients = [
    {
        "name": "Mauricio",
        "email": "mauricio.servatius@gmail.com",
    }
]
reply_to = [
    {
        "name": "Mauricioe",
        "email": "mauricio.servatius@gmail.com",
    }
]

# Set email properties
mailer.set_mail_from(mail_from, mail_body)
mailer.set_mail_to(recipients, mail_body)
mailer.set_subject("Hello!", mail_body)
mailer.set_html_content("Hello, this is an example email from MailerSend", mail_body)
mailer.set_plaintext_content("Hello, this is an example email from MailerSend", mail_body)
mailer.set_reply_to(reply_to, mail_body)

# Send the email
mailer.send(mail_body)

print(mailer)

breakpoint
