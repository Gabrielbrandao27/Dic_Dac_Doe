# Project for TCC00274 - TÓPICOS EM REDES DE COMPUTADORES I course from UFF RJ

How to run in Host-mode:

-> In one terminal for docker machine:<br>
    cd Dic_Dac_Doe/tic-tac-toe<br>
    docker compose -f ../docker-compose.yml -f ./docker-compose.override.yml -f ../docker-compose-host.yml up<br>

-> Another terminal for back-end:<br>
    cd Dic_Dac_Doe/tic-tac-toe<br>
    python3 -m venv .venv<br>
    . .venv/bin/activate<br>
    pip install -r requirements.txt<br>
    ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004" python3 tic-tac-toe.py<br>

-> Another terminal for front-end:<br>
    cd Dic_Dac_Doe/frontend-console<br>
    sudo yarn<br>
    sudo yarn build

    - To make move as player 1:
    yarn start input send --payload '0x70997970C51812dc3A010C7d01b50e0d17dc79C8,0,0'

    - To make move as player 2:
    yarn start input send --payload '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266,0,1' --accountIndex '1'

    - For game status:
    yarn start inspect --payload 'status,0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266,0x70997970C51812dc3A010C7d01b50e0d17dc79C8'

    - For your game-keys:
    yarn start inspect --payload 'game-key,0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

-> To stop the Application:<br>
    docker compose -f ../docker-compose.yml -f ./docker-compose.override.yml down -v


-> Extra address for multiple games:<br>
    0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC -> use accountIndex '2'