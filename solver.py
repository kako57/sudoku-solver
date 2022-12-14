#!/usr/bin/env python3.11
import subprocess
import time
from pprint import pprint
import struct

adb = "adb.exe"

dimensions = subprocess.check_output(f"{adb} shell wm size", shell=True)
width, height = map(int, dimensions.decode("utf-8").strip().split(" ")[-1].split("x"))


delay = 0.5

def tap(x, y):
    subprocess.run(
        # "start /b adb shell input tap {} {}".format(x, y),
        f"{adb} shell input tap {x} {y} &",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(delay)


data = bytearray()

grid_left = width
grid_top = height
grid_right = 0
grid_bottom = 0
grid_height = 0
grid_width = 0
grid_screen = bytearray()


def get_color(data, offset):
    return struct.unpack("BBB", data[offset : offset + 3])


def get_screen():
    global data, grid_right, grid_left, grid_top, grid_bottom, grid_height, grid_width, grid_screen
    data = bytearray(subprocess.check_output(f"{adb} exec-out screencap", shell=True))[
        12:
    ]

    grid_screen.clear()

    # to get the sudoku grid, hex color #9b915d is a good color to watch out for, because it separates the nonets
    # get the leftmost, topmost, rightmost, and bottommost pixels of the sudoku grid
    for i in range(0, len(data), 4):
        if get_color(data, i) == (0x9B, 0x91, 0x5D):
            x = i // 4 % width
            y = i // 4 // width
            grid_left = min(grid_left, x)
            grid_top = min(grid_top, y)
            grid_right = max(grid_right, x)
            grid_bottom = max(grid_bottom, y)

    # print(grid_left, grid_top, grid_right, grid_bottom)

    # crop the image to the bounding box
    for i in range(grid_top, grid_bottom + 1):
        for j in range(grid_left, grid_right + 1):
            index = (i * width + j) * 4
            grid_screen += data[index : index + 4]

    # recalculate the width and height
    grid_width = grid_right - grid_left + 1
    grid_height = grid_bottom - grid_top + 1


get_screen()

# to get the options for the numbers, hex color #57554c is a good color to watch out for, because it is the color for the circles
# take the topmost, leftmost, bottommost, and rightmost pixels for that section

options_left = width
options_top = height
options_right = 0
options_bottom = grid_bottom
for i in range(0, len(data), 4):
    if get_color(data, i) == (0x57, 0x55, 0x4C):
        x = i // 4 % width
        y = i // 4 // width
        options_left = min(options_left, x)
        options_top = min(options_top, y)
        options_right = max(options_right, x)
        options_bottom = max(options_bottom, y)

# recalculate the width and height
options_width = options_right - options_left + 1
options_height = options_bottom - options_top + 1

k = 1
sudoku_grid = [[0 for i in range(9)] for j in range(9)]


def get_highlighted_cells():
    global k, sudoku_grid, data, grid_width, grid_height, grid_left, grid_top

    get_screen()

    for i in range(grid_height // 18, grid_height, grid_height // 9):
        for j in range(grid_width // 18 - 25, grid_width, grid_width // 9):
            index = ((i + grid_top) * width + (j + grid_left)) * 4
            if get_color(data, index) == (0x66, 0x63, 0x55):
                sudoku_grid[i // (grid_height // 9)][j // (grid_width // 9)] = k

    pprint(sudoku_grid)


def put_solution():
    global k, sudoku_grid, grid_screen, grid_width, grid_height, grid_left, grid_top

    for i in range(9):
        for j in range(9):
            assert sudoku_grid[i][j] != 0

    row = 0
    for i in range(grid_height // 18, grid_height, grid_height // 9):
        col = 0
        for j in range(grid_width // 18, grid_width, grid_width // 9):
            if sudoku_grid[row][col] == k:
                # tap the center of the cell
                print("tapping", row, col, k)
                tap(j + grid_left, i + grid_top)
            col += 1
        row += 1


def iterate_options(callback):
    global k
    # options is a 2 x 5 grid
    k = 1
    for i in range(options_height // 4, options_height, options_height // 2):
        for j in range(options_width // 10, options_width, options_width // 5):
            # tap the center of the cell (this taps works already)
            tap(j + options_left, i + options_top)
            if k <= 9:
                callback()
                k += 1


def is_valid(row, col, val):
    global sudoku_grid
    # check if the value is valid in the row
    for i in range(9):
        if sudoku_grid[row][i] == val:
            return False

    # check if the value is valid in the column
    for i in range(9):
        if sudoku_grid[i][col] == val:
            return False

    # check if the value is valid in the nonet
    for i in range(row // 3 * 3, row // 3 * 3 + 3):
        for j in range(col // 3 * 3, col // 3 * 3 + 3):
            if sudoku_grid[i][j] == val:
                return False

    return True


def solve():
    global sudoku_grid, delay
    for i in range(9):
        for j in range(9):
            if sudoku_grid[i][j] == 0:
                for val in range(1, 10):
                    if is_valid(i, j, val):
                        sudoku_grid[i][j] = val
                        solve()
                        sudoku_grid[i][j] = 0
                return
    print("solution:")
    pprint(sudoku_grid)
    delay = 0.1
    iterate_options(put_solution)
    assert False


iterate_options(get_highlighted_cells)

try:
    solve()
    print("did not find a solution")
except AssertionError:
    # Yes, error is actually succ W
    print("solution:")
    pprint(sudoku_grid)
    print("done")
