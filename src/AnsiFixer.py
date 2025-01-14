def colorizeStr(str, color):
    return f"\033[{color}m{str}\033[0m"

# def colorizeStr(str, foreground_color, background_color):
#     return f"\033[{foreground_color};{background_color}m{str}\033[0m"

RED = "31"
GREEN = "32"
YELLOW = "33"
BLUE = "34"
MAGENTA = "35"
CYAN = "36"
WHITE = "37"

# BG_RED = "41"
# BG_GREEN = "42"
# BG_YELLOW = "43"
# BG_BLUE = "44"
# BG_MAGENTA = "45"
# BG_CYAN = "46"
# BG_WHITE = "47"