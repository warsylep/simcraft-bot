import os
import discord
import asyncio
import time
import json

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

async def sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents, compare, maxtime, varylength):
    default = 'armory="%s,%s,%s" calculate_scale_factors="%s" scale_only="agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating" html="%ssims/%s/%s" threads="%s" iterations="%s" fight_style="%s" max_time="%s" vary_combat_length="%s"' % (region, realm, char, scale, htmldir, char, htmladdr, threads, iterations, fightstyle, maxtime, varylength)
    if talents > '1' and compare == '0':
        options = '%s talents="%s"' % (default, talents)
    elif talents > '1' and compare > '1':
        options = '%s talents="%s" copy="%s" talents="%s"' % (default, talents, compare, compare)
    elif talents == '0' and compare > '1':
        options = '%s copy="%s" talents="%s"' % (default, compare, compare)
    else:
        options = default
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
            print(err_check[-1])
            if 'ERROR' in err_check[-1] or 'Segmentation fault' in err_check[-1]:
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Simulation: Ready'))
                await bot.edit_message(load, 'Error, something went wrong:\n ' + "\n".join(err_check))
                return
        if len(process_check) > 1:
            if 'html report took' in process_check[-2]:
                loop = False
                link = 'Full report: %ssims/%s/%s' % (website, char.replace("'",""), htmladdr)
                line = '0'
                if compare == '0':
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
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Simulation: Ready'))

            else:
                if 'Generating' in process_check[-1]:
                    done = '█' * (20 - process_check[-1].count('.'))
                    missing = '░' * (process_check[-1].count('.'))
                    progressbar = done + missing
                    procent = 100 - process_check[-1].count('.') * 5
                    load = await bot.edit_message(load, process_check[-1].split()[1] + ' ' + progressbar + ' ' + str(procent) + '%')

# Not the best solution to add queue system, but it works
async def queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents, compare, maxtime, varylength):
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
            bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents, compare, maxtime, varylength))
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

@bot.event
async def on_message(message):
    # don't set variables unless the message is for the bot
    if not message.content.startswith('!sim'):
        return
    if message.author == bot.user:
        return
    args = message.content.lower()
    server = bot.get_server(user_opt['server_opt'][0]['serverid'])
    channel = bot.get_channel(user_opt['server_opt'][0]['channelid'])
    realm = user_opt['simcraft_opt'][0]['default_realm']
    region = user_opt['simcraft_opt'][0]['region']
    iterationsset = False
    loop = True
    timestr = time.strftime("%Y%m%d-%H%M%S")
    scale = 0
    scaling = 'No'
    char = ''
    fightstyle = user_opt['simcraft_opt'][0]['fightstyle']
    talents = '0'
    compare = '0'
    fullscale = False
    varylength = user_opt['simcraft_opt'][0]['varylength']
    maxtime = user_opt['simcraft_opt'][0]['maxtime']
    global queuenr

    if message.server and message.server == bot.get_server('1'):
        iterations = user_opt['simcraft_opt'][0]['default_iterations']
    else:
        iterations = '10000'

    if message.server and message.server == bot.get_server('9'):
        fightstyle = 'Patchwerk'
 
    if '/' in args:
        print(args)
        temp = args.split('/')
        temp2 = temp[0].split(' ',1)
        if args.count('/') == 1:
           args = temp2[0] + ' -c ' + temp[1] + '-r ' + temp2[1]                
        elif args.count('/') == 2:
            args = temp2[0] + ' -c ' + temp[2] + '-r ' + temp[1] + '-z ' + temp2[1]
    if '-' in args:
        args = args.split('-')
    else:
        await bot.send_message(message.channel, 'Unknown command. Use !sim -h/help for commands')
        return
    if args:
        print(args, message.author, message.server, message.channel)
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
        else:
            for i in range(len(args)):
                if args[i] != '!simc ' and args[i] != '!sim ':
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
                        if len(temp[1]) > 4:
                            await bot.send_message(message.author, 'Invalid data given for option: region')
                            return
                        else:
                            region = clean(temp[1])
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
                                elif iterations > 35000:
                                    iterations = 35000
                                elif iterations < 1:
                                    iterations = 1
                            else:
                                await bot.send_message(message.author, 'Invalid data given for option: iterations')
                                return
                        else:
                            await bot.send_message(message.channel, 'Custom iterations is disabled')
                            return
                    elif args[i].startswith(('ct ', 'compare ')):
                        temp = args[i].split()
                        if len(clean(temp[1])) == 7 and isint(temp[1]):
                            compare = clean(temp[1])
                        else:
                            await bot.send_message(message.author, 'Invalid data given for option: compare')
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
                    else:
                        await bot.send_message(message.channel, 'Unknown command. Use !sim -h/help for commands')
                        return
            if char == '':
                await bot.send_message(message.channel, 'Character name is needed')
                return
            if scaling == 'yes' and compare == '0':
                scale = 1
                if not iterationsset:
                    iterations = '20000'
            user = message.author
            os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
            if message.server:
                # Dr
                if message.server == bot.get_server('1'):
                    print('Dr - override')
                    message.channel = message.author
                # Ea
                elif message.server == bot.get_server('9'):
                    print('Ea - override')
                    message.channel = message.author
                # Ef
                elif message.server == bot.get_server('1'):
                    print('Ef - override')
                    message.channel = bot.get_channel('2')
            htmladdr = '%s-%s.html' % (char, timestr)
            if server.me.status != discord.Status.online or fullscale:
                if queuenr > 5:
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
                bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents, compare, maxtime, varylength))
                if fullscale:
                    fightstyle = 'HeavyMovement'
                    htmladdr = '%s-%s-2.html' % (char, timestr)
                    bot.loop.create_task(queue(realm, char, scale, htmladdr, region, iterations, loop, message, scaling, fightstyle, talents, compare, maxtime, varylength))
            else:
                msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s\nFight style: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize(), fightstyle)
                await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Simulation: In Progress'))
                print('Simming ' + char + ' @ ' + realm + ' - ', end="")
                print(user, end="")
                print(' @', message.server, '#', message.channel)
                print('--------------')
                await bot.send_message(message.channel, msg)
                bot.loop.create_task(sim(realm, char, scale, htmladdr, region, iterations, loop, message, fightstyle, talents, compare, maxtime, varylength))


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