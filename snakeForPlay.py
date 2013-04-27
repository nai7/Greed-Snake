__author__ = 'nai7'
# coding: utf-8

import sys,copy
import pygame
from pygame.locals import *
from pygame.color import Color
from random import randint

import threading
import time


# 格子宽度
d = 20
# 蛇运动的场地长宽
height = 600
width = 800
#矩阵大小
HEIGHT = height/d
WIDTH = width/d
FIELD_SIZE = HEIGHT * WIDTH


# 用来代表不同东西的数字，由于矩阵上每个格子会处理成到达食物的路径长度，
# 因此这三个变量间需要有足够大的间隔(>HEIGHT*WIDTH)
FOOD = 0
UNDEFINED = (HEIGHT + 1) * (WIDTH + 1)
SNAKE = 2 * UNDEFINED

# 由于snake是一维数组，所以对应元素直接加上以下值就表示向四个方向移动,注意坐标点的不同
LEFT = -1
RIGHT = 1
UP = -WIDTH
DOWN = WIDTH

#蛇头方向的全局变量
direct = RIGHT

# 错误码
ERR = -1111

# 蛇身向前速度
speed = 10

# 蛇头总是位于snake数组的第一个元素
HEAD = 0

# 用一维数组来表示二维的东西
# board表示蛇运动的矩形场地
# 初始化蛇头在(1,1)的地方，第0行，HEIGHT行，第0列，WIDTH列为围墙，不可用
# 初始蛇长度为1
board = [0] * FIELD_SIZE
snake = [0] * (FIELD_SIZE+1)
snake[HEAD] = 1*WIDTH+1
snake_size = 1

# 与上面变量对应的临时变量，蛇试探性地移动时使用
tmpboard = [0] * FIELD_SIZE
tmpsnake = [0] * (FIELD_SIZE+1)
tmpsnake[HEAD] = 1*WIDTH+1
tmpsnake_size = 1

# food:食物位置(0~FIELD_SIZE-1),初始在(3, 3)
# best_move: 运动方向
food = 3 * WIDTH + 3 #初始位置
best_move = ERR

#运动方向组
mov = [LEFT,RIGHT,UP,DOWN]

# 接收到的键 和 分数
key = K_RIGHT
score = 1 #分数也表示蛇长

#检查一个cell是否被蛇身覆盖
def is_cell_free(idx,psize,psnake):
    return not (idx in psnake[:psize])

# 检查某个位置idx是否可向move方向运动，主要是为了防止数组溢出
def is_move_possible(idx, move):
    flag = False
    if move == LEFT:
        flag = True if idx%WIDTH > 0 else False
    elif move == RIGHT:
        flag = True if idx%WIDTH < (WIDTH-1) else False
    elif move == UP:
        flag =True if idx/WIDTH > 0 else False # 即idx/WIDTH > 1
    elif move == DOWN:
        flag = True if idx/WIDTH < HEIGHT-1 else False # 即
    return flag

#将整个数组向前推动一步
def shift_array(arr, size):
    for i in xrange(size, 0, -1):
        arr[i] = arr[i-1]

#产生一个新的食物
def new_food():
    global food, snake_size
    cell_free = False
    while not cell_free:
        w = randint(1, WIDTH-2)
        h = randint(1, HEIGHT-2)
        food = h * WIDTH + w
        cell_free = is_cell_free(food, snake_size, snake)
    drawFood(food)

# 真正的蛇在这个函数中，朝pbest_move走1步
def make_move(pbest_move):
    global key, snake, board, snake_size, score

    #你死了祝你幸福
    # s = snake[HEAD] + pbest_move
    # if not is_move_possible(s,pbest_move):
    #     print '你死了祝你幸福！'
    #     sys.exit()

    #蛇身会自动向前一次，暂时先引用掉
    shift_array(snake, snake_size)
    snake[HEAD] += pbest_move
    p = snake[HEAD]
    drawSnakeHead(p)

    #如果吃到了食物
    if snake[HEAD] == food:
        board[snake[HEAD]] = SNAKE # 新的蛇头
        snake_size += 1
        score += 1
        if snake_size < FIELD_SIZE: new_food()
    else: # 如果新加入的蛇头不是食物的位置
        board[snake[HEAD]] = SNAKE # 新的蛇头
        board[snake[snake_size]] = UNDEFINED # 蛇尾变为空格
        drawBlock(snake[snake_size])



##############################以下是绘制函数############################
#背景横竖线
def drawbackground():
    for x in range(0,width,d):
        pygame.draw.line(window,Color('grey'),(x,0),(x,height),1)
    for y in range(0,height,d):
        pygame.draw.line(window,Color('grey'),(0,y),(width,y),1)

#绘制方格
def drawpane():
    for r in range(1,HEIGHT-1):
        for c in range(1,WIDTH-1):
            color=Color('white')
            pygame.draw.rect(window,color,(c*d,r*d,d,d))


#将食物绘制到界面上,注意food不能只绘制一次,绘制正方形时先绘制横坐标，后绘制纵坐标
def drawFood(food):
    color = Color('red')
    pygame.draw.rect(window,color,(food%WIDTH*d,food/WIDTH*d,d,d))

#绘制蛇,循环绘制每个蛇身子的节点
def drawSnake(snake):
    color  = Color('black')
    for c in snake:
        pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d,d,d))

def drawSnakeHead(head):
    color = Color('black')
    pygame.draw.rect(window,color,(head%WIDTH*d,head/WIDTH*d,d,d))

def drawBlock(c):
    color = Color('white')
    pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d,d,d))

def drawBroder():
    color = Color('green')
    for c in range(0,WIDTH):
        pygame.draw.rect(window,color,(c*d,0,d,d))
    for c in range(0,HEIGHT):
        pygame.draw.rect(window,color,(0,c*d,d,d))
    for c in range(0,HEIGHT):
        pygame.draw.rect(window,color,((WIDTH-1)*d,c*d,d,d))
    for c in range(0,WIDTH):
        pygame.draw.rect(window,color,(c*d,(HEIGHT-1)*d,d,d))


    #######################创建一个多线程类来控制蛇的运动####################
class SnakeMoveThread(threading.Thread):
    global direct
    def __init__(self,interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            make_move(direct)
            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True

###############################以下是程序主函数##########################
if __name__ == '__main__':
    pygame.init()
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Greed Snake!')
    font = pygame.font.Font(None, 12)
    snakeThread = SnakeMoveThread(0.05)
    snakeThread.start()
    while True:
        drawpane()
        drawBroder()
        drawbackground()
        drawFood(food)
        #监听各种外部事件
        for event in pygame.event.get():
            if event.type == QUIT:
                snakeThread.stop()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    sys.exit()
                if event.key == K_DOWN :
                    make_move(DOWN)
                    direct = DOWN
                if event.key == K_RIGHT:
                    make_move(RIGHT)
                    direct = RIGHT
                if event.key == K_LEFT:
                    make_move(LEFT)
                    direct = LEFT
                if event.key == K_UP:
                    make_move(UP)
                    direct = UP
        #make_move(direct)
        drawSnake(snake)
        pygame.display.update()

