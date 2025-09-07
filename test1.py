from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ---------- Global / Config ----------
camera_pos = (0, 500, 500)
fovY = 120
GRID_LENGTH = 600

# Snake config
CELL = 40                 # Increased for larger snake and food (was 32)
SNAKE_INIT_LEN = 5
SNAKE_STEP_FRAMES = 12    # Slower movement
SNAKE_MIN_LEN = 3

# Food spawn margins so items don't overlap walls
SPAWN_MARGIN = 60

# Game state
snake = []                # list of [x,y,z] (z fixed = 20)
direction = [CELL, 0]     # initial dir along +x
pending_turn = None       # queued turn to avoid double-turns in one step
move_frame_counter = 0
score = 0
game_over = False


# Items
food_normal = None        # cube: grow +1, +1 point
food_shrink = None        # cube: release 2 tail cubes, +0 points
food_special = None       # sphere: +5 points, no length change

# Camera control (keep from template)
camera_angle_horizontal = 0
camera_height = 500

# ---------- Utility ----------
def snap_to_cell(v):
    # keep items aligned to CELL grid
    return int(round(v / CELL)) * CELL

def rand_cell_pos():
    x = random.randint(-(GRID_LENGTH - SPAWN_MARGIN)//CELL, (GRID_LENGTH - SPAWN_MARGIN)//CELL) * CELL
    y = random.randint(-(GRID_LENGTH - SPAWN_MARGIN)//CELL, (GRID_LENGTH - SPAWN_MARGIN)//CELL) * CELL
    return x, y

def spawn_food_away_from_snake():
    while True:
        x, y = rand_cell_pos()
        if all(abs(seg[0]-x) > CELL or abs(seg[1]-y) > CELL for seg in snake):
            return [x, y, 20]

# ---------- Template UI ----------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Grid (kept like your template) ----------
def draw_grid_and_boundaries():
    glBegin(GL_QUADS)
    divisions = 4
    sec = GRID_LENGTH // divisions
    for i in range(-divisions, divisions):
        for j in range(-divisions, divisions):
            if (i + j) % 2 == 0:
                glColor3f(0.9, 0.9, 0.9)
            else:
                glColor3f(0.7, 0.5, 0.95)
            x1 = i * sec
            x2 = (i + 1) * sec
            y1 = j * sec
            y2 = (j + 1) * sec
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x1, y2, 0)
    glEnd()

    boundary_height = 100
    glColor3f(0.15, 0.78, 0.85)
    glPushMatrix()
    glTranslatef(0, GRID_LENGTH, boundary_height / 2)
    glScalef(GRID_LENGTH * 2, 10, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.68, 0.84, 0.51)
    glPushMatrix()
    glTranslatef(0, -GRID_LENGTH, boundary_height / 2)
    glScalef(GRID_LENGTH * 2, 10, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.0, 0.0, 0.545)
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 0, boundary_height / 2)
    glScalef(10, GRID_LENGTH * 2, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(1, 1, 1)
    glPushMatrix()
    glTranslatef(GRID_LENGTH, 0, boundary_height / 2)
    glScalef(10, GRID_LENGTH * 2, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

# ---------- Camera (uses your template approach) ----------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    cam_dist = 500
    cam_x = cam_dist * math.cos(math.radians(camera_angle_horizontal))
    cam_y = cam_dist * math.sin(math.radians(camera_angle_horizontal))
    gluLookAt(cam_x, cam_y, camera_height, 0, 0, 0, 0, 0, 1)

# ---------- Snake Rendering ----------
def draw_snake():
    # Head (distinct color)
    if not snake:
        return
    hx, hy, hz = snake[0]
    glPushMatrix()
    glTranslatef(hx, hy, hz)
    glColor3f(0.2, 0.9, 0.2)
    glutSolidCube(CELL * 1.1)  # Slightly larger head
    glPopMatrix()

    # Body
    glColor3f(0.0, 0.6, 0.0)
    for seg in snake[1:]:
        glPushMatrix()
        glTranslatef(seg[0], seg[1], seg[2])
        glutSolidCube(CELL)
        glPopMatrix()

# ---------- Food Rendering ----------
def draw_food():
    # normal cube (grow) - orange
    if food_normal:
        glPushMatrix()
        glTranslatef(food_normal[0], food_normal[1], food_normal[2])
        glColor3f(1.0, 0.6, 0.0)  # orange
        glutSolidCube(CELL * 1.1)  # larger
        glPopMatrix()

    # shrink cube (release 2) - red
    if food_shrink:
        glPushMatrix()
        glTranslatef(food_shrink[0], food_shrink[1], food_shrink[2])
        glColor3f(0.9, 0.1, 0.1)  # red
        glutSolidCube(CELL * 1.1)  # larger
        glPopMatrix()

    # special sphere (bonus) - yellow
    if food_special:
        glPushMatrix()
        glTranslatef(food_special[0], food_special[1], food_special[2])
        glColor3f(1.0, 1.0, 0.0)  # yellow
        gluSphere(gluNewQuadric(), CELL * 0.9, 24, 24)  # larger sphere
        glPopMatrix()

# ---------- Game Logic ----------
def reset_game():
    global snake, direction, score, game_over
    global food_normal, food_shrink, food_special
    global move_frame_counter, pending_turn

    score = 0
    game_over = False
    move_frame_counter = 0
    pending_turn = None

    # center-start snake along +x
    snake = []
    start_x, start_y = 0, 0
    for i in range(SNAKE_INIT_LEN):
        snake.append([start_x - i * CELL, start_y, 20])
    direction = [CELL, 0]

    # Food rarity: orange (normal) most common, yellow (special) rare, red (shrink) most rare
    food_normal = spawn_food_away_from_snake()   # always at least one orange
    food_special = None
    food_shrink = None
    roll = random.random()
    if roll < 0.2:
        food_special = spawn_food_away_from_snake()  # yellow, rare
    elif roll < 0.3:
        food_shrink = spawn_food_away_from_snake()   # red, most rare

def move_snake_one_step():
    global snake, food_normal, food_shrink, food_special, score, game_over

    apply_pending_turn()

    hx, hy, hz = snake[0]
    nx = hx + direction[0]
    ny = hy + direction[1]
    nz = hz

    if abs(nx) >= GRID_LENGTH or abs(ny) >= GRID_LENGTH:
        game_over = True
        return

    for seg in snake[1:]:
        if seg[0] == nx and seg[1] == ny:
            game_over = True
            return

    snake.insert(0, [nx, ny, nz])

    ate_normal = food_normal and nx == food_normal[0] and ny == food_normal[1]
    ate_shrink = food_shrink and nx == food_shrink[0] and ny == food_shrink[1]
    ate_special = food_special and nx == food_special[0] and ny == food_special[1]

    if ate_normal:
        score += 1
        food_normal = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        # no tail pop
    elif ate_special:
        score += 5
        food_special = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        snake.pop()
    elif ate_shrink:
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
        food_shrink = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
    else:
        snake.pop()

def apply_pending_turn():
    global pending_turn, direction
    if not pending_turn:
        return
    # ignore reversal if length > 1
    ndx, ndy = pending_turn
    if len(snake) > 1 and snake[0][0] + ndx == snake[1][0] and snake[0][1] + ndy == snake[1][1]:
        pending_turn = None
        return
    direction = [ndx, ndy]
    pending_turn = None

def speed_frames():
    # Only yellow food (score +5) increases speed, others do not
    # So, speed only increases for multiples of 5 score (yellow sphere)
    yellow_score = score // 10
    return max(2, SNAKE_STEP_FRAMES - yellow_score)

# ---------- Input ----------
def keyboardListener(key, x, y):
    global game_over
    if game_over and key == b"r":
        reset_game()

def keyboardUpListener(key, x, y):
    pass  # not needed for snake

def specialKeyListener(key, x, y):
    # queue turn to apply exactly on next step
    global pending_turn, camera_angle_horizontal, camera_height
    if key == GLUT_KEY_LEFT:
        pending_turn = [0, -CELL]
    elif key == GLUT_KEY_RIGHT:
        pending_turn = [0, CELL]
    elif key == GLUT_KEY_UP:
        pending_turn = [-CELL, 0]
    elif key == GLUT_KEY_DOWN:
        pending_turn = [CELL, 0]

def mouseListener(button, state, x, y):
    # not used in snake; kept for template consistency
    pass

# ---------- Idle / Draw ----------
def idle():
    global move_frame_counter, game_over
    if not game_over:
        move_frame_counter += 1
        if move_frame_counter >= speed_frames():
            move_frame_counter = 0
            move_snake_one_step()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    draw_grid_and_boundaries()
    draw_snake()
    draw_food()

    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 740, "Controls: Arrow keys to turn | R to Restart (after game over)")
    draw_text(10, 710, "Foods: Orange=Grow +1 | Red=Release 2 | Yellow Sphere=+5")

    if game_over:
        draw_text(380, 420, "GAME OVER!")
        draw_text(360, 390, "Press R to restart")

    glutSwapBuffers()

# ---------- Main ----------
def main():
    reset_game()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Snake - OpenGL (Template-Compliant)")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()