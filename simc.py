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

def check_simc():
    os.system(os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' > ' + htmldir, 'debug', 'simc.ver 2> ' + os.devnull))
    readversion = open(os.path.join(htmldir, 'debug', 'simc.ver'), 'r')
    return readversion.read().splitlines()

async def sim(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message, fightstyle, talents):
    if talents > '1':
        options = 'armory=%s,%s,%s calculate_scale_factors=%s scale_only=agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating,speed_rating html=%ssims/%s/%s threads=%s iterations=%s fight_style=%s talents=%s' % (region, realm, char, scale, htmldir, char, htmladdr, threads, iterations, fightstyle, talents)
    else:
        options = 'armory=%s,%s,%s calculate_scale_factors=%s scale_only=agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating,speed_rating html=%ssims/%s/%s threads=%s iterations=%s fight_style=%s' % (region, realm, char, scale, htmldir, char, htmladdr, threads, iterations, fightstyle)

    os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
    load = await bot.send_message(message.channel, 'Simulating: Starting...')
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
                await bot.edit_message(load, 'Error, something went wrong: ' + website + 'debug/simc.sterr')
                return
        if len(process_check) > 1:
            if 'html report took' in process_check[-2]:
                loop = False
                link = 'Simulation: %ssims/%s/%s' % (website, char, htmladdr)
                for line in process_check:
                    if 'DPS:' in line:
                        line = line
                        break
                line = line.strip()
                line = line.split(" ")
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Simulation: Ready'))
                if len(line) > 1:
                    await bot.edit_message(load,  link + ' (' + line[0] + ' ' + line[1] + ') {0.author.mention}'.format(message))
                else:
                    await bot.edit_message(load, link + ' {0.author.mention}'.format(message))
            else:
                if 'Generating' in process_check[-1]:
                    done = '█' * (20 - process_check[-1].count('.'))
                    missing = '░' * (process_check[-1].count('.'))
                    progressbar = done + missing
                    procent = 100 - process_check[-1].count('.') * 5
                    load = await bot.edit_message(load, process_check[-1].split()[1] + ' ' + progressbar + ' ' + str(procent) + '%')


# Not the best solution to add queue system, but it works
async def queue(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message, scaling, fightstyle, talents):
    server = bot.get_server(user_opt['server_opt'][0]['serverid'])
    queueloop = True
    while queueloop:
        if server.me.status != discord.Status.online:
             await asyncio.sleep(10)
        else:
            queueloop = False
            loop = True
            msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize())
            await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Simulation: In Progress'))
            await bot.send_message(message.channel, msg)
            bot.loop.create_task(sim(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message, fightstyle, talents))
            return


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
    iterations = user_opt['simcraft_opt'][0]['default_iterations']
    loop = True
    timestr = time.strftime("%Y%m%d-%H%M%S")
    scale = 0
    scaling = 'No'
    data = 'armory'
    char = ''
    addon = ''
    fightstyle = 'LightMovement'
    talents = '0'

    if message.author == bot.user:
        return
    elif args.startswith('!sim'):
        args = args.split('-')
        if args:
            if args[1].startswith(('hh', 'helphere')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.channel, msg)
            elif args[1].startswith(('h', 'help')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.author, msg)
            elif args[1].startswith(('v', 'version')):
                await bot.send_message(message.channel, *check_simc())
            else:
                for i in range(len(args)):
                    if args[i] != '!simc ' and args[i] != '!sim ':
                        if args[i].startswith(('r ', 'realm ')):
                            temp = args[i].split()
                            realm = temp[1]
                        elif args[i].startswith(('c ', 'char ', 'character ')):
                            temp = args[i].split()
                            char = temp[1]
                        elif args[i].startswith(('s ', 'scaling ')):
                            temp = args[i].split()
                            scaling = temp[1]
                        elif args[i].startswith(('z ', 'region ')):
                            temp = args[i].split()
                            region = temp[1]
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
                        elif args[i].startswith(('t ', 'talents ')):
                            temp = args[i].split()
                            if len(temp[1]) == 7:
                                talents = temp[1]
                        elif args[i].startswith(('i ', 'iterations ')):
                            if user_opt['simcraft_opt'][0]['allow_iteration_parameter']:
                                temp = args[i].split()
                                iterations = temp[1]
                                if iterations > '35000':
                                    iterations = '35000'
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
                user = message.author
                os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
                # Channel override, replace with actual ids
                if message.channel == bot.get_channel('1'):
                    message.channel = bot.get_channel('2')
                elif message.channel == bot.get_channel('1'):
                    message.channel = bot.get_channel('2')
                htmladdr = '%s-%s.html' % (char, timestr)               
                if server.me.status != discord.Status.online:
                    msg = 'Simulation queued, a URL will be provided once your request have been processed.'
                    print('Queued ' + char + ' @ ' + realm + ' - ', end="")
                    print(user, end="")
                    print(' @', message.server, '#', message.channel)
                    print('--------------')
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(queue(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message, scaling, fightstyle, talents))
                else:
                    msg = '\nSimulationCraft:\nCharacter: %s @ %s\nScaling: %s' % (char.capitalize(), realm.capitalize(), scaling.capitalize())
                    await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Simulation: In Progress'))
                    print('Simming ' + char + ' @ ' + realm + ' - ', end="")
                    print(user, end="")
                    print(' @', message.server, '#', message.channel)
                    print('--------------')
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(sim(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message, fightstyle, talents))


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