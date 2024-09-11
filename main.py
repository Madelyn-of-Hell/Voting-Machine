import discord.app_commands
from tokens import TOKEN
import discord
import asyncio
import json
import time
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

db:dict = {}




try: 
    open('db.json', 'x')
    db:dict = {'candidates': {}, 
               'voters':[], 
               'config': {
                   'is_election_running':False, 
                   'start_time':None, 
                   'total_duration_seconds':None}}
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))
except: 
    with open('db.json', 'r') as f:
        db = json.load(f)


@client.event
async def on_ready():
    print('Syncing Commands...')
    await tree.sync()
    print('Connected and Synced!')
    if db['config']['is_election_running']:
        print('Restarting timer...')
        asyncio.create_task(election_timer())

        

@tree.command(
        name='start-election',
        description='an admin-only command; starts an election if one is not current running'
)
# @discord.app_commands.checks.has_permissions(administrator=True)
async def start_election(interaction, duration_hours:float):
    if not db['config']['is_election_running']:
        db['config']['is_election_running'] = True
        db['config']['start_time'] = time.time()
        db['config']['total_duration_seconds'] = duration_hours * 60 * 60
        for voter in interaction.guild.members:
            db['voters'].append(voter.name)
        write()
        asyncio.create_task(election_timer())
        await interaction.response.send_message(f'Election has begun! Ends <t:{round(db["config"]["start_time"]) +round(db["config"]["total_duration_seconds"])}:R>')
    else: await interaction.response.send_message(f'There is already an election in progress, ending <t:{round(db["config"]["start_time"]) + round(db["config"]["total_duration_seconds"])}:R>', ephemeral=True)




@tree.command(
    name='register',
    description='Run this command to become a candidate for the current election'
)
async def register_command(interaction):
    if await verify_election_duration():
        if not interaction.user.name in db['candidates']:
            db['candidates'][interaction.user.name] = 0
            write()
            await interaction.response.send_message(f'{interaction.user} has been registered as a candidate in the election. there are now {len(db['candidates'])} candidates.', ephemeral=True)
            await tree.sync()
        else: await interaction.response.send_message(f'{interaction.user} is already registered as a candidate in the current election.', ephemeral=True)
    else: await interaction.response.send_message('There is no currently active election.', ephemeral=True)

@tree.command(
    name='vote',
    description='Run this command to cast a vote in the current election. Users may cast a maximum of one vote.'
)
async def vote_command(interaction, candidate:str):
    if await verify_election_duration():
        if interaction.user.name in db['voters']:
            db['candidates'][candidate] += 1
            db['voters'].remove(interaction.user.name)
            write()
            await interaction.response.send_message(f'Your vote for {candidate.capitalize()} has been registered! if you didn\'t vote for {candidate.capitalize()}, please DM <@566579790556037140>', ephemeral=True)
        else: await interaction.response.send_message('You may only vote once per election!', ephemeral=True)
    else: await interaction.response.send_message('There is no currently active election.', ephemeral=True)

@vote_command.autocomplete('candidate')
async def candidate_list(interaction, input_string) -> list[discord.app_commands.Choice[str]]:
    return [discord.app_commands.Choice(name=choice, value=choice) for choice in db['candidates'] if input_string in choice]

@tree.command(
        name='countdown',
        description='Displays a live countdown of the election timer.'
)
async def countdown_command(interaction):
    if await verify_election_duration():
        embed = discord.Embed(title='Countdown',color=0xff0000)
        embed.add_field(name='',value=f'Election ends <t:{round(db["config"]["start_time"]) + round(db["config"]["total_duration_seconds"])}:R>')
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message('There is no currently active election.')

@tree.command(
        name='candidates',
        description='Displays a list of all candidates for the current election.'
)
async def candidates_command(interaction):
    if await verify_election_duration():
        embed = discord.Embed(title='Candidates',color=0xff0000)
        for candidate in db['candidates']:
            embed.add_field(name='',value=candidate, inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message('There is no currently active election.')

def write():
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))

async def verify_election_duration():
    if not db['config']['is_election_running']: return False
    if time.time() > db['config']['start_time'] + db['config']['total_duration_seconds']:
        db['config']['is_election_running'] = False
        db['config']['start_time'] = None
        db['config']['total_duration_seconds'] = None
        write()
        return False
    return True

async def election_timer():
    global db
    print(f'sleeping for {db['config']['total_duration_seconds'] - (time.time()-db['config']['start_time'])} seconds')
    await asyncio.sleep(db['config']['total_duration_seconds'] - (time.time()-db['config']['start_time']))


    mods = [('',-1),('',-1)]
    for candidate in db['candidates'].items():
        if candidate[1] > mods[0][1]:
            mods[1] = mods[0]
            mods[0] = candidate
        elif candidate[1] > mods[1][1]:
            mods[1] = candidate
    print(f"Election is complete - our new mods are {mods[0][0]} & {mods[1][0]} with {mods[0][1]} and {mods[1][1]} votes respectively!")
    announcements = await client.fetch_channel(1241410455633920041)
    await announcements.send(f"Election is complete - our new mods are {mods[0][0]} & {mods[1][0]} with {mods[0][1]} and {mods[1][1]} votes respectively!")
    db = {'candidates': {}, 
               'voters':[], 
               'config': {
                   'is_election_running':False, 
                   'start_time':None, 
                   'total_duration_seconds':None}}
    write()

client.run(TOKEN)