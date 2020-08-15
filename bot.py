import numpy as np
import math
import sys
import heapq
import time

INF = 2000000000
BIG_INF = 2000000000000000000
mx_step = 10000
one_turn = False

class Card:
    def __init__(self, num, type_, id_, cost, attack, hp, abilities, cardDraw,  myhealthChange, opponentHealthChange, side, can_attack = 0):
        self.type_ = type_
        self.cost = cost
        self.attack = attack
        self.hp = hp
        self.can_attack = can_attack
        self.id_ = id_
        self.abilities = abilities
        self.cardDraw = cardDraw
        self.myhealthChange = myhealthChange
        self.opponentHealthChange = opponentHealthChange
        self.side = side
        self.num = num

    def __eq__(self, other):
        return self.id_ == other.id_

    def __hash__(self):
        return (self.num, self.type_, self.id_, self.cost, self.attack, self.hp, self.abilities, self.cardDraw, self.myhealthChange, self.opponentHealthChange, self.side, self.can_attack).__hash__()

    def copy(self):
        return Card(self.num, self.type_, self.id_, self.cost, self.attack, self.hp, self.abilities, self.cardDraw, self.myhealthChange, self.opponentHealthChange, self.side, self.can_attack)

    def getValue(self, with_attack = 0):
        if self.hp <= 0:
            return 0
        result = self.hp + 0.5 + self.attack + (self.hp * self.attack)**0.5
        if (32&self.abilities) > 0:
            result += 2.0
            if self.attack > 4:
                result += 0.4
        if (8&self.abilities) > 0:
            result += 1.0
            if self.hp > 4:
                result += 0.4
        if (16&self.abilities) > 0:
            result += 4.0
        if self.can_attack * with_attack:
            result += 2.0

        return result * 100.0

class Creature(Card):
    def __init__(self, id_, attack, hp, abilities, side, can_attack = 0):
        self.attack = attack
        self.hp = hp
        self.can_attack = can_attack
        self.id_ = id_
        self.abilities = abilities
        self.side = side

    @staticmethod
    def make_creature(card):
        return Creature(card.id_, card.attack, card.hp, card.abilities, card.side, card.can_attack)

    def __hash__(self):
        return (self.attack, self.hp, self.abilities, self.side, self.can_attack).__hash__()

    def copy(self):
        return Creature(self.id_, self.attack, self.hp, self.abilities, self.side, self.can_attack)

    def makeAttack(self, val, game = -1):
        if game == -1:
            game = GameState()
        if self.hp <= 0:
            return
        game.hash ^= self.__hash__()
        self.can_attack = val
        game.hash ^= self.__hash__()

    def deal_damage(self, x, game = -1):
        if game == -1:
            game = GameState()
        if x == 0:
            return
        game.hash ^= self.__hash__()

        if (32&self.abilities) > 0 and x < 0:
            self.abilities &= (63 - 32)
        else:
            self.hp += x

        if self.hp > 0:
            game.hash ^= self.__hash__()

    def castSpell(self, spell, red, game = -1):
        if game == -1:
            game = GameState()
        game.hash ^= self.__hash__()

        if not red:
            self.abilities |= spell.abilities
        else:
            self.abilities &= (63 - spell.abilities)

        self.attack += spell.attack
        self.attack = max(self.attack, 0)

        game.hash ^= self.__hash__()

        self.deal_damage(spell.hp, game)

class GameState:
    player_health_hash = [list(map(int, np.random.randint(0, BIG_INF, 100, dtype=np.int64))), list(map(int, np.random.randint(0, BIG_INF, 100, dtype=np.int64)))]
    turn_hash = list(map(int, np.random.randint(0, BIG_INF, 2, dtype=np.int64)))

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.hash == other.hash
    def __ne__(self, other):
        if type(other) != type(self):
            return True
        return self.hash != other.hash

    @staticmethod
    def getValue(self):
        if self.myHero.hp <= 0:
            return -INF - 1
        if self.enemyHero.hp <= 0:
            return INF + 1

        value = 0

        value = float((math.log(self.myHero.hp) - math.log(self.enemyHero.hp)) * 100.0)
        for i in self.my_board:
            value += i.getValue()
        for i in self.enemy_board:
            value -= i.getValue()
        return value

    def __init__(self):
        self.turn = 1

        self.myHero = Creature(-610, 0, 30, 1, 0)
        self.enemyHero = Creature(-1, 0, 30, 0, 0)

        self.hand, self.my_board, self.enemy_board = [], [], []

        self.hash = 0
        self.update_hash()

    def __hash__(self):
        return self.hash

    def update_hash(self):
        self.hash = 0
        self.hash ^= self.turn_hash[self.turn]
        for i in (self.enemy_board + self.my_board):
            self.hash ^= i.__hash__()

    def summon(self, minion_card):
        self.enemyHero.deal_damage(minion_card.opponentHealthChange, self)
        self.myHero.deal_damage(minion_card.myhealthChange, self)

        self.hand.remove(minion_card)
        self.hash ^= minion_card.__hash__()

        minion = Creature.make_creature(minion_card)
        self.hash ^= minion.__hash__()
        self.my_board.append(minion)

    def attack(self, id0, id1):
        if self.turn == 1:
            id0, id1 = id1, id0
        c0, c1 = 0,0
        for i in range(len(self.enemy_board)):
            if self.enemy_board[i].id_ == id0:
                c0 = self.enemy_board[i]
                self.enemy_board = self.enemy_board[:i] + self.enemy_board[i + 1:]
                break
        for i in range(len(self.my_board)):
            if self.my_board[i].id_ == id1:
                c1 = self.my_board[i]
                self.my_board = self.my_board[:i] + self.my_board[i + 1:]
                break

        if type(c1) == type(0) or type(c0) == type(0):
            print(id0, id1)
        if (16&c1.abilities) == 0:
            c0.deal_damage(-c1.attack, self)
        else:
            c0.deal_damage(-INF, self)

        if (16&c0.abilities) == 0:
            c1.deal_damage(-c0.attack, self)
        else:
            c1.deal_damage(-INF, self)

        c1.makeAttack(0, self)
        c0.makeAttack(0, self)

        if c0.hp > 0:
            self.enemy_board.append(c0)
        if c1.hp > 0:
            self.my_board.append(c1)
    
    def castSpell(self, spell, id_target, red = False):
        creature = Creature(-INF, 0, 0, 0, 0)
        for i in range(len(self.enemy_board)):
            if self.enemy_board[i].id_ == id_target:
                creature = self.enemy_board[i]
                self.enemy_board = self.enemy_board[:i] + self.enemy_board[i + 1:]
                break
        for i in range(len(self.my_board)):
            if self.my_board[i].id_ == id_target:
                creature = self.my_board[i]
                self.my_board = self.my_board[:i] + self.my_board[i + 1:]
                break
        
        creature.castSpell(spell, red, self)
        self.hand.remove(spell)
        self.hash ^= spell.__hash__()
        
        if creature.hp > 0:
            if creature.side == 0:
                self.enemy_board.append(creature)
            else:
                self.my_board.append(creature)

    
    def nextTurn(self):
        self.hash ^= GameState.turn_hash[self.turn]
        self.turn ^= 1
        self.hash ^= GameState.turn_hash[self.turn]

        for i in self.hand:
            self.hash ^= i.__hash__()
        self.hand.clear()

        for i in range(len(self.enemy_board)):
            self.enemy_board[i].makeAttack(1, self)
        for i in range(len(self.my_board)):
            self.my_board[i].makeAttack(1, self)

    def doStep(self, st):
        if st.attacker == -1:
            self.nextTurn()
            return 'PASS;'
        if st.target == -5:
            for card in self.hand:
                if card.id_ == st.attacker:
                    self.summon(card)
                    return ' '.join(['SUMMON', str(st.attacker), ';'])
        
        for card in self.hand:
            if card.id_ != st.attacker:
                continue
            if card.type_ != 0:
                self.castSpell(card, st.target, card.type_ == 2)
                return ' '.join(['USE', str(st.attacker), str(st.target if st.target >= 0 else -1), ';'])

        self.attack(st.attacker, st.target)

        return ' '.join(['ATTACK', str(st.attacker), str(st.target if st.target >= 0 else -1), ';'])

    def copy(self):
        res = GameState()
        res.hash, res.my_board, res.enemy_board, res.turn, res.mana, res.hand = self.hash, [i.copy() for i in self.my_board], [i.copy() for i in self.enemy_board], self.turn, self.mana, [i.copy() for i in self.hand]
        return res

class Step:
    def __init__(self, attacker, target):
        self.attacker = attacker
        self.target = target

game_result, best_step = {}, {}

def hasTaunt(board):
    for i in board:
        if (8&i.abilities) > 0:
            return True
    return False

def getResult(v, alpha, beta):
    if v.hash in game_result:
        return game_result[v.hash]

    sum1, sum2 = 0,0
    
    if v.myHero.hp <= 0:
        game_result[v.hash] = -INF
        best_step[v.hash] = Step(-1, -1)
        return game_result[v.hash]
    if v.enemyHero.hp <= 0:
        game_result[v.hash] = INF
        best_step[v.hash] = Step(-1, -1)
        return game_result[v.hash]

    for i in v.enemy_board:
        if i.attack > 0:
            sum1 += 1
    for i in v.my_board:
        if i.attack > 0:
            sum2 += 1

    if (sum1 == 0 or sum2 == 0) and len(v.hand) == 0:
        game_result[v.hash] = GameState.getValue(v)
        best_step[v.hash] = Step(-1, -1)
        return game_result[v.hash]

    func,mb,eb = 0,0,0
    can_do = False
    steps = 0

    if v.turn == 0:
        game_result[v.hash] = INF
        best_step[v.hash] = Step(-1, -1)
        func = lambda x, y : x > y
        mb = [i.copy() for i in v.enemy_board]
        eb = [i.copy() for i in v.my_board]
    else:
        game_result[v.hash] = -INF
        best_step[v.hash] = Step(-1, -1)
        func = lambda x, y : x < y
        mb = [i.copy() for i in v.my_board]
        eb = [i.copy() for i in v.enemy_board]

    for card in v.hand:
        if card.cost > v.mana:
            continue
        if card.type_ == 0 and len(v.my_board) == 6:
            continue

        if card.type_ == 0:
            can_do = True

            new_game = v.copy()

            new_game.summon(card)
            new_game.mana -= card.cost

            if func(game_result[v.hash], getResult(new_game, alpha, beta)):
                game_result[v.hash] = getResult(new_game, alpha, beta)    
                best_step[v.hash] = Step(card.id_, -5)
                if v.turn == 1:
                    alpha = max(alpha, game_result[v.hash])
                else:
                    beta = min(beta, game_result[v.hash])
            continue
        
        if card.type_ == 3:
                if card.hp < 0:
                    card.type_ = 2
                else:
                    card.type_ = 1
                
        board = v.enemy_board
        if card.type_ == 1:
            board = v.my_board

        for creature in board:
            can_do = True

            new_game = v.copy()
            new_game.castSpell(card, creature.id_, card.type_ == 2)
            new_game.mana -= card.cost

            if func(game_result[v.hash], getResult(new_game, alpha, beta)):
                game_result[v.hash] = getResult(new_game, alpha, beta)    
                best_step[v.hash] = Step(card.id_, creature.id_)
                if v.turn == 1:
                    alpha = max(alpha, game_result[v.hash])
                else:
                    beta = min(beta, game_result[v.hash])
    

    for i in mb:
        if i.can_attack == 0 or i.attack == 0:
            continue
        if alpha >= beta or steps >= mx_step:
            return game_result[v.hash]

        new_game = 0

        for j in eb:
            if (8&j.abilities) == 0 and hasTaunt(eb):
                continue
            if alpha >= beta or steps >= mx_step:
                return game_result[v.hash]
            can_do = True
            steps += 1
            new_game = v.copy()
            new_game.attack(i.id_, j.id_)
            if func(game_result[v.hash], getResult(new_game, alpha, beta)):
                game_result[v.hash] = getResult(new_game, alpha, beta)    
                best_step[v.hash] = Step(i.id_, j.id_)
                if v.turn == 1:
                    alpha = max(alpha, game_result[v.hash])
                else:
                    beta = min(beta, game_result[v.hash])
        
    if not can_do:
        if one_turn:
            game_result[v.hash] = GameState.getValue(v)
            best_step[v.hash] = Step(-1, -1)
            return game_result[v.hash]
        new_game = v.copy()
        new_game.nextTurn()
        game_result[v.hash] = getResult(new_game, alpha, beta)
        best_step[v.hash] = Step(-1, -1)

    return game_result[v.hash]

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
    
    
def parse_abilities(abilities):
    mask = 0
    for i in range(6):
        if abilities[i] != '-':
            mask |= (1 << i)
    return mask          
        
def parse_creautures(cards):
    return [Creature(i.id_, i.attack, i.hp, i.abilities, i.side, i.can_attack) for i in cards]

class MonteCarloVertex:
    def __le__(self, other):
        return self.state_estimate >= other.state_estimate
    def __lt__(self, other):
        return self.state_estimate > other.state_estimate

    @staticmethod
    def getMoves(game_state):
        if game_state.enemyHero.hp <= 0 or game_state.myHero.hp <= 0:
            return []

        moves = []

        mb = game_state.my_board
        eb = game_state.enemy_board
        if game_state.turn == 0:
            mb, eb = eb, mb

        for card in game_state.hand:
            if card.cost > game_state.mana:
                continue
            if card.type_ == 0 and len(game_state.my_board) == 6:
                continue

            if card.type_ == 0:
                moves.append(Step(card.id_, -5))
                continue
        
            if card.type_ == 3:
                if card.hp < 0:
                    card.type_ = 2
                else:
                    card.type_ = 1
                
            board = game_state.enemy_board
            if card.type_ == 1:
                board = game_state.my_board

            for creature in board:
                moves.append(Step(card.id_, creature.id_))

        for ally in mb:
            if ally.can_attack == 0 or ally.attack == 0:
                continue
            for enemy in eb:
                if (enemy.abilities&8) == 0 and hasTaunt(eb):
                    continue
                moves.append(Step(ally.id_, enemy.id_))

        if moves == []:
            moves = [Step(-1, -1)]

        return [i for i in moves if i.attacker != i.target]

    def __init__(self, game_state, ancestor = -1):
        self.ancestor = ancestor
        self.game_state = game_state
        
        self.state_estimate = GameState.getValue(game_state)
        
        self.moves = MonteCarloVertex.getMoves(game_state)
        self.sons = []

        np.random.shuffle(self.moves)

    def updateEstimate(self, node_heap):
        if self.game_state.turn == 1:
            self.state_estimate = max(i[1].state_estimate for i in self.sons)
        else:
            self.state_estimate = min(i[1].state_estimate for i in self.sons)

        if self.moves:
            heapq.heappush(node_heap, (-self.state_estimate, self))

        if type(self.ancestor) == type(-1):
            return
        self.ancestor.updateEstimate(node_heap)

class MonteCarloTree:
    def addVertex(self, game_state, ancestor = -1):
        if not game_state.hash in self.vertexes:
            self.vertexes[game_state.hash] = MonteCarloVertex(game_state, ancestor)
        return self.vertexes[game_state.hash]
    def __init__(self, game_state):
        self.vertexes = {}
        self.root = self.addVertex(game_state)
        self.expandable_nodes = []
        heapq.heappush(self.expandable_nodes, (-self.root.state_estimate, self.root))

    def expand(self):
        if not self.expandable_nodes:
            return
        val, node = heapq.heappop(self.expandable_nodes)
        val = -val
        if not node.moves or val != node.state_estimate:
            self.expand()
            return

        move = node.moves.pop()
        new_game = node.game_state.copy()
        new_game.doStep(move)

        new_son = self.addVertex(new_game, node)
        node.sons.append((move, new_son))

        node.updateEstimate(self.expandable_nodes)

        if node.moves:
            heapq.heappush(self.expandable_nodes, (-node.state_estimate, node))
        if new_son.moves:
            heapq.heappush(self.expandable_nodes, (-new_son.state_estimate, new_son))

def MiniMaxPlay(game):
    s = ''
    while True:
        getResult(game.copy(), -INF - 5, INF + 5)
        if best_step[game.hash].attacker == -1 or game_result[game.hash] < GameState.getValue(game):
            break

        s += game.doStep(best_step[game.hash])

    return s

def MonteCarloPlay(game):
    Tree = MonteCarloTree(game)

    start = time.time()
    while time.time() - start < 0.07:
        Tree.expand()

    s = ''
    cur_node = Tree.root
    while cur_node.sons:
        best_val = -INF - 5
        best_son = -1
        best_step = -1

        for step, son in cur_node.sons:
            if son.state_estimate > best_val:
                best_val, best_son, best_step = son.state_estimate, son, step
        
        if best_val == INF - 5 or best_step.attacker == -1:
            break
        s += game.doStep(best_step)
        cur_node = best_son

    return s
        
########################################################################################################################################

turns = 0
card_list = [69, 116, 7, 65, 15, 17, 53, 9, 68, 67, 3, 151, 49, 103, 95, 8, 96, 26, 6, 99, 105, 19, 109, 80, 23, 62, 44, 114, 37, 150, 51, 36, 158, 111, 106, 75, 73, 79, 119, 118, 91, 152, 12, 104, 97, 64, 48, 38, 77, 59, 34, 112, 
82, 61, 33, 32, 98, 21, 29, 83, 87, 45, 144, 66, 28, 27, 58, 76, 60, 22, 52, 135, 148, 18, 84, 43, 101, 85, 120, 121, 40, 129, 128, 46, 115, 142, 39, 47, 50, 94, 108, 74, 71, 131, 72, 70, 100, 102, 86, 130, 88, 54, 122, 155, 93, 1, 107, 11, 41, 137, 4, 138, 42, 2, 56, 132, 25, 24, 117, 160, 154, 140, 153, 123, 149, 13, 125, 35, 159, 126, 134, 10, 31, 16, 57, 133, 127, 145, 92, 5, 136, 157, 30, 113, 89, 124, 20, 146, 147, 81, 78, 90, 143, 156, 141, 14, 55, 139, 63, 110]
pos = {}
for i in range(len(card_list)):
    pos[card_list[i]] = i

while True:
    game_result, best_step = {}, {}
    game = GameState()
    u = 0

    inp = input().split()
    game.myHero.hp = int(inp[0])
    game.mana = int(inp[1])
    inp = input().split()
    game.enemyHero.hp = int(inp[0])

    for i in range(int(input().split()[1])):
        input()
    
    cardCount = int(input())
    my_cards, enemy_cards, hand = [], [], []
    nums = []

    for i in range(cardCount):
        cardNumber, instanceId, location, cardType, cost, attack, defense, abilities, myhealthChange, opponentHealthChange, cardDraw = list(map(get_int, input().split()))
        abilities = parse_abilities(abilities)
        if location == 1:
            my_cards.append(Card(cardNumber, cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange, 1,  int(location == 1 or (abilities&2) > 0)))
        elif location == -1:
            enemy_cards.append(Card(cardNumber, cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange, 0, int(location == 1 or (abilities&2) > 0)))
        else:
            hand.append(Card(cardNumber, cardType, instanceId, cost, attack, defense, abilities, cardDraw, myhealthChange, opponentHealthChange, 1, int(location == 1 or (abilities&2) > 0)))
    
    if turns < 30:
        nhand = list(range(3))

        best_opt = nhand[int(np.random.randint(0, len(nhand)))]
        best_ad = -INF

        for i in nhand:
            ad = -pos[hand[i].num]

            if ad > best_ad:
                best_ad = ad
                best_opt = i

        print('PICK', best_opt)
        turns += 1
    else:
        s = ''
        game.enemy_board = parse_creautures(enemy_cards)
        game.my_board = parse_creautures(my_cards)
        game.hand = hand
        game.update_hash()

        if not hasTaunt(game.enemy_board) and sum(creature.attack * creature.can_attack for creature in game.my_board) >= game.enemyHero.hp:
            for i in game.my_board:
                s += ' '.join(['ATTACK', str(i.id_), str(-1), 'Lethal', ';'])
            print(s)
            continue

        #if len(game.enemy_board) * len(game.my_board) >= 4:
        #    print(str(game.getMoves()))

        if True:#sum(i.can_attack for i in game.enemy_board) * sum(i.can_attack for i in game.my_board) > 10:
            game.my_board.append(game.myHero)
            game.enemy_board.append(game.enemyHero)
            s += MonteCarloPlay(game)
        else:
            s += MiniMaxPlay(game)

        for i in game.my_board:
            s += ' '.join(['ATTACK', str(i.id_), str(-1), 'did i forget anything?', ';'])
        
        if s == '':
            s = 'PASS'

        print(s)

'''
10 10 0 0
10 10 0 0
0 0
1
1 1 0 0 1 1 1 ------ 0 0 0
'''