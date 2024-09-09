from tokens import TOKEN
import threading
import discord
import json
import time
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
db:dict = {}
mabdie = discord.User
tree = discord.app_commands.CommandTree(client)

try: 
    open('db.json', 'x')
    db:dict = {'candidates': [], 'voters':{}, 'config': {'is_election_running':False, 'start_time':int, 'total_duration_seconds':int}}
except: 
    with open('db.json', 'r') as f:
        db:dict = json.load(f)


@client.event
async def on_ready():
    await tree.sync()
    print('connected and loaded!')

@tree.app_command(
        name='start-election',
        description='an admin-only command; starts an election if one is not current running'
)
async def start_election(interaction, duration_hours:int):
    if not db['config']['is_election_running']:
        db['config']['is_election_running'] = True
        db['config']['start_time'] = time.time()
        db['config']['total_duration_seconds'] = duration_hours * 60 * 60
        for voter in interaction.guild.members:
            db['voters'][voter] = 0
        write()



@tree.app_command(
    name='register',
    description='Run this command to become a candidate for the current election'
)
async def register_command(interaction):
    if await verify_election_duration():
        if interaction.user in db['candidates']:
            db['candidates'].append(interaction.user)
            write()
            interaction.response.send_message(f'{interaction.user} has been registered as a candidate in the election. there are now {len(db['candidates'])} candidates.')
        else: interaction.response.send_message(f'{interaction.user} is already registered as a candidate in the current election.')
    else: interaction.response.send_message('There is no currently active election.')

@tree.app_command(
    name='vote',
    description='Run this command to cast a vote in the current election. Users may cast a maximum of one vote.'
)
async def vote(interaction, candidate):
    if verify_election_duration() and interaction.user in db['voters']:
        db['candidates'][candidate] += 1
        db['voters'].remove(candidate)
        write()


async def write():
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))

async def verify_election_duration():
    if not db['config']['is_election_running']: return False
    if time.time > db['config']['start_time'] + db['config']['total_duration_seconds']:
        db['config']['is_election_running'] = False
        db['config']['start_time'] = None
        db['config']['total_duration_seconds'] = None
        write()
        return False
    return True

async def election_timer(duration):
    time.sleep(duration)
    mods = [['',0],['',0]]
    for i in db['candidates']:
        if db[i] >= mods[0][1]:
            mods[1] = mods[0]
            mods[0][0] = i
            mods[0][1] = db[i]
        elif db[i] >= mods[1][1]:
            mods[1][0] = i
            mods[1][1] = db[i]
    discord.utils.get(client.get_all_channels(), guild_name='• gay cl☆wn group •', name='announcements').send(f"Election is complete - our new mods are {mods[0][0]} & {mods[1][0]} with {mods[0][1]} and {mods[1][1]} votes respectively!")

    
client.run()