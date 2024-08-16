from datetime import datetime, timedelta
from pynput import keyboard, mouse
import threading
import sqlite3
import psutil
import ctypes
import time
import math
import sys
import os

scriptName = os.path.basename(__file__)

# Checks if the script is already running
def isAlreadyRunning():
    mutex_name = "MyPCStatsMutex"  # Unique identifier for your application
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()

    # ERROR_ALREADY_EXISTS is 183; indicates another instance is running
    ERROR_ALREADY_EXISTS = 183

    if last_error == ERROR_ALREADY_EXISTS:
        return True
    else:
        return False

# If the script is already running, exit
if isAlreadyRunning():
    sys.exit()

try:
    # Get the directory of the script/executable
    if getattr(sys, 'frozen', False):
        # If the app is an exe
        scriptDirectory = os.path.dirname(sys.executable)
    else:
        # If running as a script
        scriptDirectory = os.path.dirname(os.path.abspath(__file__))

    # Path to the database
    DATABASE = os.path.join(scriptDirectory, 'InputDB.db')    
    
    # Dictionaries to keep track of inputs and timestamps
    pressedKeys = {}
    pressedButtons = {}

    # Conversion factor for calculations
    PIXEL_TO_METER_CONVERSION = 0.0002646

    # Mapping control characters for more readable names
    CONTROL_CHAR_MAP = {
        '\x01': 'ctrl+a',
        '\x02': 'ctrl+b',
        '\x03': 'ctrl+c',
        '\x04': 'ctrl+d',
        '\x05': 'ctrl+e',
        '\x06': 'ctrl+f',
        '\x07': 'ctrl+g',
        '\x08': 'ctrl+h',
        '\x09': 'ctrl+i',
        '\x0a': 'ctrl+j',
        '\x0b': 'ctrl+k',
        '\x0c': 'ctrl+l',
        '\x0d': 'ctrl+m',
        '\x0e': 'ctrl+n',
        '\x0f': 'ctrl+o',
        '\x10': 'ctrl+p',
        '\x11': 'ctrl+q',
        '\x12': 'ctrl+r',
        '\x13': 'ctrl+s',
        '\x14': 'ctrl+t',
        '\x15': 'ctrl+u',
        '\x16': 'ctrl+v',
        '\x17': 'ctrl+w',
        '\x18': 'ctrl+x',
        '\x19': 'ctrl+y',
        '\x1a': 'ctrl+z'
    }

    # All letters, numbers, special characters, and mouse inputs that will be tracked
    ALL_KEYS = list('abcdefghijklmnopqrstuvwxyz0123456789-=[]\\;\',./!@#$%^&*()_+{}|:"<>?') + \
            ['space', 'tab', 'capslock', 'shift', 'ctrl', 'alt', 'win', 'enter', 'backspace', 'esc', 'up', 'down', 'left', 'right'] + \
            ['mouseleft', 'mouseright', 'mousemiddle', 'scrollup', 'scrolldown']

    # Sets up the tables and data in the database, readying for collection
    def setupDatabase():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Create tables if they are not made yet
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS eventTypes (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                eventTypeID INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                key TEXT,
                button TEXT,
                positionX INTEGER,
                positionY INTEGER,
                duration REAL,
                FOREIGN KEY (eventTypeID) REFERENCES eventTypes(id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mousePositions (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                positionX INTEGER,
                positionY INTEGER
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS totalCounts (
                id INTEGER PRIMARY KEY,
                inputName TEXT UNIQUE NOT NULL,
                totalCount INTEGER DEFAULT 0
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS lifetimeLongestDurations (
                id INTEGER PRIMARY KEY,
                inputName TEXT UNIQUE NOT NULL,
                duration REAL DEFAULT 0
            )
            ''')

            cursor.execute('''
            INSERT OR IGNORE INTO eventTypes (id, name) VALUES
            (1, 'keyPress'),
            (2, 'keyRelease'),
            (3, 'mouseClick'),
            (4, 'mouseRelease'),
            (5, 'mouseScroll')
            ''')

            # Insert all inputs into totalCounts and lifetimeLongestDurations
            for key in ALL_KEYS:
                cursor.execute('''
                INSERT OR IGNORE INTO totalCounts (inputName) VALUES (?)
                ''', (key,))
                cursor.execute('''
                INSERT OR IGNORE INTO lifetimeLongestDurations (inputName) VALUES (?)
                ''', (key,))

            # Insert mouse position tracking total into totalCounts
            cursor.execute('''
            INSERT OR IGNORE INTO totalCounts (inputName) VALUES (?)
            ''', ('mouseposition',))

            # Insert mouse distance traversed into totalCounts
            cursor.execute('''
            INSERT OR IGNORE INTO totalCounts (inputName) VALUES (?)
            ''', ('mousedistance',))

    setupDatabase()

    # Helper for database queries
    def executeDB(query, params=()):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
    # Functions for logging inputs
    def logEvent(eventTypeID, key=None, button=None, positionX=None, positionY=None, duration=None):
        executeDB('''
            INSERT INTO events (eventTypeID, timestamp, key, button, positionX, positionY, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (eventTypeID, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key, button, positionX, positionY, duration))

    def logMousePosition(positionX, positionY):
        executeDB('''
            INSERT INTO mousePositions (timestamp, positionX, positionY)
            VALUES (?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), positionX, positionY))

    def incrementTotalCount(inputName):
        executeDB('''
            UPDATE totalCounts SET totalCount = totalCount + 1 WHERE inputName = ?
        ''', (inputName.lower(),))

    def updateLifetimeLongestDuration(inputName, duration):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT duration FROM lifetimeLongestDurations WHERE inputName = ?
            ''', (inputName,))
            result = cursor.fetchone()
            if result and duration > result[0]:
                cursor.execute('''
                    UPDATE lifetimeLongestDurations SET duration = ? WHERE inputName = ?
                ''', (duration, inputName))
                conn.commit()
                
    def updateMouseTraversedDistance(distance):
        executeDB('''
            UPDATE totalCounts SET totalCount = totalCount + ? WHERE inputName = 'mousedistance'
        ''', (distance,))
        
    def updateLifetimeLongestDurations():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT inputName, duration FROM lifetimeLongestDurations WHERE duration > 0
            ''')
            return cursor.fetchall()

    # Makes keys into more readable strings
    def formatKey(key):
        if hasattr(key, 'char') and key.char is not None:
            char = key.char.lower()
            if char in CONTROL_CHAR_MAP:
                return CONTROL_CHAR_MAP[char]
            elif char.isprintable():
                return char
            else:
                return repr(char)
        else:
            keyStr = str(key).lower()
            if 'key.' in keyStr:
                keyStr = keyStr.split('.')[1]
                if keyStr.startswith('ctrl_'):
                    return 'ctrl'
                elif keyStr.startswith('alt_'):
                    return 'alt'
                elif keyStr.startswith('cmd'):
                    return 'win'
                elif keyStr == 'caps_lock':
                    return 'capslock'
                elif keyStr in ['shift_r', 'shift_l']:
                    return 'shift'
                return keyStr
            return keyStr

    # Wipes old data to avoid taking up too much storage
    def wipeOldData():
        while True:
            removeMousePositions = datetime.now() - timedelta(days=7)
            executeDB('DELETE FROM mousePositions WHERE timestamp < ?', (removeMousePositions.strftime('%Y-%m-%d %H:%M:%S'),))

            time.sleep(86400)

    # Input handling functions
    def onKeyPress(key):
        keyStr = formatKey(key)
        if keyStr not in pressedKeys:
            pressedKeys[keyStr] = datetime.now()

    def onKeyRelease(key):
        keyStr = formatKey(key)
        if keyStr in pressedKeys:
            pressTime = pressedKeys.pop(keyStr)
            duration = (datetime.now() - pressTime).total_seconds()
            logEvent(1, key=keyStr, duration=duration)
            incrementTotalCount(keyStr)
            updateLifetimeLongestDuration(keyStr, duration)

    def onMouseClick(x, y, button, pressed):
        buttonString = f"mouse{str(button).split('.')[1].lower()}"
        if pressed:
            if buttonString not in pressedButtons:
                pressedButtons[buttonString] = (datetime.now(), x, y)
        else:
            if buttonString in pressedButtons:
                pressTime, posX, posY = pressedButtons.pop(buttonString)
                duration = (datetime.now() - pressTime).total_seconds()
                logEvent(3, button=buttonString, positionX=posX, positionY=posY, duration=duration)
                logEvent(4, button=buttonString, positionX=x, positionY=y)
                incrementTotalCount(buttonString)
                updateLifetimeLongestDuration(buttonString, duration)

    def onScroll(x, y, dx, dy):
        scrollDirection = 'scrollup' if dy > 0 else 'scrolldown'
        incrementTotalCount(scrollDirection)

    def trackMousePosition():
        mouseController = mouse.Controller()
        lastPosition = mouseController.position

        while True:
            try:
                currentPosition = mouseController.position
                if currentPosition is None:
                    # Skip if the position is None (lock screen)
                    time.sleep(0.1)
                    continue

                x, y = currentPosition
                if (x, y) != lastPosition:
                    dx = x - lastPosition[0]
                    dy = y - lastPosition[1]
                    distance = math.sqrt(dx * dx + dy * dy) * PIXEL_TO_METER_CONVERSION

                    logMousePosition(x, y)
                    incrementTotalCount('mouseposition')
                    updateMouseTraversedDistance(distance)

                    lastPosition = (x, y)
                time.sleep(0.1)
            except Exception as e:
                time.sleep(0.1)
                
    # Starts the background process for tracking inputs
    def startBGProcess():
        threading.Thread(target=trackMousePosition, daemon=True).start()
        threading.Thread(target=wipeOldData, daemon=True).start()
        
    # Start listeners and background processes
    keyboardListener = keyboard.Listener(on_press=onKeyPress, on_release=onKeyRelease)
    mouseListener = mouse.Listener(on_click=onMouseClick, on_scroll=onScroll)

    keyboardListener.start()
    mouseListener.start()
    startBGProcess()

    keyboardListener.join()
    mouseListener.join()

    pass

finally:
    print("exiting...")
