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
#间隔
dev = 3
# 蛇运动的场地长宽
height = 300
width = 500
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
    #drawSnakeHead(p)

    #如果吃到了食物
    if snake[HEAD] == food:
        board[snake[HEAD]] = SNAKE # 新的蛇头
        snake_size += 1
        score += 1
        if snake_size < FIELD_SIZE: new_food()
    else: # 如果新加入的蛇头不是食物的位置
        board[snake[HEAD]] = SNAKE # 新的蛇头
        board[snake[snake_size]] = UNDEFINED # 蛇尾变为空格
        drawBlock(snake[snake_size],'white')

######################AI函数##########################

# 广度优先搜索遍历整个board，
# 计算出board中每个非SNAKE元素到达食物的路径长度
def board_refresh(pfood, psnake, pboard):
    queue = []
    queue.append(pfood)
    inqueue = [0] * FIELD_SIZE
    found = False
    # while循环结束后，除了蛇的身体，
    # 其它每个方格中的数字代码从它到食物的路径长度
    while len(queue)!=0:
        idx = queue.pop(0)
        if inqueue[idx] == 1: continue
        inqueue[idx] = 1
        for i in xrange(4):
            if is_move_possible(idx, mov[i]):
                if idx + mov[i] == psnake[HEAD]:
                    found = True
                if pboard[idx+mov[i]] < SNAKE: # 如果该点不是蛇的身体

                    if pboard[idx+mov[i]] > pboard[idx]+1:
                            pboard[idx+mov[i]] = pboard[idx] + 1
                    if inqueue[idx+mov[i]] == 0:
                        queue.append(idx+mov[i])

    return found


# 重置board
# board_refresh后，UNDEFINED值都变为了到达食物的路径长度
# 如需要还原，则要重置它
def board_reset(psnake, psize, pboard):
    for i in xrange(FIELD_SIZE):
        if i == food:
            pboard[i] = FOOD
        elif is_cell_free(i, psize, psnake): # 该位置为空
            pboard[i] = UNDEFINED
        else: # 该位置为蛇身
            pboard[i] = SNAKE

# 从蛇头开始，根据board中元素值，
# 从蛇头周围4个领域点中选择最短路径
def choose_shortest_safe_move(psnake, pboard):
    best_move = ERR
    min = SNAKE
    for i in xrange(4):
        if is_move_possible(psnake[HEAD], mov[i]) and pboard[psnake[HEAD]+mov[i]]<min:
            min = pboard[psnake[HEAD]+mov[i]]
            best_move = mov[i]
    return best_move



# 虚拟地运行一次，然后在调用处检查这次运行可否可行
# 可行才真实运行。
# 虚拟运行吃到食物后，得到虚拟下蛇在board的位置
def virtual_shortest_move():
    global snake, board, snake_size, tmpsnake, tmpboard, tmpsnake_size, food
    tmpsnake_size = snake_size
    tmpsnake = snake[:] # 如果直接tmpsnake=snake，则两者指向同一处内存
    tmpboard = board[:] # board中已经是各位置到达食物的路径长度了，不用再计算
    board_reset(tmpsnake, tmpsnake_size, tmpboard)

    food_eated = False
    while not food_eated:
        board_refresh(food, tmpsnake, tmpboard)
        move = choose_shortest_safe_move(tmpsnake, tmpboard)
        shift_array(tmpsnake, tmpsnake_size)
        tmpsnake[HEAD] += move # 在蛇头前加入一个新的位置
        # 如果新加入的蛇头的位置正好是食物的位置
        # 则长度加1，重置board，食物那个位置变为蛇的一部分(SNAKE)
        if tmpsnake[HEAD] == food:
            tmpsnake_size += 1
            board_reset(tmpsnake, tmpsnake_size, tmpboard) # 虚拟运行后，蛇在board的位置(label101010)
            tmpboard[food] = SNAKE
            food_eated = True
        else: # 如果蛇头不是食物的位置，则新加入的位置为蛇头，最后一个变为空格
            tmpboard[tmpsnake[HEAD]] = SNAKE
            tmpboard[tmpsnake[tmpsnake_size]] = UNDEFINED

# 如果蛇与食物间有路径，则调用本函数
def find_safe_way():
    global snake, board
    safe_move = ERR
    # 虚拟地运行一次，因为已经确保蛇与食物间有路径，所以执行有效
    # 运行后得到虚拟下蛇在board中的位置，即tmpboard，见label101010
    virtual_shortest_move() # 该函数唯一调用处
    if is_tail_inside(): # 如果虚拟运行后，蛇头蛇尾间有通路，则选最短路运行(1步)
        return choose_shortest_safe_move(snake, board)
    safe_move = follow_tail() # 否则虚拟地follow_tail 1步，如果可以做到，返回true
    return safe_move

# 从蛇头开始，根据board中元素值，
# 从蛇头周围4个领域点中选择最短路径
def choose_shortest_safe_move(psnake, pboard):
    best_move = ERR
    min = SNAKE
    for i in xrange(4):
        if is_move_possible(psnake[HEAD], mov[i]) and pboard[psnake[HEAD]+mov[i]]<min:
            min = pboard[psnake[HEAD]+mov[i]]
            best_move = mov[i]
    return best_move

# 从蛇头开始，根据board中元素值，
# 从蛇头周围4个领域点中选择最远路径
def choose_longest_safe_move(psnake, pboard):
    best_move = ERR
    max = -1
    for i in xrange(4):
        if is_move_possible(psnake[HEAD], mov[i]) and pboard[psnake[HEAD]+mov[i]]<UNDEFINED and pboard[psnake[HEAD]+mov[i]]>max:
            max = pboard[psnake[HEAD]+mov[i]]
            best_move = mov[i]
    return best_move

# 检查是否可以追着蛇尾运动，即蛇头和蛇尾间是有路径的
# 为的是避免蛇头陷入死路
# 虚拟操作，在tmpboard,tmpsnake中进行
def is_tail_inside():
    global tmpboard, tmpsnake, food, tmpsnake_size
    tmpboard[tmpsnake[tmpsnake_size-1]] = 0 # 虚拟地将蛇尾变为食物(因为是虚拟的，所以在tmpsnake,tmpboard中进行)
    tmpboard[food] = SNAKE # 放置食物的地方，看成蛇身
    result = board_refresh(tmpsnake[tmpsnake_size-1], tmpsnake, tmpboard) # 求得每个位置到蛇尾的路径长度
    for i in xrange(4): # 如果蛇头和蛇尾紧挨着，则返回False。即不能follow_tail，追着蛇尾运动了
        if is_move_possible(tmpsnake[HEAD], mov[i]) and tmpsnake[HEAD]+mov[i]==tmpsnake[tmpsnake_size-1] and tmpsnake_size>3:
            result = False
    return result

# 让蛇头朝着蛇尾运行一步
# 不管蛇身阻挡，朝蛇尾方向运行
def follow_tail():
    global tmpboard, tmpsnake, food, tmpsnake_size
    tmpsnake_size = snake_size
    tmpsnake = snake[:]
    board_reset(tmpsnake, tmpsnake_size, tmpboard) # 重置虚拟board
    tmpboard[tmpsnake[tmpsnake_size-1]] = FOOD # 让蛇尾成为食物
    tmpboard[food] = SNAKE # 让食物的地方变成蛇身
    board_refresh(tmpsnake[tmpsnake_size-1], tmpsnake, tmpboard) # 求得各个位置到达蛇尾的路径长度
    tmpboard[tmpsnake[tmpsnake_size-1]] = SNAKE # 还原蛇尾

    return choose_longest_safe_move(tmpsnake, tmpboard) # 返回运行方向(让蛇头运动1步)

# 在各种方案都不行时，随便找一个可行的方向来走(1步),
def any_possible_move():
    global food , snake, snake_size, board
    best_move = ERR
    board_reset(snake, snake_size, board)
    board_refresh(food, snake, board)
    min = SNAKE

    for i in xrange(4):
        if is_move_possible(snake[HEAD], mov[i]) and board[snake[HEAD]+mov[i]]<min:
            min = board[snake[HEAD]+mov[i]]
            best_move = mov[i]
    return best_move


#########################################################

##############################以下是绘制函数############################
#背景横竖线
def drawbackground():
    for x in range(0,width,d):
        pygame.draw.line(window,Color('grey'),(x,0),(x,height),1)
    for y in range(0,height,d):
        pygame.draw.line(window,Color('grey'),(0,y),(width,y),1)

#绘制方格
def drawpane():
    for r in range(0,HEIGHT):
        for c in range(0,WIDTH):
            color=Color('white')
            pygame.draw.rect(window,color,(c*d,r*d,d,d))


#将食物绘制到界面上,注意food不能只绘制一次,绘制正方形时先绘制横坐标，后绘制纵坐标
def drawFood(food):
    color = Color('red')
    pygame.draw.rect(window,color,(food%WIDTH*d +dev,food/WIDTH*d+dev,d-2*dev,d-2*dev))

#绘制蛇,根据每个节点的前后节点绘制每个节点的样子
def drawSnake(snake):
    color  = Color('pink')
    color2 = Color('white')
    i = 0
    for c in snake:
        #为了提高性能
        if i == snake_size:
            return

        p = snake[i] - snake[i-1]
        #左右节点
        if p == 1or p == -1:
            pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d+dev,d,d-2*dev))
        #上下节点
        if p == WIDTH or p == -WIDTH:
            pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d,d-2*dev,d))

        if snake[i+1] != 0:
            s = snake[i+1] - snake[i]

            #四种拐点的绘制,左下
            if (p == -1 and s == -WIDTH)  or (p == WIDTH and s == 1):
                #现将当前节点设为空节点
                pygame.draw.rect(window,color2,(c%WIDTH*d,c/WIDTH*d,d,d))
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d+dev,d-2*dev,d-2*dev))
                #上边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d,d-2*dev,dev))
                #右边小方块
                pygame.draw.rect(window,color,((c%WIDTH+1)*d-dev,c/WIDTH*d+dev,dev,d-2*dev))

            #四种拐点的绘制,左上
            if (p == -1 and s == WIDTH) or (p == -WIDTH and s == 1):
                pygame.draw.rect(window,color2,(c%WIDTH*d,c/WIDTH*d,d,d))
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d+dev,d-2*dev,d-2*dev))
                #右边小方块
                pygame.draw.rect(window,color,((c%WIDTH+1)*d-dev,c/WIDTH*d+dev,dev,d-2*dev))
                # #下边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,(c/WIDTH+1)*d-dev,d-2*dev,dev))

            #四种拐点的绘制,右下
            if (p == 1 and s == -WIDTH) or (p == WIDTH and s == -1):
                pygame.draw.rect(window,color2,(c%WIDTH*d,c/WIDTH*d,d,d))
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d+dev,d-2*dev,d-2*dev))
                #上边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d,d-2*dev,dev))
                #左边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d+dev,dev,d-2*dev))

            #四种拐点的绘制,右上
            if ( p == 1 and s ==WIDTH ) or (p == -WIDTH and s== -1):
                pygame.draw.rect(window,color2,(c%WIDTH*d,c/WIDTH*d,d,d))
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d+dev,d-2*dev,d-2*dev))
                #左边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d+dev,dev,d-2*dev))
                # #下边小方块
                pygame.draw.rect(window,color,(c%WIDTH*d+dev,(c/WIDTH+1)*d-dev,d-2*dev,dev))

        i += 1


def drawBlock(c,colorString):
    color = Color(colorString)
    pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d+dev,d-2*dev,d-2*dev))

def drawHead(c,colorString):
    color = Color(colorString)
    if abs(snake[1] - snake[0]) == 1:
        pygame.draw.rect(window,color,(c%WIDTH*d,c/WIDTH*d+dev,d,d-2*dev))
    if abs(snake[1] - snake[0]) == WIDTH:
        pygame.draw.rect(window,color,(c%WIDTH*d+dev,c/WIDTH*d,d-2*dev,d))


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

def show_text(surface_handle, pos, text, color, font_bold = False, font_size = 2, font_italic = False):
    '''''
    Function:文字处理函数
    Input：surface_handle：surface句柄
           pos：文字显示位置
           color:文字颜色
           font_bold:是否加粗
           font_size:字体大小
           font_italic:是否斜体
    Output: NONE
    author: socrates
    blog:http://blog.csdn.net/dyx1024
    date:2012-04-15
    '''
    #获取系统字体，并设置文字大小
    cur_font = pygame.font.SysFont("宋体", font_size)

    #设置是否加粗属性
    cur_font.set_bold(font_bold)

    #设置是否斜体属性
    cur_font.set_italic(font_italic)

    #设置文字内容
    text_fmt = cur_font.render(text, 1, color)

    #绘制文字
    surface_handle.blit(text_fmt, pos)


#######################创建一个多线程类来控制蛇的运动####################
class SnakeMoveThread(threading.Thread):
    global direct
    def __init__(self,interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:

        #重置矩阵
            board_reset(snake, snake_size, board)
        # 如果蛇可以吃到食物，board_refresh返回true
        # 并且board中除了蛇身(=SNAKE)，其它的元素值表示从该点运动到食物的最短路径长
            if board_refresh(food, snake, board):
                best_move  = find_safe_way() # find_safe_way的唯一调用处
            else:
                best_move = follow_tail()
            if best_move == ERR:
                best_move = any_possible_move()
                # 上面一次思考，只得出一个方向，运行一步
            if best_move != ERR:
                make_move(best_move)

            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True

###############################以下是程序主函数##########################
if __name__ == '__main__':
    pygame.init()
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Greed Snake!')
    font = pygame.font.Font(None, 12)
    # snakeThread = SnakeMoveThread(0.05)
    # snakeThread.start()
    while True:
        drawpane()
        #drawBroder()
        #drawbackground()
        drawFood(food)
        #监听各种外部事件
        for event in pygame.event.get():
            if event.type == QUIT:
                #snakeThread.stop()
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

                    #重置矩阵
        board_reset(snake, snake_size, board)
        # 如果蛇可以吃到食物，board_refresh返回true
        # 并且board中除了蛇身(=SNAKE)，其它的元素值表示从该点运动到食物的最短路径长
        if board_refresh(food, snake, board):
            best_move  = find_safe_way() # find_safe_way的唯一调用处
        else:
            best_move = follow_tail()
        if best_move == ERR:
            best_move = any_possible_move()
            # 上面一次思考，只得出一个方向，运行一步
        if best_move != ERR:
            make_move(best_move)
        #绘制蛇身
        drawSnake(snake)
        #绘制蛇头
        drawHead(snake[HEAD],'pink')
        title_info = 'your score: ' + str(snake_size)
        color = Color('grey')
        show_text(window, (20, 20), title_info, color , False, 20)
        pygame.display.update()

