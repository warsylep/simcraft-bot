import os
import discord
import asyncio
import time
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('user_data.json') as data_file:
    user_opt = json.load(data_file)


def check_version():
    git = os.popen('git rev-parse --is-inside-work-tree').read()
    if git:
        check_https = os.popen('git remote -v').read().splitlines()
        for i in range(len(check_https)):
            if 'https' in check_https[i] and '(fetch)' in check_https[i]:
                os.system('git fetch')
                git_commits = os.popen('git log --oneline origin/master').read().splitlines()
                git_current = os.popen('git rev-parse HEAD').read()
                if git_current[:7] in git_commits[0]:
                    return 'Bot is up to date'
                else:
                    for checks in range(len(git_commits)):
                        if git_current[:7] in git_commits[i]:
                            return 'Bot is %s commits behind master.' % checks
            else:
                return 'Can\'t fetch git remote'
    else:
        return 'Bot version is unknown'

bot = discord.Client()
threads = os.cpu_count()
htmldir = user_opt['simcraft_opt'][0]['htmldir']
website = user_opt['simcraft_opt'][0]['website']
os.makedirs(os.path.dirname(os.path.join(htmldir + 'debug', 'test.file')), exist_ok=True)
os.system(
    os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' > ' + htmldir, 'debug', 'simc.ver 2> ' + os.devnull))
readversion = open(os.path.join(htmldir, 'debug', 'simc.ver'), 'r')
version = readversion.readlines()

async def sim(realm, char, scale, htmladdr, data, addon, region, iterations, loop, message):
    icon_num = 0
    load_icon = ['◐', '◓', '◑', '◒']
    if data == 'addon':
        options = 'calculate_scale_factors=%s html=%ssims/%s/%s threads=%s iterations=%s input=%s' % (
            scale, htmldir, char, htmladdr, threads, iterations, addon)
    else:
        options = 'armory=%s,%s,%s calculate_scale_factors=%s html=%ssims/%s/%s threads=%s iterations=%s' % (
            region, realm, char, scale, htmldir, char, htmladdr, threads, iterations)

    load = await bot.send_message(message.channel, 'Simulating: Starting...')
    os.system(os.path.join(user_opt['simcraft_opt'][0]['executable'] + ' ' + options + ' > ' + htmldir, 'debug',
                           'simc.stout 2> ' + htmldir, 'debug', 'simc.sterr &'))
    await asyncio.sleep(1)
    while loop:
        readstout = open(os.path.join(htmldir, 'debug', 'simc.stout'), "r")
        readsterr = open(os.path.join(htmldir, 'debug', 'simc.sterr'), "r")
        process_check = readstout.readlines()
        err_check = readsterr.readlines()
        await asyncio.sleep(1)
        if len(err_check) > 0:
            if 'ERROR' in err_check[-1]:
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready'))
                await bot.edit_message(load, 'Error, something went wrong: ' + website + 'debug/simc.sterr')
                return
        if len(process_check) > 1:
            if 'html report took' in process_check[-2]:
                loop = False
                link = 'Simulation: %ssims/%s/%s' % (website, char, htmladdr)
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready'))
                await bot.edit_message(load, link + ' {0.author.mention}'.format(message))
            else:
                load = await bot.edit_message(load, 'Simulating: ' + load_icon[icon_num])
                icon_num += 1
                if icon_num == 4:
                    icon_num = 0


def check(addon_data):
    return addon_data.content.endswith('DONE')


@bot.event
async def on_message(message):
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
    args = message.content.lower()

    if message.author == bot.user:
        return
    elif args.startswith('!simc'):
        args = args.split('-')
        if args:
            if args[1].startswith(('h', 'help')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.author, msg)
            elif args[1].startswith(('v', 'version')):
                await bot.send_message(message.channel, check_version())
                await bot.send_message(message.channel, *version[:1])
            else:
                if message.channel != channel:
                    await bot.send_message(message.channel, 'Please use the correct channel.')
                    return
                for i in range(len(args)):
                    if args[i] != '!simc ':
                        if args[i].startswith(('r ', 'realm ')):
                            temp = args[i].split()
                            realm = temp[1]
                        elif args[i].startswith(('c ', 'char ', 'character ')):
                            temp = args[i].split()
                            char = temp[1]
                        elif args[i].startswith(('s ', 'scaling ')):
                            temp = args[i].split()
                            scaling = temp[1]
                        elif args[i].startswith(('d ', 'data ')):
                            temp = args[i].split()
                            data = temp[1]
                        elif args[i].startswith(('i ', 'iterations ')):
                            if user_opt['simcraft_opt'][0]['allow_iteration_parameter']:
                                temp = args[i].split()
                                iterations = temp[1]
                            else:
                                await bot.send_message(message.channel, 'Custom iterations is disabled')
                                return
                        else:
                            await bot.send_message(message.channel, 'Unknown command. Use !simc -h/help for commands')
                            return
                if server.me.status != discord.Status.online:
                    err_msg = 'Only one simulation can run at the same time.'
                    await bot.send_message(message.channel, err_msg)
                    return
                else:
                    if char == '':
                        await bot.send_message(message.channel, 'Character name is needed')
                        return
                    if scaling == 'yes':
                        scale = 1
                    user = message.author
                    os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
                    if data == 'addon':
                        await bot.change_presence(status=discord.Status.idle, game=discord.Game(name='Sim: Waiting...'))
                        msg = 'Please paste the output of your simulationcraft addon here and finish with DONE'
                        await bot.send_message(user, msg)
                        addon_data = await bot.wait_for_message(author=message.author, check=check, timeout=60)
                        if addon_data is None:
                            await bot.send_message(message.channel, 'No data given. Resetting session.')
                            await bot.change_presence(status=discord.Status.online,
                                                      game=discord.Game(name='Sim: Ready'))
                            return
                        else:
                            addon = '%ssims/%s/%s-%s.simc' % (htmldir, char, char, timestr)
                            f = open(addon, 'w')
                            f.write(addon_data.content[:-4])
                            f.close()
                    await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Sim: In Progress'))
                    msg = '\nSimulationCraft:\nRealm: %s\nCharacter: %s\nIterations: %s\nScaling: %s\nData: %s' % (
                        realm.capitalize(), char.capitalize(), iterations, scaling.capitalize(), data.capitalize())
                    htmladdr = '%s-%s.html' % (char, timestr)
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(sim(realm, char, scale, htmladdr, data, addon, region, iterations, loop,
                                             message))


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(check_version())
    print(*version[:1], '--------------')
    await bot.change_presence(game=discord.Game(name='Simulation: Ready'))


bot.run(user_opt['server_opt'][0]['token'])