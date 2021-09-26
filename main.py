import re
import json
import praw
import requests
import configparser

class accountLookup:
    def __init__(self, username):

        self.username = username

        self.playerInfoApi = "https://playerdb.co/api/player/minecraft/"

        self.header = {'User-agent': f'This code is associated with the reddit bot /u/{self.username}'}

    def lookup(self, inputID):

        # If the username/UUID is valid look it up
        if self.validateInput(inputID):
            playerFound, data = self.sendApiRequest(inputID)

            if playerFound:
                return self.genFoundReply(data)

            else:
                return self.genNotFoundReply(inputID)

        else:
            return self.genInvalidReply(inputID)

    # Test to see if the input provided is a valid MC account name or UUID
    def validateInput(self, inputID):
        # TODO: Minecraft usernames cannot have a - but UUIDs do. Regex passes - regardless of input.
        # TODO: Condition ignores that MC names can't be longer than 16 chars
        if len(inputID) > 36 or len(inputID) < 4 or bool(re.search("[^A-Za-z0-9_-]+", inputID)):
            return False
        else:
            return True

    def genFoundReply(self, data):
        reply = f"{data['data']['player']['username']} has been found!  \n" \
                f"Their account UUID is {data['data']['player']['id']}  \n" \
                f"There player head can be found [here]({data['data']['player']['avatar']}).  \n" \
                "This comment was sent by a bot!"

        return reply

    def genInvalidReply(self, inputID):
        reply = f"{inputID} is not a valid UUID/username.  \n" \
                "Please check the spelling of the username and try again.  \n"\
                f"Reply with '\\u\\{self.username} !help' for a quick help guide.  \n" \
                "This comment was sent by a bot!"

        return reply

    def genNotFoundReply(self, inputID):
        reply = f"{inputID} could not be found.  \n" \
                "Please check the spelling of the username and try again.  \n" \
                f"Reply with '\\u\\{self.username} !help' for a quick help guide.  \n"\
                "This comment was sent by a bot!"

        return reply

    def sendApiRequest(self, inputID):
        url = self.playerInfoApi + inputID

        # TODO: Encase request in try except block in case the api is down
        r = requests.get(url, headers=self.header)

        data = json.loads(r.text)

        if data['code'] == 'player.found':
            playerFound = True

        else:
            playerFound = False

        return (playerFound, data)

    def sendHelp(self):
        reply = "To see this comment use the command '!help'  \n" \
                "To use this bot simply:  \n" \
                f"u/{self.username} PlayerName  \n" \
                f"u/{self.username} UUID  \n" \
                "Examples:  \n" \
                f"u/{self.username} Notch  \n" \
                f"u/{self.username} 069a79f4-44e9-4726-a5be-fca90e38aaf5  \n" \
                "This comment was sent by a bot!"

        return reply





if __name__ == '__main__':

    # Open up the config file with the reddit bot login info

    config = configparser.ConfigParser()

    config.read('config.ini')

    try:
        r = praw.Reddit(username=config['LOGIN']['username'],
                        password=config['LOGIN']['password'],
                        client_id=config['LOGIN']['client_id'],
                        client_secret=config['LOGIN']['client_secret'],
                        user_agent=config['LOGIN']['user_agent'])

    except KeyError:
        print("The configuration file is not set up correctly")
        quit()

    username = config['LOGIN']['username']

    # initialize that account lookup class
    a = accountLookup(username)

    # Get the reddit inbox stream
    messages = r.inbox.stream()

    # Iterate through the items in the stream
    for message in messages:
        try:

            # split up each word in the message body
            splitmsg = message.body.split()

            # Look for messages that are both unread and reddit mentions
            if message in r.inbox.mentions() and message in r.inbox.unread():

                # If the mention is from the bots account mark it as read
                if message.author.name == username:
                    message.mark_read()

                # If the message is a help request send it
                elif len(splitmsg) == 1 or len(splitmsg) > 2 or splitmsg[1] == '!help':
                    message.reply(a.sendHelp())
                    print("Help sent")

                # Lookup the requested MC account
                else:
                    message.reply(a.lookup(splitmsg[1]))
                    print("Main message Sent")

                message.mark_read()

        # If praw throws an exception just catch it
        except praw.exceptions.APIException:
            print("Probably hit a rate limit")
