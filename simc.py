import os
import subprocess
import discord
import aiohttp
import asyncio
import time
import json
from urllib.parse import quote

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('user_data.json') as data_file:
    user_opt = json.load(data_file)

bot = discord.Client()
threads = os.cpu_count()
htmldir = user_opt['simcraft_opt'][0]['htmldir']
website = user_opt['simcraft_opt'][0]['website']
os.makedirs(os.path.dirname(os.path.join(htmldir + 'debug', 'test.file')), exist_ok=True)
queuenum = 0
busy = False

def check_simc():
    # remove comment below if you are using this. (I write to this file during compile, thus have no need to read build version on each run)
    #os.system(os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' > ' + htmldir, 'debug', 'simc.ver 2> ' + os.devnull))
    readversion = open(os.path.join(htmldir, 'debug', 'simc.ver'), 'r')
    return readversion.read().splitlines()

async def check_api(region, realm, char, apikey):
    url = "https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_GB&apikey=%s" % (region, realm, quote(char), apikey)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if 'reason' in data:
                return data['reason']
            else:
                spec = 0
                for i in range(len(data['talents'])):
                    for line in data['talents']:
                        if 'selected' in line:
                            role = data['talents'][spec]['spec']['role']
                            return role
                        else:
                            spec += +1
        
async def sim(realm, char, scale, htmladdr, region, iterations, message, fightstyle, talents, compare, maxtime, varylength, enemies, compareitem, replaceitem):
    global busy
    loop = True
    options = 'armory=%s,%s,%s calculate_scale_factors=%s scale_only=agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating html=%s%s/%s/%s threads=%s iterations=%s fight_style=%s max_time=%s vary_combat_length=%s' % (region, realm, char, scale, htmldir, region, realm, htmladdr, threads, iterations, fightstyle, maxtime, varylength)
    if enemies:
        options = '%s %s' % (options, enemies)
    if replaceitem:
        options = '%s %s' % (options, replaceitem)
    if talents:
        options = '%s talents=%s' % (options, talents)
    if compare and not compareitem:
        options = '%s copy=%s talents=%s' % (options, compare, compare)
    if compareitem and not compare:
        options = '%s copy=%s_2 %s' % (options, char, compareitem)
    os.makedirs(os.path.dirname(os.path.join(htmldir, region, realm, 'test.file')), exist_ok=True)
    load = await bot.send_message(message.channel, 'Simulation: Starting...')
    command = "%s %s" % (user_opt['simcraft_opt'][0]['executable'], options)
    stdout = open(os.path.join(htmldir, 'debug', 'simc.stdout'), "w")
    stderr = open(os.path.join(htmldir, 'debug', 'simc.stderr'), "w")
    process = subprocess.Popen(command.split(" "), universal_newlines=True, stdout=stdout, stderr=stderr)

    await asyncio.sleep(1)
    while loop:
        readstdout = open(os.path.join(htmldir, 'debug', 'simc.stdout'), "r")
        readstderr = open(os.path.join(htmldir, 'debug', 'simc.stderr'), "r")
        process_check = readstdout.readlines()
        err_check = readstderr.readlines()
        await asyncio.sleep(1)
        if len(err_check) > 0:
            if 'ERROR' in err_check[-1] or 'Segmentation fault' in err_check[-1]:
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready (!sim -h for help)'))
                await bot.edit_message(load, 'Error, something went wrong:\n ' + "\n".join(err_check))
                busy = False
                process.terminate()
                return
        if len(process_check) > 1:
            if 'html report took' in process_check[-2]:
                loop = False
                link = 'Full report: %s%s/%s/%s' % (website, region, realm, htmladdr)
                line = '0'
                if not compare and not compareitem:
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
                    await bot.edit_message(load,  'Simulation: Complete')
                    await bot.send_message(message.channel, link + ' {0.author.mention}'.format(message))
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready (!sim -h for help)'))
                busy = False
                process.terminate()

            else:
                if 'Generating' in process_check[-1]:
                    done = '█' * (20 - process_check[-1].count('.'))
                    missing = '░' * (process_check[-1].count('.'))
                    progressbar = done + missing
                    procent = 100 - process_check[-1].count('.') * 5
                    load = await bot.edit_message(load, process_check[-1].split()[1] + ' ' + progressbar + ' ' + str(procent) + '%')

# Not the best solution to add queue system, but it works
async def queue(realm, char, scale, htmladdr, region, iterations, message, scaling, fightstyle, talents, compare, maxtime, varylength, enemies, compareitem, replaceitem):
    global queuenum
    global busy
    queueloop = True
    while queueloop:
        if busy:
             await asyncio.sleep(10)
        else:
            queueloop = False
            queuenum = queuenum - 1
            busy = True
            msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s\nFight style: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize(), fightstyle)
            await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Sim: In Progress (!sim -h for help)'))
            await bot.send_message(message.channel, msg)
            bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, message, fightstyle, talents, compare, maxtime, varylength, enemies, compareitem, replaceitem))
            return

# Might look ugly but is surprisingly fast for some reason
def clean(text):
    return text.replace('"', '').replace("'", "").replace('/', '').replace('.', '').replace('\\', '').replace(',', '').replace(':', '').replace(';', '').replace('%', '').replace('(', '').replace(')', '').replace('|', '')

# whyyy
def isint(number):
    try:
        int(number)
        return True
    except ValueError:
        return False

def checkitem(item):
    return item.startswith(("head=", "neck=", "shoulder=", "back=", "chest=", "wrists=", "hands=", "waist=", "legs=", "feet=", "finger1=", "finger2=", "trinket1=", "trinket2=", "main_hand=", "off_hand="))    

@bot.async_event
async def on_message(message):
    # don't set variables unless the message is for the bot
    if (message.server and not message.content.startswith('!sim ')) or (not message.server and not message.content.startswith('!sim')):
        return
    if message.author == bot.user:
        return
    args = message.content.lower()
    server = bot.get_server(user_opt['server_opt'][0]['serverid'])
    channel = bot.get_channel(user_opt['server_opt'][0]['channelid'])
    region = user_opt['simcraft_opt'][0]['region']
    regions = ['us', 'eu', 'tw', 'kr', 'zh']
    apikey = user_opt['simcraft_opt'][0]['apikey']
    apicheck = user_opt['simcraft_opt'][0]['apicheck']
    iterationsset = False
    timestr = time.strftime("%Y%m%d-%H%M%S")
    scale = 0
    scaling = 'No'
    char = ''
    fightstyle = user_opt['simcraft_opt'][0]['fightstyle']
    talents = 0
    compare = 0
    enemies = ''
    compareitem = ''
    replaceitem = ''
    fullscale = False
    varylength = user_opt['simcraft_opt'][0]['varylength']
    maxtime = user_opt['simcraft_opt'][0]['maxtime']
    global queuenum
    global busy

    if message.server and message.server == bot.get_server('1'):
        realm = user_opt['simcraft_opt'][0]['default_realm']
        iterations = user_opt['simcraft_opt'][0]['default_iterations']
    else:
        realm = ''
        iterations = '10000'

    if '/' in args[:40]:
        temp2 = ''
        extra = ''
        temp = args.split(' ', 1)
        if '-' in temp[1]:
            temp2 = temp[1].split('-', 1)
            temp3 = temp2[0].split('/')
            check = temp2[0]
            extra = temp2[1]
        else:
            temp3 = temp[1].split('/')
            check = temp[1]
        if check.count('/') == 1:
            args = temp[0] + ' -c ' + temp3[1] + ' -r ' + temp3[0]
        elif check.count('/') == 2:
            args = temp[0] + ' -c ' + temp3[2] + ' -r ' + temp3[1] + ' -z ' + temp3[0]
        if extra:
            args = args + ' -' + temp2[1]
    if '-' in args:
        args = args.split('-')
    else:
        await bot.send_message(message.author, 'Unknown command. Use !sim -h for commands')
        return
    if args:
        if args[1].startswith(('hh', 'helphere')):
            msg = open('help.file', 'r', encoding='utf8').read()
            msg2 = open('help2.file', 'r', encoding='utf8').read()
            await bot.send_message(message.channel, msg)
            await bot.send_message(message.channel, msg2)
        elif args[1].startswith(('h', 'help')):
            msg = open('help.file', 'r', encoding='utf8').read()
            msg2 = open('help2.file', 'r', encoding='utf8').read()
            await bot.send_message(message.author, msg)
            await bot.send_message(message.author, msg2)
        elif args[1].startswith(('gif')):
            await bot.send_message(message.channel, 'https://i.giphy.com/3o7TKMyfMHjPEQLumI.gif')
        elif args[1].startswith(('v', 'version')):
            await bot.send_message(message.channel, *check_simc())
        elif args[1].startswith(('queue')):
            msg = 'Request queue: %s' % (queuenum)
            await bot.send_message(message.channel, msg)
        else:
            for i in range(len(args)):
                if args[i] != '!sim ':
                    if args[i].startswith(('r ', 'realm ')):
                        temp = args[i][2:].strip()
                        realm = clean(temp.replace('_', '-').replace(' ', '-'))
                    elif args[i].startswith(('c ', 'char ', 'character ')):
                        temp = args[i].split()
                        if len(temp[1]) > 12:
                            await bot.send_message(message.author, 'Invalid data given for option: character')
                            return
                        else:
                            char = clean(temp[1])
                    elif args[i].startswith(('s ', 'scaling ')):
                        temp = args[i].split()
                        if temp[1] == 'yes':
                            scaling = clean(temp[1])
                        elif temp[1] == 'no':
                            scaling = '0'
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: scaling')
                            return
                    elif args[i].startswith(('z ', 'region ')):
                        temp = args[i].split()
                        if len(temp) > 4 or len(temp) <= 1:
                            await bot.send_message(message.author, 'Invalid data given for option: region')
                            return
                        else:
                            region = clean(temp[1])
                    elif args[i].startswith(('f ', 'fightstyle ')):
                        temp = args[i].split()
                        if temp[1] == 'light' or temp[1] == 'lightmovement':
                            fightstyle = 'LightMovement'
                        elif temp[1] == 'heavy' or temp[1] == 'heavymovement':
                            fightstyle = 'HeavyMovement'
                        elif temp[1] == 'patchwerk':
                            fightstyle = 'Patchwerk'
                        elif temp[1] == 'beast' or temp[1] == 'beastlord':
                            fightstyle = 'Beastlord'
                        elif temp[1] == 'cleave' or temp[1] == 'hecticaddcleave':
                            fightstyle = 'HecticAddCleave'
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: fightstyle')
                            return
                    elif args[i].startswith(('t ', 'talents ')):
                        temp = args[i].split()
                        if len(clean(temp[1])) == 7 and isint(temp[1]):
                            talents = clean(temp[1])
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: talents')
                            return
                    elif args[i].startswith(('fs ', 'fullscale ')):
                        temp = args[i].split()
                        fullscale = True
                        iterations = '40000'
                        scaling = 'yes'
                    elif args[i].startswith(('i ', 'iterations ')):
                        if user_opt['simcraft_opt'][0]['allow_iteration_parameter']:
                            temp = args[i].split()
                            if isint(clean(temp[1])):
                                iterationsset = True
                                iterations = int(clean(temp[1]))
                                if iterations > 200000:
                                    iterations = 1000
                                elif iterations > 40000:
                                    iterations = 40000
                                elif iterations < 1:
                                    iterations = 1
                            else:
                                await bot.send_message(message.author, 'Invalid data given for option: iterations')
                                return
                        else:
                            await bot.send_message(message.author, 'Custom iterations is disabled')
                            return
                    elif args[i].startswith(('ct ', 'compare ')):
                        temp = args[i].split()
                        if len(clean(temp[1])) == 7 and isint(temp[1]):
                            compare = clean(temp[1])
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: compare')
                            return
                    elif args[i].startswith(('ci ', 'compareitem ')):
                        temp = args[i].split()
                        if checkitem(temp[1]):
                            compareitem = temp[1].replace(' ', '')
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: compareitem')
                            return
                    elif args[i].startswith(('ri ', 'replaceitem ')):
                        temp = args[i].split()
                        if checkitem(temp[1]):
                            replaceitem = temp[1].replace(' ', '')
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: replaceitem')
                            return
                    elif args[i].startswith(('vary ')):
                        temp = args[i].split()
                        if temp[1] == 'yes':
                            varylength = '0.20'
                        elif temp[1] == 'no':
                            varylength = '0'
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: vary')
                            return
                    elif args[i].startswith(('time ')):
                        temp = args[i].split()
                        if isint(clean(temp[1])):
                            maxtime = int(clean(temp[1]))
                            if maxtime > 600:
                                maxtime = 600
                            elif maxtime < 10:
                                maxtime = 10
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: time')
                            return 
                    elif args[i].startswith(('e ', 'enemies ')):
                        temp = args[i].split()
                        temp[1] = clean(temp[1])
                        if isint(temp[1]):
                            temp[1] = int(temp[1])
                            if temp[1] > 1 and temp[1] <= 5:
                                for i in range(1, temp[1]+1):
                                    enemies += 'enemy=Fluffy_Pillow%s ' % i
                            else:
                                await bot.send_message(message.author, 'Invalid data given for option: enemies')
                                return
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: enemies')
                            return
                    else:
                        await bot.send_message(message.author, 'Unknown command. Use !sim -h for commands')
                        return
            if message.server:
                # Dr
                if message.server == bot.get_server('1'):
                    message.channel = message.author
                # Ea
                elif message.server == bot.get_server('9'):
                    message.channel = message.author
                # Ef
                elif message.server == bot.get_server('1'):
                    message.channel = bot.get_channel('2')
                # Bl
                elif message.server == bot.get_server('1'):
                    message.channel = message.author
            if char == '':
                await bot.send_message(message.channel, 'Character name is needed')
                return
            if realm == '':
                await bot.send_message(message.channel, 'Realm name is needed')
                return
            if not region in regions:
                await bot.send_message(message.channel, 'Region is not valid or is unsupported, see help for valid regions')
                return
            if scaling == 'yes' and not compare:
                scale = 1
                if not iterationsset:
                    iterations = '20000'
            if compare and compareitem:
                await bot.send_message(message.channel, "You can't compare items and talents at the same time")
                return
            if apicheck:
                api = await check_api(region, realm, char, apikey)
                if api == 'HEALING':
                    await bot.send_message(message.channel, 'SimulationCraft does not support healing specializations.')
                    return
                elif api == 'TANK':
                    await bot.send_message(message.channel, 'Warning: Tank specializations is poorly supported in SimulationCraft and will probably provide inaccurate results.')
                elif not api == 'DPS':
                    msg = 'Something went wrong when trying to fetch character data: %s' % (api)
                    await bot.send_message(message.channel, msg)
                    return
            htmladdr = '%s-%s.html' % (char, timestr)
            os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
            if busy or fullscale:
                if queuenum > 5:
                    await bot.send_message(message.channel, 'Too many requests in queue, please try again later')
                    return
                queuenum = queuenum + 1
                if queuenum > 1:
                    s = 's'
                else:
                    s = ''
                msg = 'Simulation queued, a URL will be provided once your request have been processed.\nThere are currently %s request%s in queue.' % (queuenum, s)
                await bot.send_message(message.channel, msg)
                bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, message, scaling, fightstyle, talents, compare, maxtime, varylength, enemies, compareitem, replaceitem))
                if fullscale:
                    fightstyle = 'HeavyMovement'
                    htmladdr = '%s-%s-2.html' % (char, timestr)
                    bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, message, scaling, fightstyle, talents, compare, maxtime, varylength. enemies, compareitem, replaceitem))
            else:
                msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s\nFight style: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize(), fightstyle)
                busy = True
                await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Sim: In Progress (!sim -h for help)'))
                await bot.send_message(message.channel, msg)
                bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, message, fightstyle, talents, compare, maxtime, varylength, enemies, compareitem, replaceitem))


@bot.async_event
async def on_server_join(server):
    print('I JOINED A SERVER')
    print(server)

@bot.async_event
async def on_server_remove(server):
    print('I LEFT A SERVER')
    print(server)

@bot.async_event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(bot.user)
    print(*check_simc())
    print('--------------')
    await bot.change_presence(game=discord.Game(name='Sim: Ready (!sim -h for help)'))


bot.run(user_opt['server_opt'][0]['token'])