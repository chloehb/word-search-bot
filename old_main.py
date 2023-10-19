from pyautogui import *
import pyautogui
import time
import keyboard
import cv2
import pytesseract as pyt
from pytesseract import Output
import numpy as np
import math
import time

pyt.pytesseract.tesseract_cmd = "C:\\Users\\Chloe_B\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

def preprocess(image_path):
    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 27, 2)
    kernel = np.ones((1, 1), np.uint8)
    dilate = cv2.dilate(bw, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    erode = cv2.erode(dilate, kernel, iterations=1)
    morph = cv2.morphologyEx(erode, cv2.MORPH_CLOSE, kernel)
    no_noise = cv2.medianBlur(morph, 3)
    cv2.imwrite("temp/no_noise.jpg", no_noise)
    
    roi_main, roi_col, grid_corner = separateSections(gray, no_noise)
    cv2.imwrite("temp/roi_col.jpg", roi_col)

    bw = cv2.threshold(roi_main, 127, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((1, 1), np.uint8)
    dilate = cv2.dilate(bw, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    erode = cv2.erode(dilate, kernel, iterations=1)
    morph = cv2.morphologyEx(erode, cv2.MORPH_CLOSE, kernel)
    roi_main = thickFont(morph)

    cv2.imwrite("temp/roi_main.jpg", roi_main)
    return roi_main, roi_col, grid_corner

def separateSections(gray, processedImg):
    # separate main grid and word list
    im_h, im_w = processedImg.shape
    
    col_x = 580

    grid_tcorner = (105, 105)
    grid_bcorner = (515, 515)

    roi_col = processedImg[40:im_h, col_x:im_w]
    roi_main = gray[grid_tcorner[1]:grid_bcorner[1], grid_tcorner[0]:grid_bcorner[0]]

    return roi_main, roi_col, grid_tcorner

def thickFont(img):
    img = cv2.bitwise_not(img)
    kernel = np.ones((2, 2), np.uint8)
    erode = cv2.dilate(img, kernel, iterations=1)
    thick = cv2.bitwise_not(erode)
    return thick

def getWordBank(roi_col):
    # read side words into list
    myconfig = r"--psm 4 --oem 3"
    bank_text = pyt.image_to_string(roi_col, config=myconfig, output_type=Output.STRING)
    
    word_bank = []
    for term in bank_text.splitlines():
        if term != '':
            word_bank.append(term)
    if len(word_bank) != 12:
        print('Adjusting word bank...')
        word_bank = []
        hImg, wImg = roi_col.shape
        myconfig = r"--psm 6 --oem 3"
        d = pyt.image_to_data(roi_col, config=myconfig, output_type=Output.DICT)
        n_boxes = len(d['level'])
        for i in range(n_boxes):
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            if h<50 and d['text'][i] != '':
                word_bank.append(d['text'][i])

    return word_bank

def getLetterGrid(roi_main):
    # read main grid into 2d array of letters
    myconfig = r'--psm 6 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ" '

    hImg, wImg = roi_main.shape
    boxes = pyt.image_to_boxes(roi_main, config=myconfig)

    # the word grid to be populated by the temp_arr
    word_grid=[]
    # stores the rows of the letter grid
    temp_arr=[]
    # used to tell when the next row/column is read
    prev_y= 0
    prev_x = -15

    for b in boxes.splitlines():
        b = b.split(' ')
        x,y,w,h = int(b[1]),int(b[2]),int(b[3]),int(b[4])
        letter_box=roi_main[hImg-h:hImg-y, x:w]

        # this checks to see if the box containing the letter is less than 90% blank
        if np.count_nonzero(letter_box)/(len(letter_box)*len(letter_box[0]))<.9 and abs(prev_x-x)>20:

            if abs(prev_y-y)>20 and len(temp_arr)>0:
                if len(temp_arr) < 10:
                    temp_arr.pop()
                    dist = 10 - len(temp_arr)
                    for i in range(0, dist):
                        temp_arr.append('')
                word_grid.append(temp_arr)
                temp_arr=[]
            elif abs(prev_x-x)>60 and len(temp_arr)<10:
                if len(temp_arr) != 0:
                    temp_arr.pop()
                dist = math.ceil(abs(prev_x-x) / 45)
                for i in range(0, dist):
                    temp_arr.append('')
            
            temp_arr.append(b[0])
            prev_y = y
            prev_x = x
        

    if len(temp_arr) < 10:
        temp_arr.pop()
        dist = 10 - len(temp_arr)
        for i in range(0, dist):
            temp_arr.append('')
    word_grid.append(temp_arr)

    return fillInBlanks(roi_main, word_grid)

def fillInBlanks(roi_main, word_grid):
    myconfig = r'--psm 6 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ" '
    grid_h, grid_w = roi_main.shape
    cell_h = int(grid_h / 10)
    cell_w = int(grid_w /10)

    for row in range(0, 10):
        y_start = row * cell_h
        y_end = y_start + cell_h
        for col in range(0, 10):
            x_start = col * cell_w
            x_end = x_start + cell_w
            if word_grid[row][col] == '':
                cell_region = roi_main[y_start:y_end, x_start:x_end]
                res = pyt.image_to_string(cell_region, config=myconfig, output_type=Output.STRING)

                if len(res) > 1:
                    res = res[0]
                    print(res)
                elif len(res) < 1:
                    res = ''

                word_grid[row][col] = res    
    print("Letter grid: " + str(word_grid)) 
    return word_grid

# iterate through grid and check for word in all directions 
def findWordInGrid(chars, word_grid):
    # determine start and end array locations in grid for word
    array_start = (0,0)
    array_end = (0,0)

    num_rows = 10
    num_cols = 10
    found = False
    for row in range(0, num_rows):
        for col in range(0, num_cols):
            if word_grid[row][col] == chars[0] or word_grid[row][col] == '' or chars[0] == '':
                letter = 0
                while col + letter < num_cols and (word_grid[row][col + letter] == chars[letter] or word_grid[row][col + letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col + letter - 1, row)
                        found = True
                        break

                letter = 0
                while col - letter >= 0 and (word_grid[row][col - letter] == chars[letter] or word_grid[row][col - letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and (word_grid[row + letter][col] == chars[letter] or word_grid[row + letter][col] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and (word_grid[row - letter][col] == chars[letter] or word_grid[row - letter][col] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col, row - letter + 1)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and col + letter < num_cols and (word_grid[row + letter][col + letter] == chars[letter] or word_grid[row + letter][col + letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col + letter - 1, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and col - letter >= 0 and (word_grid[row - letter][col - letter] == chars[letter] or word_grid[row - letter][col - letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row - letter + 1)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and col - letter >= 0 and (word_grid[row + letter][col - letter] == chars[letter] or word_grid[row + letter][col - letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and col + letter < num_cols and (word_grid[row - letter][col + letter] == chars[letter] or word_grid[row - letter][col + letter] == '' or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col + letter - 1, row - letter + 1)
                        found = True
                        break
            if found:
                break

    return (array_start, array_end)

def convertCoords(found_words, cell_w, cell_h):
    found_coords = {}
    for word in found_words.keys():
        start = (int(found_words[word][0][0])*cell_w + cell_w/2, int(found_words[word][0][1])*cell_h + cell_h/2)
        end = (int(found_words[word][1][0])*cell_w + cell_w/2, int(found_words[word][1][1])*cell_h + cell_h/2)
        found_coords[word] = (start,end)
    return found_coords


def findGameScreen(img_path):
    
    # found game screen -> store coords
    main_coords = str(pyautogui.locateOnScreen(img_path, grayscale=True, confidence=0.85))
    main_coords = main_coords[4:-1].split(', ')
    left = int(main_coords[0].split('=')[1])
    top = int(main_coords[1].split('=')[1])
    width = int(main_coords[2].split('=')[1])
    height = int(main_coords[3].split('=')[1])

    return left, top, width, height

def selectWords(left, top, grid_corner, found_coords):
    for word in found_coords.keys():
        pyautogui.moveTo(int(found_coords[word][0][0]+ left + grid_corner[0]), int(found_coords[word][0][1] + top + grid_corner[1]))
        pyautogui.dragTo(int(found_coords[word][1][0]+ left + grid_corner[0]), int(found_coords[word][1][1] + top + grid_corner[1]), 1, button='left')
        time.sleep(.5)

if __name__ == '__main__':

    while pyautogui.locateOnScreen('gamescreen.jpg', grayscale=True, confidence=0.85) == None:
        print('I can NOT see the screen')
        time.sleep(1)
    left, top, width, height = findGameScreen('gamescreen.jpg')

    stop = False
    games_played = 0
    play_btn = (400, 531)

    print("Bot session started.")
    print("------------------------------------------------------------------------------------------------")

    # press the play button
    pyautogui.click(x=(play_btn[0] + left), y=(play_btn[1] + top))

    while not stop:
        time.sleep(2)
        pyautogui.screenshot('temp/game.jpg', [left, top, width, height])

        # process game data
        img_path = "temp/game.jpg"

        roi_grid, roi_bank, grid_corner = preprocess(img_path)
        grid_h, grid_w = roi_grid.shape

        word_bank = getWordBank(roi_bank)
        word_grid = getLetterGrid(roi_grid)

        found_words = {}
        for word in word_bank:
            chars = [c for c in str(word)]
            found_words[word] = findWordInGrid(chars, word_grid)
            if found_words[word] == ((0,0),(0,0)):
                print("Error: \'{}\' not found in grid".format(word))
                for i in range(0, len(chars)):
                    copy_word = [c for c in str(word)]
                    copy_word[i] = ''
                
                    found_words[word] = findWordInGrid(copy_word, word_grid)
                    if found_words[word] != ((0,0),(0,0)):
                        cp = ""
                        for x in copy_word:
                            if x != '':
                                cp += x
                            else:
                                cp += '_'
                        print("\'{}\' found in grid when altered to \'{}\'".format(word, cp))
                        break

        cell_h = int(grid_h / 10)
        cell_w = int(grid_w /10)
        found_coords = convertCoords(found_words, cell_w, cell_h)
        print("\nFound coordinates: " + str(found_coords))

        # input solutions to game interface
        selectWords(left, top, grid_corner, found_coords)
        fail = False
        timeout = time.time() + 5
        while pyautogui.locateOnScreen('solved.jpg', grayscale=True, confidence=0.85) == None:
            time.sleep(1)
            if time.time() > timeout:
                fail = True
                break
        if fail:
            print("------------------------------------------------------------------------------------------------")
            print("Bot session terminated.")
            print('Last attempted puzzle was not fully solved.')
            if games_played == 1:
                print(str(games_played) + ' puzzle solved.')
            else:
                print(str(games_played) + ' puzzles solved.')
            stop = True
            break  
        
        l_s, t_s, w_s, h_s = findGameScreen('solved.jpg')
        games_played += 1

        # home_btn = (97, 112)
        # new_pzl_btn = (317, 110)
        timeout = time.time() + 5
        print("\nPress 'q' to stop botting session.\n")
        while True: 
            if keyboard.is_pressed('q'): 
                stop = True
                print("------------------------------------------------------------------------------------------------")
                print("Bot session terminated.")
                if games_played == 1:
                    print(str(games_played) + ' puzzle solved.')
                else:
                    print(str(games_played) + ' puzzles solved.')
                pyautogui.click(x=(97 + l_s), y=(112 + t_s))
                break  
            if time.time() > timeout:
                print('\nNew puzzle...\n')
                pyautogui.click(x=(317 + l_s), y=(110 + t_s))
                break
            