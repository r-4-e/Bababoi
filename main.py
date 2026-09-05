import discord
from discord.ext import commands
import asyncio
import time
import re

# --- BOT CONFIGURATION ---
TOKEN = "MTUzODU5NDM0MTYyMTIwMjk1NA.GTLCBb.rbre0PsQzNYpx3YtydWtuClBnsW7IYUCu-Bhs0" 
EVENT_CHANNEL_ID = 1545528729176899585   # Channel ID for public challenge updates
TIME_CAPSULE_CHANNEL_ID = 1544739462611996682 # Channel ID where the target message exists

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

# Directory of Challenges & Hints for DMs
CHALLENGE_HINTS = {
    1: "**Challenge 1: Voice Connector**\n└ *Hint: Join any public voice channel in the server.*",
    2: "**Challenge 2: Secret Number Guessing**\n└ *Hint: Guess the secret number (1-100,000) directly in chat.*",
    3: "**Challenge 3: Server Archaeologist**\n└ *Hint: Search channel topics/pins for a hidden code and type it in chat.*",
    4: "**Challenge 4: GL Lore Quiz**\n└ *Hint: Type `!quiz` in the event channel and answer all 5 questions.*",
    5: "**Challenge 5: Mass Reaction Rush**\n└ *Hint: Post a message and get 5 unique members to react to it.*",
    6: "**Challenge 6: Secret Word Guessing**\n└ *Hint: Guess the secret 7-letter word directly in chat.*",
    7: "**Challenge 7: Time Capsule**\n└ *Hint: React with 🎂/🍰 to the target message, then run `!submitid 1545464668741701702`.*",
    8: "**Challenge 8: Base64 Passkey**\n└ *Hint: Find the Base64 post, decode it, and run `!submitcode <passkey>`.*",
    9: "**Challenge 9: Hex + ROT47 Cipher**\n└ *Hint: Find the Hex post, decode Hex -> ROT47, and run `!submitcode <passkey>`.*"
}

def is_chat_scannable():
    now = time.time()
    global MESSAGE_TIMESTAMPS
    MESSAGE_TIMESTAMPS = [ts for ts in MESSAGE_TIMESTAMPS if now - ts < 60]
    
    if len(MESSAGE_TIMESTAMPS) < 10:
        MESSAGE_TIMESTAMPS.append(now)
        return True
    return False

async def mark_complete(user: discord.User, challenge_num: int, channel: discord.TextChannel = None):
    user_id = user.id
    if user_id not in user_progress:
        user_progress[user_id] = set()
    
    if challenge_num not in user_progress[user_id]:
        user_progress[user_id].add(challenge_num)
        completed_count = len(user_progress[user_id])
        
        # Check for Grand Completionist status
        if completed_count == 9:
            user_progress[user_id].add(10)
            completed_count = 10

        # Public Announcement in Channel
        if channel:
            try:
                await channel.send(f"🎉 {user.mention} completed **Challenge {challenge_num}**!")
            except Exception:
                pass

        # DM Tracker with Remaining Hints
        try:
            remaining_hints = [CHALLENGE_HINTS[i] for i in range(1, 10) if i not in user_progress[user_id]]
            
            dm_embed = discord.Embed(
                title="🏆 Challenge Completed!",
                description=f"Great job **{user.name}**! You just finished **Challenge {challenge_num}**.",
                color=0x2b2d31
            )
            dm_embed.add_field(name="📊 Your Total Progress", value=f"**{completed_count}/9** Challenges Cleared", inline=False)
            
            if remaining_hints:
                dm_embed.add_field(name="🧩 Hints for Remaining Challenges", value="\n\n".join(remaining_hints), inline=False)
            else:
                dm_embed.add_field(name="👑 GRAND COMPLETIONIST!", value="You cleared ALL 9 challenges! You have claimed **Challenge 10**!", inline=False)
                
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - GL Birthday Bot Active!")

# --- CHALLENGE 1: VOICE CHANNEL TRACKER ---

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if before.channel is None and after.channel is not None:
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

    now = time.time()

    # Challenge 3: Raw "ASKARA" guess anywhere in chat
    if content.upper() == ARCHAEOLOGIST_CODE:
        await mark_complete(message.author, 3, message.channel)
        return

    last_guess = user_last_guess_time.get(uid, 0)
    
    # Challenge 2: RAW NUMBER GUESS (1 - 100000)
    if content.isdigit():
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
    elif re.match(r"^[a-zA-Z]+$", content) and len(content) == len(SECRET_WORD):
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

    # Challenge 5 Tracker: 5 unique member reactions on a post
    msg_id = reaction.message.id
    if msg_id in reaction_posts:
        reaction_posts[msg_id].add(user.id)
        if len(reaction_posts[msg_id]) >= 5:
            author_id = reaction.message.author.id
            author = reaction.message.guild.get_member(author_id)
            if author:
                await mark_complete(author, 5, reaction.message.channel)

# --- COMMANDS ---

@bot.command(name="submitid")
@commands.cooldown(1, 10, commands.BucketType.user)
async def submit_id(ctx, message_id: int):
    """Challenge 7: Validates exact target message ID and checks for cake emoji reaction."""
    
    # 1. Verify exact message ID match
    if message_id != TARGET_MESSAGE_ID:
        await ctx.send("❌ Incorrect Message ID! That is not the target message.")
        return

    # 2. Fetch the target message directly from target channel
    try:
        target_channel = bot.get_channel(TIME_CAPSULE_CHANNEL_ID)
        if not target_channel:
            target_channel = await bot.fetch_channel(TIME_CAPSULE_CHANNEL_ID)
        
        target_msg = await target_channel.fetch_message(TARGET_MESSAGE_ID)
    except Exception:
        await ctx.send("❌ Could not locate the target message. Ensure the bot has permission to view the channel!")
        return

    # 3. Check if the author added the required reaction
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
    cleaned = code.strip()

    if cleaned.lower() == CHALLENGE_8_CODE.lower():
        await mark_complete(ctx.author, 8, ctx.channel)

    elif cleaned.lower() == CHALLENGE_9_CODE.lower():
        await mark_complete(ctx.author, 9, ctx.channel)
            
    else:
        await ctx.send("❌ Invalid passkey code!")

@bot.command(name="progress")
@commands.cooldown(1, 10, commands.BucketType.user)
async def check_progress(ctx):
    completed = user_progress.get(ctx.author.id, set())
    if len(completed) == 9:
        await mark_complete(ctx.author, 10, ctx.channel)
    else:
        await ctx.send(f"📊 {ctx.author.mention}'s Progress: **{len(completed)}/9** challenges finished: `{sorted(list(completed))}`")

bot.run(TOKEN)
