import re
import json
import requests
import discord
from discord.ext import commands
import os


# Put the configuration settings in the api
model_config = {
    "use_story": False,
    "use_authors_note": False,
    "use_world_info": False,
    "use_memory": False,
    "max_context_length": 2400,
    "max_length": 80,
    "rep_pen": 1.02,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 0.9,
    "tfs": 0.9,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": [6, 0, 1, 2, 3, 4, 5]
}
# Send a PUT request to modify the settings


CHATLOG_DIR = "chatlog_dir"


class Chatbot:
    def __init__(self, char_filename, chatlog_dir, endpoint):
        self.endpoint = endpoint
        requests.put(f"{endpoint}/config", json=model_config)
        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]

        # create chatlog directory if it doesn't exist
        if not os.path.exists(chatlog_dir):
            os.makedirs(chatlog_dir)

        # initialize conversation history and character information
        self.convo_filename = None
        self.conversation_history = ""
        self.character_info = f"{self.char_name}'s Persona: {self.char_persona}\nScenario: {self.world_scenario}\n{self.example_dialogue}\n"

        self.num_lines_to_keep = 20

    async def set_convo_filename(self, convo_filename):
        # set the conversation filename and load conversation history from file
        self.convo_filename = convo_filename
        log_filename = os.path.join(CHATLOG_DIR, f"{self.char_name}.log")
        with open(log_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            num_lines = min(len(lines), self.num_lines_to_keep)
            self.conversation_history = "<START>\n" + "".join(lines[-num_lines:])

    async def log_chat(self, name, message):
        # write message to chat log file
        log_filename = os.path.join(CHATLOG_DIR, f"{self.char_name}.log")
        with open(log_filename, "a", encoding="utf-8") as f:
            f.write(f"{name}: {message}\n")

    async def save_conversation(self, message, cleaned_message):
        self.conversation_history += f"{message.author.name}: {cleaned_message}\n"
        print(f"{message.author.name}: {cleaned_message}")
        await self.log_chat(message.author.name, cleaned_message)
        # format prompt
        prompt = {
            "prompt": self.character_info + '\n'.join(
                self.conversation_history.split('\n')[-self.num_lines_to_keep:]) + f'{self.char_name}:',
        }
        # send a post request to the API endpoint
        response = requests.post(f"{self.endpoint}/api/v1/generate", json=prompt)
        # check if the request was successful
        if response.status_code == 200:
            # get the results from the response
            results = response.json()['results']
            text = results[0]['text']
            # split the response to remove excess dialogue
            parts = re.split(r'\n[a-zA-Z]', text)[:1]
            response_text = parts[0][1:]
            # add bot response to conversation history
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
            print(f"{self.char_name}: {response_text}")
            await self.log_chat(self.char_name, response_text)
            return response_text

class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot, chatlog_dir):
        self.bot = bot
        self.chatlog_dir = chatlog_dir
        self.endpoint = bot.endpoint
        self.chatbot = Chatbot("chardata.json", chatlog_dir=chatlog_dir, endpoint=self.endpoint)

    # converts user ids and emoji ids
    async def replace_user_mentions(self, content):
        user_ids = re.findall(r'<@(\d+)>', content)
        for user_id in user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user:
                display_name = user.display_name
                content = content.replace(f"<@{user_id}>", display_name)

        emojis = re.findall(r'<:[^:]+:(\d+)>', content)
        for emoji_id in emojis:
            if ':' in content:
                emoji_name = content.split(':')[1]
                content = content.replace(f"<:{emoji_name}:{emoji_id}>", f"[{emoji_name} emoji]")
        return content

    # Normal Chat handler 
    @commands.command(name="chat")
    async def chat_command(self, message, message_content) -> None:
        # Get the gnarly response message from the chatbot and return it, dude!
        if message.guild is not None:
            server_name = message.guild.name
            chatlog_filename = os.path.join(self.chatlog_dir, f"{self.bot.user.name} - {server_name} - chatlog.log")
        else:
            # name file after sender
            chatlog_filename = os.path.join(self.chatlog_dir,
                                            f"{self.bot.user.name} - {message.author.name} - chatlog.log")

        # If this is the first message in the convo, set the convo filename, bro!
        if self.chatbot.convo_filename != chatlog_filename:
            await self.chatbot.set_convo_filename(chatlog_filename)

        # Save the convo and get a sweet response, my man!
        cleaned_message = await self.replace_user_mentions(message_content)
        response = await self.chatbot.save_conversation(message, cleaned_message)
        return response


async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot, chatlog_dir=CHATLOG_DIR))
