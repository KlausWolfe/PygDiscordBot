import re
import json
import requests
import discord
from discord.ext import commands
import os

# configuration settings for the api
model_config = {
    "use_story": False,
    "use_authors_note": False,
    "use_world_info": False,
    "use_memory": False,
    "max_context_length": 2400,
    "max_length": 180,
    "rep_pen": 1.02,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 1.0,
    "tfs": 0.9,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": [6, 0, 1, 2, 3, 4, 5]
}

class Chatbot:
    def __init__(self, char_filename, bot):
        self.prompt = None
        self.endpoint = bot.endpoint
        self.bot = bot
        # Send a PUT request to modify the settings
        requests.put(f"{self.endpoint}/config", json=model_config)
        # read character data from JSON file
        with open(char_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.char_name = data["char_name"]
            self.char_persona = data["char_persona"]
            self.char_greeting = data["char_greeting"]
            self.world_scenario = data["world_scenario"]
            self.example_dialogue = data["example_dialogue"]
        bot.char_name = self.char_name
        # initialize conversation history and character information
        self.convo_filename = None
        self.conversation_history = ""
        self.character_info = f"{self.char_name}'s Persona: {self.char_persona}\nScenario: {self.world_scenario}\n{self.example_dialogue}\n"

        self.num_lines_to_keep = 20

    async def set_convo_filename(self, convo_filename):
        # set the conversation filename and load conversation history from file
        self.convo_filename = convo_filename
        if not os.path.isfile(convo_filename):
            # create a new file if it does not exist
            with open(convo_filename, "w", encoding="utf-8") as f:
                f.write("<START>\n")
        with open(convo_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            num_lines = min(len(lines), self.num_lines_to_keep)
            self.conversation_history = "<START>\n" + "".join(lines[-num_lines:])

    async def save_conversation(self, message, message_content):
        self.conversation_history += f'{message.author.name}: {message_content}\n'
        user_message = f"{message.author.name}: {message_content}"
        #world_info = await self.bot.get_cog("scan_message").world_info(message)
        meme_text = await self.bot.get_cog("scan_message").meme_scan(message)
        print(user_message)
        # prepare conversation history for user info injection
        lines = self.conversation_history.split('\n')
        # inject user info if available
        user_info = await self.bot.get_cog("user_info_cog").get_userinfo(message)
        if (user_info is not None):
            if len(lines) >= 5:
                lines[-5] += user_info
            else:
                num = len(lines) - 1
                lines[num] += user_info
        # define the prompt
        self.prompt = {
            "prompt": self.character_info + '\n'.join(lines[-self.num_lines_to_keep:]) + f'{meme_text}' + f'{self.char_name}:',
        }
        # send a post request to the API endpoint
        response = requests.post(f"{self.endpoint}/api/v1/generate", json=self.prompt)
        # check if the request was successful
        if response.status_code == 200:
            # Get the results from the response
            results = response.json()["results"]
            text = results[0]["text"]
            response_text = self.parse_text_end(text)[0] if self.parse_text_end(text) else ""
            # add bot response to conversation history
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
            if(meme_text):
                print(f'{meme_text}')
            print(f"{self.char_name}: {response_text}")
            with open(self.convo_filename, "a", encoding="utf-8") as f:
                f.write(f'{message.author.name}: {message_content}\n')
                if(meme_text):
                    f.write(f'{meme_text}')
                f.write(f'{self.char_name}: {response_text}\n')  # add a separator between
            await self.bot.get_cog("scan_message").gif_scan(message, response_text)
            return response_text
        
    def parse_text_end(self, text):
        return [line.strip() for line in str(text).split("\n")]

    def batch_save_conversation(self, message):
        # add user message to conversation history
        self.conversation_history += f"{message}\n"
        # define the prompt
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
            print(results)
            text = results[0]['text']
            # split the response to remove excess dialogue
            parts = re.split(r'\n[a-zA-Z]', text)[:1]
            response_text = parts[0][1:]
            # add bot response to conversation history
            self.conversation_history = self.conversation_history + f'{self.char_name}: {response_text}\n'
            return response_text


class ChatbotCog(commands.Cog, name="chatbot"):
    def __init__(self, bot):
        self.bot = bot
        self.chatlog_dir = bot.chatlog_dir
        self.chatbot = Chatbot("chardata.json", bot)

        # create chatlog directory if it doesn't exist
        if not os.path.exists(self.chatlog_dir):
            os.makedirs(self.chatlog_dir)

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
                content = content.replace(f"<:{emoji_name}:{emoji_id}>", f":{emoji_name}:")
        return content

    # Normal Chat handler 
    @commands.command(name="chat")
    async def chat_command(self, message, message_content) -> None:
        if message.guild:
            server_name = message.channel.name
        else:
            server_name = message.author.name
        if (await self.bot.get_cog("scan_message").send_scan(message, await self.replace_user_mentions(message_content))):
            return
        if (await self.bot.get_cog("scan_message").dm_scan(message, await self.replace_user_mentions(message_content))):
            return
        chatlog_filename = os.path.join(self.chatlog_dir, f"{server_name} - chatlog.log")
        if message.guild and self.chatbot.convo_filename != chatlog_filename or \
                not message.guild and self.chatbot.convo_filename != chatlog_filename:
            await self.chatbot.set_convo_filename(chatlog_filename)
        response = await self.chatbot.save_conversation(message, await self.replace_user_mentions(message_content))
        return response  
    @commands.command(name="batch_chat")
    async def batch_chat_command(self, message_content) -> None:

        # get response message from chatbot and return it
        response = self.chatbot.batch_save_conversation(await self.replace_user_mentions(message_content))
        return response
    
async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(ChatbotCog(bot))