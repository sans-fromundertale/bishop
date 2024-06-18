import traceback
import asyncio

# To-do for refactoring:

# combine blackKingLocation and whiteKingLocation into a list
# do more multithreading where possible
# make getLegalMoves use del instead of .remove
# FEN notation? eventually? in the distant future?
# convert ints to raw bits and use bit logic instead of int logic

class GameState():
    def __init__(self):
        self.board = [
            #  8*8 2d list, pieces represented by numbers
            #  0 represents an empty space
            [5, 4, 3, 2, 1, 3, 4, 5],
            [6, 6, 6, 6, 6, 6, 6, 6],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [22, 22, 22, 22, 22, 22, 22, 22],
            [21, 20, 19, 18, 17, 19, 20, 21],
            # white: +16
            # black: +0
            # K: 1
            # Q: 2
            # B: 3
            # N: 4
            # R: 5
            # P: 6
            # number comparisons are faster than string comparisons, also this system would allow for 5-bit piece handling 
            # first two bits are white/black and last 3 bits are what piece it is
            # unfortunately I don't get how to do bit comparisons in python very well but ints are still much faster than strings
        ]
        self.whiteToMove = True
        self.moveLog = []
        self.notationMoveLog = []
        self.moveFunctions = [self.getKingMoves, self.getQueenMoves, self.getBishopMoves, self.getKnightMoves, self.getRookMoves, self.getPawnMoves]
        self.checkmate = False
        self.stalemate = False
        self.pInCheck = False
        self.pins = []
        self.checks = []
        self.whiteKingLocation = ()
        self.blackKingLocation = ()
        self.enPassantLocation = ()
        self.currentCastleRights = CastlingRights(True, True, True, True)
        self.castleRightsLog = []
        self.checkingCastling = False
        self.fiftyMoveRule = 0
        self.fiftyMoveRuleLog = [0]

    async def findKingLocations(self):
        self.whiteKingLocation = ()
        self.blackKingLocation = ()
        for r in range(len(self.board)):
            for c in range(len(self.board)):
                if self.board[r][c] == 17:
                    if self.whiteKingLocation == ():
                        self.whiteKingLocation = (r, c)
                    else:
                        print("Error - Multiple white kings on board")
                        print("Computer has picked the king on " + getRankFile(self.whiteKingLocation[0], self.whiteKingLocation[1]) + " for use in game")
                elif self.board[r][c] == 1:
                    if self.blackKingLocation == ():
                        self.blackKingLocation = (r, c)
                    else:
                        print("Error - Multiple black kings on board")
                        print("Computer has picked the king on " + getRankFile(self.blackKingLocation[0], self.blackKingLocation[1]) + " for use in game")
    # does not do castling
    # executes moves on the board - could be faster
    # analysis ONLY prevents updating notation moves, not moveLog. A separate way of handling it is needed for analysis board.
    async def makeMove(self, move, analysis = False):   
        # move piece
        self.board[move.row_2][move.col_2] = move.pieceMoved
        self.board[move.row_1][move.col_1] = 0
        # switch turn
        self.whiteToMove = not self.whiteToMove
        if move.pieceMoved == 17:
            self.whiteKingLocation = (move.row_2, move.col_2)
        elif move.pieceMoved == 1:
            self.blackKingLocation = (move.row_2, move.col_2)
        
        # log move in computer format and in chess notation
        # don't run this when computer uses it to think about moves
        self.moveLog.append(move)

        if move.isPawnPromotion:
            self.board[move.row_2][move.col_2] = int(move.pieceMoved / 16) * 16 + move.pieceDesired
        
        if move.isEnPassant:
            # print("EN PASSANT, YOU SON OF A SILLY PERSON! AH'LL BLOW MAH NOSE ATCH YOU! AH'LL FART IN YOUR GENERAL DIRECTION!")
            self.board[move.row_1][move.col_2] = 0
        
        self.enPassantLocation = ()

        if move.pieceMoved % 16 == 6 and abs(move.row_1 - move.row_2) == 2:
            self.enPassantLocation = ((move.row_1 + move.row_2) / 2, move.col_2)
        
        if move.castlingMove:
            self.board[move.row_2][int((move.col_1 + move.col_2) / 2)] = move.pieceMoved // 16 * 16 + 5
            if move.col_1 > move.col_2:
                self.board[move.row_2][0] = 0
            else:
                self.board[move.row_2][7] = 0

        self.fiftyMoveRule += 1
        if move.pieceCaptured != 0:
            self.fiftyMoveRule = 0
        self.fiftyMoveRuleLog.append(self.fiftyMoveRule)
        if not analysis: 
            self.notationMoveLog.append(await getChessNotation(move, self))
        await self.updateCastleRights(move)
    # bug DISCOVERED - GLITCHY WITH UNDOS (PARTICULARLY MULTIPLE IN A ROW)
    async def updateCastleRights(self, move):
        if move.pieceMoved == 17:
            self.currentCastleRights.whiteKingSide = False
            self.currentCastleRights.whiteQueenSide = False
        elif move.pieceMoved == 1:
            self.currentCastleRights.blackKingSide = False
            self.currentCastleRights.blackQueenSide = False
        elif (move.pieceMoved == 21 or move.pieceCaptured == 21) and move.row_1 == 7:
            if move.col_1 == 0:
                self.currentCastleRights.whiteQueenSide = False
            elif move.col_1 == 7:
                self.currentCastleRights.whiteKingSide = False
        elif (move.pieceMoved == 5 or move.pieceCaptured == 5) and move.row_1 == 0:
            if move.col_1 == 0:
                self.currentCastleRights.blackQueenSide = False
            elif move.col_1 == 7:
                self.currentCastleRights.blackKingSide = False
        castleRights = CastlingRights(self.currentCastleRights.whiteKingSide, self.currentCastleRights.whiteQueenSide, 
                                      self.currentCastleRights.blackKingSide, self.currentCastleRights.blackQueenSide)
        self.castleRightsLog.append(castleRights)
        

    # Undo the last move made according to the move log
    async def undoMove(self, analysis = False):
        if len(self.moveLog) != 0: # make sure there is a move to undo
            move = self.moveLog.pop()
            self.board[move.row_2][move.col_2] = move.pieceCaptured
            if move.pieceCaptured % 16 == 1:
                print("captured king with moves " + str(self.notationMoveLog) + " dumbass")
            self.board[move.row_1][move.col_1] = move.pieceMoved
            self.whiteToMove = not self.whiteToMove
            if not analysis:
                del self.notationMoveLog[len(self.notationMoveLog) - 1] # don't do this on an analysis board?
            if move.pieceMoved == 17:
                self.whiteKingLocation = (move.row_1, move.col_1)
            elif move.pieceMoved == 1:
                self.blackKingLocation = (move.row_1, move.col_1)

            # special undo for en passant moves
            if move.isEnPassant:
                # print("YOU UNDID IT? YOU SILLY ENGLISH TYPE! YOUR MOTHER WAS A HAMSTER AND YOUR FATHER SMELLED OF ELDERBERRIES!")
                self.board[move.row_1][move.col_2] = move.pieceCaptured
                self.board[move.row_2][move.col_2] = 0
            
            if len(self.moveLog) > 0:
                # update en passant location
                if self.moveLog[len(self.moveLog) - 1].pieceMoved % 16 == 6 and abs(self.moveLog[len(self.moveLog) - 1].row_1 - self.moveLog[len(self.moveLog) - 1].row_2) == 2:
                    self.enPassantLocation = (move.row_2, move.col_2)
                else:
                    self.enPassantLocation = ()
            else:
                self.enPassantLocation = ()
            
            # undo any update to castling rights

            del self.castleRightsLog[len(self.castleRightsLog) - 1] # remove castle rights of the move we are undoing from the log
            if len(self.castleRightsLog) != 0:
                self.currentCastleRights = self.castleRightsLog[len(self.castleRightsLog)-1]
                # set castle rights to the last entry in the log

            if move.castlingMove: # special undo for castles
                self.board[move.row_2][int((move.col_1 + move.col_2) / 2)] = 0
                if move.col_1 > move.col_2:
                    self.board[move.row_2][0] = move.pieceMoved // 16 * 16 + 5 # replaces with the correct color of rook
                else:
                    self.board[move.row_2][7] = move.pieceMoved // 16 * 16 + 5
            
            self.fiftyMoveRuleLog.pop()
            self.fiftyMoveRule = self.fiftyMoveRuleLog[len(self.fiftyMoveRuleLog)-1]

            # BUG DISCOVERED - if you make a move and undo on the same frame it can duplicate pieces and do glitchy things

    async def inCheck(self):
        if self.whiteToMove:
            return await self.squareUnderAttack(self.whiteKingLocation)
        else:
            return await self.squareUnderAttack(self.blackKingLocation)

    async def squareUnderAttack(self, square): # can use similar logic to checkForPinsAndChecks for efficiency
        self.whiteToMove = not self.whiteToMove
        opponentMoves = await self.getPossibleMoves() # does not actually find attacks - misses pawn captures and piece protection
        self.whiteToMove = not self.whiteToMove
        for move in opponentMoves:
            if move.row_2 == square[0] and move.col_2 == square[1]:
                return True
        return False

    # filter moves for type of piece
    async def getPossibleMoves(self):
        possibleMoves = []
        moveGetterTasks = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])): 
                piece = self.board[row][col]
                if ( (int(piece / 16) == 1 and self.whiteToMove) or (int(piece / 16) == 0 and not self.whiteToMove) ) and piece != 0:
                    try:
                        temp = asyncio.create_task(self.moveFunctions[(piece % 16) - 1](row, col, possibleMoves))
                        moveGetterTasks.append(temp)
                    except Exception as e:
                        print(f"Error creating task for piece at ({row},{col}): {e}")
        try:
            await asyncio.wait(moveGetterTasks, return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            print(f"Error waiting for tasks to complete: {e}")
        
        return possibleMoves
                        
    async def getPawnMoves(self, prow, pcol, possibleMoves, checkingAttack = False):     # slight ugliness with needing to check if it's promoting every time   
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == prow and self.pins[i][1] == pcol:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i]) # could probably work with del
                break               
        if self.whiteToMove: # white pawns only (racism???)
            if self.board[prow-1][pcol] == 0:
                if (not piecePinned) or pinDirection == (-1, 0): # if the piece is not pinned or if the piece is moving in the same direction as the pin
                    if prow == 1:
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol), self.board, True, 2)) #promotion
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol), self.board, True, 3))
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol), self.board, True, 4))
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol), self.board, True, 5))
                    else:
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol), self.board))
                        if prow == 6 and self.board[prow-2][pcol] == 0:
                            possibleMoves.append(Move((prow, pcol), (prow - 2, pcol), self.board))
                        # pawn may move 2 squares
                
            if pcol >= 1: # capture handling with error handling built in
                if (not piecePinned) or pinDirection == (-1, -1):
                    if int(self.board[prow-1][pcol-1] / 16) == 0 and self.board[prow-1][pcol-1] / 16 != 0:
                        if prow == 1:
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board, True, 2))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board, True, 3))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board, True, 4))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board, True, 5))
                        else:
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board))
                    elif (prow-1, pcol-1) == self.enPassantLocation:
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol - 1), self.board, False, 0, False, True))
            if pcol <= 6:
                if (not piecePinned) or pinDirection == (-1, 1):
                    if int(self.board[prow-1][pcol+1] / 16) == 0 and self.board[prow-1][pcol+1] / 16 != 0:
                        if prow == 1:
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board, True, 2))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board, True, 3))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board, True, 4))
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board, True, 5))
                        else:
                            possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board))
                    elif (prow-1, pcol+1) == self.enPassantLocation:
                        possibleMoves.append(Move((prow, pcol), (prow - 1, pcol + 1), self.board, False, 0, False, True))
        
        
        else: # black pawns only
            if self.board[prow+1][pcol] == 0: 
                if (not piecePinned) or pinDirection == (1, 0):
                    if prow == 6:
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol), self.board, True, 2))
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol), self.board, True, 3))
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol), self.board, True, 4))
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol), self.board, True, 5))
                    else:
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol), self.board))
                        if prow == 1 and self.board[prow+2][pcol] == 0:
                            possibleMoves.append(Move((prow, pcol), (prow + 2, pcol), self.board))
                        # pawn may move 2 squares

            if pcol >= 0: # capture handling with error handling built in
                if (not piecePinned) or pinDirection == (1, -1):
                    if int(self.board[prow+1][pcol-1] / 16) == 1:
                        if prow == 6:
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board, True, 2))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board, True, 3))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board, True, 4))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board, True, 5))
                        else:    
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board))
                    elif (prow+1, pcol-1) == self.enPassantLocation:
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol - 1), self.board, False, 0, False, True))
            if pcol <= 6:
                if (not piecePinned) or pinDirection == (1, 1):
                    if int(self.board[prow+1][pcol+1] / 16) == 1:
                        if prow == 6:
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board, True, 2))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board, True, 3))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board, True, 4))
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board, True, 5))
                        else:    
                            possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board))
                    elif (prow+1, pcol+1) == self.enPassantLocation:
                        possibleMoves.append(Move((prow, pcol), (prow + 1, pcol + 1), self.board, False, 0, False, True))

    async def getRookMoves(self, rrow, rcol, possibleMoves, checkingAttack = False):                
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == rrow and self.pins[i][1] == rcol:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break               # say if the piece is pinned and if so in what direction while clearing the pin
        for d in directions:
            for i in range(1,8): # min-max number of squares it is possible for a rook to move in a given direction
                r = rrow + d[0] * i
                c = rcol + d[1] * i
                if 0 <= r <= 7 and 0 <= c <= 7:
                    if not piecePinned or d == pinDirection or d == (-pinDirection[0], -pinDirection[1]):     # may be able to move this to just under "for d in directions"
                        if self.board[r][c] == 0:
                            possibleMoves.append(Move((rrow, rcol), (r, c), self.board))
                        elif int(self.board[r][c] / 16) != int(self.whiteToMove): # if piece is not same color as whose turn it is
                            possibleMoves.append(Move((rrow, rcol), (r, c), self.board))
                            break
                        else:
                            break
                else:
                    break

    async def getKnightMoves(self, nrow, ncol, possibleMoves, checkingAttack = False):                
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == nrow and self.pins[i][1] == ncol:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        # same as RBQ but with no distance (only a flat move)
        moves = ((1, 2), (-1, 2), (-1, -2), (1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1))
        for move in moves:
            r = nrow + move[0]
            c = ncol + move[1]
            if 0 <= r <= 7 and 0 <= c <= 7:
                if not piecePinned:
                    if self.board[r][c] == 0 or int(self.board[r][c] / 16) != int(self.whiteToMove):
                        possibleMoves.append(Move((nrow, ncol), (r, c), self.board))

    async def getBishopMoves(self, brow, bcol, possibleMoves, checkingAttack = False):                
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == brow and self.pins[i][1] == bcol:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        directions = ((1, 1), (1, -1), (-1, -1), (-1, 1))
        for d in directions:
            for i in range(1,8): # min-max number of squares it is possible for a bishop to move in a given direction
                r = brow + d[0] * i
                c = bcol + d[1] * i
                if 0 <= r <= 7 and 0 <= c <= 7:
                    if not piecePinned or d == pinDirection or d == (-pinDirection[0], -pinDirection[1]):
                        if self.board[r][c] == 0:
                            possibleMoves.append(Move((brow, bcol), (r, c), self.board))
                        elif int(self.board[r][c] / 16) != int(self.whiteToMove): # if piece is not same color as whose turn it is
                            possibleMoves.append(Move((brow, bcol), (r, c), self.board))
                            break
                        else:
                            break
                else:
                    break

    async def getQueenMoves(self, qrow, qcol, possibleMoves, checkingAttack = False):       # can technically do this by just calling rook and bishop moves but that creates a bug I don't want to fix with pins         
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == qrow and self.pins[i][1] == qcol:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1))
        for d in directions:
            for i in range(1,8): # min-max number of squares it is possible for a queen to move in a given direction
                r = qrow + d[0] * i
                c = qcol + d[1] * i
                if 0 <= r <= 7 and 0 <= c <= 7:
                    if not piecePinned or d == pinDirection or d == (-pinDirection[0], -pinDirection[1]):
                        if self.board[r][c] == 0:
                            possibleMoves.append(Move((qrow, qcol), (r, c), self.board))
                        elif int(self.board[r][c] / 16) != int(self.whiteToMove): # if piece is not same color as whose turn it is
                            possibleMoves.append(Move((qrow, qcol), (r, c), self.board))
                            break
                        else:
                            break
                else:
                    break

    async def getKingMoves(self, krow, kcol, possibleMoves, checkingAttack = False):
        moves = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1))
        allyColor = 16 if self.whiteToMove else 0
        pCurrentlyInCheck, checks, pins = await self.checkForPinsAndChecks()
        for move in moves:
            r = krow + move[0]
            c = kcol + move[1]
            
            if 0 <= r <= 7 and 0 <= c <= 7: # these if statements cannot be combined because it would be searching r and cs outside of board

                if self.board[r][c] == 0 or int(self.board[r][c] / 16) != int(self.whiteToMove):

                    possibleMoves.append(Move((krow, kcol), (r, c), self.board))

        if not self.checkingCastling:
            self.checkingCastling = True
            await self.getCastleMoves(krow, kcol, allyColor, possibleMoves, pCurrentlyInCheck)
            self.checkingCastling = False

    async def getCastleMoves(self, krow, kcol, allyColor, possibleMoves, pInCheck):
        if allyColor == 16:
            # white king side
            if self.currentCastleRights.whiteKingSide: # this is decoupled to make it more efficient after losing castling rights at the cost of being slightly less efficient before - engine will be better in endgames
                if self.board[krow][kcol + 1] == 0 and self.board[krow][kcol + 2] == 0:
                    possibleMoves.append(Move((krow, kcol), (krow, kcol + 2), self.board, False, 0, True))
            if self.currentCastleRights.whiteQueenSide:
                if self.board[krow][kcol - 1] == 0 and self.board[krow][kcol - 2] == 0:
                    possibleMoves.append(Move((krow, kcol), (krow, kcol - 2), self.board, False, 0, True))
        else:
            if self.currentCastleRights.blackKingSide:
                if self.board[krow][kcol + 1] == 0 and self.board[krow][kcol + 2] == 0:
                    possibleMoves.append(Move((krow, kcol), (krow, kcol + 2), self.board, False, 0, True))
            if self.currentCastleRights.blackQueenSide:
                if self.board[krow][kcol - 1] == 0 and self.board[krow][kcol - 2] == 0:
                    possibleMoves.append(Move((krow, kcol), (krow, kcol - 2), self.board, False, 0, True))
        
                        

# filter moves by legality (things like pins)
    async def getLegalMoves(self, analysis = False):
        tempEnPassantLocation = self.enPassantLocation
        # initializing variables
        possibleMoves = []
        self.pInCheck, self.checks, self.pins = await self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        # logic for if king is in check
        if self.pInCheck:
            if len(self.checks) == 1:
                # this messes with self.pInCheck and self.checks with king moves - fix
                possibleMoves = await self.getPossibleMoves()
                
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = [] # squares that non-king friendly pieces can move to
                
                if pieceChecking % 16 == 4: # knights cannot be blocked so must be captured
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1,8): # can move anywhere between the checking piece and the king (block) or on the checking piece (capture)
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) # kingPos + direction * distance to king
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break

                for i in range(len(possibleMoves)-1, -1, -1):
                    move = possibleMoves[i]
                    if move.pieceMoved % 16 != 1: # why is this here?
                        if (move.row_2, move.col_2) not in validSquares:
                            possibleMoves.remove(move) # possibly worth using an index rather than a .remove here to speed up the loop
            else: # double check - no one square can block both, so the king must move
                await self.getKingMoves(kingRow, kingCol, possibleMoves)
        # pieces that are pinned are handled individually, so this is all that's needed if not in check
        else:
            possibleMoves = await self.getPossibleMoves()

        # remove any moves that move into check
        for i in range(len(possibleMoves) - 1, -1, -1):
            kingMove = possibleMoves[i]
            if kingMove.pieceMoved % 16 == 1:
                await self.makeMove(kingMove, True)
                self.whiteToMove = not self.whiteToMove
                pInCheck, checks, pins =  await self.checkForPinsAndChecks() # inefficient but it's fine for now
                self.whiteToMove = not self.whiteToMove
                if pInCheck:
                    del possibleMoves[i]
                await self.undoMove(True)

                # does not remove castle moves that move through check

                    
                    
                
                    
                
                
                
        # logic for ending the game
        if len(possibleMoves) == 0 or self.fiftyMoveRule > 99:
            if self.pInCheck and len(possibleMoves) == 0:
                self.checkmate = True
                if not analysis:
                    print("Checkmate!")
                    if self.whiteToMove:
                        print("Black wins!")
                    else:
                        print("White Wins!")
            else:
                self.stalemate = True
                if not analysis:
                    print("Stalemate!")
        # probably don't need this part
        else:
            self.checkmate = False
            self.stalemate = False
        
        self.enPassantLocation = tempEnPassantLocation
        return possibleMoves

    #    for i in range(len(possibleMoves)-1, -1, -1):
    #        self.makeMove(possibleMoves[i])
    #        self.whiteToMove = not self.whiteToMove
    #        if self.inCheck():                                               legacy code
    #            possibleMoves.pop(i)                              generates all possible responses to each move and 
    #        self.whiteToMove = not self.whiteToMove                if one of them captures the king, prunes the move
    #        self.undoMove()

    # def inCheck(self):
    #    self.whiteToMove = not self.whiteToMove
    #    opponentMoves = self.getPossibleMoves()
    #    self.whiteToMove = not self.whiteToMove
    #    for move in opponentMoves:
    #        if move.pieceCaptured == 16 * int(self.whiteToMove) + 1:
    #            return True
    #    return False
    
    async def checkForPinsAndChecks(self):
        # initialize variables
        pins = []
        checks = []
        pInCheck = False
        if self.whiteToMove:
            enemyColor = 0
            friendlyColor = 16
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            enemyColor = 16
            friendlyColor = 0
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        # iterate through each direction a piece could attack the king from - knights handled seperately
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range(1,8):
                endRow = kingRow + d[0] * i
                endCol = kingCol + d[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    # this bit runs
                    endPiece = self.board[endRow][endCol]
                    if endPiece - (endPiece % 16) == friendlyColor and endPiece != 0:
                        if possiblePin == ():
                            # print("friendly piece found")
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            # print("second piece found - breaking")
                            break
                    elif endPiece - (endPiece % 16) == enemyColor and endPiece != 0: # just color without piece value
                        pieceType = endPiece % 16 # found enemy piece along diagonal/orthogonal line from king
                        # 5 parts
                        # orthogonal + rook
                        # diagonal + bishop
                        # pawn 1 space away diagonally in front
                        # king 1 space away (for preventing moves)
                        # queen
                        # print("ENEMY PIECE FOUND - " + pieceNumsToLetters(endPiece))
                        if  (pieceType == 5 and -1 < j < 4) or \
                            (pieceType == 3 and 3 < j < 8) or \
                            (pieceType == 6 and i == 1 and ((enemyColor == 0 and 5 < j < 8) or (enemyColor == 16 and 3 < j < 6))) or \
                            (pieceType == 1 and i == 1) or \
                            (pieceType == 2):
                            if possiblePin == ():
                                # print("check by non-knight move")
                                pInCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePin)
                                break
                        else:
                            break
        knightMoves = ((1, 2), (-1, 2), (-1, -2), (1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1))
        for move in knightMoves:
            endRow = kingRow + move[0]
            endCol = kingCol + move[1]
            if -1 < endRow < 8 and -1 < endCol < 8:
                if self.board[endRow][endCol] == 4 + 16 * int(not self.whiteToMove):
                    # print("check by knight move")
                    pInCheck = True
                    checks.append((endRow, endCol, move[0], move[1]))
        return pInCheck, checks, pins




class CastlingRights():
    def __init__(self, wks, wqs, bks, bqs):
        self.whiteKingSide = wks
        self.whiteQueenSide = wqs
        self.blackKingSide = bks
        self.blackQueenSide = bqs


        


        
        
# castling and special cases

class Move(): # for creating move objects - needs to be *very fast*
    def __init__(self, pos_1, pos_2, board, isPawnPromotion = False, pieceDesired = 0, castlingMove = False, enPassantMove = False): #handling these in the move-finding logic is much, much faster than finding them in here, even though it is also much uglier
        self.row_1 = pos_1[0]
        self.col_1 = pos_1[1]
        self.row_2 = pos_2[0]
        self.col_2 = pos_2[1]
        self.current_board = board # slow but necessary
        self.pieceMoved = board[self.row_1][self.col_1]
        self.pieceCaptured = board[self.row_2][self.col_2]
        self.isPawnPromotion = isPawnPromotion
        self.pieceDesired = pieceDesired
        self.castlingMove = castlingMove
        self.isEnPassant = enPassantMove
        if self.isEnPassant:
            self.pieceCaptured = board[self.row_1][self.col_2]

        self.MoveID = hash((self.row_1, self.col_1, self.row_2, self.col_2, self.pieceDesired, self.isEnPassant)) # does not handle lists - how can i factor board state into this hash?
    def __eq__(self, other):
        if isinstance(other, Move):
            return other.MoveID == self.MoveID
        else:
            return False


ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
rowsToRanks = {rank: row for row, rank in ranksToRows.items()}
filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
colsToFiles = {file: col for col, file in filesToCols.items()}

def getRankFile(row, col):
    if col in range(0, 8) and row in range(0, 8):
        return(colsToFiles[col] + rowsToRanks[row])
    else:
        return "error - invalid row/col"

def pieceNumsToLetters(num):
    if num % 16 == 6:
        return("") # is having this an inefficiency?
    elif num % 16 == 5:
        return("R")
    elif num % 16 == 4:
        return("N")
    elif num % 16 == 3:
        return("B")
    elif num % 16 == 2:
        return("Q")
    else:
        return("K")

async def isAttackOn(piece, move, gS):
    if piece == 1: 
        if move.pieceMoved != 1:
            moves = []
            await gS.moveFunctions[move.pieceMoved % 16 - 1](move.row_2, move.col_2, moves, True) # get list of moves from current square
            for possibleAttack in moves:
                if possibleAttack.pieceCaptured % 16 == piece:
                    return True
            return False
    else:
        moves = []
        gS.moveFunctions[move.pieceMoved % 16 - 1](move.row_2, move.col_2, moves, True) # get list of moves from current square
        for possibleAttack in moves:
            if possibleAttack.pieceCaptured % 16 == piece:
                return True
        return False

async def getChessNotation(move, gSAfterMove: GameState = None):
    notation = ""
    if move.castlingMove:
        if move.col_1 > move.col_2:
            notation = "O-O-O"
        else:
            notation = "O-O"
    else:
        notation += pieceNumsToLetters(move.pieceMoved)
        # this part would be where ambiguity would be handled - unfortunately I'm too lazy to do that
        if move.pieceCaptured != 0:
            if move.pieceMoved % 16 == 6:
                notation += colsToFiles[move.col_1]
            notation += "x"
        notation += getRankFile(move.row_2, move.col_2)
        if move.isPawnPromotion:
            notation += "="
            notation += pieceNumsToLetters(move.pieceDesired)
        if gSAfterMove != None:
            if await gSAfterMove.inCheck():
                notation += "+"
    return notation

async def getChessNotationOfList(lst):
    result = []
    for move in lst:
        result.append(await getChessNotation(move))
    return result