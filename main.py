from asyncio import sleep
import logging


from discord import Intents, Activity, ActivityType, Interaction, app_commands, FFmpegPCMAudio, ui, ButtonStyle, VoiceChannel
from discord.ext import commands

import utils as u
from config import Config

# region logging-init

# init logger
l = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
root_logger = logging.getLogger()
root_logger.handlers.clear()  # clear default handler
# set stream handler
shandler = logging.StreamHandler()
shandler.setFormatter(u.CustomFormatter(colorful=True))
root_logger.addHandler(shandler)

# init config
c = Config().config

# continue init logger
root_logger.level = logging.DEBUG if c.debug else logging.INFO  # set log level
# reset stream handler
root_logger.handlers.clear()
shandler = logging.StreamHandler()
shandler.setFormatter(u.CustomFormatter(colorful=True))
root_logger.addHandler(shandler)
# set file handler
if c.log_file:
    log_file_path = u.get_path(c.log_file)
    l.info(f'Saving logs to {log_file_path}')
    fhandler = logging.FileHandler(log_file_path, encoding='utf-8', errors='ignore')
    fhandler.setFormatter(u.CustomFormatter(colorful=False))
    root_logger.addHandler(fhandler)

# endregion logging-init

bot = commands.Bot("/", intents=Intents.all(), proxy=c.proxy)

ids = []
names = []
playing = False
playlist_id = []
playlist_name = []


@bot.event
async def on_ready():
    activity = Activity(name="Type / and select this bot to start music player.", type=ActivityType.playing)
    await bot.change_presence(activity=activity)
    await bot.tree.sync()


# player = app_commands.Group(name="player", description="A simple player to play music into Voice Channel.")
# bot.tree.add_command(player)


@bot.tree.command(name="search", description="Search music by name.")
@app_commands.describe(music_name="Music Name")
async def search(interaction: Interaction, music_name: str):
    await interaction.response.send_message(f"Searching for `{music_name}`...")
    global ids
    global names
    ids = []
    names = []
    content = await do_search(music_name, 0, False)
    view = Control(music_name)
    await interaction.edit_original_response(content=content, view=view)


offset = 0


class Control(ui.View):
    def __init__(self, music_name):
        global m_name
        m_name = music_name
        super().__init__()

    @ui.button(label="Previous", style=ButtonStyle.danger, emoji="👈")
    async def approve(self, interaction: Interaction, button: ui.Button):
        global offset
        await interaction.response.defer()
        if not offset == 0:
            offset -= 30
            content = await do_search(m_name, offset, True)
            view = Control(m_name)
            await interaction.edit_original_response(content=content, view=view)

    @ui.button(label="Next", style=ButtonStyle.success, emoji="👉")
    async def reject(self, interaction: Interaction, button: ui.Button):
        global offset
        await interaction.response.defer()
        offset += 30
        content = await do_search(m_name, offset, False)
        view = Control(m_name)
        await interaction.edit_original_response(content=content, view=view)


num = 0


async def do_search(music_name: str, offset: int, previous: bool) -> str:
    global num
    search = await u.get_json(f"{c.ncm_api}/cloudsearch?keywords={music_name}&limit=30&offset={offset}&type=1")
    if not search:
        return "Search failed!"
    messages = "**Search result:**\n"
    if search["code"] == 200:
        for songs in search["result"]["songs"]:
            ids.append(songs["id"])
            name = songs["ar"][0]["name"] + " - " + songs["name"]
            names.append(name)
            messages += str(num) + ". " + name + "\n"
            if not previous:
                num += 1
            else:
                num -= 1
        messages += "**Type /play <music_num> to start player.**"
        return messages
    else:
        return "**No search result. Check your music name and try again**"


@bot.tree.command(name="list", description="See the playlist.")
async def list(interaction: Interaction):
    global playlist_id
    global playlist_name
    if not playlist_id or not playlist_name:
        await interaction.response.send_message("**No items in the playlist**")
        return
    messages = "**Playlist:**\n"
    num = 0
    for playlist in playlist_name:
        ids.append(playlist)
        messages += str(num) + ". " + playlist + "\n"
        num += 1
    await interaction.response.send_message(messages)


@bot.tree.command(name="play", description="Play a music into Voice Channel.")
@app_commands.describe(music_num="Music Num")
async def play(interaction: Interaction, music_num: int):
    global ids
    global names
    global playing
    if not ids or not names:
        await interaction.response.send_message("**Please search a music first!**")
        return
    music_id = ids[music_num - 1]
    music_name = names[music_num - 1]
    try:
        voice_chan: VoiceChannel = interaction.user.voice.channel # type: ignore
    except AttributeError:
        await interaction.response.send_message("**Please join the Voice Channel first!**")
        return
    playlist_id.append(music_id)
    playlist_name.append(music_name)
    if playing:
        await interaction.response.send_message(f"Added `{music_name}` to playlist.")
        return
    await interaction.response.send_message("Starting player...")
    # lyric = await u.get_json(f"{c.ncm_api}/lyric/new?id={music_id}")
    # if lyric:
    #     music_lrc = lyric["lrc"]["lyric"]
    voice_cli = await voice_chan.connect()
    while True:
        if playlist_id:
            await start_play(playlist_id.pop(0), playlist_name.pop(0), interaction, voice_cli)
        else:
            playing = False
            await voice_cli.disconnect()
            break


async def start_play(music_id, music_name, interaction: Interaction, voice_cli):
    global playing
    match = await u.get_json(f"{c.unm_api}/match?id={music_id}&server=qq,pyncmd")
    if match and match["message"] == "匹配成功":
        audio = FFmpegPCMAudio(match["data"]["url"])
        voice_cli.play(audio)
        playing = True
        await interaction.edit_original_response(content=f"Player started.")
        await interaction.channel.send(content=f"Now playing: {music_name}") # type: ignore
        while voice_cli.is_playing():
            await sleep(1)
        await interaction.edit_original_response(content="Player stopped.")


bot.run(c.token)
