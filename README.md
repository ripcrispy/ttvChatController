# ttvChatController

This Python script allows you to control an emulator using commands typed in Twitch TV Chat. You can define which buttons on the emulator's controller correspond to which chat commands using the `controller_profiles.yaml` file, and you can specify which Twitch users have moderator privileges to control the emulator using the `mods.yaml` file.

## Requirements

- Python 3.x
- Twitch API credentials
- Emulator software

## Installation

1. Clone or download this repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt`.
3. Edit the `mods.yaml` file to specify the Twitch usernames of the users who have moderator privileges over the emulator.
4. Edit the `controller_profiles.yaml` file to define the mapping between chat commands and emulator controller buttons.
5. Set up your Twitch API credentials in `twitch.yaml`.
6. Edit `main.py` with your Emulator run command. For example (line 16 of main.py): `emulator_command = "./PSX/EmuHawk.exe --load-state=./PSX/PSX/State/1.State ./PSX/FinalFantasyTactics.cue"`
7. Edit `main.py` with your prefered console setting (matching controller_profiles.yaml). For example on line 12: `console = 'PSX'`

## Usage

1. Run the script by typing `python main.py`.
2. In your Twitch chat, type one of the chat commands defined in the `controller_profiles.yaml` file to control the emulator.

## Configuration

### `mods.yaml`

This file contains a list of Twitch usernames who have moderator privileges to control the emulator's load/save states. Add or remove usernames as needed.

### `twitch.yaml`

This file contains your Twitch TV API credentials and channel name that this chat bot will be applied to, it's best to use separate account to your Twitch account for this as it is considered a bot.

### `controller_profiles.yaml`

This file contains chat mappings for actions that will be called upon the emulator. The file currently has bindings for PSX. This is set in `main.py` on line 12 `console = 'PSX'`

