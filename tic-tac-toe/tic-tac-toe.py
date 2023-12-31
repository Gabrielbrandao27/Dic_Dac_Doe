from os import environ
import logging
import requests

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


games = {}  # {game_key: {board: [], turn: 0, games_count: 1, player_turn: address_current, address_current: 0, address_opponent: 0}


def handle_advance(data):
    logger.info(f"Handling advance request data {data}")
    notice = {"payload": data["payload"]}
    response = requests.post(rollup_server + "/notice", json=notice)
    logger.info(
        f"Received notice status {response.status_code} body {response.content}"
    )
    address_current = data["metadata"]["msg_sender"].lower()

    address_opponent, row, col = hex2str(data["payload"]).split(",")

    address_opponent = address_opponent.lower()

    if address_current == address_opponent:
        logger.info(f"Can't start a game with yourself!")
        return "reject"
    game_key = get_game_key(address_current, address_opponent)

    if game_key not in games:
        games[game_key] = {
            "board": [["", "", ""], ["", "", ""], ["", "", ""]],
            "turn": 0,
            "games_count": 1,
            "player_turn": address_current,
            address_current: 0,
            address_opponent: 0,
        }

    if make_play(game_key, address_current, int(row), int(col)) != "reject":

        if check_winner(games[game_key]["board"]) == "winner":
            games[game_key]["games_count"] += 1
            games[game_key]["board"] = [["", "", ""], ["", "", ""], ["", "", ""]]
            games[game_key]["turn"] = 0
            games[game_key]["player_turn"] = None
            games[game_key][address_current] += 1
            logger.info(
                f"Victory!! Player {address_current} Wins!! That makes it {games[game_key][address_current]} x {games[game_key][address_opponent]}"
            )
            logger.info(f"Games after win: {games}")
            return "accept"

        elif check_winner(games[game_key]["board"]) == "tie":
            games[game_key]["games_count"] += 1
            games[game_key]["board"] = [["", "", ""], ["", "", ""], ["", "", ""]]
            games[game_key]["turn"] = 0
            games[game_key]["player_turn"] = None
            logger.info(f"It's a Tie!! Both players keep their scores.")
            logger.info(f"Games after draw: {games}")
            return "accept"

        games[game_key]["player_turn"] = address_opponent

        return "accept"
    else:
        return "reject"


def get_game_key(address_current, address_opponent):
    if address_current < address_opponent:
        player1 = address_current
        player2 = address_opponent
    else:
        player1 = address_opponent
        player2 = address_current

    game_key = f"{player1}-{player2}"

    return game_key


def make_play(game_key, address_current, row, col):
    board = games[game_key]["board"]

    if games[game_key]["player_turn"] != address_current:
        logger.info(f"Not this player's turn!!")
        return "reject"

    else:
        if board[row][col] == "":
            if games[game_key]["turn"] % 2 != 0:
                play = "O"
            else:
                play = "X"

            board[row][col] = play

            games[game_key]["board"] = board
            games[game_key]["turn"] += 1
        else:
            logger.info(f"Slot already taken! Choose a new one!")
            return "reject"


def check_winner(board):
    # Check for a win
    if (
        board[0][0] == board[0][1] == board[0][2] == "O"
        or board[0][0] == board[0][1] == board[0][2] == "X"
        or board[1][0] == board[1][1] == board[1][2] == "O"
        or board[1][0] == board[1][1] == board[1][2] == "X"
        or board[2][0] == board[2][1] == board[2][2] == "O"
        or board[2][0] == board[2][1] == board[2][2] == "X"
        or board[0][0] == board[1][0] == board[2][0] == "O"
        or board[0][0] == board[1][0] == board[2][0] == "X"
        or board[0][1] == board[1][1] == board[2][1] == "O"
        or board[0][1] == board[1][1] == board[2][1] == "X"
        or board[0][2] == board[1][2] == board[2][2] == "O"
        or board[0][2] == board[1][2] == board[2][2] == "X"
        or board[0][0] == board[1][1] == board[2][2] == "O"
        or board[0][0] == board[1][1] == board[2][2] == "X"
        or board[0][2] == board[1][1] == board[2][0] == "O"
        or board[0][2] == board[1][1] == board[2][0] == "X"
    ):
        return "winner"
    # Check for a tie
    for row in board:
        for cell in row:
            if cell != "O" and cell != "X":
                return False  # If any cell is empty, the game is not a tie
    return "tie"  # All cells are filled, and no player has won, indicating a tie


def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    logger.info("Adding report")
    payload = hex2str(data["payload"])
    logger.info(f"data payload: {payload}")

    inputs = []
    inputs = payload.split(",")

    if inputs[0] == "status":
        address_current = inputs[1].lower()
        address_opponent = inputs[2].lower()

        game_key = get_game_key(address_current, address_opponent)

        if game_key in games:
            board = "\n".join(
                [
                    " | ".join([" " if cell == "" else cell for cell in row])
                    for row in games[game_key]["board"]
                ]
            )

            if games[game_key]["turn"] == 1:
                report = {
                    "payload": str2hex(
                        f'\n\nWelcome to Dic Dac Doe!\n\nGame Key: {games[game_key]}\n\nBoard:\n{board}\n\nPlayer Turn: {games[game_key]["player_turn"]}\n'
                    )
                }

            elif games[game_key]["player_turn"] == None:
                report = {
                    "payload": str2hex(
                        f"\n\nThe match has ended. Start a new one.\n\n{board}\n\nScores: {address_current} {games[game_key][address_current]} x {games[game_key][address_opponent]} {address_opponent}\n"
                    )
                }

            else:
                report = {
                    "payload": str2hex(
                        f'\n\nMatch underway!\n\nGame Key: {games[game_key]}\n\nBoard:\n{board}\n\nPlayer Turn: {games[game_key]["player_turn"]}\n'
                    )
                }
        else:
            report = {
                "payload": str2hex(
                    f'\n\nGame does not exist!! Make a move with "yarn start input send --payload "<oponent_address>,<row>,<col>""\nTo start playing.\n'
                )
            }

    elif inputs[0] == "game-key":
        games_list = []
        for game in games:
            if inputs[1].lower() in game:
                games_list.append(game)

        report = {"payload": str2hex(f"\n\nYour Game-Keys: {games_list}")}

    else:
        report = {
            "payload": str2hex(
                f'\n\nInput does not match any case. Try "status,<game-key>" for game status.\nTry "game-key,<your-address>" for your game-keys.\n'
            )
        }

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
