import os, json
import requests, random, asyncio, pytz, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from cogs.devcommands import embedder

class TimedEventsCog(commands.Cog, name="timed_events"):
    def __init__(self, bot):
        self.bot = bot
        self.endpoint = bot.endpoint
        self.chatlog_dir = bot.chatlog_dir
        self.char_name = bot.char_name
        self.channel_id = bot.channel_id
        self.message_storage = 'CharacterInfo/relationship/message_storage.json'
        self.users_dict = []
        with open('user_lists.json', 'r') as f:
            data = json.load(f)
            self.blacklist_list = data['blacklist']
            self.priority_list = data['priority']
        with open(self.message_storage, 'r') as f:
            data = json.load(f)
            self.starter_messages = data['starter_messages']
            self.noreply_messages = data['noreply_dm_messages']
            self.noreply_channel_messages = data['noreply_channel_messages']
            self.goodbye_words = data['goodbye_words']


    # Random Message Sending
    async def timed_message(self):
        # Divide the length of the dictionary by 4 and assign to num_to_message
        if (len(self.users_dict) >= 4):
            num_to_message = int(len(self.users_dict) / 4)
        else:
            num_to_message = len(self.users_dict)
        # Select num_to_message amount of users randomly from the dictionary
        users_to_message = random.sample(list(self.users_dict), num_to_message) + self.priority_list
        for user in users_to_message:
            try:
                user = self.bot.get_user(user)
            except:
                user = None
            if (user is not None) and not (user == self.bot.user) and (user.id not in self.blacklist_list):
                # Create a DM channel with the user
                try:
                    dm_channel = await user.create_dm()
                except:
                    dm_channel = None
                if (dm_channel is not None):
                    try:
                        last_message = [message async for message in dm_channel.history(limit=1)][0]
                    except:
                        last_message = None
                    try:
                        user_path = f"UserConfig/{last_message.author.id}.json"
                        with open(user_path, "r") as f:
                            user_data = json.load(f)
                    except:
                        user_data = None
                    if(user_data is not None):
                        if(user_data['relationship_level'] == 'romantic partner'):
                            with open(self.message_storage, 'r') as f:
                                data = json.load(f)
                                self.noreply_messages = data['romantic_starter_messages']
                        else:
                            with open(self.message_storage, 'r') as f:
                                data = json.load(f)
                                self.noreply_messages = data['starter_messages']
                    if (last_message is not None):
                        # Get the timestamp of the message
                        message_timestamp = last_message.created_at.replace(tzinfo=pytz.UTC)
                        current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
                        time_since_message = current_time - message_timestamp
                        time_since_message_minutes = int(time_since_message.total_seconds() / 60)
                        if (time_since_message_minutes >= 480) and (last_message.author == self.bot.user):
                            try:
                                await dm_channel.send(embed=embedder(f"You have been selected by {self.char_name} for a private message.\nIf you do not wish to be selected again run the '/blacklist' command.\nIf you wish to be selected more run the '/priority' command."))
                                random_message = str(random.sample(self.starter_messages, 1)[0]).replace('{user}', user.name).replace('{time_since}', f'{time_since_message_minutes} minutes').replace('{char_name}', self.char_name)
                                await dm_channel.send(random_message)
                                self.save_logs(user.name, random_message)
                                print(f"{user.name} was sent: {random_message} by {self.char_name}")
                            except:
                                pass
                    elif(last_message is None):
                        try:
                            await dm_channel.send(embed=embedder(f"You have been selected by {self.char_name} for a private message.\nIf you do not wish to be selected again run the '/blacklist' command.\nIf you wish to be selected more run the '/priority' command."))
                            random_message = str(random.sample(self.starter_messages, 1)[0]).replace('{user}', user.name).replace('{time_since}', f'{time_since_message_minutes} minutes').replace('{char_name}', self.char_name)
                            await dm_channel.send(random_message)
                            print(f"{user.name} was sent: {random_message} by {self.char_name}")
                            self.save_logs(user.name, random_message)
                        except:
                            pass
            else:
                pass
    async def reboot_reply(self):
        users_to_message = self.priority_list + self.users_dict
        for user in users_to_message:
            try:
                user = self.bot.get_user(user)
            except:
                user = None
            if (user is not None) and not (user == self.bot.user) and (user.id not in self.blacklist_list):
                # Create a DM channel with the user
                try:
                    dm_channel = await user.create_dm()
                except:
                    dm_channel = None
                if (dm_channel is not None):
                    try:
                        last_message = [message async for message in dm_channel.history(limit=1)][0]
                    except:
                        last_message = None
                    if (last_message is not None) and (last_message.author != self.bot.user):
                        try:
                            path = (f"{self.chatlog_dir}/{last_message.author.name} - chatlog.log")
                            last_message = f"{last_message.author.name}: {last_message.content}\n"
                            if os.path.exists(path):
                                with open(path, 'a+', encoding="utf-8") as f:
                                    f.seek(0)
                                    lines = f.readlines()[-1:]
                                    if (last_message not in lines[0]):
                                        f.write(last_message)
                                sorry = f"Hey, {last_message.author.name}. Sorry about that, I got distracted with something else. What's up?"
                                print(f"{user.name} was sent: {sorry} by {self.char_name}")
                                await dm_channel.send(sorry)
                                self.save_logs(user.name, sorry)
                        except:
                            pass

    async def timed_reply(self):
        # Select num_to_message amount of users randomly from the dictionary
        for user in self.users_dict:
            try:
                user = self.bot.get_user(user)
            except:
                user = None
            if (user is not None) and (user.id not in self.blacklist_list):
                # Create a DM channel with the user
                try:
                    dm_channel = await user.create_dm()
                except:
                    dm_channel = None
                if (dm_channel is not None):
                    try:
                        last_message = [message async for message in dm_channel.history(limit=1)][0]
                    except discord.errors.Forbidden:
                        last_message = None
                    try:
                        user_path = f"UserConfig/{last_message.author.id}.json"
                        with open(user_path, "r") as f:
                            user_data = json.load(f)
                    except:
                        user_data = None
                    if(user_data is not None):
                        if(user_data['relationship_level'] == 'romantic partner'):
                            with open(self.message_storage, 'r') as f:
                                data = json.load(f)
                                self.starter_messages = data['romantic_noreply_dm_messages']
                        else:
                            with open(self.message_storage, 'r') as f:
                                data = json.load(f)
                                self.starter_messages = data['noreply_dm_messages']
                    if (last_message is not None) and (last_message.author == self.bot.user) and not any(word in last_message.content for word in self.goodbye_words):
                        # Get the timestamp of the message
                        message_timestamp = last_message.created_at.replace(tzinfo=pytz.UTC)
                        current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
                        time_since_message = current_time - message_timestamp
                        time_since_message_minutes = int(time_since_message.total_seconds() / 60)
                        if ((time_since_message_minutes <= 90)):
                            if (time_since_message_minutes >= 30) and (random.random() <= 0.5):
                                random_message = str(random.sample(self.noreply_messages, 1)[0]).replace('{user}', user.name).replace('{time_since}', f'{time_since_message_minutes} minutes').replace('{char_name}', self.char_name)
                                try:
                                    print(f"{user.name} was sent: {random_message} by {self.char_name}")
                                    await dm_channel.send(random_message)
                                    self.save_logs(user.name, random_message)
                                except:
                                    pass


    async def timed_channel(self):
        for channel in self.channel_id:
            try:
                channel = self.bot.get_channel(int(channel))
                if channel is not None:
                    try:
                        last_message = [message async for message in channel.history(limit=1)][0]
                    except IndexError:
                        last_message = None
                    if (last_message is not None):
                        # Get the timestamp of the message
                        message_timestamp = last_message.created_at.replace(tzinfo=pytz.UTC)
                        current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
                        time_since_message = current_time - message_timestamp
                        time_since_message_minutes = int(time_since_message.total_seconds() / 60)
                        if time_since_message_minutes >= 30:
                            random_message = str(random.sample(self.noreply_channel_messages, 1)[0]).replace('{user}', channel.name).replace('{time_since}', f'{time_since_message_minutes} minutes').replace('{char_name}', self.char_name)
                            print(f"{channel.name} was sent: {random_message} by {self.char_name}")
                            await channel.send(random_message)
                            self.save_logs(channel.name, random_message)
            except:
                pass

    # Save logs
    def save_logs(self, name, message):
        path = (f"{self.chatlog_dir}/{name} - chatlog.log")
        if os.path.exists(path):
            with open(path, 'a', encoding="utf-8") as f:
                f.write(f"{self.char_name}: {message}\n")
        else:
            with open(path, 'w', encoding="utf-8") as f:
                f.write(f"{self.char_name}: {message}\n")

    # Scan Server Members
    async def scan_servers(self):
        # Iterate through each server the bot is a member of
        for guild in self.bot.guilds:
            # Iterate through each member of the server
            for member in guild.members:
                # Add the user ID to the dictionary with a unique number
                if (member.id not in self.users_dict) and (member.id not in self.blacklist_list):
                    self.users_dict.append(member.id)
    
    async def run_timed_events(self):
        while True:
            await self.scan_servers()
            await self.timed_message()
            await asyncio.sleep(5400) # pause for 90 minutes
    
    async def run_timed_reply(self):
        while True:
            await self.scan_servers()
            await self.timed_reply()
            await self.timed_channel()
            await asyncio.sleep(1800) # pause for 30 minutes
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Timed Events Cog Loaded.")
        await self.scan_servers()
        await self.reboot_reply()
        await asyncio.gather(self.run_timed_reply(), self.run_timed_events())

    @commands.command()
    async def blacklist(self, ctx) -> None:
        with open('user_lists.json', 'r') as f:
            data = json.loads(f.read())
        data['blacklist'].append(ctx.author.id)
        with open('user_lists.json', 'w') as f:
            json.dump(data, f)
        self.blacklist_list.append(ctx.author.id)
        await ctx.send(embed=embedder(f"{ctx.author.name} has been blacklisted."))
        print(f"{ctx.author.name} has been blacklisted.")

    @commands.command()
    async def priority(self, ctx) -> None:
        with open('user_lists.json', 'r') as f:
            data = json.loads(f.read())
        data['priority'].append(ctx.author.id)
        with open('user_lists.json', 'w') as f:
            json.dump(data, f)
        self.priority_list.append(ctx.author.id)
        await ctx.send(embed=embedder(f"{ctx.author.name} has been set to priority."))
        print(f"{ctx.author.name} has been set to priority.")

async def setup(bot):
    # add chatbot cog to bot
    await bot.add_cog(TimedEventsCog(bot))