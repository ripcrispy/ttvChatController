import socket
import time
import re
import sys
import yaml
import asyncio
from pywinauto.application import Application
from pywinauto.keyboard import SendKeys

# Global defaults
retries = 3             # Number of connection attempts to Twitch IRC server before giving up
console = 'PSX'         # Console emulator used (for importing applicable button profile)
twitch_profile_file = './twitch.yaml'
mods_file = './mods.yaml'
controller_profile = './controller_profiles.yaml'
emulator_command = "./PSX/EmuHawk.exe --load-state=./PSX/PSX/State/1.State ./PSX/FinalFantasyTactics.cue"
game = emulator_command.rsplit('/', 1)[1].split('.')[0]


# Global exit function, to be called on critical errors
def close_app(error):
    print(f'[!] {error}')
    print('\n    The application will close in 5 seconds.')
    time.sleep(5)
    sys.exit()


# Load controller profile
controller = {}
try:
    with open(controller_profile) as file:
        controller = yaml.safe_load(file)
except:
    close_app('Failed to open controller profile file')

button_actions = {}     # Dictionary mapping button inputs to their corresponding actions in the game
button_points = {}      # Dictionary to keep track of the number of points for each button input
command_inputs = {}     # Dictionary mapping accepted inputs per action
mod_inputs = {}         # Dictionary mapping accepted inputs for admin commands
button_keybind = {}     # Dictionary mapping action keybinds
button_holdtime = {}    # Dictionary mapping action sleep time
for action in controller[console]['default']:
    if "description" in controller[console]['default'][action]:
        button_actions[action] = controller[console]['default'][action]['description']
    button_points[action] = 0
    command_inputs[action] = controller[console]['default'][action]['inputs']
    button_keybind[action] = controller[console]['default'][action]['keybind']
    button_holdtime[action] = controller[console]['default'][action]['holdtime'] \
        if "holdtime" in controller[console]['default'][action] \
           and isinstance(controller[console]['default'][action]['holdtime'], [int, float]) \
        else 0.1
if game in controller[console]:
    for action in controller[console]['game']:
        if "description" in controller[console]['game'][action]:
            button_actions[action] = controller[console]['game'][action]['description']
        button_points[action] = 0
        command_inputs[action] = controller[console]['game'][action]['inputs']
        button_keybind[action] = controller[console]['game'][action]['keybind']
        button_holdtime[action] = controller[console]['game'][action]['holdtime'] \
            if "holdtime" in controller[console]['game'][action] \
               and isinstance(controller[console]['game'][action]['holdtime'], [int, float]) \
            else 0.1
for action in controller[console]['mods']:
    mod_inputs[action] = controller[console]['mods'][action]['inputs']
    button_keybind[action] = controller[console]['mods'][action]['keybind']
    button_holdtime[action] = controller[console]['mods'][action]['holdtime'] \
        if "holdtime" in controller[console]['mods'][action] \
           and isinstance(controller[console]['mods'][action]['holdtime'], [int, float]) \
        else 0.1

# Load moderator list
mods = {}
try:
    with open(mods_file) as file:
        mods = yaml.safe_load(file)
except:
    close_app('Failed to open mods file')

# Load profile for connection to Twitch IRC server
twitch = {}
try:
    with open(twitch_profile_file) as file:
        twitch = yaml.safe_load(file)
except:
    close_app('Failed to open twitch profile file')

if twitch != {}:
    TWITCH_USER = twitch['user'] if 'user' in twitch and isinstance(twitch['user'], str) else ""
    TWITCH_PASS = twitch['pass'] if 'pass' in twitch and isinstance(twitch['pass'], str) else ""
    TWITCH_HOST = twitch['host'] if 'host' in twitch and isinstance(twitch['host'], str) else ""
    TWITCH_PORT = twitch['port'] if 'port' in twitch and isinstance(twitch['port'], int) else 6667
    TWITCH_CHAN = twitch['chan'] if 'chan' in twitch and isinstance(twitch['chan'], str) else ""

    if TWITCH_USER == "" or TWITCH_PASS == "" or TWITCH_HOST == "" or TWITCH_CHAN == "":
        close_app("Parameters missing in twitch profile config file")

# Connect to Twitch IRC server
print(f"[+] Opening socket to: {TWITCH_HOST}...")
for retry in range(retries):
    try:
        s = socket.socket()
        s.connect((TWITCH_HOST, TWITCH_PORT))
        s.send(f"PASS {TWITCH_PASS}\n".encode("utf-8"))
        s.send(f"NICK {TWITCH_USER}\n".encode("utf-8"))
        s.send(f"JOIN #{TWITCH_CHAN}\n".encode("utf-8"))
        print(f"[+] Twitch user authentication success!")
        break
    except:
        print("[!] Socket connection or authentication failed! Reattempting connection in 3 seconds...") \
            if retry != retries \
            else close_app("Twitch IRL connection or authentication failed!")
        time.sleep(3)
        print(f'[!] Attempt {retry + 1}')

# TO-DO: Turn this in to a useful function
print("[+] Launching Game...")
emulator_process = Application(backend="win32").start(emulator_command)
emu = emulator_process.window()
time.sleep(1)


# Function to send a message to the Twitch chat
async def send_message(message):
    try:
        s.send(f"PRIVMSG #{TWITCH_CHAN} :{message}\n".encode("utf-8"))
    except:
        print("[!] Error: Problem sending message!")


# Function to press the required button
async def press_button(action):
    try:
        print(f'{action}')
        if isinstance(button_keybind[action], str):
            emu.type_keys('{' + button_keybind[action] + ' down}')
            time.sleep(button_holdtime[action])
            emu.type_keys('{' + button_keybind[action] + ' up}')
        elif isinstance(button_keybind[action], list):
            for keybind in button_keybind[action]:
                emu.type_keys('{' + keybind + ' down}')
            time.sleep(button_holdtime[action])
            for keybind in button_keybind[action]:
                emu.type_keys('{' + keybind + ' up}')
    except:
        print("[!] Error: Emulator button press failed!")


# Function to print dictionary key value pairs to a string
def print_dict(dct):
    detail = ""
    for key, value in dct.items():
        detail += f"{key} ({value}) "
    return detail


# Function to request buffer of 2048 bytes from the socket connection
async def get_messages():
    try:
        response = s.recv(2048).decode("utf-8").split("\n")
    except:
        print("[!] Failed to receive messages.")
        return
    await asyncio.sleep(1)
    return response


async def main():
    while True:
        loop_start = time.time()
        responses = await get_messages()

        for messages in responses:
            try:
                # regex to token group Username, Channel and Message
                chat_user, chat_channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', messages).groups()
                # message must be filtered due to blank special characters
                message = ''.join(filter(str.isalnum, message)).lower()

                for action in command_inputs:
                    if message in command_inputs[action]:
                        button_points[action] += 1
                        if button_points[action] >= 1:
                            await press_button(action)
                            # await send_message(f"{chat_user} pressed: {message.upper()}")
                            button_points[action] = 0

                # Useless help message, will be removed.
                if message == "help":
                    await send_message(f"{chat_user} use the commands listed in the overlay to control the game on screen. Control commands can be shortened, for example: cross is also: press_cross, cross_button, cross, cros, cro, cr, x")
                
                # Mod commands
                if chat_user in mods['mods']:
                    for action in mod_inputs:
                        if message in mod_inputs[action]:
                            await press_button(action)
            except:
                # must be continue to repeat while loop, non usable messages cause exception.
                continue
            
        loop_end = time.time()
        print(f"[i] Time since last message: {(loop_end-loop_start):0.2f} seconds.")
        # Sleep for 0.25 seconds to avoid spamming chat
        await asyncio.sleep(0.25)

asyncio.run(main())
