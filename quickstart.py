# http://localhost:8080/?code=4/3ajYsUTJixMauDfTKf78y9wU9o4m.8mpZ0auStZwTmmS0T3UFEsPE67IYjgI
import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
import poster
import media_sources

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = './apiclient/client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://mail.google.com/'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

class Gmail:
    def __init__(self):
        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
        http = httplib2.Http()

        # Try to retrieve credentials from storage or run the flow to generate them
        credentials = STORAGE.get()
        if credentials is None or credentials.invalid:
          credentials = run(flow, STORAGE, http=http)

        # Authorize the httplib2.Http object with our credentials
        http = credentials.authorize(http)

        # Build the Gmail service from discovery
        self.gmail_service = build('gmail', 'v1', http=http)



    def get_header_value(self, headers, name):
        for h in headers:
            if h['name'] == name:
                return h['value']
        return None


    def delete_message(self, id):
        self.gmail_service.users().messages().delete(userId='me', id=id).execute()

    def get_messages_to_post(self):
        threads = self.gmail_service.users().threads().list(userId='me').execute()
        ret = []
        # Print ID for each thread
        if 'threads' not in threads:
            return
        if threads['threads']:
          for thread in threads['threads']:
            t = self.gmail_service.users().threads().get(userId='me', id=thread['id']).execute()
            for message in t['messages']:
                parts = message['payload']['parts']
                string = None
                for p in parts:
                  data = p['body']['data']
                  import json       
                  print json.dumps(message, sort_keys=True, indent=4, separators=(',', ': '))
                  import base64
                  if p['mimeType'] == "text/plain":
                    data = data.replace("-", "+").replace("_", "/")
                    string = base64.b64decode(data)
                    print "str is " + string
                    break
                headers = message['payload']['headers']
                title = self.get_header_value(headers, 'Subject')
                isZarar = "zarars@gmail.com" in self.get_header_value(headers, 'From')
                string = string.strip()
                import re
                string = re.sub(r'<.*>', '', string)
                string = string.replace("*", "")
                string = re.sub(r'[\r\n]+', '\r\n', string)
                print "str2 " + string

                message_parts = string.strip().split("\r\n")
                url = message_parts[0]
                primary = message_parts[1]
                secondary = None
                if (len(message_parts) > 2):
                    secondary = message_parts[2]
                eventDate = None
                if (len(message_parts) > 3):
                    eventDate = message_parts[3]
                if isZarar:
                    ret.append(
                        {
                        'postInfo':  (title, url, primary, secondary, eventDate),
                        'messageId': message['id']
                        }
                    )
        return ret

            #import json
            #print json.dumps(message, sort_keys=True, indent=4, separators=(',', ': '))    
        """

                #m = gmail_service.users().messages().get(userId='me', id=message['id']).execute()
            #print json.dumps(m, sort_keys=True, indent=4, separators=(',', ': '))
            #print thread.keys()
            #print thread['snippet']
        """
gmail = Gmail()
while True:
    print "get messages"
    messages = gmail.get_messages_to_post()


    if messages != None:
        print messages
        messages = reversed(messages)
        for message in messages:
            m = message['postInfo']
            """
            print m[0]
            print m[1]
            print m[2]
            print m[3]
            print m[4]
            """
            d = None;
            if m[4] == None:
                import datetime
                d = datetime.date.today().strftime('%Y-%m-%d')
            else:
                d = m[4]
            wpp = poster.WordPressPoster(d, m[2], m[3])
            #print MediaPostFactory.create(args['url']).get_embed()
            wpp.create_match_post(poster.MediaPostFactory.create(m[1]), m[0], [], '')
            message_id = message['messageId']
            gmail.delete_message(message_id)



    import time
    time.sleep(300)
