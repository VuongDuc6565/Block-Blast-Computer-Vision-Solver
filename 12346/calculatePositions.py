import os
from matplotlib import pyplot as plt
import cv2
import math
import copy
import numpy as np
import time
import random
from mss import mss
from PIL import Image

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def take_screenshot(filename=None):
    """Cross-platform screenshot function. Returns numpy array (BGR)."""
    with mss() as sct:
        # Capture entire screen
        monitor = sct.monitors[1]  # Primary monitor
        screenshot = sct.grab(monitor)
        # Convert to numpy array (BGRA -> BGR)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        if filename:
            filepath = os.path.join(SCRIPT_DIR, filename)
            try:
                cv2.imwrite(filepath, img)
            except Exception as e:
                print(f"Warning: Could not save screenshot to {filepath}: {e}")
            return img, filepath
    return img, None

def calculate(blocksDone):
    print("Capturing screenshot...")
    # Take screenshot directly to memory
    img, _ = take_screenshot("temp/screen.png")
    
    print("Processing board...")
    # CALIBRATED COORDINATES FOR WINDOWS
    # Board Area: [210:695, 32:517]
    imgBoard = img[210:695, 32:517]
    imgBoardGray = cv2.cvtColor(imgBoard, cv2.COLOR_BGR2GRAY)
    
    # Analyze board state (filled/empty cells)
    rows, cols = imgBoardGray.shape
    cell_h = rows // 8
    cell_w = cols // 8
    
    bigList = np.zeros(64)
    count = 0
    
    print("--- Board Analysis Debug ---")
    for i in range(8):
        for j in range(8):
            # Crop each cell with margin
            y1 = i * cell_h
            y2 = (i + 1) * cell_h
            x1 = j * cell_w
            x2 = (j + 1) * cell_w
            
            margin = 10 # Increase margin to avoid borders
            cell = imgBoardGray[y1+margin:y2-margin, x1+margin:x2-margin]
            
            avg_val = np.average(cell)
            
            # Debug print for first few cells
            if i < 2 and j < 2:
                print(f"Cell ({i},{j}) avg brightness: {avg_val:.2f}")
            
            # ADJUST THRESHOLD HERE
            # Based on user feedback: Empty cells ~80-146. 
            # Assuming filled cells are significantly brighter (> 180) or darker (< 50).
            # Let's try > 180 for filled cells.
            if avg_val > 180: 
                bigList[count] = 1
            else:
                bigList[count] = 0
            count += 1
    print("----------------------------")
            
    board = np.reshape(bigList, (8, -1))
    
    # Detect available blocks
    blocks = []
    
    # Calibrated Block Coordinates for Windows
    screenCoords = [
        [733, 880, 32, 193],   # Block 1
        [733, 880, 193, 354],  # Block 2
        [733, 880, 354, 517]   # Block 3
    ]
    
    coordsUsed = []
    
    for index, coords in enumerate(screenCoords):
        # Ensure coordinates are within image bounds
        y1 = max(0, min(img.shape[0], coords[0]))
        y2 = max(0, min(img.shape[0], coords[1]))
        x1 = max(0, min(img.shape[1], coords[2]))
        x2 = max(0, min(img.shape[1], coords[3]))
        
        blockImg = img[y1:y2, x1:x2]
        
        # Process block image to find shape
        grayBlock = cv2.cvtColor(blockImg, cv2.COLOR_BGR2GRAY)
        
        # Use a higher threshold to isolate the block from background
        # Background seems to be around 80-150 too? Let's try 170.
        _, thresh = cv2.threshold(grayBlock, 170, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            # Find largest contour
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 100:
                # Approximate shape to 5x5 grid (max block size)
                x, y, w, h = cv2.boundingRect(c)
                roi = thresh[y:y+h, x:x+w]
                
                # Resize to a standard small size to determine shape
                grid_rows = max(1, round(h / 60))
                grid_cols = max(1, round(w / 60))
                
                # Resize ROI to grid size
                small_roi = cv2.resize(roi, (grid_cols, grid_rows), interpolation=cv2.INTER_NEAREST)
                
                # Convert to binary matrix (0/1)
                block_shape = (small_roi > 128).astype(int)
                
                blocks.append(block_shape)
                coordsUsed.append([block_shape, index, x1, y1, coords])

    # --- Helper Functions ---
    def swap(blocks, i, fi):
        temp = blocks[i]
        blocks[i] = blocks[fi]
        blocks[fi] = temp
        return blocks

    def permutations(blocks, fi):
        result = []
        if fi == len(blocks) - 1:
            return [blocks[:]]
        for i in range(fi, len(blocks)):
            blocks = swap(blocks, i, fi)
            result.extend(permutations(blocks, fi + 1))
            blocks = swap(blocks, i, fi)
        return result

    def waysToFit(figure, board):
        firstFit = []
        for rowNumber in range(board.shape[0]):
            for cellNumber in range(board.shape[1]):
                cellValue = board[rowNumber][cellNumber]
                if (cellValue == 1 and figure[0][0] == 0) or (cellValue == 0 and figure[0][0] == 1) or (cellValue == 0 and figure[0][0] == 0):
                    canFit = True
                    if cellNumber + figure.shape[1] > board.shape[0]:
                        canFit = False
                    elif rowNumber + figure.shape[0] > board.shape[1]:
                        canFit = False
                    else:
                        for figureRow in range(figure.shape[0]):
                            for figureColumn in range(figure.shape[1]):
                                if figure[figureRow][figureColumn] == 1:
                                    if board[rowNumber + figureRow][cellNumber + figureColumn] == 1:
                                        canFit = False
                                        break
                            if not canFit: break
                    if canFit:
                        firstFit.append([figure, rowNumber, cellNumber])
        return firstFit

    def updateBoard(board, figure, x, y):
        board = board.copy()
        for row in range(figure.shape[0]):
            for column in range(figure.shape[1]):
                board[x+row][y+column] += figure[row][column]
        
        rowsToClear = []
        for row in range(board.shape[0]):
            if np.all(board[row, :] == 1):
                 rowsToClear.append(row)
        
        colsToClear = []
        for col in range(board.shape[1]):
            if np.all(board[:, col] == 1):
                colsToClear.append(col)
        
        for row in range(board.shape[0]):
            for column in range(board.shape[1]):
                if row in rowsToClear or column in colsToClear:
                    board[row][column] = 0
                    
        clearedRow = len(colsToClear) + len(rowsToClear)
        return board, clearedRow

    originalBoard = board.copy()
    allPermutations = permutations(blocks, 0)
    
    def tryOutAllMethods(board, permutation, fi):
        workingPaths = []
        pathTaken = []
        
        if len(permutation) == 0: return []
        
        for _, rowToFit, colToFit in waysToFit(permutation[0], board):
            board1, clearedRow = updateBoard(board, permutation[0], rowToFit, colToFit)
            pathTaken.append([permutation[0], rowToFit, colToFit, clearedRow])
            
            if len(permutation) > 1:
                for _, rowToFit2, colToFit2 in waysToFit(permutation[1], board1):
                    board2, clearedRow2 = updateBoard(board1, permutation[1], rowToFit2, colToFit2)
                    pathTaken.append([permutation[1], rowToFit2, colToFit2, clearedRow2])
                    
                    if len(permutation) > 2:
                        for _, rowToFit3, colToFit3 in waysToFit(permutation[2], board2):
                            board3, clearedRow3 = updateBoard(board2, permutation[2], rowToFit3, colToFit3)
                            pathTaken.append([permutation[2], rowToFit3, colToFit3, clearedRow3])
                            pathTaken.append(board3)
                            workingPaths.append(copy.deepcopy(pathTaken))
                            pathTaken.pop()
                            pathTaken.pop()
                    else:
                        pathTaken.append(board2)
                        workingPaths.append(copy.deepcopy(pathTaken))
                        pathTaken.pop()
                    pathTaken.pop()
            else:
                pathTaken.append(board1)
                workingPaths.append(copy.deepcopy(pathTaken))
                pathTaken.pop()
            pathTaken.pop()
            
        return workingPaths

    allSolutions = []
    
    # --- DEBUG LOGGING ---
    print(f"Detected {len(blocks)} blocks.")
    for i, b in enumerate(blocks):
        print(f"Block {i} shape:\n{b}")
    print("Board state:\n", board)
    # ---------------------
    
    print(f"Calculating solutions for {len(allPermutations)} permutations...")
    for index, p in enumerate(allPermutations):
        results = tryOutAllMethods(board, copy.deepcopy(p), 0)
        if results:
            allSolutions.append(results)
            
    print(f"Found {len(allSolutions)} solution sets.")
    return allSolutions, blocks, coordsUsed, originalBoard

def bestOption(output, moveToReset, copyOfBoard):
    if not output: return [] # Fix IndexError if no solutions

    def waysToFit(figure, board, optimized=False):
            if optimized==False:
                firstFit = []
                for rowNumber in range(board.shape[0]):
                    # print(board[rowNumber])
                    for cellNumber in range(board.shape[1]):
                        # print(board[rowNumber][cellNumber])
                        cellValue = board[rowNumber][cellNumber]
                        if (cellValue == 1 and figure[0][0] == 0) or (cellValue == 0 and figure[0][0] == 1) or (cellValue == 0 and figure[0][0] == 0):
                            canFit = True
                            if cellNumber + figure.shape[1] > board.shape[0]:
                                canFit = False
                                break
                            if rowNumber + figure.shape[0] > board.shape[1]:
                                canFit = False
                                break
                            for figureRow in range(figure.shape[0]):
                                for figureColumn in range(figure.shape[1]):
                                    if figure[figureRow][figureColumn] == 1:
                                        if board[rowNumber + figureRow][cellNumber + figureColumn] == 1:
                                            canFit = False
                                            break
                            if canFit:
                                firstFit.append([figure, rowNumber, cellNumber])
                return firstFit
            else:
                howManyFits = 0
                for rowNumber in range(board.shape[0]):
                    # print(board[rowNumber])
                    for cellNumber in range(board.shape[1]):
                        # print(board[rowNumber][cellNumber])
                        cellValue = board[rowNumber][cellNumber]
                        if (cellValue == 1 and figure[0][0] == 0) or (cellValue == 0 and figure[0][0] == 1) or (cellValue == 0 and figure[0][0] == 0):
                            canFit = True
                            if cellNumber + figure.shape[1] > board.shape[0]:
                                canFit = False
                                break
                            if rowNumber + figure.shape[0] > board.shape[1]:
                                canFit = False
                                break
                            for figureRow in range(figure.shape[0]):
                                for figureColumn in range(figure.shape[1]):
                                    if figure[figureRow][figureColumn] == 1:
                                        if board[rowNumber + figureRow][cellNumber + figureColumn] == 1:
                                            canFit = False
                                            break
                            if canFit:
                                howManyFits += 1
                return howManyFits
    def countHoles(board, number):
        def traverseHoles(board, row, col):
            countHoles = 0
            if row-1 >= 0:
                if board[row-1][col] == number:
                    board[row-1][col] = abs(number-1)
                    countHoles += 1
                    countHoles += traverseHoles(board, row-1, col)
            if row+1 < board.shape[0]:
                if board[row+1][col] == number:
                    board[row+1][col] = abs(number-1)
                    countHoles += 1
                    countHoles += traverseHoles(board, row+1, col)
            if col-1 >= 0:
                if board[row][col-1] == number:
                    board[row][col-1] = abs(number-1)
                    countHoles += 1
                    countHoles += traverseHoles(board, row, col-1)
            if col+1 < board.shape[1]:
                if board[row][col+1] == number:
                    board[row][col+1] = abs(number-1)
                    countHoles += 1
                    countHoles += traverseHoles(board, row, col+1)
            return countHoles
        holes = []
        for row in range(board.shape[0]):
            for col in range(board.shape[1]):
                if board[row][col] == number:
                    numberOfHoles = traverseHoles(board, row, col)
                    if numberOfHoles == 0:
                        holes.append(1)
                    else:
                        if numberOfHoles < 8:
                            holes.append(numberOfHoles)
        return holes
    def creviceCount(board):
        creviceCount = 0
        for row in range(board.shape[0]):
            for col in range(board.shape[1]):
                if board[row][col] == 1:
                    if row+1 < board.shape[0]-2 and col+1 < board.shape[1]-2:
                        if board[row+1][col] != 1:
                            creviceCount += 1
                        if board[row+1][col+1] != 1:
                            creviceCount += 1
                        if board[row][col+1] != 1:
                            creviceCount += 1
        for row in range(board.shape[0]-1, 0, -1):
            for col in range(board.shape[1]-1, 0, -1):
                if board[row][col] == 1:
                    if row-1 >= 0 and col-1 >= 0:
                        if board[row-1][col] != 1:
                            creviceCount += 1
                        if board[row-1][col-1] != 1:
                            creviceCount += 1
                        if board[row][col-1] != 1:
                            creviceCount += 1
        for row in range(board.shape[0]-1, 0, -1):
            for col in range(board.shape[1]):
                if board[row][col] == 1:
                    if row-1 >= 0 and col+1 < board.shape[1]-2:
                        if board[row-1][col] != 1:
                            creviceCount += 1
                        if board[row-1][col+1] != 1:
                            creviceCount += 1
                        if board[row][col+1] != 1:
                            creviceCount += 1
        for row in range(board.shape[0]):
            for col in range(board.shape[1]-1, 0, -1):
                if board[row][col] == 1:
                    if row+1 < board.shape[0]-2 and col-1 >= 0:
                        if board[row+1][col] != 1:
                            creviceCount += 1
                        if board[row+1][col-1] != 1:
                            creviceCount += 1
                        if board[row][col-1] != 1:
                            creviceCount += 1
        return creviceCount
    def squareCheck(area):
        numBRFit = np.array([[0, 0, 1], 
                            [0, 0, 1], 
                            [1, 1, 1]])
        numBLFit = np.array([[1, 0, 0], 
                            [1, 0, 0], 
                            [1, 1, 1]])
        numTRFit = np.array([[1, 1, 1], 
                            [0, 0, 1], 
                            [0, 0, 1]])
        numTLFit = np.array([[1, 1, 1], 
                            [1, 0, 0], 
                            [1, 0, 0]])
        
        if np.array_equal(area, numBRFit) or np.array_equal(area, numBLFit) or np.array_equal(area, numTRFit) or np.array_equal(area, numTLFit):
            return 0
        
        rowIndicesFilled = np.array([])
        colIndicesFilled = np.array([])
        for row in range(area.shape[0]):
            for col in range(area.shape[1]):
                if area[row][col] == 1:
                    rowIndicesFilled = np.append(rowIndicesFilled, row)
                    colIndicesFilled = np.append(colIndicesFilled, col)
        if len(colIndicesFilled) == 0 or len(rowIndicesFilled) == 0:
            return 0
        minX = min(colIndicesFilled)
        maxX = max(colIndicesFilled)
        minY = min(rowIndicesFilled)
        maxY = max(rowIndicesFilled)
        count = 0
        for row in range(int(minY), int(maxY)+1):
            for col in range(int(minX), int(maxX)+1):
                if area[row][col] == 0:
                    count += 1
        return count

    def roughEdgesScore(board):
        count = 0
        for row in range(1, board.shape[0] - 1):
            for col in range(1, board.shape[1] - 1):
                count += squareCheck(board[row-1:row+2, col-1:col+2])
        return count
    def assignPoints(board, output):
        num2x2Fit = waysToFit(np.array([[1, 1], [1, 1]]), np.array(board), True)
        num3x3Fit = waysToFit(np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]), np.array(board), True)
        num5x1Fit = waysToFit(np.array([[1], [1], [1], [1], [1]]), np.array(board), True)
        num4x1Fit = waysToFit(np.array([[1], [1], [1], [1]]), np.array(board), True)
        num3x1Fit = waysToFit(np.array([[1], [1], [1]]), np.array(board), True)

        num1x5Fit = waysToFit(np.array([[1, 1, 1, 1, 1]]), np.array(board), True)
        num1x4Fit = waysToFit(np.array([[1, 1, 1, 1]]), np.array(board), True)
        num1x3Fit = waysToFit(np.array([[1, 1, 1]]), np.array(board), True)

        numBRFit = waysToFit(np.array([[0, 0, 1], 
                                      [0, 0, 1], 
                                      [1, 1, 1]]), np.array(board), True)
        numBLFit = waysToFit(np.array([[1, 0, 0], 
                                      [1, 0, 0], 
                                      [1, 1, 1]]), np.array(board), True)
        numTRFit = waysToFit(np.array([[1, 1, 1], 
                                      [0, 0, 1], 
                                      [0, 0, 1]]), np.array(board), True)
        numTLFit = waysToFit(np.array([[1, 1, 1], 
                                      [1, 0, 0], 
                                      [1, 0, 0]]), np.array(board), True)

        #                                                                                                                                                                                       Checks if a row clears                            Counts number of holes (Empty)        Num of spaces filled                Counts the number of holes (filled)   How many are two or one holes?                                                   Amount of standalone islands                                                     Rough edges count                  favors later clears
        return numBRFit*10 + numBLFit*10 + numTRFit*10 + numTLFit*10 + num2x2Fit*5 + num3x3Fit*20 + num5x1Fit*2 + num1x5Fit*2 + num4x1Fit*0.8 + num3x1Fit*0.5 + num1x4Fit*0.8 + num1x3Fit*0.5 + sum([i[3] for i in output[:-1] if i[3] > 0])*30 - len(countHoles(board.copy(), 0))*5 - abs(np.count_nonzero(board==1))*0.5- len(countHoles(board.copy(), 1))*10 - len([i for i in countHoles(board.copy(), 1) if i == 2 or i == 1 or i == 3])*20 - len([i for i in countHoles(board.copy(), 0) if i == 2 or i == 1 or i == 3])*20 - roughEdgesScore(board.copy()) * 0.5 + [index for index, i in enumerate(output[:-1]) if i[3]>0][0] if len([index for index, i in enumerate(output[:-1]) if i[3]>0]) > 0 else 0
    def assignPointsVisualizer(board, output):
        # Simplified visualizer to avoid print spam
        pass

    numberOfSolutions = sum(len(row) for row in output)
    # print(f"number of possible solutions: {numberOfSolutions}")
    if numberOfSolutions > 50000:
        maxScore = 0
        bestArray = []
        # print("we doing it the easy way")
        for i in range(len(output)):
            for j in range(100):
                a = random.randint(0, len(output[i])-1)
                score = assignPoints(output[i][a][-1], output[i][a])
                if score > maxScore:
                    maxScore = score
                    bestArray = output[i][a]
        if bestArray != []:
            assignPointsVisualizer(bestArray[-1], bestArray)
            return bestArray

    firstMoveClear = []
    secondMoveClear = []
    thirdMoveClear = []
    for permutation in output:
        for solution in permutation:
            if len(solution) == 4:
                if solution[0][3] > 0:
                    firstMoveClear.append(solution)
                elif solution[1][3] > 0:
                    secondMoveClear.append(solution)
                elif solution[2][3] > 0:
                    thirdMoveClear.append(solution)
            elif len(solution) == 3:
                if solution[0][3] > 0:
                    secondMoveClear.append(solution)
                elif solution[1][3] > 0:
                    thirdMoveClear.append(solution)
            elif len(solution) == 2:
                if solution[0][3] > 0:
                    thirdMoveClear.append(solution)

    
    maxScore = -10000
    bestArray = []
    # print("MOVE TO RESET: " + str(moveToReset))
    if numberOfSolutions >= 5000 and np.count_nonzero(copyOfBoard==1) <= 40:
        # print("Playing offensively")
        if moveToReset == 3:
            for i in thirdMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                print(f"Max score: {maxScore}")
                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            for i in secondMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                print(f"Max score: {maxScore}")
                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            for i in firstMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                print(f"Max score: {maxScore}")
                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            return output[0][0]
        elif moveToReset == 2:
            goodOnes = []
            for i in secondMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
                if i[len(i)-2][3] > 0:
                    goodOnes.append(i)
            for i in firstMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
                if i[len(i)-2][3] > 0 or i[len(i)-3][3] > 0:
                    goodOnes.append(i)
            maxGoodOnesScore = -100000
            goodOnesArray = []
            for i in goodOnes:
                score = assignPoints(i[-1], i)
                if score > maxGoodOnesScore:
                    maxGoodOnesScore = score
                    bestArray = i
            if goodOnesArray != []:
                return goodOnesArray
            if bestArray != []:
                print(f"Max score: {maxScore}")

                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            for i in thirdMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                print(f"Max score: {maxScore}")
                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            return output[0][0]
        elif moveToReset == 1:
            for i in firstMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
                if i[len(i)-2][3] > 0 or i[len(i)-3][3] > 0:
                    return i
            for i in thirdMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                print(f"Max score: {maxScore}")

                assignPointsVisualizer(bestArray[-1], bestArray)

                return bestArray
            for i in secondMoveClear:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
            if bestArray != []:
                return bestArray
            return output[0][0]
    else:
        # print("Playing defensively")
        for permutation in output:
            for i in permutation:
                score = assignPoints(i[-1], i)
                if score > maxScore:
                    maxScore = score
                    bestArray = i
        print(f"Max score: {maxScore}")

        assignPointsVisualizer(bestArray[-1], bestArray)

        return bestArray