import Game
import random
import math
import asyncio

# some of the moves are slightly sus - blundering pawns in one move seems pretty common

# the best lines it's finding are complete ass lmfao - it keeps assuming you'll be able to take it and yet it's better

pieceValue = [0,0,9,3,3,5,1]
CHECKMATE = 65535
STALEMATE = 0
MAX_DEPTH = 3
bestMove = []
bestValue = -CHECKMATE
EARLYGAME = 2.0
ENDGAME = 0.1


VALUEMAPS = [
    # Pawn earlygame map
    [ 
        [0,0,0,0,0,0,0,0],
        [.3,.3,.3,.3,.3,.3,.3,.3],
        [.1,.05,.05,.1,.1,.05,.05,.1],
        [.05,.05,.075,.075,.075,.075,.05,.05],
        [.075,.075,.1,.15,.15,.1,.075,.075],
        [.075,.1,.125,.125,.125,.125,.1,.075],
        [.05,.1,.1,.05,.05,.1,.1,.05],
        [0,0,0,0,0,0,0,0]
    ],
    # King earlygame map
    [ 
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [.05,.05,.025,.025,.025,.025,.05,.05],
        [.3,.4,.4,.2,.2,.4,.4,.3]
    ]
]

def boardValue(board):
    value = 0
    for r in range(len(board)):
        for c in range(len(board)):
            piece = board[r][c]
            if piece // 16 == 1:
                color = 1
            else:
                color = -1
            value += pieceValue[piece % 16] * color
    return value


async def eval(gS):
    if gS.stalemate:
        return STALEMATE
    elif gS.checkmate:
        return CHECKMATE * (-1 if gS.whiteToMove else 1)
    else:
        value = 0
        for r in range(len(gS.board)):
            for c in range(len(gS.board)):
                piece = gS.board[r][c]
                if piece // 16 == 1:
                    color = 1
                else:
                    color = -1
                if piece % 16 == 6:
                    value += color * (1 + EARLYGAME * (VALUEMAPS[0][r][c] if color == 1 else VALUEMAPS[0][7-r][c]) + 0.05 * ENDGAME)
                elif piece % 16 == 5:
                    value += color * (5 + ENDGAME * 0.1)
                elif piece % 16 == 4:
                    value += 3 * color
                elif piece % 16 == 3:
                    value += 3 * color
                elif piece % 16 == 2:
                    value += color * (9 + ENDGAME * 0.15)
                elif piece % 16 == 1:
                    value += color * (EARLYGAME * (VALUEMAPS[1][r][c] if color == 1 else VALUEMAPS[1][7-r][c]))
        return value

async def getRandomMove(validMoves):
    try:
        moveNo = random.randint(0, len(validMoves) - 1)
    except:
        moveNo = 0
    print("Selected move number " + str(moveNo + 1) + " from a list of " + str(len(validMoves)) + " possible moves.")
    return validMoves[moveNo]

async def getRandomGrandmasterMove(board):
    pass

async def greedyMove(gS, validMoves):
    currentPlayer = 1 if gS.whiteToMove else -1
    bestValue = -(currentPlayer) * CHECKMATE
    greediestMove = None
    for move in validMoves:
        await gS.makeMove(move)
        moveValue = boardValue(gS.board)
        if gS.stalemate:
            moveValue = STALEMATE
        elif gS.checkmate:
            print("Mate in One")
            moveValue = CHECKMATE * currentPlayer
        if moveValue > bestValue:
            print("move found with value", moveValue)
            greediestMove = move
            print(greediestMove)
            bestValue = moveValue
        await gS.undoMove()
    print("best move found:", greediestMove)
    return greediestMove

bestLine = list(range(MAX_DEPTH))
async def findBestMoveMinMax(gS, validMoves, depth):
    global bestMove
    global evaluation
    global bestLine
    bestMove = None
    evaluation = -CHECKMATE * 1 if gS.whiteToMove else -1
    await recursiveMinMaxMove(gS, validMoves, MAX_DEPTH, 1 if gS.whiteToMove else -1, -CHECKMATE, CHECKMATE)
    print("The move that was just played has value " + str(evaluation) + " after the line " + str(list(await Game.getChessNotationOfList(bestLine))))
    print("AI evaluation of the current board state: %s" % (str(await eval(gS))))
    return bestMove

''' algorithm can still be recursive, but what it should do should be to send out a bunch of threads 
 that all look at various lines and come back to the main one with an eval
 
 this can also be used to do things like search in more depth on higher value lines
 
 need to figure out how to properly cancel tasks to make this work - AI should search infinitely until a 1 second sleep is finished'''

async def recursiveMinMaxMove(gS: Game.GameState, validMoves, depth, currentPlayer, alpha, beta):
    global bestMove
    global evaluation
    global bestLine
    if depth == 0 or gS.checkmate or gS.stalemate:
        return currentPlayer * await eval(gS)
    # move ordering
    if depth > 1:
        orderedMoves = []
        promotions = []
        checks = []
        captures = []
        castles = []
        attacks = []
        remaining = validMoves
        for i in range(len(validMoves) - 1, -1, -1):
            move = validMoves[i]
            if move.isPawnPromotion:
                promotions.append(move)
                remaining.remove(move)
            elif await Game.isAttackOn(1, move, gS): # is it an attack on the king?
                checks.append(move) # optimization - use gS.checks!
                remaining.remove(move)
            elif move.pieceCaptured != None:
                captures.append(move)
                remaining.remove(move)
            elif move.isCastlingMove:
                castles.append(move)
                remaining.remove(move)
            elif await Game.isAttackOn(2, move, gS) or await Game.isAttackOn(5, move, gS): #optimization - handle these both at once!
                attacks.append(move)
                remaining.remove(move)
        for l in [promotions, checks, captures, castles, attacks, remaining]:
            appendToOrdered(l, orderedMoves)
    else:
        orderedMoves = validMoves

    bestValue = -CHECKMATE
    bestMoveAtCurrentStep = None
    for move in orderedMoves:
        
        #for row in gS.board:
            #print(row)
        await gS.makeMove(move, True) # add back True
        
        if depth > 1:
            nextMoves = await gS.getLegalMoves(True)
        else:
            nextMoves = None
        moveValue = -(await recursiveMinMaxMove(gS, nextMoves, depth - 1, -currentPlayer, -beta, -alpha))
        if moveValue >= bestValue:
            if depth == MAX_DEPTH:
                bestMove = move
                evaluation = bestValue * 1 if gS.whiteToMove else -1
            bestMoveAtCurrentStep = move
            bestValue = moveValue
        await gS.undoMove(True) # add back True
        if bestValue >= alpha:
            alpha = bestValue
        if alpha >= beta: # https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning
            break 
    bestLine[MAX_DEPTH - depth] = bestMoveAtCurrentStep
    return bestValue

def appendToOrdered(listToAppend, orderedMoves): # pretty sure there's a built in function that does this
    for move in listToAppend:
        orderedMoves.append(move)
    return orderedMoves
