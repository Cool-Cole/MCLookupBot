import re
import json
import praw
import requests
import configparser


class accountLookup:
    def __init__(self):
        self.playerInfoApi = "https://playerdb.co/api/player/minecraft/"

        self.header = {'User-agent': 'This code is associated with the reddit bot /u/MCLookup'}

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
    # TODO: Minecraft usernames cannot have a - but UUIDs do. Regex passes - regardless of input.
    # TODO: Regex ignores that MC names can't be longer than
    def validateInput(self, inputID):
        if len(inputID) > 36 or bool(re.search("[^A-Za-z0-9_-]+", inputID)):
            return False
        else:
            return True

    def genFoundReply(self, data):
        reply = f"{data['data']['player']['username']} has been found!  \n" \
                f"Their account UUID is {data['data']['player']['id']}.  \n" \
                f"There player head can be found [here]({data['data']['player']['avatar']}).  \n" \
                "This post was sent by a bot!"

        return reply

    def genInvalidReply(self, inputID):
        reply = f"{inputID} is not a valid UUID/username.  \n" \
                "Please check the spelling of the username and try again.  \n"\
                "Reply with '\\u\\MCLookup !help' for a quick help guide.  \n" \
                "This post was sent by a bot!"

        return reply

    def genNotFoundReply(self, inputID):
        reply = f"{inputID} could not be found.  \n" \
                "Please check the spelling of the username and try again.  \n" \
                "Reply with '\\u\\MCLookup !help' for a quick help guide.  \n"\
                "This post was sent by a bot!"

        return reply

    def sendApiRequest(self, inputID):
        url = self.playerInfoApi + inputID

        r = requests.get(url, headers=self.header)

        data = json.loads(r.text)

        if data['code'] == 'player.found':
            playerFound = True

        else:
            playerFound = False

        return (playerFound, data)


def sendHelp(message):
    message.reply("To see this comment use the command '!help'  \n"
                  "To use this bot simply:  \n"
                  "u/MCLookup PlayerName  \n"
                  "u/MCLookup UUID  \n"
                  "Examples:  \n"
                  "u/MCLookup 069a79f4-44e9-4726-a5be-fca90e38aaf5  \n"
                  "u/MCLookup Notch  \n"
                  "This post was sent by a bot!")


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

    # initialize that account lookup class
    a = accountLookup()

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
                if message.author.name == 'MCLookup':
                    message.mark_read()

                # If the message is a help request send it
                elif (len(splitmsg) >= 2 and splitmsg[1] == '!help') or len(splitmsg) <= 1:
                    sendHelp(message)
                    print("Help sent")

                # Lookup the requested MC account
                else:
                    message.reply(a.lookup(splitmsg[1]))
                    print("Main message Sent")

                message.mark_read()

        # If praw throws an exception just catch it
        except praw.exceptions.APIException:
            print("Probably hit a rate limit")
