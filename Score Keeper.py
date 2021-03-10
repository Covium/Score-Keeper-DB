# Imports Discord commands.
import discord
from discord.ext import commands

# Imports commands to work with coroutine.
import asyncio

# Imports commands to work with json files.
import json

# Imports OS commands.
import os

# Imports sleep function.
from time import sleep

# Imports random integer function.
from random import randint as random


# Creates non-existent files.
def startup_check(path):
    if os.path.isfile(path) and os.access(path, os.R_OK):
        return True
    else:
        with open(path, 'w+') as db_file:
            if path[-5:] == '.json':
                json.dump({}, db_file, indent=4)
            else:
                pass

        return False


used_files = ['Activities.txt', 'Private Data/Guilds Data.json', 'Private Data/Token.txt']

# Checks if all the needed files exist & kills the program if token wasn't found.
for file_path in used_files:
    if not startup_check(file_path) and file_path == 'Private Data/Token.txt':
        print('Token file was created but the bot won\'t start until you enter your token.\n'
              'Edit «Private Data/Token.txt» with your token for bot to run.\n'
              '\n'
              'Program will kill itself in 30 seconds.')

        sleep(30)

        quit()

# Sets default Discord bot prefix.
prefix = '.'

# Loads intents needed for guild members info.
intents = discord.Intents.default()
intents.members = True

# Sets 'dbot' as future reference to Discord bot commands.
dbot = commands.Bot(command_prefix=prefix, intents=intents)


"""
|=== Time In Milliseconds ===|

Description:
Converts «M:S:MS» string to milliseconds integer.
"""


def time_in_ms(time_string):

    separators = []

    # Finds non-numeric symbols in the string.
    for symbol_id in range(len(time_string)):
        if time_string[symbol_id] not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            separators.append(symbol_id)

    # Error if too many separators (a sign of user wrote something other than time).
    if len(separators) != 2:
        return False

    m, s, ms = [int(time_string[:separators[0]]),
                int(time_string[separators[0] + 1:separators[1]]),
                int(time_string[separators[1] + 1:])]

    return m * 60000 + s * 1000 + ms


"""
|=== Time In Minutes ===|

Description:
Converts milliseconds integer to «mm:ss.mss» string.
"""


def time_in_m(time):

    # Just gets the whole number of everything & adds zeros if not enough symbols.
    m = str(time // 60000)
    m = ('0' + m if len(m) == 1 else m)
    time %= 60000

    s = str(time // 1000)
    s = ('0' + s if len(s) == 1 else s)
    time %= 1000

    ms = str(time)
    ms = ('0' + ms if len(ms) < 3 else ms)
    ms = ('0' + ms if len(ms) < 3 else ms)

    return m + ':' + s + '.' + ms


"""
|=== Get Leaderboard ===|

Description:
Constructs a leaderboard from runners dictionary.
"""


def get_leaderboard(ctx, runners):

    runners_amount_string_length = len(str(len(runners)))  # used every loop so it's better to just get it once.
    runners_data_string = '```fix\n'
    position = 1  # just a count.

    for runner in runners:
        # Adds white spaces in the beginning depending on the number of runners &
        # adds endings to make numbers ordinal.
        rank = ' ' * (runners_amount_string_length - len(rank) + 1) + \
               str(position) + \
               {1: 'st', 2: 'nd', 3: 'rd'}.get(4 if 10 <= position % 100 < 20 else position % 10, 'th')

        # Adds the runner info to the leaderboard string.
        runners_data_string += rank + ' | ' + \
                               time_in_m(runners[runner]) + ' | ' + \
                               ctx.guild.get_member(int(runner)).name + '\n'

        position += 1

    return runners_data_string + '```'


"""
|=== Error Alert ===|

Description:
Sends error message to the channel & deletes it after some time.
"""


async def error_alert(ctx, error_message, time=5):
    await asyncio.sleep(time)
    await error_message.delete()

    return


"""
|=== Is Admin ===|

Description:
Checks if the message sender is a guild admin.
"""


async def is_admin(ctx):

    if not ctx.author.guild_permissions.administrator:
        error_message = await ctx.send('You need administrator permission to use that.')
        await error_alert(ctx, error_message)

        return False

    return True


"""
|=== Get Leaderboard Message ===|

Description:
Fetches leaderboard message object.
"""


async def get_leaderboard_message(ctx):

    with open('Private Data/Guilds Data.json', 'r') as ids_storage:
        ids = json.load(ids_storage)

    channel_id = ids[str(ctx.guild.id)]['channel_id']
    message_id = ids[str(ctx.guild.id)]['message_id']

    return await dbot.get_channel(channel_id).fetch_message(message_id)


"""
|=== Give WR Role ===|

Description:
Gives WR Holder role to the #1 runner.
"""


async def give_wr_role(ctx, runners):

    # Gets the user in the 1st place & the role of WR holder.
    wr_holder = ctx.guild.get_member(int(list(runners.keys())[0]))
    wr_role = discord.utils.get(ctx.guild.roles, name='WR Holder')

    # Deletes every other member in this role & gives it to the winner.
    for member in wr_role.members:
        await member.remove_roles(wr_role)

    await wr_holder.add_roles(wr_role)


"""
    |======================|
    |====== ON READY ======|
    |======================|

Description:
Actions that bot does on log in.
"""


@dbot.event
async def on_ready():

    print(f'\nLogged on as {dbot.user}!\n')

    # Gets random activity for bots status from the list.
    with open('Activities.txt', 'r') as activities_file:
        activities_list = activities_file.read().split('\n')

    activity_type, activity_name = activities_list[random(0, len(activities_list) - 2)].split(':')

    if activity_type == 'listening':
        activity_type = discord.ActivityType.listening

    elif activity_type == 'watching':
        activity_type = discord.ActivityType.watching

    elif activity_type == 'playing':
        activity_type = discord.ActivityType.playing

    elif activity_type == 'streaming':
        activity_type = discord.ActivityType.streaming

    # Sets activity status.
    await dbot.change_presence(
        activity=discord.Activity(
            type=activity_type,
            name=activity_name
        )
    )


"""
    |================|
    |====== LB ======|
    |================|

Description:
Creates brand new leaderboard message.
"""


# Changes any available element.
@dbot.command(name='lb')
async def _lb(ctx):

    await ctx.message.delete()

    if not await is_admin(ctx):
        return

    with open('Private Data/Guilds Data.json', 'r') as ids_storage:
        ids = json.load(ids_storage)

    # Message to ensure if the user really wants to create new leaderboard.
    if str(ctx.guild.id) in ids:
        agreement_message = await ctx.send('Are you sure you want to create a new leaderboard?\n'
                                           'Your previous leaderboard will be completely removed.')

        await agreement_message.add_reaction('✅')
        await agreement_message.add_reaction('❎')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in ['✅', '❎']

        try:
            reaction, user = await dbot.wait_for('reaction_add', timeout=7, check=check)
            if reaction.emoji == '✅':
                await agreement_message.delete()

            elif reaction.emoji == '❎':
                await agreement_message.delete()

                return

        except asyncio.TimeoutError:
            await agreement_message.delete()

            return

        channel_id = ids[str(ctx.guild.id)]['channel_id']
        message_id = ids[str(ctx.guild.id)]['message_id']

        try:
            message = await dbot.get_channel(channel_id).fetch_message(message_id)
            await message.delete()

        except Exception:
            error_message = await ctx.send('Either channel or message with previous leaderboard was deleted.\n'
                                           'Creating a new one right now!')
            await error_alert(ctx, error_message)

    # Creates empty leaderboard message text.
    message = await ctx.send('```fix\n'
                             'LEADERBOARD\n'
                             '```')

    # Adds leaderboard info into the dictionary.
    ids[str(ctx.guild.id)] = {'channel_id': message.channel.id, 'message_id': message.id, 'runners': {}}

    with open('Private Data/Guilds Data.json', 'w') as ids_storage:
        json.dump(ids, ids_storage, indent=4)

    # Clears all the previous members of WR Holder role.
    wr_role = discord.utils.get(ctx.guild.roles, name='WR Holder')

    for member in wr_role.members:
        await member.remove_roles(wr_role)


"""
    |=================|
    |====== ADD ======|
    |=================|

Description:
Adds a new runner to the leaderboard.
"""


# Changes any available element.
@dbot.command(name='add')
async def _add(ctx, *, args):

    await ctx.message.delete()

    if not await is_admin(ctx):
        return

    mentions = ctx.message.mentions

    # Check if there is a mention of a user in the message & if there is only one.
    if len(mentions) != 1:
        error_message = await ctx.send('There should be one mention.')
        await error_alert(ctx, error_message)

        return

    else:
        add_user = mentions[0]

    args = args.split()

    # Checks if enough arguments were given.
    if len(args) != 2:
        error_message = await ctx.send('There should be only two arguments.')
        await error_alert(ctx, error_message)

        return

    else:
        add_time = args[-1]

    # Checks if time was given in the allowed format.
    try:
        add_time = time_in_ms(add_time)

    except Exception:
        error_message = await ctx.send('Time should be in **M:S:MS** format.\n'
                                       '«**:**» is any separator but the white space.')
        await error_alert(ctx, error_message)

        return

    if not add_time:
        error_message = await ctx.send('Time should be in **M:S:MS** format.\n'
                                       '«**:**» is any separator but the white space.')
        await error_alert(ctx, error_message)

        return

    # Loads ids from the storage & checks if guild is in there.
    with open('Private Data/Guilds Data.json', 'r') as ids_storage:
        ids = json.load(ids_storage)

    if str(ctx.guild.id) in ids:
        runners = ids[str(ctx.guild.id)]['runners']

    else:
        error_message = await ctx.send(f'Create the table first be sending «{prefix}lb» first.')
        await error_alert(ctx, error_message)

        return

    leaderboard_message = await get_leaderboard_message(ctx)

    # Adds the new runner to the dictionary & sorts it by value.
    runners[str(add_user.id)] = add_time
    runners = {k: v for k, v in sorted(runners.items(), key=lambda item: item[1])}

    leaderboard = get_leaderboard(ctx, runners)

    await give_wr_role(ctx, runners)

    # Loads ids back into the storage & edits the message.
    ids[str(ctx.guild.id)]['runners'] = runners

    with open('Private Data/Guilds Data.json', 'w') as ids_storage:
        json.dump(ids, ids_storage, indent=4)

    await leaderboard_message.edit(content=leaderboard)


"""
    |====================|
    |====== REMOVE ======|
    |====================|

Description:
Removes a runner from the leaderboard.
"""


@dbot.command(name='remove')
async def _remove(ctx, *, args):

    await ctx.message.delete()

    if not await is_admin(ctx):
        return

    mentions = ctx.message.mentions

    # Check if there is a mention of a user in the message & if there is only one.
    if len(mentions) != 1:
        error_message = await ctx.send('There should be one mention.')
        await error_alert(ctx, error_message)

        return

    else:
        remove_user = mentions[0]

    args = args.split()

    # Checks if enough arguments were given.
    if len(args) != 1:
        error_message = await ctx.send('There should be only one argument.')
        await error_alert(ctx, error_message)

        return

    # Loads ids from the storage & checks if guild is in there.
    with open('Private Data/Guilds Data.json', 'r') as ids_storage:
        ids = json.load(ids_storage)

    if str(ctx.guild.id) in ids:
        runners = ids[str(ctx.guild.id)]['runners']

    else:
        error_message = await ctx.send('Create the table first.')
        await error_alert(ctx, error_message)

        return

    leaderboard_message = await get_leaderboard_message(ctx)

    # Deletes the runner from the dictionary
    del runners[str(remove_user.id)]

    if not runners:
        # Creates empty leaderboard message text.
        leaderboard = '```fix\n' \
                      'LEADERBOARD\n' \
                      '```'

    else:
        # Sorts dictionary by value.
        runners = {k: v for k, v in sorted(runners.items(), key=lambda item: item[1])}

        leaderboard = get_leaderboard(ctx, runners)

        await give_wr_role(ctx, runners)

    # Loads ids back into the storage & edits the message.
    ids[str(ctx.guild.id)]['runners'] = runners

    with open('Private Data/Guilds Data.json', 'w') as ids_storage:
        json.dump(ids, ids_storage, indent=4)

    await leaderboard_message.edit(content=leaderboard)


"""
    |===================|
    |====== CLEAR ======|
    |===================|

Description:
Deletes multiple messages above the request & the request itself.
"""


@dbot.command(name='clear')
async def _clear(ctx, amount=0):

    if not await is_admin(ctx):
        return

    # Checks if author didn't specify amount of messages to delete.
    if not amount:
        await ctx.send(f'Please, specify the amount of messages you want to be deleted.\n'
                       f'Enter «{prefix}clear [amount]».')

        return

    # Deletes requested amount of messages and request itself (+1).
    await ctx.channel.purge(limit=amount + 1)

    print(f'Cleared {amount} message' + ('s' if amount > 1 else '') +
          f' on <{ctx.channel.id}> channel in «{ctx.guild.id}» guild.')


# Gets the token & sends an error if not exist.
with open('Private Data/Token.txt', 'r') as token_file:
    token = token_file.read()

if not token:
    print('Token file was created but the bot won\'t start until you enter your token.\n'
          'Edit «Private Data/Token.txt» with your token for bot to run.\n'
          '\n'
          'Program will kill itself in 30 seconds.')

    sleep(30)

    quit()

# Runs a dbot using it's unique token.
dbot.run(token)


# All the code  below client.run() method won't work.
