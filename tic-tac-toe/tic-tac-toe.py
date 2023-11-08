# Running in host-mode:
#
# In one terminal for docker machine: 
#   docker compose -f ../docker-compose.yml -f ./docker-compose.override.yml -f ../docker-compose-host.yml up
#
# another terminal for back-end:
#   python3 -m venv .venv
#   . .venv/bin/activate
#   pip install -r requirements.txt
#   ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004" python3 tic-tac-toe.py
#
# Another terminal for front-end:
#   sudo yarn
#   sudo yarn build
#   yarn start input send --payload '0x2329840, 0, 0'
#
# To stop the Application:
#   docker compose -f ../docker-compose.yml -f ./docker-compose.override.yml down -v

from os import environ
import logging
import requests
import json

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()

games = {} # {game_key: {board: [], turn: 0, games_count: 1, player_turn: address_current, address_current: 0, address_opponent: 0}

initial_board = [
        ['', '', ''],
        ['', '', ''],
        ['', '', '']
    ]

def handle_advance(data):
    logger.info(f"Handling advance request data {data}")

    notice = {"payload": data["payload"]}
    response = requests.post(rollup_server + "/notice", json=notice)
    logger.info(f"Received notice status {response.status_code} body {response.content}")
    address_current = data["metadata"]["msg_sender"]
        
    address_opponent, row, col = hex2str(data['payload']).split(',')

    logger.info(f'address_opponent: {address_opponent}, address_current: {address_current}, row: {row} and col: {col}')
    
    game_key = get_game_key(address_current, address_opponent)

    if game_key not in games:
        games[game_key] = {'board': initial_board, 'turn': 0, 'games_count': 1, 'player_turn': address_current, address_current: 0, address_opponent: 0}

    logger.info(f'\nGames before play: {games}')

    # if games[game_key]['player_turn'] != None and games[game_key]['player_turn'] != address_current:
    #     return "reject"
    
    # logger.info(f'\nGames after turn check: {games}')

    make_play(game_key, int(row), int(col))

    logger.info(f'\nGames after make play: {games}')

    if check_winner(games[game_key]['board']):
        games[game_key]['games_count'] += 1
        games[game_key]['board'] = [['', '', ''],['', '', ''],['', '', '']]
        games[game_key]['turn'] = 0
        games[game_key]['player_turn'] = None
        games[game_key][address_current] += 1
        logger.info(f"Victory!! Player {address_current} Wins!! That makes it {games[game_key][address_current]} x {games[game_key][address_opponent]}")
        logger.info(f'Games after win: {games}')
        return "accept"
    
    elif check_winner(games[game_key]['board']) == 'Tie':
        games[game_key]['games_count'] += 1
        games[game_key]['board'] = [['', '', ''],['', '', ''],['', '', '']]
        games[game_key]['turn'] = 0
        games[game_key]['player_turn'] = None
        logger.info(f"It's a Tie!! Both players keep their scores.")
        logger.info(f'Games after win: {games}')
        return "accept"
        
    games[game_key]['player_turn'] = address_opponent

    logger.info(f'\nGames after check winner: {games}')

    return "accept"


def get_game_key(address_current, address_opponent):
    address_current = address_current.lower()
    address_opponent = address_opponent.lower()

    if address_current < address_opponent:
        player1 = address_current
        player2 = address_opponent
    else:
        player1 = address_opponent
        player2 = address_current

    game_key = f"{player1}-{player2}"

    return game_key

def make_play(game_key, row, col):
    
    if games[game_key]['turn'] % 2 != 0:
        play = 'O'
    else:
        play = 'X'

    board = games[game_key]['board']
    board[row][col] = play

    games[game_key]['board'] = board
    games[game_key]['turn'] += 1


def check_winner(board):
    # Check for a win
    if (
        board[0][0] == board[0][1] == board[0][2] == 'O' or
        board[0][0] == board[0][1] == board[0][2] == 'X' or
        board[1][0] == board[1][1] == board[1][2] == 'O' or
        board[1][0] == board[1][1] == board[1][2] == 'X' or
        board[2][0] == board[2][1] == board[2][2] == 'O' or
        board[2][0] == board[2][1] == board[2][2] == 'X' or
        board[0][0] == board[1][0] == board[2][0] == 'O' or
        board[0][0] == board[1][0] == board[2][0] == 'X' or
        board[0][1] == board[1][1] == board[2][1] == 'O' or
        board[0][1] == board[1][1] == board[2][1] == 'X' or
        board[0][2] == board[1][2] == board[2][2] == 'O' or
        board[0][2] == board[1][2] == board[2][2] == 'X' or
        board[0][0] == board[1][1] == board[2][2] == 'O' or
        board[0][0] == board[1][1] == board[2][2] == 'X' or
        board[0][2] == board[1][1] == board[2][0] == 'O' or
        board[0][2] == board[1][1] == board[2][0] == 'X'
    ):
        return True
    # Check for a tie
    for row in board:
        for cell in row:
            if cell != 'O' and cell != 'X':
                return False  # If any cell is empty, the game is not a tie
    return 'Tie'  # All cells are filled, and no player has won, indicating a tie

# 1 payload: 0x2329840, 0, 0
# 2 payload: 0x1111111, 0, 1


def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    logger.info("Adding report")
    logger.info(f'data payload: {hex2str(data["payload"])}')
    address_current, address_opponent = hex2str(data['payload']).split(',')
    game_key = get_game_key(address_current, address_opponent)
    
    if games[game_key]['player_turn'] == None:
        if games[game_key][address_current] > games[game_key][address_opponent]:
            report = {"payload": str2hex(f'Victory! Player {address_current} has won!! Its now {games[game_key][address_current]} x {games[game_key][address_opponent]}')}
        else:
            report = {"payload": str2hex(f'Victory! Player {address_opponent} has won!! Its now {games[game_key][address_current]} x {games[game_key][address_opponent]}')}
    
    report = {"payload": str2hex(f'Welcome to Tic Tac Toe!\nGame Key: {games[game_key]}\n\nBoard: {games[game_key]["board"]}\n\nPlayer Turn: {games[game_key]["player_turn"]}')}
    response = requests.post(rollup_server + "/report", json=report)
    logger.info(f"Received report status {response.status_code}")

    return "accept"


handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}
rollup_address = None


while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])
