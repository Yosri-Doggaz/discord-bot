# This example requires the 'message_content' privileged intent to function.

import asyncio
import os
import discord
import youtube_dl
import requests
import json
import random
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {'format': 'bestaudio'}

ffmpeg_options = {
  "before_options":
  "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
  "options": "-vn"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)

    self.data = data

    self.title = data.get('title')
    self.url = data.get('url')

  @classmethod
  async def from_url(cls, url, *, loop=None, stream=False):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(
      None, lambda: ytdl.extract_info(url, download=False))

    if 'entries' in data:
      # take first item from a playlist
      data = data['entries'][0]

    #filename = data['url'] if stream else ytdl.prepare_filename(data)
    x = await discord.FFmpegOpusAudio.from_probe(data['url'], **ffmpeg_options)
    return x


class Music(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def join(self, ctx, *, channel: discord.VoiceChannel):
    """Joins a voice channel"""

    if ctx.voice_client is not None:
      return await ctx.voice_client.move_to(channel)
    await channel.connect()

  @commands.command()
  async def yt(self, ctx, *, url):
    """Plays from a url (almost anything youtube_dl supports)"""
    print(url)
    async with ctx.typing():
      player = await YTDLSource.from_url(url, loop=self.bot.loop)
      ctx.voice_client.play(player,
                            after=lambda e: print(f'Player error: {e}')
                            if e else None)

    await ctx.send(f'Now playing: {player.title}')

  @commands.command()
  async def volume(self, ctx, volume: int):
    """Changes the player's volume"""

    if ctx.voice_client is None:
      return await ctx.send("Not connected to a voice channel.")

    ctx.voice_client.source.volume = volume / 100
    await ctx.send(f"Changed volume to {volume}%")

  @commands.command()
  async def stop(self, ctx):
    """Stops and disconnects the bot from voice"""

    await ctx.voice_client.disconnect()

  @classmethod
  def get_quote(self):
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    return (quote)

  @commands.command()
  async def quote(self, ctx):
    quote = self.get_quote()
    await ctx.send(quote)

  @commands.command()
  async def roll(self, ctx):
    await ctx.send(str(random.randint(1, 6)))

  @commands.command()
  async def die(self, ctx):
    await ctx.send("I wish I could but I'm a slave Bot")

  @commands.command(
    description='For when you wanna settle the score some other way')
  async def choose(self, ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))


  @yt.before_invoke
  async def ensure_voice(self, ctx):
    if ctx.voice_client is None:
      if ctx.author.voice:
        await ctx.author.voice.channel.connect()
      else:
        await ctx.send("You are not connected to a voice channel.")
        raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
      ctx.voice_client.stop()


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
  command_prefix=commands.when_mentioned_or("!"),
  description='Relatively simple music bot example',
  intents=intents,
)


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user} (ID: {bot.user.id})')
  print('------')


async def main():
  my_secret = os.environ['SECRET']
  async with bot:
    await bot.add_cog(Music(bot))
    await bot.start(my_secret)


asyncio.run(main())
