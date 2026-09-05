import os
import discord
from discord.ext import commands
import asyncio
import time
import re

# --- BOT CONFIGURATION ---
# Loads token safely from environment variables
TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE") 

EVENT_CHANNEL_ID = 1545528729176899585   # Channel ID for public challenge updates
TIME_CAPSULE_CHANNEL_ID = 1544739462611996682 # Channel ID where the target message exists

import discord
from discord.ext import commands
import asyncio
import time
import re

# --- BOT CONFIGURATION ---
TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" 
EVENT_CHANNEL_ID = 123456789012345678      # Channel ID for public challenge updates
TIME_CAPSULE_CHANNEL_ID = 123456789012345678 # Channel ID where the target message exists

# --- HARD-CODED EVENT SECRETS ---
SECRET_NUMBER = 73942
SECRET_WORD = "KINETIC"
ARCHAEOLOGIST_CODE = "ASKARA"
TARGET_MESSAGE_ID = 1545464668741701702   # Challenge 7 Target Message ID

# Decoded Passkeys
CHALLENGE_8_CODE = "gl{ItHiNkNoOnEcAnGeTtHiSfAsT}"
CHALLENGE_9_CODE = "gl.{yOuArEtHeChAmPiOn}"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_progress = {}
number_guesses = {}  
word_guesses = {}    
reaction_posts = {} 

user_last_guess_time = {}
MESSAGE_TIMESTAMPS = []

# Directory of Challenges & Hints for Sequential DM Delivery
CHALLENGE_HINTS = {
    1: "**Challenge 1: Voice Connector**\n└ *Objective: Join any public voice channel in the server.*",
    2: "**Challenge 2: Secret Number Guessing**\n└ *Objective: Guess the secret number (1-100,000) directly in chat.*",
    3: "**Challenge 3: Server Archaeologist**\n└ *Objective: Search channel topics/pins for a hidden code and type it in chat.*",
    4: "**Challenge 4: GL Lore Quiz**\n└ *Objective: Type `!quiz` in the event channel and answer all 5 questions.*",
    5: "**Challenge 5: Mass Reaction Rush**\n└ *Objective: Post a message and get 5 unique members to react to it.*",
    6: "**Challenge 6: Secret Word Guessing**\n└ *Objective: Guess the secret 7-letter word directly in chat.*",
    7: "**Challenge 7: Time Capsule**\n└ *Objective: React with 🎂/🍰 to the target message, then run `!submitid 1545464668741701702`.*",
    8: "**Challenge 8: Base64 Passkey**\n└ *Objective: Find the Base64 post, decode it, and run `!submitcode <passkey>`.*",
    9: "**Challenge 9: Hex + ROT47 Cipher**\n└ *Objective: Find the Hex post, decode Hex -> ROT47, and run `!submitcode <passkey>` Magnitite have a tuff server tho.*"
}

def is_chat_scannable():
    now = time.time()
    global MESSAGE_TIMESTAMPS
    MESSAGE_TIMESTAMPS = [ts for ts in MESSAGE_TIMESTAMPS if now - ts < 60]
    
    if len(MESSAGE_TIMESTAMPS) < 10:
        MESSAGE_TIMESTAMPS.append(now)
        return True
    return False

def get_current_active_challenge(user_id: int) -> int:
    """Returns the current challenge the user is on (1-9), or 10 if all finished, or 0 if not started."""
    if user_id not in user_progress:
        return 0
    completed = user_progress[user_id]
    if len(completed) >= 9:
        return 10
    # Current active challenge is the first uncompleted challenge number from 1 to 9
    for c in range(1, 10):
        if c not in completed:
            return c
    return 10

async def mark_complete(user: discord.User, challenge_num: int, channel: discord.TextChannel = None):
    user_id = user.id
    
    # Require user to have started
    if user_id not in user_progress:
        return

    # Enforce sequential order: User must be on this specific challenge
    active_challenge = get_current_active_challenge(user_id)
    if challenge_num != active_challenge:
        return

    user_progress[user_id].add(challenge_num)
    completed_count = len(user_progress[user_id])
    
    # Public Announcement in Channel
    if channel:
        try:
            await channel.send(f"🎉 {user.mention} completed **Challenge {challenge_num}**!")
        except Exception:
            pass

    # Send completion update & next challenge info in DM
    try:
        dm_embed = discord.Embed(
            title="🏆 Challenge Completed!",
            description=f"Great job **{user.name}**! You just finished **Challenge {challenge_num}**.",
            color=0x2b2d31
        )
        dm_embed.add_field(name="📊 Your Total Progress", value=f"**{completed_count}/9** Challenges Cleared", inline=False)
        
        next_challenge = get_current_active_challenge(user_id)
        if next_challenge <= 9:
            dm_embed.add_field(name=f"🔓 Next Challenge Unlocked (Challenge {next_challenge})", value=CHALLENGE_HINTS[next_challenge], inline=False)
        else:
            user_progress[user_id].add(10)
            dm_embed.add_field(name="👑 GRAND COMPLETIONIST!", value="You cleared ALL 9 challenges! You have claimed the ultimate achievement!", inline=False)
            
        await user.send(embed=dm_embed)
    except discord.Forbidden:
        pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - GL Birthday Bot Active!")

# --- START COMMAND ---

@bot.command(name="start")
@commands.cooldown(1, 5, commands.BucketType.user)
async def start_event(ctx):
    user_id = ctx.author.id
    
    if user_id not in user_progress:
        user_progress[user_id] = set()
        
        try:
            embed = discord.Embed(
                title="🎮 Welcome to the Challenge Event!",
                description="Complete challenges sequentially from 1 to 9. Finish one to reveal the next!",
                color=0x2b2d31
            )
            embed.add_field(name="🔓 Challenge 1 Unlocked", value=CHALLENGE_HINTS[1], inline=False)
            embed.set_footer(text="Type !progress anytime to check your active challenge.")
            
            await ctx.author.send(embed=embed)
            await ctx.send(f"✅ {ctx.author.mention}, your event journey has started! Check your DMs for **Challenge 1**.")
        except discord.Forbidden:
            await ctx.send(f"⚠️ {ctx.author.mention}, I couldn't send you a DM. Please enable direct messages from server members!")
    else:
        active = get_current_active_challenge(user_id)
        if active <= 9:
            await ctx.send(f"ℹ️ {ctx.author.mention}, you've already started! You are currently on **Challenge {active}**. Check your DMs or use `!progress`.")
        else:
            await ctx.send(f"👑 {ctx.author.mention}, you have already cleared all challenges!")

# --- CHALLENGE 1: VOICE CHANNEL TRACKER ---

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if before.channel is None and after.channel is not None:
        if get_current_active_challenge(member.id) == 1:
            channel = bot.get_channel(EVENT_CHANNEL_ID)
            if not channel:
                try:
                    channel = await bot.fetch_channel(EVENT_CHANNEL_ID)
                except Exception:
                    channel = None
            await mark_complete(member, 1, channel)

# --- MAIN AUTOMATIC CHAT SCANNER ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Track message for Challenge 5 (Mass Reaction Rush)
    reaction_posts[message.id] = set()

    uid = message.author.id
    content = message.content.strip()

    if content.startswith("!"):
        await bot.process_commands(message)
        return

    if not is_chat_scannable():
        return

    active_challenge = get_current_active_challenge(uid)
    if active_challenge == 0 or active_challenge > 9:
        return

    now = time.time()

    # Challenge 3: Raw "ASKARA" guess anywhere in chat
    if active_challenge == 3 and content.upper() == ARCHAEOLOGIST_CODE:
        await mark_complete(message.author, 3, message.channel)
        return

    last_guess = user_last_guess_time.get(uid, 0)
    
    # Challenge 2: RAW NUMBER GUESS (1 - 100000)
    if active_challenge == 2 and content.isdigit():
        num = int(content)
        if 1 <= num <= 100000:
            if now - last_guess < 6:
                return
            
            user_last_guess_time[uid] = now
            number_guesses[uid] = number_guesses.get(uid, 0) + 1

            if number_guesses[uid] > 20:
                await message.channel.send(f"❌ <@{uid}> You have used all 20 attempts for Challenge 2!", delete_after=5)
            elif num == SECRET_NUMBER:
                await mark_complete(message.author, 2, message.channel)
            else:
                attempts_left = 20 - number_guesses[uid]
                await message.channel.send(f"❌ Incorrect number guess for <@{uid}>! ({attempts_left} attempts left)", delete_after=5)

    # Challenge 6: RAW WORD GUESS (7 Letters)
    elif active_challenge == 6 and re.match(r"^[a-zA-Z]+$", content) and len(content) == len(SECRET_WORD):
        if now - last_guess < 6:
            return

        user_last_guess_time[uid] = now
        word_guesses[uid] = word_guesses.get(uid, 0) + 1

        if word_guesses[uid] > 20:
            await message.channel.send(f"❌ <@{uid}> You have used all 20 attempts for Challenge 6!", delete_after=5)
        elif content.upper() == SECRET_WORD:
            await mark_complete(message.author, 6, message.channel)
        else:
            attempts_left = 20 - word_guesses[uid]
            await message.channel.send(f"❌ Incorrect word guess for <@{uid}>! ({attempts_left} attempts left)", delete_after=5)

# --- REACTION TRACKER ---

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    if msg_id in reaction_posts:
        reaction_posts[msg_id].add(user.id)
        if len(reaction_posts[msg_id]) >= 5:
            author_id = reaction.message.author.id
            if get_current_active_challenge(author_id) == 5:
                author = reaction.message.guild.get_member(author_id)
                if author:
                    await mark_complete(author, 5, reaction.message.channel)

# --- COMMANDS ---

@bot.command(name="submitid")
@commands.cooldown(1, 10, commands.BucketType.user)
async def submit_id(ctx, message_id: int):
    """Challenge 7: Validates exact target message ID and checks for cake emoji reaction."""
    if get_current_active_challenge(ctx.author.id) != 7:
        await ctx.send("❌ Challenge 7 is not active for you yet!")
        return

    if message_id != TARGET_MESSAGE_ID:
        await ctx.send("❌ Incorrect Message ID! That is not the target message.")
        return

    try:
        target_channel = bot.get_channel(TIME_CAPSULE_CHANNEL_ID)
        if not target_channel:
            target_channel = await bot.fetch_channel(TIME_CAPSULE_CHANNEL_ID)
        
        target_msg = await target_channel.fetch_message(TARGET_MESSAGE_ID)
    except Exception:
        await ctx.send("❌ Could not locate the target message. Ensure the bot has permission to view the channel!")
        return

    reacted = False
    for rx in target_msg.reactions:
        if str(rx.emoji) in ["🎂", "🍰"]:
            users = [u async for u in rx.users()]
            if ctx.author in users:
                reacted = True
                break

    if reacted:
        await mark_complete(ctx.author, 7, ctx.channel)
    else:
        await ctx.send("❌ You submitted the correct message ID, but you haven't reacted to that message with 🎂 or 🍰 yet!")

@bot.command(name="quiz")
@commands.cooldown(1, 300, commands.BucketType.user)
async def server_quiz(ctx):
    if get_current_active_challenge(ctx.author.id) != 4:
        await ctx.send("❌ Challenge 4 is not active for you yet!")
        return

    questions = [
        ("1. When was Global League founded? (e.g., 2023 or 2024)", ["2023", "2024", "2023/2024", "2023-2024"]),
        ("2. How many members does Global League have combined?", ["3000", "3k", "3,000"]),
        ("3. How many channels does Global League have combined?", ["83"]),
        ("4. Who owns Global League?", ["pwk"]),
        ("5. Which Global League version had the most members?", ["6", "v6", "version 6"]),
    ]
    
    await ctx.send("🧠 **GL Lore Test starting!** Answer all 5 questions correctly within 2 minutes.")
    
    for q, valid_answers in questions:
        await ctx.send(f"**Question:** {q}")
        try:
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=120.0)
            user_ans = msg.content.strip().lower()
            
            if any(user_ans == ans.lower() for ans in valid_answers):
                await ctx.send("✅ Correct!", delete_after=3)
            else:
                return await ctx.send("❌ Wrong answer! Quiz failed.")
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Time ran out! Quiz failed.")

    await mark_complete(ctx.author, 4, ctx.channel)

@bot.command(name="submitcode")
@commands.cooldown(1, 6, commands.BucketType.user)
async def submit_code(ctx, *, code: str):
    active = get_current_active_challenge(ctx.author.id)
    cleaned = code.strip()

    if active == 8 and cleaned.lower() == CHALLENGE_8_CODE.lower():
        await mark_complete(ctx.author, 8, ctx.channel)
    elif active == 9 and cleaned.lower() == CHALLENGE_9_CODE.lower():
        await mark_complete(ctx.author, 9, ctx.channel)
    else:
        await ctx.send("❌ Invalid passkey code or challenge not active!")

@bot.command(name="progress")
@commands.cooldown(1, 10, commands.BucketType.user)
async def check_progress(ctx):
    user_id = ctx.author.id
    if user_id not in user_progress:
        await ctx.send(f"❌ You haven't started the event yet! Type `!start` to unlock **Challenge 1**.")
        return

    active = get_current_active_challenge(user_id)
    completed = user_progress[user_id]
    
    if active <= 9:
        await ctx.send(f"📊 {ctx.author.mention}'s Progress: **{len(completed)}/9** cleared. Active: **Challenge {active}** (Check DMs for details).")
    else:
        await ctx.send(f"👑 {ctx.author.mention} has cleared all **9/9** challenges!")

bot.run(TOKEN)
