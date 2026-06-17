from mapres.datamap import datamap, syntax

@datamap(syntax=syntax.angles) # produces <>
class ColorMap:
    black: str = '\033[30m'
    dark_blue: str = '\033[34m'
    dark_green: str = '\033[32m'
    dark_aqua: str = '\033[36m'
    dark_red: str = '\033[31m'
    dark_purple: str = '\033[35m'
    gold: str = '\033[33m'
    gray: str = '\033[37m'
    dark_gray: str = '\033[90m'
    blue: str = '\033[94m'
    green: str = '\033[92m'
    aqua: str = '\033[96m'
    red: str = '\033[91m'
    light_purple: str = '\033[95m'
    yellow: str = '\033[93m'
    white: str = '\033[97m'
    reset: str = '\033[0m'
    bold: str = '\033[1m'
    italic: str = '\033[3m'

    def as_dict(self):
        return {f'<{k}>': getattr(self, k) for k in self.__dataclass_fields__}

# ASCII color map
ascii_colors = ColorMap()

# Minecraft color map
mc_colors = ColorMap(
    black='§0',
    dark_blue='§1',
    dark_green='§2',
    dark_aqua='§3',
    dark_red='§4',
    dark_purple='§5',
    gold='§6',
    gray='§7',
    dark_gray='§8',
    blue='§9',
    green='§a',
    aqua='§b',
    red='§c',
    light_purple='§d',
    yellow='§e',
    white='§f',
    reset='§r',
    bold='§l',
    italic='§o'
)

# Color strip map
strip_colors = ColorMap(
    black='',
    dark_blue='',
    dark_green='',
    dark_aqua='',
    dark_red='',
    dark_purple='',
    gold='',
    gray='',
    dark_gray='',
    blue='',
    green='',
    aqua='',
    red='',
    light_purple='',
    yellow='',
    white='',
    reset='',
    bold='',
    italic=''
)