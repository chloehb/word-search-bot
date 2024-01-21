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
import copy
from extractData import *
from notFound import *
 
def findWordInGrid(chars, word_grid):
    # iterate through grid and check for word in all directions

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
                while col + letter < num_cols and (word_grid[row][col + letter] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col + letter - 1, row)
                        found = True
                        break

                letter = 0
                while col - letter >= 0 and (word_grid[row][col - letter] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and (word_grid[row + letter][col] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and (word_grid[row - letter][col] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col, row - letter + 1)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and col + letter < num_cols and (word_grid[row + letter][col + letter] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col + letter - 1, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and col - letter >= 0 and (word_grid[row - letter][col - letter] == chars[letter] or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row - letter + 1)
                        found = True
                        break
                letter = 0
                while row + letter < num_rows and col - letter >= 0 and (word_grid[row + letter][col - letter] == chars[letter]or chars[letter] == ''):
                    letter += 1
                    if letter == len(chars):
                        array_start = (col, row)
                        array_end = (col - letter + 1, row + letter - 1)
                        found = True
                        break
                letter = 0
                while row - letter >= 0 and col + letter < num_cols and (word_grid[row - letter][col + letter] == chars[letter] or chars[letter] == ''):
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

def findAllWords(adj_grid, word_bank):
    words_missing = []
    adj = False

    found_words = {}
    word_list = word_bank
    count = 0
    timeout = time.time() + 10
    while word_list != [] and time.time() < timeout:
        for word in word_list:
            chars = [c for c in str(word)]
            found_words[word] = findWordInGrid(chars, adj_grid)
            if found_words[word] == ((0,0),(0,0)):
                print("Error: \'{}\' not found in grid".format(word))
                if count == 0:
                    words_missing.append(word)
                    print("words missing: " + str(words_missing))
                for i in range(0, len(chars)):
                    copy_word = [c for c in str(word)]
                    copy_word[i] = ''
                
                    found_words[word] = findWordInGrid(copy_word, adj_grid)
                    if found_words[word] != ((0,0),(0,0)):
                        cp = ""
                        for i in range(0, len(copy_word)):
                            if copy_word[i] != '':
                                cp += copy_word[i]
                            else:
                                cp += '_'
                                change_pos = []
                                adj = True

                                if found_words[word][1][0] - found_words[word][0][0] > 0:
                                    change_pos.append(int(found_words[word][0][0] + i))
                                elif found_words[word][1][0] - found_words[word][0][0] == 0:
                                    change_pos.append(int(found_words[word][0][0]))
                                else:
                                    change_pos.append(int(found_words[word][0][0] - i))
                                if found_words[word][1][1] - found_words[word][0][1] > 0:
                                    change_pos.append(int(found_words[word][0][1] + i))
                                elif found_words[word][1][1] - found_words[word][0][1] == 0:
                                    change_pos.append(int(found_words[word][0][1]))
                                else:
                                    change_pos.append(int(found_words[word][0][1] - i))

                                adj_grid[change_pos[1]][change_pos[0]] = word[i]
                        print("\'{}\' found in grid when altered to \'{}\'".format(word, cp))
                        adj = True
                        if word in words_missing:
                            words_missing.remove(word)
                        break
        time.sleep(1)
        word_list = words_missing[:]
        count += 1
    if adj:
        print("\nAdjusted letter grid: ") 
        for row in range(0, 10):
            line = ""
            for col in range(0,10):
                if adj_grid[row][col] == '':
                    line += "_"
                line += adj_grid[row][col] + "  "
            print(line)
    if words_missing != []:
        print(words_missing)
        print("Search timed out.")
    return adj_grid, found_words

def selectWords(left, top, grid_corner, found_coords):
    for word in found_coords.keys():
        pyautogui.moveTo(int(found_coords[word][0][0]+ left + grid_corner[0]), int(found_coords[word][0][1] + top + grid_corner[1]))
        pyautogui.dragTo(int(found_coords[word][1][0]+ left + grid_corner[0]), int(found_coords[word][1][1] + top + grid_corner[1]), 1, button='left')
        time.sleep(.5)

if __name__ == '__main__':

    while pyautogui.locateOnScreen('gamescreen.jpg', grayscale=True, confidence=0.85) == None:
        print('Check that the game is open and completely visible on screen.')
        time.sleep(2)
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
        letter_grid = getLetterGrid(roi_grid)

        adj_grid = copy.deepcopy(letter_grid)
        found_words = {}

        adj_grid, found_words = findAllWords(adj_grid, word_bank)
        
        cell_h = int(grid_h / 10)
        cell_w = int(grid_w /10)
        found_coords = convertCoords(found_words, cell_w, cell_h)
        print("\nFound coordinates: " + str(found_coords))

        # input solutions to game interface
        selectWords(left, top, grid_corner, found_coords)
        notdone = False
        timeout = time.time() + 5
        while pyautogui.locateOnScreen('solved.jpg', grayscale=True, confidence=0.85) == None:
            time.sleep(1)
            if time.time() > timeout:
                notdone = True
                break

        fail = False
        if notdone:
            active_words = []
            # find missing words
            pyautogui.screenshot('temp/notdone.jpg', [left, top, width, height])
            time.sleep(1)
            found_actives = {}
            found_actives = findActiveWords(adj_grid)
                        
            cell_h = int(grid_h / 10)
            cell_w = int(grid_w /10)
            active_coords = convertCoords(found_actives, cell_w, cell_h)
            print("\nNew found coordinates: " + str(active_coords))

            # input solutions to game interface
            selectWords(left, top, grid_corner, active_coords)

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
