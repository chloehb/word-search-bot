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

# pyt.pytesseract.tesseract_cmd = "C:\\Users\\chloe\\AppData\\Local\\Programs\\Tesseract-OCR"
pyt.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract'

def preprocessBank(gray):
    im_h, im_w = gray.shape  
    col_x = int(im_w*0.72)

    bw = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 27, 2)
    kernel = np.ones((1, 1), np.uint8)
    dilate = cv2.dilate(bw, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    erode = cv2.erode(dilate, kernel, iterations=1)
    morph = cv2.morphologyEx(erode, cv2.MORPH_CLOSE, kernel)
    no_noise = cv2.medianBlur(morph, 3)
    roi_col = no_noise[int(im_h*0.1):int(im_h), int(col_x):int(im_w)]

    cv2.imwrite("temp/roi_col.jpg", roi_col)
    return roi_col

def preprocessGrid(gray):
    im_h, im_w = gray.shape
    grid_tcorner = (int(im_w*0.13), int(im_w*0.14))
    grid_bcorner = (int(im_h*0.83), int(im_h*0.85))

    roi_main = gray[grid_tcorner[1]:grid_bcorner[1], grid_tcorner[0]:grid_bcorner[0]]
    bw = cv2.threshold(roi_main, 127, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((1, 1), np.uint8)
    dilate = cv2.dilate(bw, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    erode = cv2.erode(dilate, kernel, iterations=1)
    morph = cv2.morphologyEx(erode, cv2.MORPH_CLOSE, kernel)
    roi_main = thickFont(morph)

    cv2.imwrite("temp/roi_main.jpg", roi_main)
    return roi_main, grid_tcorner

def thickFont(img):
    img = cv2.bitwise_not(img)
    kernel = np.ones((2, 2), np.uint8)
    erode = cv2.dilate(img, kernel, iterations=1)
    thick = cv2.bitwise_not(erode)
    return thick

def preprocess(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    roi_col = preprocessBank(gray)
    roi_main, grid_corner = preprocessGrid(gray)

    return roi_main, roi_col, grid_corner

def getWordBank(roi_col):
    # read side words into list
    myconfig = r"--psm 4 --oem 3"
    bank_text = pyt.image_to_string(roi_col, config=myconfig, output_type=Output.STRING)
    # print(bank_text)
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
                # cv2.rectangle(roi_col, (x, y), (x + w, y + h), (0, 255, 0), 2)
                word_bank.append(d['text'][i])

        # cv2.imshow('word_bank', roi_col)
        # cv2.waitKey(0)
    print("Word Bank: " + str(word_bank) + "\n")
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
            prev_y=y
            prev_x = x
        
            # cv2.rectangle(roi_main,(x,hImg-y),(w,hImg-h),(0,0,255),1)
            # cv2.putText(roi_main,b[0],(x,hImg-y+20),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,255),1)

    if len(temp_arr) < 10:
        temp_arr.pop()
        dist = 10 - len(temp_arr)
        for i in range(0, dist):
            temp_arr.append('')
    word_grid.append(temp_arr)

    # print(word_grid)
    # cv2.imshow('Result',roi_main)
    # cv2.waitKey(0)
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
    print("Letter grid: ") 
    for row in range(0, 10):
        line = ""
        for col in range(0,10):
            if word_grid[row][col] == '':
                line += "_"
            line += word_grid[row][col] + "  "
        print(line)
            
    return word_grid

def preprocessCheckedBank(): 

    image = cv2.imread("temp/notdone.jpg")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    im_h, im_w = gray.shape 
    col_x = int(im_w*0.72)
    bw = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((1, 1), np.uint8)
    dilate = cv2.dilate(bw, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    erode = cv2.erode(dilate, kernel, iterations=1)
    morph = cv2.morphologyEx(erode, cv2.MORPH_CLOSE, kernel)
    no_noise = thickFont(morph)
    roi_col = no_noise[40:im_h, col_x:im_w]

    cv2.imwrite("temp/checked_bank.jpg", roi_col)
    return roi_col
