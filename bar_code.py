'''
program find barcode in image
'''
from time import time
from cv2 import cv2
import numpy as np
import matplotlib.pyplot as plt


def change_contour(contour, imheight, imwidth, hnoise, wnoise):
    '''
    function change contour into rectangle
    '''
    contour = np.reshape(contour, (contour.shape[0], 2))
    minels = np.min(contour, axis=0)
    maxels = np.max(contour, axis=0)
    if maxels[0] - minels[0] > imwidth * wnoise and maxels[1] - minels[1] > imheight * hnoise:
        return (minels[0], maxels[0], minels[1], maxels[1]), 1

    return None, 0

def sort(rect_contours):
    '''
    sort rectangles by their left up tip
    '''
    for i in range(len(rect_contours)):
        for j in range(len(rect_contours) - i - 1):
            if rect_contours[j][0] > rect_contours[j + 1][0]:
                temp = np.copy(rect_contours[j])
                rect_contours[j] = np.copy(rect_contours[j + 1])
                rect_contours[j + 1] = np.copy(temp)

def is_cmp(points1, points2, imwidth, closenessp, intersectionp):
    '''
    return True if 2 rectangles should be merged otherway return False
    '''
    closeness = points2[0] - points1[1] < imwidth * closenessp
    k = 0
    if points1[3] >= points2[2] >= points1[2]:
        k = min(points1[3], points2[3]) - points2[2]
    elif points1[3] >= points2[3] >= points1[2]:
        k = points2[3] - max(points1[2], points2[2])
    elif points2[2] < points1[2] and points2[3] > points1[3]:
        k = points1[3] - points1[2]
    intersection = k / max(points1[3] - points1[2], points2[3] - points2[2]) > intersectionp
    return intersection and closeness


def merge_contours(rect_contours, imwidth, closenessp, intersectionp):
    '''
    merge 2 contours if it necessari
    '''
    sort(rect_contours)
    i = 0
    while i < len(rect_contours):
        j = i + 1
        while j < len(rect_contours):
            if is_cmp(rect_contours[i], rect_contours[j], imwidth, closenessp, intersectionp):
                rect_contours[i][1] = rect_contours[j][1]
                if rect_contours[i][2] < rect_contours[j][2]:
                    rect_contours[i][2] = rect_contours[j][2]
                if rect_contours[i][3] > rect_contours[j][3]:
                    rect_contours[i][3] = rect_contours[j][3]
                rect_contours = np.delete(rect_contours, j, axis=0)
            else:
                j += 1
        i += 1

    return rect_contours

def find_max_contour(contours):
    '''
    find max rectangle by its width
    '''
    if len(contours) > 0:
        maxi = 0
        for i in range(1, len(contours)):
            if contours[i][1] - contours[i][0] > contours[maxi][1] - contours[maxi][0]:
                maxi = i
        return contours[maxi], 1
    return None, 0

def find_contours(img, eiter, diter):
    '''
    find contours that looks like barcode
    '''
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=-1)

    sobelc = cv2.convertScaleAbs(sobelx)

    _, ther = cv2.threshold(sobelc, 200, 255, cv2.THRESH_BINARY)

    kernel = np.ones((4, 1), np.uint8)
    erode = cv2.erode(ther, kernel, iterations=eiter)

    kernel = np.ones((3, 4), np.uint8)
    dilation = cv2.dilate(erode, kernel, iterations=diter)

    contours, _ = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    return contours

def make_rect_contours(gray, parameters):
    '''
    find contours and make it rectangles
    '''
    hnoise, wnoise, closenessp, intersectionp, eiter, diter = parameters
    contours = find_contours(gray, eiter, diter)
    rect_contours = []
    for contour in contours:
        shape, isfind = change_contour(contour, len(gray), len(gray[0]), hnoise, wnoise)
        if isfind:
            rect_contours.append(shape)
    rect_contours = np.array(rect_contours)
    rect_contours = merge_contours(rect_contours, len(gray[0]), closenessp, intersectionp)

    return rect_contours

def find_barcode_area(img, parameters):
    '''
    find area with barcode on image
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rect_contours = make_rect_contours(gray, parameters)

    bar_contour, isfind = find_max_contour(rect_contours)
    if isfind:
        barcode = img[bar_contour[2]:bar_contour[3], bar_contour[0]:bar_contour[1], :]
        return barcode, 1
    return None, 0

def decode_bar(barcode):
    '''
    translate binary barcode into decimal
    '''
    if len(barcode) != 95:
        return ''
    combinations = [['0001101', '0011001', '0010011', '0111101', '0100011',
                     '0110001', '0101111', '0111011', '0110111', '0001011'],
                    ['0100111', '0110011', '0011011', '0100001', '0011101',
                     '0111001', '0000101', '0010001', '0001001', '0010111'],
                    ['1110010', '1100110', '1101100', '1000010', '1011100',
                     '1001110', '1010000', '1000100', '1001000', '1110100']]
    par_seq = [[0, 0, 0, 0, 0, 0],
               [0, 0, 1, 0, 1, 1],
               [0, 0, 1, 1, 0, 1],
               [0, 0, 1, 1, 1, 0],
               [0, 1, 0, 0, 1, 1],
               [0, 1, 1, 0, 0, 1],
               [0, 1, 1, 1, 0, 0],
               [0, 1, 0, 1, 0, 1],
               [0, 1, 0, 1, 1, 0],
               [0, 1, 1, 0, 1, 0]]

    bar_list = []
    for i in range(6):
        bar_list.append(barcode[i*7 + 3:i*7 + 10])
    for i in range(6):
        bar_list.append(barcode[i*7 + 50:i*7 + 57])

    bar_dec = ''
    i = 0
    parlen = len(par_seq)
    nfind = True
    while i < parlen and nfind:
        bar_left = str(i)
        for k in range(len(par_seq[i])):
            for j in range(10):
                if bar_list[k] == combinations[par_seq[i][k]][j]:
                    bar_left += str(j)
        if len(bar_left) == 7:
            bar_dec += bar_left
            nfind = False
        i += 1

    for i in range(6, 12):
        for j in range(10):
            if bar_list[i] == combinations[2][j]:
                bar_dec += str(j)

    return bar_dec

def control_digit(bar_code):
    '''
    check last digit in barcode
    '''
    even = 0
    odd = 0
    for i in range(0, 12, 2):
        odd += int(bar_code[i])
    for i in range(1, 12, 2):
        even += int(bar_code[i])
    control_sum = 3 * even + odd
    if control_sum % 10 != 0:
        control_round = (control_sum // 10 + 1) * 10
    else:
        control_round = control_sum

    return control_round - control_sum == int(bar_code[12])

def strcmp(string1, string2):
    '''
    count symbols that match in two strings
    '''
    match = 0
    for i in range(min(len(string1), len(string2))):
        if string1[i] == string2[i]:
            match += 1
    return match

def bar_varity(barbin):
    '''
    count special digits in binary barcode
    '''
    if len(barbin) == 95:
        return 0
    varity = strcmp(barbin[0:3], '101')
    varity += strcmp(barbin[-3:], '101')
    varity += strcmp(barbin[44:49], '10101')
    return varity

def detect(th1, rowstep):
    '''
    take threshold and step and return decoded barcode or number of digits that were decoded right
    '''
    height, width = th1.shape
    i = 0
    res = 0
    while i < height:
        j = 0
        while j < width and th1[i][j] == 0:
            j += 1
        while j < width and th1[i][j] == 255:
            j += 1
        bar_bin = ''
        reference = 1
        while j < width and th1[i][j] == 0:
            j += 1
            reference += 1
        bar_bin += '1'
        while len(bar_bin) < 95 and j < width:
            white = 1
            while j < width and th1[i][j] == 255:
                white += 1
                j += 1
            bar_bin += '0' * round(white / reference)
            black = 1
            while j < width and th1[i][j] == 0:
                black += 1
                j += 1
            bar_bin += '1' * round(black / reference)
        res += bar_varity(bar_bin)
        bar_dec = decode_bar(bar_bin)
        if len(bar_dec) == 13:
            if control_digit(bar_dec):
                return bar_dec, 1
        i += rowstep
    return res, 0

def find_ther_percent(hist, percent, black, ther, square):
    '''
    return colour that consist percent of image brightness
    '''
    while black < square * percent:
        black += hist[0][ther]
        ther += 1
    return ther, black

def possible_thr(img, percents):
    '''
    return colours that consists percents of image brightness
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist = plt.hist(gray.ravel(), 256, [0, 256])
    square = len(img) * len(img[0])
    res = []
    black, ther = 0, 0
    for percent in percents:
        ther, black = find_ther_percent(hist, percent, black, ther, square)
        res.append(ther)

    return res

def make_thrs(img):
    '''
    make different thresholds of left and right parts of picture and concatenate them
    '''
    imleft = img[:, 0:(len(img[0]) // 2), :]
    imright = img[:, len(img[0]) // 2:len(img[0]), :]
    left_thrs = possible_thr(imleft, (0.40, 0.45, 0.50, 0.55))
    right_thrs = possible_thr(imright, (0.40, 0.45, 0.50, 0.55))
    imleft = cv2.cvtColor(imleft, cv2.COLOR_BGR2GRAY)
    imright = cv2.cvtColor(imright, cv2.COLOR_BGR2GRAY)
    thrl = []
    thrr = []
    for thr in left_thrs:
        _, thl = cv2.threshold(imleft, thr, 255, cv2.THRESH_BINARY)
        thrl.append(thl)
    for thr in right_thrs:
        _, thr = cv2.threshold(imright, thr, 255, cv2.THRESH_BINARY)
        thrr.append(thr)
    con = []
    for left in thrl:
        for right in thrr:
            con.append(np.concatenate((left, right), axis=1))

    return con, left_thrs, right_thrs

def make_thrs_range(img, lmin, lmax, rmin, rmax):
    '''
    do the same that last function, but takes thresholds range
    '''
    imleft = img[:, 0:(len(img[0]) // 2), :]
    imright = img[:, len(img[0]) // 2:len(img[0]), :]
    imleft = cv2.cvtColor(imleft, cv2.COLOR_BGR2GRAY)
    imright = cv2.cvtColor(imright, cv2.COLOR_BGR2GRAY)
    thrl = []
    thrr = []
    for i in range(lmin, lmax, 5):
        _, thr = cv2.threshold(imleft, i, 255, cv2.THRESH_BINARY)
        thrl.append(thr)
    for i in range(rmin, rmax, 5):
        _, thr = cv2.threshold(imright, i, 255, cv2.THRESH_BINARY)
        thrr.append(thr)
    con = []
    for left in thrl:
        for right in thrr:
            con.append(np.concatenate((left, right), axis=1))

    return con

def is_bar_area(diffs):
    '''
    check if is there any digit upper than six in array
    '''
    for diff in diffs:
        if diff > 6:
            return False
    return True

def find_start_end(thre):
    '''
    find first and last lines of barcode
    '''
    rows, cols = thre.shape
    last, start = 0, -1
    diff = []
    for i in range(6):
        black = 0
        for j in range(cols):
            if thre[i][j] == 0:
                black += 1
        diff.append(abs(black - last))
        last = black
    i = 6
    while i < rows and start == -1:
        black = 0
        for j in range(cols):
            if thre[i][j] == 0:
                black += 1
        if is_bar_area(diff):
            start = i
        for j in range(len(diff) - 1):
            diff[j] = diff[j + 1]
        diff[len(diff) - 1] = black - last
        last = black
        i += 1
    if start < rows // 2:
        end = rows // 2
    else:
        end = rows - 1
    return start, end

def find_bar_rec(thre):
    '''
    make perspective form of barcode threshold image
    '''
    start, end = find_start_end(thre)
    rows, cols = thre.shape
    left_up, right_up, left_bottom, right_bottom = 0, 0, 0, 0
    for j in range(1, cols - 1):
        if thre[start][j] == 0:
            if not left_up:
                left_up = j - 2
            right_up = j + 2
        if thre[end][j] == 0:
            if not left_bottom:
                left_bottom = j - 2
            right_bottom = j + 2

    pts1 = np.float32([[left_up, start], [right_up, start],
                       [left_bottom, end], [right_bottom, end]])
    pts2 = np.float32([[0, 0], [cols, 0], [0, rows], [cols, rows]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(thre, matrix, (cols, rows))
    return dst

def bar_thr(img, diff):
    '''
    my way to make threshold of barcode image
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    my_thr = np.copy(gray)
    for i in range(len(img)):
        my_thr[i][0] = 255
    colour = 0
    for i in range(len(img)):
        for j in range(1, len(img[0])):
            if abs(int(gray[i][j]) - int(gray[i][j - 1])) > diff:
                if int(gray[i][j]) - int(gray[i][j - 1]) > 0:
                    colour = 255
                else:
                    colour = 0
            my_thr[i][j] = colour
    return my_thr

def pos_thrs_way(barcode_area):
    '''
    find barcode using possible_thr
    '''
    best = 0
    besti = 0
    bar_thrs, left, right = make_thrs(barcode_area)
    for i, barthr in enumerate(bar_thrs):
        barcode, isdec = detect(barthr, 2)
        if isdec:
            return barcode, besti, left, right
        if barcode > best:
            best = barcode
            besti = i

    return '', besti, left, right

def bar_thr_way(barcode_area):
    '''
    find barcode using bar_thr
    '''
    pos_thrs = possible_thr(barcode_area, (0.40, 0.45, 0.5, 0.6, 0.65, 0.7))
    for i in range(len(pos_thrs) - 1, 0, -1):
        for j in range(0, i):
            thr = bar_thr(barcode_area, pos_thrs[i] - pos_thrs[j])
            rec = find_bar_rec(thr)
            _, rec = cv2.threshold(rec, 133, 255, cv2.THRESH_BINARY)
            barcode, isdec = detect(thr, 7)
            if isdec:
                return barcode

    return ''

def make_thrs_way(barcode_area, left, right, besti):
    '''
    find barcode using make_thrs
    '''
    bestl = left[besti // len(right)]
    bestr = right[besti % len(right)]
    barthrs = make_thrs_range(barcode_area, bestl - 25, bestl + 25, bestr - 25, bestr + 25)
    for barthr in barthrs:
        rec = find_bar_rec(barthr)
        _, rec = cv2.threshold(rec, 133, 255, cv2.THRESH_BINARY)
        barcode, isdec = detect(rec, 7)
        if isdec:
            return barcode

    return ''

def get_barcode(location):
    '''
    takes loсation of image with barcode, returns decoded barcode or message with relevant text
    '''
    img = cv2.imread(location, 1)
    barcode_area, isfind = find_barcode_area(img, (0.01, 0.01, 0.02, 0.4, 8, 4))
    if isfind:
        barcode, besti, left, right = pos_thrs_way(barcode_area)
        if barcode.isdigit():
            return barcode

        barcode = bar_thr_way(barcode_area)
        if barcode.isdigit():
            return barcode

        barcode = make_thrs_way(barcode_area, left, right, besti)
        if barcode.isdigit():
            return barcode

    return u'Почему-то я не вижу штрих-кода. Попробуйте ещё раз!'


if __name__ == "__main__":
    TESTS = 0
    PASSED = 0
    t = time()
    for number in range(0, 83):
        try:
            bar = get_barcode('shtrih'+str(number)+'.jpg')
            print(number, bar)
            if bar.isdigit():
                PASSED += 1
            TESTS += 1
        except (cv2.error, IndexError) as exc:
            print(exc)
            continue
    print("time ", end="")
    print(time() - t)
    print("pass", PASSED, "of", TESTS)
