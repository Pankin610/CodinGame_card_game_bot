import numpy as np

INF = 2000000000

class Creature:
    creature_hashes = {}

    def __init__(self, id_, cost, attack, hp, can_attack = 0, side = 1):
        self.cost = cost
        self.attack = attack
        self.hp = hp
        self.side = side
        self.can_attack = can_attack
        self.id_ = id_

    def __hash__(self):
        return (self.attack, self.hp, self.side, self.can_attack).__hash__()

    def copy(self):
        return Creature(self.id_, self.cost, self.attack, self.hp, self.can_attack, self.side)

class GameState:
    player_health_hash = [list(map(int, np.random.randint(0, INF, 100))), list(map(int, np.random.randint(0, INF, 100)))]
    turn_hash = list(map(int, np.random.randint(0, INF, 2)))

    @staticmethod
    def getValue(self):
        value = (self.myHP - self.enemyHP) / 2.0
        for i in self.my_board:
            value += i.hp
            value += i.attack
        for i in self.enemy_board:
            value -= i.hp
            value -= i.attack
        return value

    def __init__(self):
        self.enemyHP, self.myHP = 30, 30
        self.my_board, self.enemy_board = [], []
        self.turn = 1
        self.hash = GameState.player_health_hash[0][30] ^ GameState.player_health_hash[1][30] ^ GameState.turn_hash[self.turn]

    def __hash__(self):
        return self.hash

    def update_hash(self):
        self.hash = GameState.player_health_hash[0][self.enemyHP] ^ GameState.player_health_hash[1][self.myHP] ^ GameState.turn_hash[self.turn]
        for i in (self.enemy_board + self.my_board):
            self.hash ^= i.__hash__()

    def attack(self, id0, id1):
        if self.turn == 1:
            id0, id1 = id1, id0
        c0, c1 = 0,0
        for i in range(len(self.enemy_board)):
            if self.enemy_board[i].id_ == id0:
                c0 = self.enemy_board[i].copy()
                del self.enemy_board[i]
                break
        for i in range(len(self.my_board)):
            if self.my_board[i].id_ == id1:
                c1 = self.my_board[i].copy()
                del self.my_board[i]
                break

        self.hash ^= c0.__hash__()
        self.hash ^= c1.__hash__()

        c0.hp -= c1.attack
        c1.hp -= c0.attack
        c1.can_attack = 0
        c0.can_attack = 0

        if c0.hp > 0:
            self.hash ^= c0.__hash__()
            self.enemy_board.append(c0)
        if c1.hp > 0:
            self.hash ^= c1.__hash__()
            self.my_board.append(c1)
    
    def attackHero(self, id_):
        creature = 0
        for i in range(len(self.enemy_board)):
            if self.enemy_board[i].id_ == id_:
                creature = self.enemy_board[i]
        for i in range(len(self.my_board)):
            if self.my_board[i].id_ == id_:
                creature = self.my_board[i]

        self.hash ^= GameState.player_health_hash[0][self.enemyHP] ^ GameState.player_health_hash[1][self.myHP]
        self.hash ^= creature.__hash__()
        creature.can_attack = 0

        if creature.side == 0:
            self.myHP -= creature.attack
        else:
            self.enemyHP -= creature.attack
        
        self.hash ^= GameState.player_health_hash[0][self.enemyHP] ^ GameState.player_health_hash[1][self.myHP]
        self.hash ^= creature.__hash__()
    
    def nextTurn(self):
        self.hash ^= GameState.turn_hash[self.turn]
        self.turn ^= 1

        for i in range(len(self.enemy_board)):
            self.enemy_board[i].can_attack = 1
        for i in range(len(self.my_board)):
            self.my_board[i].can_attack = 1

    def doStep(self, st):
        if st.is_pass:
            self.nextTurn()
            return 'PASS;'

        if st.target == -1:
            self.attackHero(st.attacker)
        else:
            self.attack(st.attacker, st.target)

        return ' '.join(['ATTACK', str(st.attacker), str(st.target), ';'])

    def copy(self):
        res = GameState()
        res.hash, res.my_board, res.enemy_board, res.myHP, res.enemyHP, res.turn = self.hash, [i.copy() for i in self.my_board], [i.copy() for i in self.enemy_board], self.myHP, self.enemyHP, self.turn
        return res

class Step:
    def __init__(self, attacker, target, is_pass=False):
        self.attacker = attacker
        self.target = target
        self.is_pass = is_pass

game_result, best_step = {}, {}

def getResult(v):
    if v in game_result:
        return game_result[v]

    if v.myHP <= 0:
        game_result[v] = -INF
        best_step[v] = Step(-1, -1, True)
        return game_result[v]
    if v.enemyHP <= 0:
        game_result[v] = INF
        best_step[v] = Step(-1, -1, True)
        return game_result[v]

    if len(v.enemy_board) == 0 or len(v.my_board) == 0:
        game_result[v] = GameState.getValue(v)
        best_step[v] = Step(-1, -1, True)
        return game_result[v]

    func,mb,eb = 0,0,0

    if v.turn == 0:
        game_result[v] = INF
        func = lambda x, y : x > y
        mb = v.enemy_board
        eb = v.my_board
    else:
        game_result[v] = -INF
        func = lambda x, y : x < y
        mb = v.my_board
        eb = v.enemy_board
        
    can_do = False

    for i in mb:
        if i.can_attack == 0:
            continue
        can_do = True

        new_game = v.copy()
        new_game.attackHero(i.id_)
        if func(game_result[v], getResult(new_game)):
            game_result[v] = getResult(new_game)
            best_step[v] = Step(i.id_, -1)
        for j in eb:
            new_game = v.copy()
            new_game.attack(i.id_, j.id_)
            if func(game_result[v], getResult(new_game)):
                game_result[v] = getResult(new_game)    
                best_step[v] = Step(i.id_, j.id_)
        
    if not can_do:
        new_game = v.copy()
        new_game.nextTurn()
        if func(game_result[v], getResult(new_game)):
            game_result[v] = getResult(new_game)
            best_step[v] = Step(-1, -1, True)

    return game_result[v]

def get_int(x):
    try:
        return int(x)
    except:
        return x

turns = 0
while True:
    game_result, best_step = {}, {}
    game = GameState()
    u = 0

    inp = input().split()
    game.myHP = int(inp[0])
    mana = int(inp[1])
    inp = input().split()
    game.enemyHP = int(inp[0])

    for i in range(int(input().split()[1])):
        input()
    
    cardCount = int(input())
    my_cards, enemy_cards, hand = [], [], []

    for i in range(cardCount):
        cardNumber, instanceId, location, cardType, cost, attack, defense, abilities, myhealthChange, opponentHealthChange, cardDraw = list(map(get_int, input().split()))
        if location == 1:
            my_cards.append(Creature(instanceId, cost, attack, defense, int(location == 1)))
        elif location == -1:
            enemy_cards.append(Creature(instanceId, cost, attack, defense, int(location == 1)))
        else:
            hand.append(Creature(instanceId, cost, attack, defense, int(location == 1)))
    


    if turns < 30:
        print('PICK', np.random.randint(0, 3))
        turns += 1
    else:
        s = ''
        game.enemy_board = enemy_cards
        game.my_board = my_cards
        game.update_hash()

        if len(game.enemy_board) == 0:
            for i in game.my_board:
                s += game.doStep(Step(i.id_, -1))

        while True:
            getResult(game)
            if best_step[game].is_pass:
                break

            s += game.doStep(best_step[game])

        for i in hand:
            if mana >= i.cost:
                s += 'SUMMON ' + str(i.id_) + ';'
                mana -= i.cost

        print(s)
            






