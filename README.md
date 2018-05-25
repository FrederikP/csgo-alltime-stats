# csgo-alltime-stats

Script for fetching and aggregating your matchmaking data using this official feature:

https://www.reddit.com/r/GlobalOffensive/comments/8lyzb6/so_the_steam_client_has_been_keeping_track_of/

## Requirements

- Python + pip + virtualenv are installed
- Chrome browser is installed

## Installation

Clone this repository.

On Linux go to projects folder and run

`./install.sh`

The script will download selenium web driver for chrome, setup virtualenv and and install required packages

On mac you can replace the platform with mac64. On windows you can use win32 and cygwin/mingw or write your own .bat
On Windows you can also try WSFL.

## Usage

`python fetch_stats.py`

Enter user name password and steam guardtwo factor code or email auth code.

Raw stats will be in playerscores.json

`python aggregate_stats.py`

Will show a simple overview of the 10 players with most matches (you (and your friends)).
**This is very much work in progress**