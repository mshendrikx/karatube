from mailjet_rest import Client
import os

api_key = 'c847b4f2ee15b0ac5ae31d7d0943e4d0'
api_secret = '23bffef98a23819a8e50a040aacd1092'

#api_key = '49421fab95c47aac60a502b82cb36e3a'
#api_secret = '504c74f9068d61b20e8d910b15222e49'

mailjet = Client(auth=(api_key, api_secret), version='v3.1')
data = {
  'Messages': [
    {
      "From": {
        "Email": "karatubebr@gmail.com",
        "Name": "Karatube"
      },
      "To": [
        {
          "Email": "mauricio.servatius@gmail.com",
          "Name": "Maurício"
        }
      ],
      "Subject": "My first Mailjet Email!",
      "TextPart": "Greetings from Mailjet!",
      "HTMLPart": "<h3>Dear passenger 1, welcome to <a href=\"https://www.mailjet.com/\">Mailjet</a>!</h3><br />May the delivery force be with you!"
    }
  ]
}
result = mailjet.send.create(data=data)
print (result.status_code)
print (result.json())