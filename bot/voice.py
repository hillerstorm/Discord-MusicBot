import threading
import discord
import time
import asyncio
from song import Song as Song

class Voice():
    def __init__(self, bot, gid):
        print("Created voice bot")
        self.bot = bot
        self.gid = gid
        self.voice_client = None
        self.current_server = None
        self.is_running = True
        self.songs = []
        self.is_playing = False
        self.is_paused = False

        self.channel = None #temp

    def on_finished_play(self, song, error):
        print("Finished playing", song)
        if error:
            print(f'An error occurred: {error}')

        self.is_playing = False    
        
    async def start_playing(self, song):
        self.is_playing = True
        #await self.send_message(self.channel, "Playing: " + song.url)
        source = discord.FFmpegPCMAudio(source=song.full_path)
        self.voice_client.play(source, after=lambda error: self.on_finished_play(song, error))
        
    async def long_task(self):
        await asyncio.sleep(5)

    async def display_queue(self, channel):
        st = "Total songs: " + str(len(self.songs)) + "\n"
        i = 0
        for song in self.songs:
            i = i + 1
            st = st + str(i) + ". " + song.name + "\n"
            if(i >= 5):
                break
        if(i > 0):
            await self.send_message(channel, st)
        else:
            await self.send_message(channel, "Queue is empty")
        
    async def handle_message(self, message):
        if(message.author.bot == True):
            return
        self.channel = message.channel
        print(f'{message.author} said {message.content}')
        if(message.content == "!join"):
            await self.join(message.author)

        if(message.content == "!move"):
            await self.join(message.author, force=True)

        if(message.content == "!leave"):
            await self.leave()

        if(message.content == "!sleep"):
            await self.send_message(message.channel, "Sleeping for five secounds")
            await self.long_task()
            await self.send_message(message.channel, "Finished sleeping!")

        if(message.content == "jo"):
            await self.send_message(message.channel, "jo")

        if((message.content.split(' ')[0] == "!p" or message.content.split(' ')[0] == "!play") and len(message.content.split(' ')) == 2):

            if(self.voice_client is None):
                await self.join(message.author)
            
            s = Song(message.content.split(' ')[1], message.author)
            print("Downloading:",message.content.split(' ')[1])
            self.songs.append(s)
            r = await s.download()
            if(r == False):
                print("Failed to download song!")
                return
            return

        if(message.content.split(' ')[0] == "!skip"):
            self.voice_client.stop()

        if(message.content == "!pause"):
            if(self.is_paused):
                self.voice_client.resume()
                self.is_paused = False
            else:
                self.voice_client.pause()
                self.is_paused = True

        if(message.content == "!queue" or message.content == "!q"):
            await self.display_queue(message.channel)

        if(message.content == "!skip"):
            self.voice_client.stop()

        if(message.content == "!stop"):
            await self.leave()
            
    async def send_message(self, channel, msg):
        await channel.send(msg)
        
    async def join(self, author, force=False):
        channel = author.voice.channel

        if(channel == self.current_server):
            print("Already in that server")
            return
        
        if(self.voice_client is None):
            self.voice_client = await channel.connect(self_deaf=True)
            self.current_server = channel
        else:
            if(len(self.current_server.members) > 1 and force == False):
                #print("I'm connected in channel with other users, use -move to override")
                #return
                pass
            await self.voice_client.disconnect()
            self.voice_client = await channel.connect(self_deaf=True)
            self.current_server = channel

    async def leave(self):
        if(self.voice_client is not None):
            await self.voice_client.disconnect()
            for i in range(len(self.songs)):
                s = self.songs.pop()
                del s
        self.voice_client = None
        self.current_server = None

    async def on_kicked(self):
        await self.leave()

    async def on_move(self, new_channel):
        self.current_server = new_channel
        
        await self.voice_client.move_to(new_channel)

        if(not self.is_paused):
            await asyncio.sleep(0.5)
            self.voice_client.resume()