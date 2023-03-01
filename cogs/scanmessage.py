import io, random, json, os, discord
from discord.ext import commands

class ScanMessageCog(commands.Cog, name="scan_message"):
    def __init__(self, bot):
        self.bot = bot
        self.chatlog_dir = bot.chatlog_dir
    #World Info
    @commands.command(name="world_info")
    async def world_info(self, message, char_name) -> None:
        world_info = ""
        json_file = f"CharacterInfo/{str(char_name)}_world_info.json"
        if os.path.exists(json_file):
            with open(json_file) as f:
                try:
                    json_data = json.load(f)
                    entries = json_data['entries']
                    for value in entries.values():
                        keys = [str(value['key']).split(",")]
                        keys = [key.lower() for sublist in keys for key in sublist]
                        search_criteria = str(f"{message.author.name}: {message.content}").lower().strip()
                    for key in keys:
                        clean = str(key).lower().replace("'","").replace(']','').replace('[','')
                        if (clean.strip()) in search_criteria:
                            world_info += str(value['content']) + "\n"
                    if world_info:
                        return world_info
                    else:
                        #print(f"No matching world info found for key '{message.content}'.")
                        return ""
                except Exception as e:
                    #print(f"Error loading world info: {e}")
                    return ""
        else:
            #print(f"World info not found for character {str(char_name)}.")
            return ""
    #Gif Scan
    @commands.command(name="gif_scan")
    async def gif_scan(self, message, response_text, char_name) -> None:
        # Define a dictionary with keywords and their corresponding gifs
        json_file = f"CharacterInfo/{str(char_name)}_gifs.json"
        if (os.path.exists(json_file)):
            with open(json_file) as f:
                keywords = json.load(f)
            # Iterate through the keywords and check if any of them are in the response_text
            for keyword in keywords:
                if keyword in str(response_text).lower():
                    gif_url = keywords[keyword]
                    await message.channel.send(str(gif_url))
                    return 
            # If no keywords are found, return None
            return 
        else:
            return 
    #Send Scan
    @commands.command(name="send_scan")
    async def send_scan(self, message, message_content, char_name) -> None:
        if ("send" in message_content.lower()) and not ("meme" in message_content.lower()):
            path = (f"{self.chatlog_dir}/{user.name} - chatlog.log")
            directory = f"Images/{str(char_name)}/"
            image_extensions = ('.png', '.jpg', '.jpeg', '.mp4')
            image_files = []
            user = message.author
            channel = await user.create_dm()
            for file in os.listdir(directory):
                if file.endswith(image_extensions):
                    # Split the number from the filename and store as separate entry in list
                    name, ext = os.path.splitext(file)
                    parts = name.split('_')
                    if len(parts) == 2 and parts[1].isdigit():
                        image_files.append((parts[0], int(parts[1]), os.path.join(directory, file)))
            for filename, number, filepath in image_files:
                names = filename.split('-')
                for name in names:
                    if name.lower() in message_content.lower():
                        # Count the number of images with the same keyword
                        count = sum(1 for f, _, _ in image_files if f == filename)
                        # Generate a random number within the range
                        rand_num = random.randint(1, count)
                        # Select a different image file with the same word but a different number
                        for exten in image_extensions:
                            try:
                                new_filename = f"{filename}_{rand_num}{exten}"
                                new_filepath = os.path.join(directory, new_filename)
                                with open(new_filepath, 'rb') as f:
                                    file = discord.File(f)
                                    await channel.send(file=file)
                                    send_text = str(f"[{str(char_name)} sends {user.name} a picture of {str(char_name)}'s {name.lower()}.]\n")
                                    with open(path, 'a') as f:
                                        f.write(f"{user.name}: {message_content}\n")
                                        f.write(f"{str(char_name)}: " + send_text)
                                    return
                            except:
                                pass
            if not (filename):
                return
        return
    #Meme Scan
    @commands.command(name="meme_scan")
    async def meme_scan(self, message, char_name) -> None:
        if ("send" in message.content.lower()) and ("meme" in message.content.lower()):
            directory = f"Images/memes/"
            image_extensions = ('.png', '.jpg', '.jpeg', '.mp4')
            image_files = []
            user = message.author
            for file in os.listdir(directory):
                if file.endswith(image_extensions):
                    # Split the number from the filename and store as separate entry in list
                    name, ext = os.path.splitext(file)
                    parts = name.split('_')
                    if len(parts) == 2 and parts[1].isdigit():
                        image_files.append((parts[0], int(parts[1]), os.path.join(directory, file)))
            for filename, number, filepath in image_files:
                names = filename.split('-')
                for name in names:
                    if name.lower() in message.content.lower():
                        # Count the number of images with the same keyword
                        count = sum(1 for f, _, _ in image_files if f == filename)
                        # Generate a random number within the range
                        rand_num = random.randint(1, count)
                        # Select a different image file with the same word but a different number
                        for exten in image_extensions:
                            try:
                                new_filename = f"{filename}_{rand_num}{exten}"
                                new_filepath = os.path.join(directory, new_filename)
                                with open(new_filepath, 'rb') as f:
                                    file = discord.File(f)
                                    await message.channel.send("How's this?")
                                    await message.channel.send(file=file)
                                    return str(f"[{str(char_name)} sends {user.name} a {name} meme.]\n")
                            except:
                                pass
                if not (filename):
                    return ""
        return ""
    #DM Scan       
    @commands.command(name="dm_scan")
    async def dm_scan(self,message, message_content, char_name)  -> None:
        # Define a dictionary with keywords and their corresponding gifs
        user = message.author
        path = (f"{self.chatlog_dir}/{user.name} - chatlog.log")
        try:
            channel = await user.create_dm()
            async for msg in channel.history(limit=1, oldest_first=True):
                first_message_id = msg.id
                break
            if (message.id == first_message_id):
                dm_message = f"A direct message? What do you wish to speak with {str(char_name)} in private for?"
                await channel.send(dm_message)
                with open(path, 'a') as f:
                    f.write(f"{user.name}: {message_content}\n")
                    f.write(f"{str(char_name)}: {dm_message}\n")
                return True
            if (self.bot.user in message.mentions):
                dm_message = f"Yes, {user.name}? You wanted to speak privately?\n"
                if ("dm" in str(message.content).lower()) or ("direct message" in str(message.content).lower()):
                    await channel.send(dm_message)
                    with open(path, 'a') as f:
                        f.write(f"{str(char_name)}: {dm_message}\n")
                    return True
                else:
                    return False
            return False
        except discord.errors.HTTPException as e:
            if "Cannot send messages to this user" in str(e):
                print("Error: Cannot send messages to this user")
            else:
                print("Error:", e)

async def setup(bot):
    await bot.add_cog(ScanMessageCog(bot))
