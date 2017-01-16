import os
import discord
import asyncio
import time
import json
import shlex

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('user_data.json') as data_file:
    user_opt = json.load(data_file)

bot = discord.Client()
threads = os.cpu_count()
htmldir = user_opt['simcraft_opt'][0]['htmldir']
website = user_opt['simcraft_opt'][0]['website']
os.makedirs(os.path.dirname(os.path.join(htmldir + 'debug', 'test.file')), exist_ok=True)
queuenr = 0

def check_simc():
    os.system(os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' > ' + htmldir, 'debug', 'simc.ver 2> ' + os.devnull))
    readversion = open(os.path.join(htmldir, 'debug', 'simc.ver'), 'r')
    return readversion.read().splitlines()

async def sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents):
    if talents > '1':
        options = 'armory=%s,%s,%s calculate_scale_factors=%s scale_only=agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating html=%ssims/%s/%s threads=%s iterations=%s fight_style=%s talents=%s' % (region, realm, char, scale, htmldir, char, htmladdr, threads, iterations, fightstyle, talents)
    else:
        options = 'armory=%s,%s,%s calculate_scale_factors=%s scale_only=agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating html=%ssims/%s/%s threads=%s iterations=%s fight_style=%s' % (region, realm, char, scale, htmldir, char, htmladdr, threads, iterations, fightstyle)

    os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
    load = await bot.send_message(message.channel, 'Simulation: Starting...')
    os.system(os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' ' + options + ' > ' + htmldir, 'debug', 'simc.stout 2> ' + htmldir, 'debug', 'simc.sterr &'))

    await asyncio.sleep(1)
    while loop:
        readstout = open(os.path.join(htmldir, 'debug', 'simc.stout'), "r")
        readsterr = open(os.path.join(htmldir, 'debug', 'simc.sterr'), "r")
        process_check = readstout.readlines()
        err_check = readsterr.readlines()
        await asyncio.sleep(1)
        if len(err_check) > 0:
            if 'ERROR' in err_check[-1]:
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Simulation: Ready'))
                await bot.edit_message(load, 'Error, something went wrong:\n ' + "\n".join(err_check))
                return
        if len(process_check) > 1:
            if 'html report took' in process_check[-2]:
                loop = False
                link = 'Full report: %ssims/%s/%s' % (website, char.replace("'",""), htmladdr)
                for line in process_check:
                    if 'DPS:' in line:
                        line = line
                        break
                line = line.strip()
                line = line.split(" ")
                if len(line) > 1:
                    await bot.edit_message(load,  'Simulation: Complete')
                    msg = '\n%s %s\n%s\n' % (line[0], line[1], link)
                    await bot.send_message(message.channel, msg + '{0.author.mention}'.format(message))
                else:
                    await bot.edit_message(load, link + ' {0.author.mention}'.format(message))
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Simulation: Ready'))

            else:
                if 'Generating' in process_check[-1]:
                    done = '█' * (20 - process_check[-1].count('.'))
                    missing = '░' * (process_check[-1].count('.'))
                    progressbar = done + missing
                    procent = 100 - process_check[-1].count('.') * 5
                    load = await bot.edit_message(load, process_check[-1].split()[1] + ' ' + progressbar + ' ' + str(procent) + '%')

# Not the best solution to add queue system, but it works
async def queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents):
    global queuenr
    server = bot.get_server(user_opt['server_opt'][0]['serverid'])
    queueloop = True
    while queueloop:
        if server.me.status != discord.Status.online:
             await asyncio.sleep(10)
        else:
            queueloop = False
            loop = True
            queuenr = queuenr - 1
            msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s\nFight style: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize(), fightstyle)
            await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Simulation: In Progress'))
            await bot.send_message(message.channel, msg)
            bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents))
            return

# Might look ugly but is surprisingly fast for some reason
def clean(text):
    return text.replace('"', '').replace("'", "").replace('/', '').replace('.', '').replace('\\', '').replace(',', '').replace(':', '').replace(';', '')

@bot.event
async def on_message(message):
    # don't set variables unless the message is for the bot
    args = message.content.lower()
    if not args.startswith('!sim'):
        return
    server = bot.get_server(user_opt['server_opt'][0]['serverid'])
    channel = bot.get_channel(user_opt['server_opt'][0]['channelid'])
    realm = user_opt['simcraft_opt'][0]['default_realm']
    region = user_opt['simcraft_opt'][0]['region']
    iterationsset = '0'
    loop = True
    timestr = time.strftime("%Y%m%d-%H%M%S")
    scale = 0
    scaling = 'No'
    char = ''
    fightstyle = 'LightMovement'
    talents = '0'
    fullscale = '0'
    global queuenr

    if message.server == bot.get_server('1') or message.server == bot.get_server('2'):
        iterations = '10000'
    else:
        iterations = user_opt['simcraft_opt'][0]['default_iterations']

    if message.author == bot.user:
        return
    elif args.startswith('!sim'):
        args = args.split('-')
        if args:
            print(args, message.author, message.server, message.channel)
            if args[1].startswith(('hh', 'helphere')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.channel, msg)
            elif args[1].startswith(('h', 'help')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.author, msg)
            elif args[1].startswith(('gif')):
                await bot.send_message(message.channel, 'https://i.giphy.com/3o7TKMyfMHjPEQLumI.gif')
            elif args[1].startswith(('v', 'version')):
                await bot.send_message(message.channel, *check_simc())
            else:
                for i in range(len(args)):
                    if args[i] != '!simc ' and args[i] != '!sim ':
                        if args[i].startswith(('r ', 'realm ')):
                            temp = args[i][2:].strip()
                            realm = shlex.quote(clean(temp.replace('_', '-').replace(' ', '-')))
                        elif args[i].startswith(('c ', 'char ', 'character ')):
                            temp = args[i].split()
                            char = clean(temp[1])
                        elif args[i].startswith(('s ', 'scaling ')):
                            temp = args[i].split()
                            scaling = temp[1]
                        elif args[i].startswith(('z ', 'region ')):
                            temp = args[i].split()
                            region = shlex.quote(clean(temp[1]))
                        elif args[i].startswith(('f ', 'fightstyle ')):
                            temp = args[i].split()
                            if temp[1] == 'light':
                                fightstyle = 'LightMovement'
                            elif temp[1] == 'heavy':
                                fightstyle = 'HeavyMovement'
                            elif temp[1] == 'patchwerk':
                                fightstyle = 'Patchwerk'
                            elif temp[1] == 'beast':
                                fightstyle = 'Beastlord'
                            elif temp[1] == 'cleave':
                                fightstyle = 'HecticAddCleave'
                        elif args[i].startswith(('t ', 'talents ')):
                            temp = args[i].split()
                            if len(temp[1]) == 7:
                                talents = shlex.quote(clean(temp[1]))
                        elif args[i].startswith(('fs ', 'fullscale ')):
                            temp = args[i].split()
                            fullscale = '1'
                            iterations = '50000'
                            scaling = 'yes'
                        elif args[i].startswith(('i ', 'iterations ')):
                            if user_opt['simcraft_opt'][0]['allow_iteration_parameter']:
                                temp = args[i].split()
                                iterations = temp[1]
                                iterationsset = '1'
                                if iterations > '40000':
                                    iterations = '40000'
                                elif iterations < '1':
                                    iterations = '1'
                            else:
                                await bot.send_message(message.channel, 'Custom iterations is disabled')
                                return
                        else:
                            await bot.send_message(message.channel, 'Unknown command. Use !sim -h/help for commands')
                            return
                if char == '':
                    await bot.send_message(message.channel, 'Character name is needed')
                    return
                if scaling == 'yes':
                    scale = 1
                    if iterationsset == '0':
                        iterations = '20000'
                user = message.author
                os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
                if message.server:
                    # D
                    if message.server == bot.get_server('1'):
                        print('D - override')
                        message.channel = message.author
                    # Ea
                    elif message.server == bot.get_server('9'):
                        print('Ea - override')
                        message.channel = bot.get_channel('2')
                    # Ef
                    elif message.server == bot.get_server('1'):
                        print('Ef - override')
                        message.channel = bot.get_channel('2')
                htmladdr = '%s-%s.html' % (char, timestr)
                if server.me.status != discord.Status.online or fullscale == '1':
                    if queuenr > 10:
                        print('Queue overflow', timestr)
                        await bot.send_message(message.channel, 'Too many requests in queue, please try again later')
                        return
                    msg = 'Simulation queued, a URL will be provided once your request have been processed.'
                    print('Queued ' + char + ' @ ' + realm + ' - ', end="")
                    print(user, end="")
                    print(' @', message.server, '#', message.channel)
                    print('--------------')
                    queuenr = queuenr + 1
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents))
                    if fullscale == '1':
                        fightstyle = 'HeavyMovement'
                        htmladdr = '%s-%s-2.html' % (char, timestr)
                        bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents))
                else:
                    msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s\nFight style: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize(), fightstyle)
                    await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Simulation: In Progress'))
                    print('Simming ' + char + ' @ ' + realm + ' - ', end="")
                    print(user, end="")
                    print(' @', message.server, '#', message.channel)
                    print('--------------')
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents))


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(bot.user)
    print(*check_simc())
    print('--------------')
    await bot.change_presence(game=discord.Game(name='Simulation: Ready'))


bot.run(user_opt['server_opt'][0]['token'])
