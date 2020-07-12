import numpy as np

INF = 2000000000
mx_step = 10000
one_turn = False

class Creature:
    creature_hashes = {}

    def __init__(self, type_, id_, cost, attack, hp, abilities, cardDraw,  myhealthChange, opponentHealthChange, can_attack = 0, side = 1):
        self.type_ = type_
        self.cost = cost
        self.attack = attack
        self.hp = hp
        self.side = side
        self.can_attack = can_attack
        self.id_ = id_
        self.abilities = abilities
        self.cardDraw = cardDraw
        self.myhealthChange = myhealthChange
        self.opponentHealthChange = opponentHealthChange

    def __hash__(self):
        return (self.attack, self.hp, self.side, self.abilities, self.can_attack).__hash__()

    def copy(self):
        return Creature(self.type_, self.id_, self.cost, self.attack, self.hp, self.abilities, self.cardDraw, self.myhealthChange, self.opponentHealthChange, self.can_attack, self.side)

    def deal_damage(self, x):
        if x == 0:
            return
        for i in range(6):
            if self.abilities[i] == 'W':
                self.abilities = self.abilities[:i] + '-' + self.abilities[i + 1:]
                return
        self.hp -= x

    def castSpell(self, spell, red):
        for i in range(6):
            if self.abilities[i] == '-':
                self.abilities = self.abilities[:i] + spell.abilities[i] + self.abilities[i + 1:]
            if red and spell.abilities[i] != '-':
                self.abilities = self.abilities[:i] + '-' + self.abilities[i + 1:]

        self.attack += spell.attack
        self.deal_damage(-spell.hp)

    def getValue(self, with_attack = False):
        if self.hp <= 0:
            return 0
        result = self.hp + 0.5 + self.attack
        if 'W' in self.abilities:
            result += 1.0
            if self.attack > 4:
                result += 0.2
        if 'G' in self.abilities:
            result += 0.5
            if self.hp > 4:
                result += 0.2
        if 'L' in self.abilities:
            result += 2.0
        if self.can_attack * with_attack:
            result += 1.0

        return result * 100.0

class GameState:
    player_health_hash = [list(map(int, np.random.randint(0, INF, 100))), list(map(int, np.random.randint(0, INF, 100)))]
    turn_hash = list(map(int, np.random.randint(0, INF, 2)))

    def __eq__(self, other):
        return self.hash == other.hash
    def __ne__(self, other):
        return self.hash != other.hash

    @staticmethod
    def getValue(self):
        value = (-(100 - self.myHP)**1.15 + (100 - self.enemyHP)**1.15)
        for i in self.my_board:
            value += i.getValue()
        for i in self.enemy_board:
            value -= i.getValue()
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

    def summon(self, minion):
        self.hash ^= minion.__hash__()
        self.hash ^= GameState.player_health_hash[0][self.enemyHP] ^ GameState.player_health_hash[1][self.myHP] ^ GameState.turn_hash[self.turn]

        self.enemyHP += minion.opponentHealthChange
        self.myHP += minion.myhealthChange

        self.hash ^= GameState.player_health_hash[0][self.enemyHP] ^ GameState.player_health_hash[1][self.myHP] ^ GameState.turn_hash[self.turn]

        self.my_board.append(minion)

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

        if not 'L' in c1.abilities:
            c0.deal_damage(c1.attack)
        else:
            c0.deal_damage(INF)

        if not 'L' in c0.abilities:
            c1.deal_damage(c0.attack)
        else:
            c1.deal_damage(INF)

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

    def castSpell(self, spell, id_target, red = False):
        creature = Creature(-INF, -INF, -INF, -INF, -INF, -INF, 0, 0, 0, '------')
        for i in range(len(self.enemy_board)):
            if self.enemy_board[i].id_ == id_target:
                creature = self.enemy_board[i]
                del self.enemy_board[i]
                break
        for i in range(len(self.my_board)):
            if self.my_board[i].id_ == id_target:
                creature = self.my_board[i]
                del self.my_board[i]
                break
        
        self.hash ^= creature.__hash__()
        creature.castSpell(spell, red)
        

        if creature.hp > 0:
            if creature.side == 0:
                self.enemy_board.append(creature)
            else:
                self.my_board.append(creature)
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

def hasTaunt(board):
    for i in board:
        if 'G' in i.abilities:
            return True
    return False

def getResult(v, alpha, beta):
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
        best_step[v] = Step(-1, -1, True)
        func = lambda x, y : x > y
        mb = [i.copy() for i in v.enemy_board]
        eb = [i.copy() for i in v.my_board]
    else:
        game_result[v] = -INF
        best_step[v] = Step(-1, -1, True)
        func = lambda x, y : x < y
        mb = [i.copy() for i in v.my_board]
        eb = [i.copy() for i in v.enemy_board]
        
    can_do = False
    steps = 0

    for i in mb:
        if i.can_attack == 0 or i.attack == 0:
            continue
        if alpha >= beta or steps >= mx_step:
            return game_result[v]

        new_game = 0

        for j in eb:
            if (not 'G' in j.abilities) and hasTaunt(eb):
                continue
            if alpha >= beta or steps >= mx_step:
                return game_result[v]
            can_do = True
            steps += 1
            new_game = v.copy()
            new_game.attack(i.id_, j.id_)
            if func(game_result[v], getResult(new_game, alpha, beta)):
                game_result[v] = getResult(new_game, alpha, beta)    
                best_step[v] = Step(i.id_, j.id_)
                if v.turn == 1:
                    alpha = max(alpha, game_result[v])
                else:
                    beta = min(beta, game_result[v])

        if not hasTaunt(eb) and steps < mx_step:
            can_do = True
            steps += 1
            new_game = v.copy()
            new_game.attackHero(i.id_)
            if func(game_result[v], getResult(new_game, alpha, beta)):
                game_result[v] = getResult(new_game, alpha, beta)
                best_step[v] = Step(i.id_, -1)
                if v.turn == 1:
                    alpha = max(alpha, game_result[v])
                else:
                    beta = min(beta, game_result[v])
            
        
    if not can_do:
        if one_turn:
            game_result[v] = GameState.getValue(v)
            best_step[v] = Step(-1, -1, True)
            return game_result[v]
        new_game = v.copy()
        new_game.nextTurn()
        game_result[v] = getResult(new_game, alpha, beta)
        best_step[v] = Step(-1, -1, True)

    return game_result[v]

def get_int(x):
    try:
        return int(x)
    except:
        return x

def get_id_least_value(board, spell, red = False):
    gain = 0
    res_id = -1

    for i in board:
        creature = i.copy()
        cur_gain = -creature.getValue()
        creature.castSpell(spell, red)
        cur_gain += creature.getValue(1)

        if cur_gain < gain:
            gain = cur_gain
            res_id = i.id_

    return res_id

def get_id_most_value(board, spell, red = False):
    gain = 0
    res_id = -1

    for i in board:
        creature = i.copy()
        cur_gain = -creature.getValue()
        creature.castSpell(spell, red)
        cur_gain += creature.getValue(1)

        if cur_gain > gain:
            gain = cur_gain
            res_id = i.id_

    return res_id

def makeTheMostValuePlay(game, hand, mana):
    best_val = GameState.getValue(game)
    best_mask = 0
    s = ''

    for mask in range(1<<len(hand)):
        manasum = 0
        cardDraw = 0
        myhealthChange, opponentHealthChange = 0, 0
        value_add = 0
        minion_count = 0

        for i in range(len(hand)):
            if (mask>>i)&1:
                manasum += hand[i].cost
                cardDraw += hand[i].cardDraw
                myhealthChange += hand[i].myhealthChange
                opponentHealthChange += hand[i].opponentHealthChange
                minion_count += (hand[i].type_ == 0)
        
        if manasum > mana or minion_count + len(game.my_board) > 6:
            continue
        manasum = 0

        new_game = game.copy()
        value_add += cardDraw * 1.5

        for i in range(len(hand)):
            if ((mask>>i)&1) == 1 and hand[i].type_ == 0:
                new_game.summon(hand[i])
                manasum += hand[i].cost
        for i in range(len(hand)):
            if ((mask>>i)&1) == 1 and hand[i].type_ != 0:
                if hand[i].type_ == 3 and hand[i].hp == 0:
                    continue
                if hand[i].type_ == 3:
                    if hand[i].hp < 0:
                        hand[i].type_ = 2
                    else:
                        hand[i].type_ = 1
                
                if hand[i].type_ == 1:
                    if get_id_most_value(new_game.my_board, hand[i]) != -1:
                        new_game.castSpell(hand[i], get_id_most_value(new_game.my_board, hand[i]))
                else:
                    if get_id_least_value(new_game.enemy_board, hand[i], True) != -1:
                        new_game.castSpell(hand[i], get_id_least_value(new_game.enemy_board, hand[i], True), True)
        if GameState.getValue(new_game) + value_add > best_val:
            best_val = GameState.getValue(new_game) + value_add
            best_mask = mask

    manasum = 0    
    mask = best_mask    
    for i in range(len(hand)):
        if ((mask>>i)&1) == 1 and hand[i].type_ == 0:
            game.summon(hand[i])
            manasum += hand[i].cost
            s += ' '.join(['SUMMON', str(hand[i].id_), ';'])
    for i in range(len(hand)):
        if ((mask>>i)&1) == 1 and hand[i].type_ != 0:
            if hand[i].type_ == 3 and hand[i].hp == 0:
                continue
            if hand[i].type_ == 3:
                if hand[i].hp < 0:
                    hand[i].type_ = 2
                else:
                    hand[i].type_ = 1
                
            if hand[i].type_ == 1:
                if get_id_most_value(game.my_board, hand[i]) != -1:
                    s += ' '.join(['USE', str(hand[i].id_), str(get_id_most_value(game.my_board, hand[i])), ';'])
                    game.castSpell(hand[i], get_id_most_value(game.my_board, hand[i]))
                    manasum += hand[i].cost
            else:
                if get_id_least_value(game.enemy_board, hand[i], True) != -1:
                    s += ' '.join(['USE', str(hand[i].id_), str(get_id_least_value(game.enemy_board, hand[i], True)), ';'])
                    game.castSpell(hand[i], get_id_least_value(game.enemy_board, hand[i], True), True)
                    manasum += hand[i].cost

    nhand = []
    for i in range(len(hand)):
        if ((mask>>i)&1) == 0:
            nhand.append(hand[i])
    hand[:] = nhand
    
    return (manasum, s)
    
    
            
        


############################################################################

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
            my_cards.append(Creature(cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange,  int(location == 1 or 'C' in abilities)))
        elif location == -1:
            enemy_cards.append(Creature(cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange, int(location == 1 or 'C' in abilities)))
        else:
            hand.append(Creature(cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange, int(location == 1 or 'C' in abilities)))
    


    if turns < 30:
        print('PICK', np.random.randint(0, 3))
        turns += 1
    else:
        s = ''
        game.enemy_board = enemy_cards
        game.my_board = my_cards
        game.update_hash()
        
        result = makeTheMostValuePlay(game, hand, mana)
        mana -= result[0]
        s += result[1]

        if len(game.enemy_board) == 0:
            for i in game.my_board:
                s += game.doStep(Step(i.id_, -1))

        if len(game.enemy_board) * len(game.my_board) > 10:
            one_turn = True
        else:
            one_turn = False

        while True:
            getResult(game.copy(), -INF - 5, INF + 5)
            if best_step[game].is_pass or game_result[game] < GameState.getValue(game):
                break

            s += game.doStep(best_step[game])

        result = makeTheMostValuePlay(game, hand, mana)
        mana -= result[0]
        s += result[1]

        while True:
            getResult(game.copy(), -INF - 5, INF + 5)
            if best_step[game].is_pass or game_result[game] < GameState.getValue(game):
                break

            s += game.doStep(best_step[game])

        for i in game.my_board:
            s += ' '.join(['ATTACK', str(i.id_), str(-1), ';'])

        print(s)
            






