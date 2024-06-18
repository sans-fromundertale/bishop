
# for i in range(depth):
#   undoMove()

import time
import math
import pygame
import Game
import AI
import os
import asyncio


pygame.init()
WIDTH = 524 # MAY BREAK THINGS
HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 30
PYTHONHASHSEED = 0
WHITEPERSPECTIVE = True

IMAGES = {}

SOUNDS = {
    "startSound": pygame.mixer.Sound("Sounds\\Start.wav"),
    "moveSound": pygame.mixer.Sound("Sounds\\Move.wav"),
    "captureSound": pygame.mixer.Sound("Sounds\\Capture.wav"),
    "checkSound": pygame.mixer.Sound("Sounds\\Check.wav"),
    "castleSound": pygame.mixer.Sound("Sounds\\Castle.wav"),
}

MUSICLIST = [] # FIND PUBLIC DOMAIN MUSIC
# feature idea - autodetect music that the user puts in a folder?

WAYSTOSAYYES = ["yes", "Yes", "YES", "y", "Y"]
WAYSTOSAYNO = ["no", "No", "NO", "n", "N"]

class EngineState():
    def __init__(self, copying = False):
        if not copying:
            self.humanWhitePlayer = True
            self.humanBlackPlayer = True
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()
            self.gS = Game.GameState()
            self.screen.fill(pygame.Color("white"))
            self.running = True
            self.validMoves = []
            self.gameOver = False
            self.humanWhitePlayer = True
            self.humanBlackPlayer = True
            self.humanTurn = True
            self.updatedHumanTurn = False
            self.prevEval = 0
            self.eval = 0
            self.evalBarFractionAway = 0
            self.mouseLocation = ()
            self.sq_selected = ()
            self.player_clicks = []
            self.sq_hovered = ()
            self.boardColors = [pygame.Color(100, 200, 200), pygame.Color(50, 150, 150), pygame.Color(50, 50, 255), pygame.Color(0, 0, 250)]
    

    async def setWhoIsAI(self, auto = False):
        if not auto:
            inp = input("Should white be a human player?")
            if inp in WAYSTOSAYYES:
                self.humanWhitePlayer = True
            elif inp in WAYSTOSAYNO:
                self.humanWhitePlayer = False
            else:
                print("Please answer either 'yes' or 'no'. Setting white to be an AI player by default.")
                self.humanWhitePlayer = False
            inp = input("Should black be a human player?")
            if inp in WAYSTOSAYYES:
                self.humanBlackPlayer = True
            elif inp in WAYSTOSAYNO:
                self.humanBlackPlayer = False
            else:
                print("Please answer either 'yes' or 'no'. Setting black to be an AI player by default.")
                self.humanBlackPlayer = False
        else:
            self.humanWhitePlayer = True
            self.humanBlackPlayer = False
        self.humanTurn = (self.gS.whiteToMove and self.humanWhitePlayer) or (not self.gS.whiteToMove and self.humanBlackPlayer)

    async def drawMenu(self, text, options, textColor = pygame.Color("Green")):
        font = pygame.font.SysFont("Times New Roman", 32, True, False)
        textObject = font.render(text, False, pygame.Color("Black"))

        #shadow to make text easier to see
        textLocation = pygame.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - textObject.get_width() // 2, HEIGHT // 2 - textObject.get_height() // 2)
        self.screen.blit(textObject, textLocation)
        self.screen.blit(textObject, textLocation.move(2,2))
        self.screen.blit(textObject, textLocation.move(0,2))
        self.screen.blit(textObject, textLocation.move(2,0))
        
        textObject = font.render(text, False, textColor)
        self.screen.blit(textObject, textLocation.move(1, 1))

    async def drawScreen(self, drawEvalBar = False):
        await self.drawBoard() # draws board
        await self.drawPieces() # draws pieces

        if self.gS.checkmate:
            self.gameOver = True
            if self.gS.whiteToMove:
                await self.drawMenu("Black wins by checkmate!", ["Reset", "Analysis Board", "Quit Game"])
            else:
                await self.drawMenu("White wins by checkmate!", ["Reset", "Analysis Board", "Quit Game"])
        elif self.gS.stalemate:
            self.gameOver = True
            await self.drawMenu("Stalemate!", ["Reset", "Analysis Board", "Quit Game"])

        if drawEvalBar:
            await self.drawEval()

        self.clock.tick(MAX_FPS)
        pygame.display.flip()
        # later - highlighting of last move, highlighting kings in check

    async def drawBoard(self): # Draw board. Top left is light.
        
        somethingSelected = self.sq_selected != ()
        for c in range(DIMENSION):
            for r in range(DIMENSION):
                if somethingSelected:
                        # complex-looking conditional - all it does is pass moves with all the possible special cases to be highlighted along with adjusting row/col for board perspective
                    #if await self.gS.squareUnderAttack((r,c)):
                        #color = pygame.Color(255, 0, 0)
                    if ((Game.Move(self.sq_selected, (r, c), self.gS.board) in self.validMoves) or (self.sq_selected ==(r, c)) or (Game.Move(self.sq_selected, (r, c), self.gS.board, True, 2) in self.validMoves) or (Game.Move(self.sq_selected, (r, c), self.gS.board, False, 0, True) in self.validMoves) or (Game.Move(self.sq_selected, (r, c), self.gS.board, False, 0, False, True) in self.validMoves)) and WHITEPERSPECTIVE or \
                        ((Game.Move(self.sq_selected, (7-r, c), self.gS.board) in self.validMoves) or (self.sq_selected == (7-r, c)) or (Game.Move(self.sq_selected, (7-r, c), self.gS.board, True, 2) in self.validMoves) or (Game.Move(self.sq_selected, (7-r, c), self.gS.board, False, 0, True) in self.validMoves) or (Game.Move(self.sq_selected, (7-r, c), self.gS.board, False, 0, False, True) in self.validMoves)) and not WHITEPERSPECTIVE:
                        color = self.boardColors[2 + ((r+c)%2)] # highlight the moves that are possible in color 2 (could maybe decouple into a highlightMoves() function)
                    else:
                        color = self.boardColors[(r + c) % 2]
                    
                else:
                    color = self.boardColors[(r + c) % 2]
                # draw the square
                pygame.draw.rect(self.screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    # later - board + piece color changes in settings?

    async def drawPieces(self):
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                if WHITEPERSPECTIVE:
                    piece = self.gS.board[r][c]
                    if piece != 0: # draw the pieces onto the board
                        if self.sq_selected == (r, c) or self.sq_selected == () and self.sq_hovered == (r, c):
                            self.screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE - 4, r*SQ_SIZE - 4, SQ_SIZE + 10, SQ_SIZE + 10)) # how do i rescale the images?
                        else:
                            self.screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE + 1, r*SQ_SIZE + 1, SQ_SIZE, SQ_SIZE))
                else: # same thing from black's perpective
                    piece = self.gS.board[7-r][c]
                    if piece != 0:
                        if self.sq_selected == (7-r, c) or self.sq_selected == () and self.sq_hovered == (7-r, c):
                            self.screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE - 4, r*SQ_SIZE - 4, SQ_SIZE + 10, SQ_SIZE + 10)) 
                        else:
                            self.screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE + 1, r*SQ_SIZE + 1, SQ_SIZE, SQ_SIZE))

    async def drawEval(self):
        blackBarHeight = (1 - self.evalBarFractionAway) * blackBarHeightFromEval(self.eval) + self.evalBarFractionAway * blackBarHeightFromEval(self.prevEval)
        blackBarTop = 0 if WHITEPERSPECTIVE else (HEIGHT - blackBarHeight)
        whiteBarTop = blackBarHeight if WHITEPERSPECTIVE else 0
        pygame.draw.rect(self.screen, pygame.Color(0,0,0), pygame.Rect(SQ_SIZE * 8, blackBarTop, WIDTH, blackBarHeight))
        pygame.draw.rect(self.screen, pygame.Color(250,250,250), pygame.Rect(SQ_SIZE * 8, whiteBarTop, WIDTH, HEIGHT - blackBarHeight))
        # print("Black bar height: %d Black bar top: %d White bar top: %d"%(blackBarHeight, blackBarTop, whiteBarTop))
        if self.evalBarFractionAway > 0:
            self.evalBarFractionAway -= 1.5 * (MAX_FPS ** -1)
        elif self.evalBarFractionAway < 0:
            self.evalBarFractionAway = 0
            # somehow doesn't draw the white bar properly???
        
def blackBarHeightFromEval(eval):
    if math.fabs(eval) > 65000:
        return HEIGHT if eval < 0 else 0
    else:
        return (HEIGHT // 2 + SQ_SIZE * 8 / math.pi * math.atan(0.27 * -eval))

async def copyES(eS: EngineState):
    newES = EngineState(True)
    newES.humanWhitePlayer = eS.humanWhitePlayer
    newES.humanBlackPlayer = eS.humanBlackPlayer
    newES.screen = eS.screen
    newES.clock = eS.clock
    newES.gS = eS.gS
    newES.running = eS.running
    newES.validMoves = eS.validMoves
    newES.gameOver = eS.gameOver
    newES.humanWhitePlayer = eS.humanWhitePlayer
    newES.humanBlackPlayer = eS.humanBlackPlayer
    newES.prevEval = eS.prevEval
    newES.eval = eS.eval
    newES.evalBarFractionAway = eS.evalBarFractionAway
    newES.humanTurn = eS.humanTurn
    newES.mouseLocation = eS.mouseLocation
    newES.sq_selected = eS.sq_selected
    newES.player_clicks = eS.player_clicks
    newES.sq_hovered = eS.sq_hovered
    newES.boardColors = eS.boardColors
    newES.updatedHumanTurn = False
    return newES
 



      
async def loadImages():
    for i in [17, 18, 19, 20, 21, 22, 1, 2, 3, 4, 5, 6]:
        imgName = "images\\"
        if int(i / 16) == 1:
            imgName = imgName + "w"
        else:
            imgName = imgName + "b"
        imgName = imgName + Game.pieceNumsToLetters(i)
        imgName = imgName + ".png"
        IMAGES[i] = pygame.image.load(imgName)

async def main():

    # WELCOME MESSAGE:

    print("Welcome to chess!")
    print("Controls:")
    print("z => undo move; space => switch perspectives; l => start/stop music; m => cycle music track; v => adjust volume; p => pause/play music")
    print("Debug tools:")
    print("Copy position to text file => c; play from position => x")

    # worth getting the controls more intuitive - one button to pause/play and also cycle music track to the first one

    # LOAD ENGINE STATE AND GLOBAL CONSTANTS:
    
    pygame.init()
    await loadImages()
    pygame.display.set_caption('Bishop')
    pygame.display.set_icon(IMAGES[3])   # ADD A PROPER ICON
    pygame.mixer.music.load("Sounds\\Start.wav")
    pygame.mixer.music.play()
    
    eS = EngineState()
    await eS.gS.findKingLocations()
    eS.validMoves = await eS.gS.getLegalMoves()
    AISet = False
    searching = False
    checkForAIMove = asyncio.create_task(asyncio.sleep(0.1))
    handlingInputs = False
    inputHandlerTask = asyncio.create_task(asyncio.sleep(0.1))
    q = asyncio.Queue()
    
    # set up tasks for use in main game loop
    
    
    # updateESTask = asyncio.create_task(updateES()) # might be necessarry if just `eS =` doesn't work

    

    while eS.running:

        if not AISet:
            AISet = True
            setAITask = asyncio.create_task(eS.setWhoIsAI())
            await setAITask

        await eS.drawScreen(True)
        
        if not handlingInputs:
            handlingInputs = True
            inputHandlerTask = asyncio.create_task(handleInputs(eS, q))
            await inputHandlerTask
        
        if inputHandlerTask.done():
            handlingInputs = False
        
        if not eS.humanTurn and len(eS.validMoves) != 0 and not eS.gameOver and not searching: 
            searching = True
            checkForAIMove = asyncio.create_task(MoveAI(eS, q)) 
            await checkForAIMove # doesn't actually pause the code!
            
        
        if checkForAIMove.done():
            searching = False
        
        while not q.empty():
            currentlyHumanTurn = eS.humanTurn
            eS = await q.get()
            if not eS.updatedHumanTurn:
                eS.humanTurn = currentlyHumanTurn
            else:
                # print("humanTurn updated")
                pass
            q.task_done()

        
        
        
        

        
def onBoard(mousePos):
    return mousePos[1] < WIDTH and mousePos[0] < HEIGHT


async def handleInputs(eS: EngineState, q):  
    newES = await copyES(eS)
    moveMade = False
    mouse_pos = pygame.mouse.get_pos()
    if mouse_pos[1] < WIDTH and mouse_pos[0] < HEIGHT:
        col = mouse_pos[0]//SQ_SIZE
        global WHITEPERSPECTIVE
        if WHITEPERSPECTIVE:
            row = mouse_pos[1]//SQ_SIZE
        else:
            row = 7 - (mouse_pos[1]//SQ_SIZE)
        newES.sq_hovered = (row, col)
    else:
        newES.sq_hovered = ()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            newES.running = False # close
        elif e.type == pygame.MOUSEBUTTONDOWN and eS.humanTurn:
            move = ()
            if eS.sq_selected != ():
                pieceSelected = eS.gS.board[eS.sq_selected[0]][eS.sq_selected[1]]
            else:
                pieceSelected = 0
            if not eS.gameOver and onBoard(mouse_pos): # a few minor bugs with sometimes not being able to take pieces properly
                if newES.sq_hovered != eS.sq_selected and ((eS.gS.board[row][col] != 0 and eS.gS.board[row][col] // 16 == int(eS.gS.whiteToMove)) or len(newES.player_clicks) == 1):
                    newES.sq_selected = newES.sq_hovered
                    newES.player_clicks.append(newES.sq_selected)
                    pieceClickedOn = eS.gS.board[newES.player_clicks[0][0]][newES.player_clicks[0][1]]
                    if len(newES.player_clicks) == 2: # 2 clicks means the player has tried to move something
                        # on pawn promotion, ask the player what piece they want to promote to and make the appropriate move
                        if (pieceClickedOn == 22 and newES.player_clicks[0][0] == 1) or (pieceClickedOn == 6 and newES.player_clicks[0][0] == 6):
                            # this should really be running after we check if the move is valid or not, but this currently does not cause problems because of intuition handling
                            pieceDesired = input("What piece would you like to promote to? (1 = Queen, 2 = Bishop, 3 = Knight, 4 = Rook) \n")
                            try: 
                                pieceNum = int(pieceDesired)
                                if pieceNum in range(1, 5): 
                                    move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, True, pieceNum + 1)
                                else:
                                    print("Please enter a number from 1-4.")
                                    newES.sq_selected = ()
                                    newES.player_clicks = []
                                    move = ()
                            except:
                                if pieceDesired in ["q", "Q", "queen", "Queen", "QUEEN"]:
                                    move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, True, 2)
                                elif pieceDesired in ["b", "B", "bishop", "Bishop", "BISHOP"]:
                                    move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, True, 3)
                                elif pieceDesired in ["n", "N", "k", "K", "knight", "Knight", "KNIGHT"]:
                                    move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, True, 4)
                                elif pieceDesired in ["r", "R", "rook", "Rook", "ROOK"]:
                                    move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, True, 5)
                                else:    
                                    print("Please enter either a positive integer or the name or first letter of a piece.")
                                    newES.sq_selected = ()
                                    newES.player_clicks = []
                                    move = ()

                        # on en passant, add the en passant flag to the move
                        elif newES.player_clicks[0][1] != newES.player_clicks[1][1] and pieceClickedOn % 16 == 6 and eS.gS.board[newES.sq_selected[0]][newES.sq_selected[1]] == 0:
                            move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board, False, 0, False, True)
                        else:
                            move = Game.Move(newES.player_clicks[0], newES.player_clicks[1], eS.gS.board)
                        # make move using object
                        if move != ():
                            for i in range(len(eS.validMoves)):
                                if move == eS.validMoves[i]:
                                    await newES.gS.makeMove(eS.validMoves[i]) # make the move with any appropriate flags
                                    moveMade = True # request a new list of valid moves
                                    if await newES.gS.inCheck(): # play a sound according to what type of move it was
                                        pygame.mixer.Sound.play(SOUNDS["checkSound"])
                                    elif newES.validMoves[i].pieceCaptured != 0:
                                        pygame.mixer.Sound.play(SOUNDS["captureSound"])
                                    elif newES.validMoves[i].castlingMove:
                                        pygame.mixer.Sound.play(SOUNDS["castleSound"]) # castle doesn't work for some reason
                                    else:
                                        pygame.mixer.Sound.play(SOUNDS["moveSound"])
                                    
                                    newES.sq_selected = ()
                                    newES.player_clicks = []
                            else: 
                                if moveMade == False: # intuition handling - allow player to select another of their own pieces
                                    if pieceSelected // 16 == eS.gS.board[row][col] // 16 and eS.gS.board[row][col] != 0:
                                        newES.player_clicks = [newES.sq_selected]
                                    else:
                                        newES.player_clicks = []
                                        newES.sq_selected = ()

                            # clear player selections to allow them to move again
                else: # player has clicked on the same square again, thus we clear their selection
                    newES.sq_selected = ()
                    newES.player_clicks = []
            else: # on game over
                pass
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_z:
                await newES.gS.undoMove() # undo and refresh valid moves
                if eS.humanTurn and not (eS.humanWhitePlayer and eS.humanBlackPlayer):
                    await newES.gS.undoMove() # undoes the AI move and the human move
                    AI.ENDGAME -= 0.02
                    AI.EARLYGAME += 0.1
                AI.EARLYGAME += 0.2
                AI.ENDGAME -= 0.04 # 0.04 because we add 0.02 later
                newES.gameOver = False
                moveMade = True
            elif e.key == pygame.K_SPACE:
                WHITEPERSPECTIVE = not WHITEPERSPECTIVE # switch perspectives (all this does is flip the way the board is drawn, not the way it's stored)
            elif e.key == pygame.K_m:
                musicno += 1            # switch current music track and remember whether it was playing or not
                musicno = musicno % len(MUSICLIST)
                musicfile = MUSICLIST[musicno]
                print("Switched music to " + musicfile)
                playing = pygame.mixer.music.get_busy()
                pygame.mixer.music.load(musicfile)
                if playing:
                    pygame.mixer.music.play()
            elif e.key == pygame.K_p:
                if pygame.mixer.music.get_busy():   # toggle music pause
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            elif e.key == pygame.K_l:
                if pygame.mixer.music.get_busy(): # toggle music play
                    pygame.mixer.music.stop() 
                else:
                    pygame.mixer.music.play()
            elif e.key == pygame.K_v:   # increase volume
                musicvol += 1
                musicvol = musicvol % 10 # if musicvol would be 1, it wraps around to 0
                pygame.mixer.music.set_volume(musicvol / 10.0)
            elif e.key == pygame.K_c:
                name = input("Enter name of file to save to or \"c\" to cancel: ")
                if name != "c":
                    positionFile = open("Saved Positions\\%s" % (name), "w")
                    for r in eS.gS.board:
                        for piece in r:
                            positionFile.write(str(piece) + " ")
                        positionFile.write("\n")
                    positionFile.write("%s\n%s\n%s\n%s\n%s" % (str(eS.gS.whiteToMove), str(eS.gS.currentCastleRights.whiteKingSide), str(eS.gS.currentCastleRights.whiteQueenSide), str(eS.gS.currentCastleRights.blackKingSide), str(eS.gS.currentCastleRights.blackQueenSide)))
                    positionFile.close()
            elif e.key == pygame.K_x:
                print("Saved positions: ")
                for position in os.listdir(path="Saved Positions"):
                    print(position)
                position = input("Enter name of saved position or \"c\" to cancel: ")
                if position != "c":
                    positionFile = open("Saved Positions\\%s" % (position), "r")
                    newES.gS.board.clear()
                    lineNo = 0
                    for line in positionFile:
                        lineNo+=1
                        if 8 >= lineNo and lineNo >= 1: # credit to https://stackoverflow.com/users/2069350/henry-keiter on https://stackoverflow.com/questions/21238242/python-read-file-into-2d-list because I was too lazy to write this myself
                            piece_strings = line.split()
                            row = [int(piece) for piece in piece_strings]
                            newES.gS.board.append(row)
                        elif lineNo == 9:
                            newES.gS.whiteToMove = True if line[0:-1] == "True" else False
                        elif lineNo == 10:
                            wks = bool(line)
                        elif lineNo == 11:
                            wqs = bool(line)
                        elif lineNo == 12:
                            bks = bool(line)
                        elif lineNo == 13:
                            bqs = bool(line)
                    newES.gS.currentCastleRights = Game.CastlingRights(wks, wqs, bks, bqs)
                    positionFile.close()
                    newES.gS.checkmate = False
                    newES.gS.pInCheck = False
                    newES.gS.pins = []
                    newES.gS.checks = []
                    newES.gS.whiteKingLocation = ()
                    newES.gS.blackKingLocation = ()
                    newES.gS.enPassantLocation = ()
                    await newES.gS.findKingLocations()
                    await newES.setWhoIsAI()
                    moveMade = True
                    
    if moveMade: # actually generate new list of valid moves                
        newES = await logicOnMoveMade(eS, newES)
        moveMade = False
    await q.put(newES)

async def MoveAI(eS: EngineState, q: asyncio.Queue):
    newES = await copyES(eS)
    # AI move finder logic
    AImove = await AI.findBestMoveMinMax(eS.gS, eS.validMoves, AI.MAX_DEPTH)
    await newES.gS.makeMove(AImove)
    if await newES.gS.inCheck(): # play a sound according to what type of move it was
        pygame.mixer.Sound.play(SOUNDS["checkSound"])
    elif AImove.pieceCaptured != 0:
        pygame.mixer.Sound.play(SOUNDS["captureSound"])
    elif AImove.castlingMove:
        pygame.mixer.Sound.play(SOUNDS["castleSound"]) #castle doesn't work for some reason
    else:
        pygame.mixer.Sound.play(SOUNDS["moveSound"])
    # print("AI found board with value", AI.boardValue(gS.board))
    await q.put(await logicOnMoveMade(eS, newES))

    
async def logicOnMoveMade(eS: EngineState, newES: EngineState):
    if len(eS.gS.notationMoveLog) < 7:
        print(eS.gS.notationMoveLog) # print the player-readable move log (still needs to handle shit like Rbd1)
    else:
        print(['...'] + eS.gS.notationMoveLog[-7:-1])
    newES.validMoves = await newES.gS.getLegalMoves()
    if AI.EARLYGAME > 0:
        AI.EARLYGAME -= 0.1
    AI.ENDGAME += 0.02
    newES.humanTurn = (newES.gS.whiteToMove and newES.humanWhitePlayer) or (not newES.gS.whiteToMove and newES.humanBlackPlayer)
    if newES.humanTurn != eS.humanTurn:
        newES.updatedHumanTurn = True
    newES.prevEval = eS.eval
    newES.evalBarFractionAway = 1
    newES.eval = await AI.eval(newES.gS)
    return newES



def resetGame(gS):
    for i in range(len(gS.moveLog)):
        gS.undoMove()

def enterAnalysis(gS):
    pass # analysis board!!!!!!!!!!!!!!!!!

def quitGame(gS):
    global running
    running = False

async def drawBoardState(screen, gS, sq_selected, validMoves, sq_hovered):
    await drawBoard(screen, gS, sq_selected, validMoves) # draws board
    await drawPieces(screen, gS, sq_selected, sq_hovered) # draws pieces
    # later - highlighting of last move, highlighting kings in check

async def drawBoard(screen, gS, sq_selected, validMoves): # Draw board. Top left is light.
    colors = [pygame.Color(100, 200, 200), pygame.Color(50, 150, 150), pygame.Color(50, 50, 255)]
    somethingSelected = sq_selected != ()
    for c in range(DIMENSION):
        for r in range(DIMENSION):
            if somethingSelected:
                    # complex-looking conditional - all it does is pass moves with all the possible special cases to be highlighted along with adjusting row/col for board perspective
                if ((Game.Move(sq_selected, (r, c), gS.board) in validMoves) or (sq_selected ==(r, c)) or (Game.Move(sq_selected, (r, c), gS.board, True, 2) in validMoves) or (Game.Move(sq_selected, (r, c), gS.board, False, 0, True) in validMoves) or (Game.Move(sq_selected, (r, c), gS.board, False, 0, False, True) in validMoves)) and WHITEPERSPECTIVE or \
                    ((Game.Move(sq_selected, (7-r, c), gS.board) in validMoves) or (sq_selected == (7-r, c)) or (Game.Move(sq_selected, (7-r, c), gS.board, True, 2) in validMoves) or (Game.Move(sq_selected, (7-r, c), gS.board, False, 0, True) in validMoves) or (Game.Move(sq_selected, (7-r, c), gS.board, False, 0, False, True) in validMoves)) and not WHITEPERSPECTIVE:
                    color = colors[2] # highlight the moves that are possible in color 2 (could maybe decouple into a highlightMoves() function)
                else:
                    color = colors[(r + c) % 2]
            else:
                color = colors[(r + c) % 2]
            # draw the square
            pygame.draw.rect(screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

# later - board + piece color changes in settings?

async def drawPieces(screen, pieces, sq_selected, sq_hovered):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            if WHITEPERSPECTIVE:
                piece = pieces.board[r][c]
                if piece != 0: # draw the pieces onto the board
                    if sq_selected == (r, c) or sq_selected == () and sq_hovered == (r, c):
                        screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE - 4, r*SQ_SIZE - 4, SQ_SIZE + 10, SQ_SIZE + 10)) # how do i rescale the images?
                    else:
                        screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE + 1, r*SQ_SIZE + 1, SQ_SIZE, SQ_SIZE))
            else: # same thing from black's perpective
                piece = pieces.board[7-r][c]
                if piece != 0:
                    if sq_selected == (7-r, c) or sq_selected == () and sq_hovered == (7-r, c):
                        screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE - 4, r*SQ_SIZE - 4, SQ_SIZE + 10, SQ_SIZE + 10)) 
                    else:
                        screen.blit(IMAGES[piece], pygame.Rect(c*SQ_SIZE + 1, r*SQ_SIZE + 1, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__": # good practice
    asyncio.run(main())