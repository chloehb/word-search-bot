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
from extractData import preprocessCheckedBank

def getActiveWords(roi_col):
    active_words = []
    myconfig = r"--psm 6 --oem 3"
    d = pyt.image_to_data(roi_col, config=myconfig, output_type=Output.DICT)
    n_boxes = len(d['level'])
    for i in range(n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        if h<50 and d['text'][i] != '':
            # cv2.rectangle(roi_col, (x, y), (x + w, y + h), (0, 255, 0), 2)
            active_words.append(d['text'][i])

    # cv2.imshow('word_bank', roi_col)
    # cv2.waitKey(0)
    print("Active words: " + str(active_words))
    return active_words

def findActiveInGrid(chars, word_grid):
    '''iterate through grid and check for word in all directions'''

    # determine start and end array locations in grid for word
    array_start = (0,0)
    array_end = (0,0)

    num_rows = 10
    num_cols = 10
    found = False
    for row in range(9, 0, -1):
        for col in range(9, 0, -1):
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

def findActiveWords(adj_grid):
    print("\nReanalyzing...")
    roi_col = preprocessCheckedBank()
    active_words = getActiveWords(roi_col)

    return findAllActives(adj_grid, active_words)

def findAllActives(adj_grid, word_bank):
    words_missing = []
    adj = False

    found_words = {}
    word_list = word_bank
    count = 0
    timeout = time.time() + 10
    last_list = []
    while word_list != [] and time.time() < timeout:
        for word in word_list:
            chars = [c for c in str(word)]
            found_words[word] = findActiveInGrid(chars, adj_grid)
            if found_words[word] == ((0,0),(0,0)):
                print("Error: \'{}\' not found in grid".format(word))
                if count == 0:
                    words_missing.append(word)
                for i in range(0, len(chars)):
                    copy_word = [c for c in str(word)]
                    copy_word[i] = ''
                
                    found_words[word] = findActiveInGrid(copy_word, adj_grid)
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
        if word_list == last_list:
            break
        last_list = copy.deepcopy(word_list)
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
    
    return found_words
