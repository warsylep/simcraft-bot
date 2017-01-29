# simc-discord
SimulationCraft Bot for discord.

This is a fork of https://github.com/stokbaek/simc-discord that is ment to be used across multiple discord "servers" instead of only one.
It adds support for queuing requests, more simulationcraft options like comparing talents, maxtime and more.
Do note that this code should not be considered production ready and may contain bugs and security issues.
If you are looking at running your own bot you should use main repo, its better suited for normal usage and is tested on multiple systems.

The following things are needed to run the bot:
* Python 3.5+
* Python Discord lib: https://github.com/Rapptz/discord.py
* Webservice on the server to hand out a link to the finished simulation.
* A working version of simulationcraft
* Blizzard API key (This is needed to use armory): https://github.com/simulationcraft/simc/wiki/BattleArmoryAPI

Tested systems:
- [x] Debian 8
- [ ] Ubuntu 16.04
- [ ] RHEL 7
- [ ] Windows Server 2016
- [ ] ~~FreeBSD 11.0~~ *SimulationCraft does not build well on FreeBSD*

The output from simulationcraft can be found: `<WEBSITE>/debug/simc.sterr or simc.stout`. These files are live updated during a simulation.

Setting the `executable` in the `user_data.json` for Windows can be abit tricky.

Here is an example on how it can be done:

`"executable": "START /B C:\\Simulationcraft^(x64^)\\710-03\\simc.exe",`
* `START` makes it run in the background, this is needed to get the update icon rotating in discord
* `/B` allows output to be written to file
* `^` is windows way to escape a character. If `( )` is not escaped will it fail because it cannot find path
