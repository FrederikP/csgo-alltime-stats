# csgo-alltime-stats

Script for fetching and aggregating your matchmaking data using this official feature:

https://www.reddit.com/r/GlobalOffensive/comments/8lyzb6/so_the_steam_client_has_been_keeping_track_of/

## Security

The tool will ask you for user name, password (and 2 factor auth). The data is only used to login to the site
using a headless browser and to grab the cookie data. The code is completely open source and quite compact, so
have a look for yourself.

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

## Example output

```
player1 -> Number of Matches: 571, K/D : 1.17, Avg K: 19.36, D: 16.61, A: 4.36
player2 -> Number of Matches: 377, K/D : 1.07, Avg K: 18.58, D: 17.42, A: 5.02
player3 -> Number of Matches: 316, K/D : 1.43, Avg K: 22.96, D: 16.04, A: 4.42
player4 -> Number of Matches: 226, K/D : 0.81, Avg K: 15.27, D: 18.89, A: 4.57
player5 -> Number of Matches: 162, K/D : 0.96, Avg K: 16.06, D: 16.65, A: 3.89
player6 -> Number of Matches: 152, K/D : 0.58, Avg K: 10.48, D: 18.09, A: 3.99
player7 -> Number of Matches: 72, K/D : 0.57, Avg K: 9.85, D: 17.22, A: 2.90
player8 -> Number of Matches: 59, K/D : 0.95, Avg K: 18.71, D: 19.76, A: 3.90
player9 -> Number of Matches: 27, K/D : 0.93, Avg K: 18.59, D: 19.89, A: 4.41
player10 -> Number of Matches: 15, K/D : 0.78, Avg K: 14.47, D: 18.67, A: 4.40
```