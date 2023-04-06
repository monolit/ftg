import inspect
import logging
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Provides this help message"""
    strings = {"name": "Help",
               "bad_module": "<b>Invalid module name specified</b>",
               "single_mod_header": "<b>Help for</b> <u>{}</u>:",
               "single_cmd": "\n• <code><u>{}</u></code>\n",
               "undoc_cmd": "No docs",
               "all_header": "<b>Prefix:<code>{pref}</code>\nAvailable FTG Modules:</b>",
               "mod_tmpl": "\n• <b>{}</b>",
               "cmd_tmpl": " <code>{}</code> "}

    @loader.unrestricted
    async def helpcmd(self, message):
        """.help [module]"""
        args = utils.get_args_raw(message)
        pref = self.db.get('friendly-telegram.main', 'command_prefix', ['.'])[0]
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.strings("name", message).lower() == args.lower():
                    module = mod
            if module is None:
                return await utils.answer(message, self.strings["bad_module"])
            commands = {name: func for name, func in module.commands.items()
                        if await self.allmodules.check_security(message, func)}
            if not commands:
                return await utils.answer(message, self.strings["undoc_cmd"])
            # Translate the format specification and the module separately
            try:
                name = module.strings("name", message)
            except KeyError:
                name = getattr(module, "name", "ERROR")
            reply = self.strings["single_mod_header"].format(utils.escape_html(name))
            if module.__doc__:
                reply += "\n" + "\n".join("  " + t for t in utils.escape_html(inspect.getdoc(module)).split("\n"))
            else:
                logger.warning("Module %s is missing docstring!", module)
            for name, fun in commands.items():
                reply += self.strings["single_cmd"].format(name)
                if fun.__doc__:
                    reply += utils.escape_html("\n".join("  " + t for t in inspect.getdoc(fun).split("\n")))
                else:
                    reply += self.strings["undoc_cmd"]
        else:
            reply = self.strings["all_header"].format(pref=pref)
            for mod in self.allmodules.modules:
                try:
                    name = mod.strings("name", message)
                except KeyError:
                    name = getattr(mod, "name", "ERROR")
                if name not in [
                    "Logger",
                    "Raphielgang Configuration Placeholder",
                    "Uniborg configuration placeholder",
                ]:
                    _temp = self.strings["mod_tmpl"].format(name)
                    first = True
                    commands = [name for name, func in mod.commands.items()
                                if await self.allmodules.check_security(message, func)]
                    if not commands:
                        continue
                    reply += _temp
                    for cmd in commands:
                        reply += self.strings["cmd_tmpl"].format(cmd)
        await utils.answer(message, reply)


    async def client_ready(self, client, db):
        self.client = client
        self.is_bot = await client.is_bot()
        self.db = db


    async def hcmd(self, message):
        """.h [module]"""
        args = utils.get_args_raw(message)
        reply = f'mods count:\t{len(self.allmodules.modules)}\n'
        pref = self.db.get('friendly-telegram.main', 'command_prefix', ['.'])[0]
        for mod in self.allmodules.modules:
            commands = [pref + name for name, func in mod.commands.items()
                        if await self.allmodules.check_security(message, func)]
            reply += ' || '.join(
                [self.strings["cmd_tmpl"].format(cmd) for cmd in commands]
                )

        await utils.answer(message, reply)