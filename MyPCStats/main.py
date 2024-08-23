from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout, QLabel, QScrollArea, QCalendarWidget, QDialog, QGraphicsView, QGraphicsScene, QGraphicsProxyWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtGui import QDesktopServices, QColor, QPainter, QPen, QIcon
from PySide6.QtCore import QEvent, QUrl, QTimer, Qt, QPoint, QDate
from datetime import datetime, timedelta
from MyPCStats_ui import Ui_MainWindow
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import sqlite3
import random
import math
import sys
import os

# Gets the app/script directory, depending on the run
if getattr(sys, 'frozen', False):
    scriptDirectory = os.path.dirname(sys.executable)
else:
    scriptDirectory = os.path.dirname(os.path.abspath(__file__))

# Path to the database
DATABASE = os.path.join(scriptDirectory, 'scripts', 'InputDB.db')

# Given a start and end time, queries the database to get all mouse inputs in that timeframe
def getMouseClicksBetweenTimes(conn, startTime, endTime):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, COUNT(*)
        FROM events
        WHERE timestamp BETWEEN ? AND ?
        AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
        AND eventTypeID IN ('3')
        GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
    ''', (startTime, endTime))
    data = cursor.fetchall()
    return data

# Given a start and end time, queries the database to get all keyboard inputs in that timeframe
def getKeyboardInputsBetweenTimes(conn, startTime, endTime):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, COUNT(*)
        FROM events
        WHERE timestamp BETWEEN ? AND ?
        AND eventTypeID = 1
        GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
    ''', (startTime, endTime))
    data = cursor.fetchall()
    return data

# Queries the totalCounts table from the database and puts it into a dictionary
def getTotalCounts(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT inputName, totalCount
        FROM totalCounts
    ''')
    data = cursor.fetchall()
    
    totalCounts = {inputName: totalCount for inputName, totalCount in data}
    return totalCounts

# Queries the lifetimeLongestDurations table from the database and puts it into a dictionary
def getLifetimeLongestDurations(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT inputName, duration
        FROM lifetimeLongestDurations
    ''')
    data = cursor.fetchall()
    return {inputName: duration for inputName, duration in data}

# Functions for getting mouse inputs
def getTotalMouseClicks(totalCounts):
    return sum(totalCounts.get(button, 0) for button in ['mouseleft', 'mouseright', 'mousemiddle'])

def getTotalLeftClicks(totalCounts):
    return totalCounts.get('mouseleft', 0)

def getTotalRightClicks(totalCounts):
    return totalCounts.get('mouseright', 0)

def getTotalMiddleClicks(totalCounts):
    return totalCounts.get('mousemiddle', 0)

def getTotalMouseMovements(totalCounts):
    return totalCounts.get('mouseposition', 0)

def getTotalScrollsDown(totalCounts):
    return totalCounts.get('scrolldown', 0)

def getTotalScrollsUp(totalCounts):
    return totalCounts.get('scrollup', 0)

def getMouseDistance(totalCounts):
    return totalCounts.get('mousedistance', 0)

# Looks for the largest of the 3 main mouse inputs in the totalCounts dictionary
def getMostUsedMouseButton(totalCounts):
    names = {
        'mouseleft': 'Left Click',
        'mousemiddle': 'Middle Click',
        'mouseright': 'Right Click'
    }

    maxButton = max(['mouseleft', 'mouseright', 'mousemiddle'], key=lambda button: totalCounts.get(button, 0))

    return names.get(maxButton, None)

# Looks for the largest of the special key keyboard inputs in the totalCounts dictionary
def getFavoriteSpecialKey(totalCounts):
    specialKeys = ['esc', 'tab', 'capslock', 'shift', 'ctrl', 'win', 'alt', 'enter']
    favoriteKey = max(specialKeys, key=lambda key: totalCounts.get(key, 0))
    
    if favoriteKey == 'capslock':
        return 'Caps Lock'
    else:
        return favoriteKey.capitalize()

# Looks for the key with the lowest total in the totalCounts dictionary
def getLeastUsedKey(totalCounts):
    keys = [key for key in totalCounts if not ('mouse' in key or 'scroll' in key)]
    leastUsedKey = min(keys, key=lambda key: totalCounts.get(key, float('inf')))
    
    if leastUsedKey == 'capslock':
        return 'Caps Lock'
    else:
        return leastUsedKey.capitalize()

# Sums all of the values pertaining to the keyboard in the totalCounts dictionary
def getTotalKeyInputs(totalCounts):
    keys = [key for key in totalCounts if not ('mouse' in key or 'scroll' in key)]
    totalInputs = sum(totalCounts[key] for key in keys)
    return totalInputs

# Finds the 5 letters with the highest counts in the totalCounts dictionary
def getTop5Letters(totalCounts):
    letters = {key: count for key, count in totalCounts.items() if key.isalpha() and len(key) == 1}

    sortedLetters = sorted(letters.items(), key=lambda item: item[1], reverse=True)[:5]
    return [(letter.upper(), count) for letter, count in sortedLetters]

# Finds the 5 letters with the lowest counts in the totalCounts dictionary
def getBottom5Letters(totalCounts):
    letters = {key: count for key, count in totalCounts.items() if key.isalpha() and len(key) == 1}

    sortedLetters = sorted(letters.items(), key=lambda item: item[1])[:5]
    return [(letter.upper(), count) for letter, count in sortedLetters]

# Finds the amount of number key inputs as well as their real total
def getNumberKeyInputs(totalCounts):
    numberKeys = [str(i) for i in range(10)]
    totalInputs = sum(totalCounts.get(key, 0) for key in numberKeys)
    realNumberTotal = sum(int(key) * totalCounts.get(key, 0) for key in numberKeys)
    return totalInputs, realNumberTotal

# Finds the mouse button that has the longest duration held down in the longestDurations dictionary
def getLongestMouseClick(longestDurations):
    mouseButtons = ['mouseleft', 'mouseright', 'mousemiddle']
    longestClick = max((longestDurations.get(button, 0) for button in mouseButtons), default=0)
    return round(longestClick, 2)

# Finds the amount of mouse clicks in the last 24 hours
def getMouseClicksLast24Hours(conn):
    nowLocal = datetime.now()
    yesterdayLocal = nowLocal - timedelta(days=1)

    nowLocalStr = nowLocal.strftime('%Y-%m-%d %H:%M:%S')
    yesterdayLocalStr = yesterdayLocal.strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*)
        FROM events
        WHERE timestamp BETWEEN ? AND ?
        AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
        AND eventTypeID IN ('3')
    ''', (yesterdayLocalStr, nowLocalStr))

    count = cursor.fetchone()[0]
    return count

# Finds the amount of key inputs in the last 24 hours
def getKeyInputsLast24Hours(conn):
    nowLocal = datetime.now()
    yesterdayLocal = nowLocal - timedelta(days=1)

    nowLocalStr = nowLocal.strftime('%Y-%m-%d %H:%M:%S')
    yesterdayLocalStr = yesterdayLocal.strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*)
        FROM events
        WHERE timestamp BETWEEN ? AND ?
        AND eventTypeID IN (1)
    ''', (yesterdayLocalStr, nowLocalStr))

    count = cursor.fetchone()[0]
    return count

# Finds the average amount of user inputs every hour
def getAverageInputsPerHour(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT strftime('%H', timestamp) as hour, COUNT(*)
        FROM events
        WHERE eventTypeID IN (1, 3)
        GROUP BY hour
    ''')
    data = cursor.fetchall()

    hourlyTotals = {int(hour): count for hour, count in data}
    hourlyAverages = [(hour, hourlyTotals.get(hour, 0) / 7) for hour in range(24)]
    return hourlyAverages

# Overlay widget for the mouse click map
class OverlayWidget(QWidget):
    def __init__(self, conn):
        super(OverlayWidget, self).__init__()
        self.conn = conn
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowOpacity(0.7)
        self.clickData = []
        self.currentClickIndex = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateOverlay)
        self.dotSize = 5
        self.animationEnabled = True
        self.showGreenDots = True
        self.showRedDots = True
        self.showYellowDots = True

    # Function to show the mouse clicks over the last 24hrs
    def showOverlay(self):
        self.clickData = []
        self.currentClickIndex = 0
        self.clickData = self.getMouseClicksLast24Hours()
        if self.clickData:
            if self.animationEnabled:
                self.timer.start(1)
            else:
                self.update()
            self.showFullScreen()

    # Hides the overlay and stops the timer
    def hideOverlay(self):
        self.timer.stop()
        self.hide()

    # Function for painting the dots on the screen
    def paintEvent(self, event):
        super(OverlayWidget, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 175))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        for i in range(self.currentClickIndex if self.animationEnabled else len(self.clickData)):
            if i < len(self.clickData):
                x, y, button = self.clickData[i]
                if button == 'mouseleft':
                    painter.setBrush(QColor(0, 255, 0, 204))
                elif button == 'mouseright':
                    painter.setBrush(QColor(255, 0, 0, 204))
                elif button == 'mousemiddle':
                    painter.setBrush(QColor(255, 255, 0, 204))
                painter.drawEllipse(QPoint(x, y), self.dotSize, self.dotSize)

    # If you press esc, the overlay is removed
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hideOverlay()
        super(OverlayWidget, self).keyPressEvent(event)

    # Handles animation and repainting the overlay
    def updateOverlay(self):
        if self.animationEnabled:
            self.currentClickIndex += 1
            if self.currentClickIndex > len(self.clickData):
                self.timer.stop()
        else:
            self.currentClickIndex = len(self.clickData)
        self.update()

    # Gets the last 24 hours of mouse inputs
    def getMouseClicksLast24Hours(self):
        nowLocal = datetime.now()
        yesterdayLocal = nowLocal - timedelta(days=1)

        nowLocalStr = nowLocal.strftime('%Y-%m-%d %H:%M:%S')
        yesterdayLocalStr = yesterdayLocal.strftime('%Y-%m-%d %H:%M:%S')

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT positionX, positionY, button
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND button IN ('mouseleft', 'mouseright', 'mousemiddle')
        ''', (yesterdayLocalStr, nowLocalStr))

        data = cursor.fetchall()
        cursor.close()

        filteredData = []
        for click in data:
            x, y, button = click
            if button == 'mouseleft' and self.showGreenDots:
                filteredData.append(click)
            elif button == 'mouseright' and self.showRedDots:
                filteredData.append(click)
            elif button == 'mousemiddle' and self.showYellowDots:
                filteredData.append(click)

        return filteredData
    
    # Handles the animation toggle
    def setAnimationEnabled(self, enabled):
        self.animationEnabled = enabled
        
# Same as the OverlayWidget, but for drawing the user's mouse movement history
class MouseDrawOverlayWidget(QWidget):
    def __init__(self, conn):
        super(MouseDrawOverlayWidget, self).__init__()
        self.conn = conn
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowOpacity(0.7)
        self.mousePositions = []
        self.currentPositionIndex = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateOverlay)
        self.animationEnabled = True
        self.lineColor = QColor(255, 255, 255, 255)
        self.lineWidth = 5
        self.historyAmount = 2000

    # Function to show the last 2,000 or 10,000 mouse movements
    def showOverlay(self):
        self.mousePositions = []
        self.currentPositionIndex = 0
        self.mousePositions = self.getMousePositions()
        if self.mousePositions:
            if self.animationEnabled:
                self.timer.start(1)
            else:
                self.update()
            self.showFullScreen()

    # Hides the overlay and stops the timer
    def hideOverlay(self):
        self.timer.stop()
        self.hide()

    # Function for painting the lines on the screen
    def paintEvent(self, event):
        super(MouseDrawOverlayWidget, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 175))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        pen = QPen(self.lineColor)
        pen.setWidth(self.lineWidth)
        painter.setPen(pen)

        for i in range(1, self.currentPositionIndex if self.animationEnabled else len(self.mousePositions)):
            if i < len(self.mousePositions):
                x1, y1 = self.mousePositions[i - 1]
                x2, y2 = self.mousePositions[i]
                painter.drawLine(QPoint(x1, y1), QPoint(x2, y2))

    # When esc is pressed, the overlay closes
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hideOverlay()
        super(MouseDrawOverlayWidget, self).keyPressEvent(event)

    # Handles animation and repainting the overlay
    def updateOverlay(self):
        if self.animationEnabled:
            self.currentPositionIndex += 1
            if self.currentPositionIndex > len(self.mousePositions):
                self.timer.stop()
        else:
            self.currentPositionIndex = len(self.mousePositions)
        self.update()

    # Gets the last x amount of mouse movements determined by a button
    def getMousePositions(self):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT positionX, positionY
            FROM mousePositions
            ORDER BY id DESC
            LIMIT {self.historyAmount}
        ''')
        data = cursor.fetchall()
        cursor.close()
        return [(x, y) for x, y in reversed(data)]

    # Function for handling the animation toggle
    def setAnimationEnabled(self, enabled):
        self.animationEnabled = enabled

    # Function for handling the line weight
    def setLineWeight(self, weight):
        self.lineWidth = weight
        self.update()

    # Function for handling the amount of lines being drawn
    def setHistoryAmount(self, amount):
        self.historyAmount = amount
        self.update()

# Graph creation and customization
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, backgroundColor='#171C30'):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.patch.set_facecolor(backgroundColor)
        self.axes.set_facecolor("#1C2540")
        super(MplCanvas, self).__init__(fig)
        self.setStyleSheet(f"background-color: {backgroundColor};")
        self.setFocusPolicy(Qt.NoFocus)
        
    # Lets mouse scroll over graphs
    def wheelEvent(self, event):
        self.parent().wheelEvent(event)
        
# Custom QDialog for choosing a date on the calendar (for active sessions)
class CustomDatePicker(QDialog):
    def __init__(self, parent=None):
        super(CustomDatePicker, self).__init__(parent)
        self.setWindowTitle("Select Date")
        self.calendar = QCalendarWidget(self)
        self.calendar.clicked.connect(self.onDateSelected)
        layout = QVBoxLayout()
        layout.addWidget(self.calendar)
        self.setLayout(layout)

    def onDateSelected(self, date):
        self.selectedDate = date
        self.accept()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        
        self.setWindowTitle("MyPCStats")

        iconPath = os.path.join(os.path.dirname(__file__), 'icons', 'MyPCStatsFavicon.ico')
        self.setWindowIcon(QIcon(iconPath))

        # Create a single database connection
        self.conn = sqlite3.connect(DATABASE)

        # List of buttons
        self.buttons = [
            self.HomeButton,
            self.MouseButton,
            self.KeyboardButton,
            self.AnalyticsButton,
            self.ConfigButton,
            self.SettingsButton
            ]

        # Changes page depending on the button
        for i, button in enumerate(self.buttons):
            button.clicked.connect(lambda _, index=i: self.changePage(index))
        
        self.highlightButton(0)
        
        # Home navigation buttons
        self.HomeMouseButton.installEventFilter(self)
        self.HomeKeyboardButton.installEventFilter(self)
        self.HomeAnalyticsButton.installEventFilter(self)
        
        # Assuming HelpHPText2 is already created in your UI
        self.HelpHPText2 = self.findChild(QLabel, "HelpHPText2")

        # Apply the event filter
        self.HelpHPText2.installEventFilter(self)

                
        # Homepage info buttons
        self.MouseExplainButton.clicked.connect(lambda: self.showExplanationPage(0))
        self.KeyboardExplainButton.clicked.connect(lambda: self.showExplanationPage(1))
        self.AnalyticsExplainButton.clicked.connect(lambda: self.showExplanationPage(2))
        self.HelpExplainButton.clicked.connect(lambda: self.showExplanationPage(3))

        # Other buttons
        self.HelpButton.clicked.connect(self.openHelpLink)
        self.ManualRefreshButton.clicked.connect(self.handleManualRefresh)
        
        # Update functions that use input totals every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAllTotals)
        self.timer.start(1000)
        
        # Update live plots every 5 seconds
        self.liveGraphTimer = QTimer(self)
        self.liveGraphTimer.timeout.connect(self.updateLivePlots)
        self.liveGraphTimer.start(5000)
        
        # Update active session info every 60 seconds
        self.activeSessionTimer = QTimer(self)
        self.activeSessionTimer.timeout.connect(self.updateActiveSessionInfo)
        self.activeSessionTimer.start(60000)

        # Update graphs every 5 minutes
        self.graphTimer = QTimer(self)
        self.graphTimer.timeout.connect(self.updateOtherPlots)
        self.graphTimer.start(300000)

        # Matplotlib Canvases for graphs
        self.liveCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.dayCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.weekCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.monthCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.yearCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.pieCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.kbPieCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.avgDayInputsCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.keyboardLiveCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.keyboardDayCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.keyboardWeekCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.keyboardMonthCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.keyboardYearCanvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.LiveGraphContainer.addWidget(self.liveCanvas)
        self.DayGraphContainer.addWidget(self.dayCanvas)
        self.WeekGraphContainer.addWidget(self.weekCanvas)
        self.MonthGraphContainer.addWidget(self.monthCanvas)
        self.YearGraphContainer.addWidget(self.yearCanvas)
        self.PieChartContainer.addWidget(self.pieCanvas)
        self.KBPieChartContainer.addWidget(self.kbPieCanvas)
        self.AvgDayInputsHolder.addWidget(self.avgDayInputsCanvas)
        self.KeyboardLiveGraphContainer.addWidget(self.keyboardLiveCanvas)
        self.KeyboardDayGraphContainer.addWidget(self.keyboardDayCanvas)
        self.KeyboardWeekGraphContainer.addWidget(self.keyboardWeekCanvas)
        self.KeyboardMonthGraphContainer.addWidget(self.keyboardMonthCanvas)
        self.KeyboardYearGraphContainer.addWidget(self.keyboardYearCanvas)
        
        self.updateAllPlots()
        
        # Overlay buttons
        self.overlay = OverlayWidget(self.conn)
        self.drawOverlay = MouseDrawOverlayWidget(self.conn)
        self.ShowOverlayButton.clicked.connect(self.showOverlay)
        self.ShowDrawOverlayButton.clicked.connect(self.showDrawOverlay)
        
        # Overlay Control buttons
        self.ToggleHighContrast.toggled.connect(self.toggleHighContrast)
        self.ToggleAnimation.toggled.connect(self.toggleAnimation)
        self.GreenDotL.toggled.connect(self.toggleGreenDots)
        self.RedDotL.toggled.connect(self.toggleRedDots)
        self.YellowDotL.toggled.connect(self.toggleYellowDots)
        
        self.ToggleHighContrast2.toggled.connect(self.toggleHighContrast2)
        self.ToggleAnimation2.toggled.connect(self.toggleAnimation2)
        self.ToggleLineWeight.toggled.connect(self.toggleLineWeight)
        self.ToggleAmountOfHistory.toggled.connect(self.toggleAmountOfHistory)
        
        # Connect randomize buttons
        self.RandomizeL.clicked.connect(self.randomizeKey)
        self.RandomizeR.clicked.connect(self.randomizeKey)
        self.randomizeKey()
        
        # Keyboard heatmap buttons
        self.RoundedButton.toggled.connect(self.toggleRoundedBorders)
        self.ToggleLetterButton.toggled.connect(self.toggleKeyTextVisibility)
        self.ToggleColorSchemeButton.toggled.connect(self.toggleColorScheme)
        self.colorScheme = 'greenToRedScheme'
        
        # Close database connection
        QApplication.instance().aboutToQuit.connect(self.closeDatabaseConnection)
        
        # Set default date to current date and update timeline chart
        currentDate = QDate.currentDate()
        self.selectedDate = currentDate
        self.SelectedDate.setText(self.selectedDate.toString('MMMM d'))
        self.updateTimelineChart(self.selectedDate)

        # Date change button
        self.DateLabel.clicked.connect(self.openDatePicker)
        
        # Handles manual refreshing
        self.manualRefreshTimer = QTimer(self)
        self.manualRefreshTimer.setSingleShot(True)
        self.manualRefreshTimer.timeout.connect(lambda: self.ManualRefreshButton.setEnabled(True))
        
        # Button that opens the application's location in file explorer
        self.OAFHolder.clicked.connect(self.openAppFolder)
        
    # Function for helping resize the homepage
    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        self.adjustFontSize()

    # Function that resizes the text font based on window height
    def adjustFontSize(self):
        height = self.height()

        HMBLabelMin = 18
        HMBLabelMax = 45
        mouseHPTitleMin = 32
        mouseHPTitleMax = 47
        mouseHPTextMin = 17
        mouseHPTextMax = 26

        HMBLabelSize = HMBLabelMin + (height - 625) * (HMBLabelMax - HMBLabelMin) / (1080 - 625)
        mouseHPTitleSize = mouseHPTitleMin + (height - 625) * (mouseHPTitleMax - mouseHPTitleMin) / (1080 - 625)
        mouseHPTextSize = mouseHPTextMin + (height - 625) * (mouseHPTextMax - mouseHPTextMin) / (1080 - 625)

        HMBLabelFont = self.HMBLabel.font()
        HMBLabelFont.setPointSizeF(HMBLabelSize)
        self.HMBLabel.setFont(HMBLabelFont)
        self.HKBLabel.setFont(HMBLabelFont)
        self.HALLabel.setFont(HMBLabelFont)
        self.HelpHPText5.setFont(HMBLabelFont)

        mouseHPTitleFont = self.MouseHPTitle.font()
        mouseHPTitleFont.setPointSizeF(mouseHPTitleSize)
        self.MouseHPTitle.setFont(mouseHPTitleFont)
        self.KeyboardHPTitle.setFont(mouseHPTitleFont)
        self.AnalyticsHPTitle.setFont(mouseHPTitleFont)
        self.HelpHPTitle.setFont(mouseHPTitleFont)
        self.WelcomeTitle.setFont(mouseHPTitleFont)

        MouseHPTextFont1 = self.MouseHPText1.font()
        MouseHPTextFont1.setPointSizeF(mouseHPTextSize)
        self.MouseHPText1.setFont(MouseHPTextFont1)
        self.KeyboardHPText1.setFont(MouseHPTextFont1)
        self.AnalyticsHPText1.setFont(MouseHPTextFont1)
        self.HelpHPText1.setFont(MouseHPTextFont1)

        MouseHPTextFont2 = self.MouseHPText2.font()
        MouseHPTextFont2.setPointSizeF(mouseHPTextSize)
        self.MouseHPText2.setFont(MouseHPTextFont2)
        self.KeyboardHPText2.setFont(MouseHPTextFont2)
        self.AnalyticsHPText2.setFont(MouseHPTextFont2)
        self.HelpHPText2.setFont(MouseHPTextFont2)
        self.HelpHPText3.setFont(MouseHPTextFont2)
        self.HelpHPText4.setFont(MouseHPTextFont2)
        self.HelpHPText5.setFont(MouseHPTextFont2)
        self.WelcomeText.setFont(MouseHPTextFont2)

    # Opens the application's folder in file explorer (changes depending on app/script)
    def openAppFolder(self):
        if getattr(sys, 'frozen', False):
            folder_path = os.path.dirname(sys.executable)
        else:
            folder_path = scriptDirectory
        os.startfile(folder_path)
        
    # Handles the popup calendar to choose the date
    def openDatePicker(self):
        datePicker = CustomDatePicker(self)
        if datePicker.exec():
            self.selectedDate = datePicker.selectedDate
            self.SelectedDate.setText(self.selectedDate.toString('MMMM d'))
            self.updateTimelineChart(self.selectedDate)

    # Handles updating the timeline chart based on the date selected
    def updateTimelineChart(self, selectedDate):
        cursor = self.conn.cursor()
        startDate = datetime(selectedDate.year(), selectedDate.month(), selectedDate.day())
        endDate = startDate + timedelta(days=1)

        cursor.execute('''
            SELECT timestamp
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND (eventTypeID = 1 OR eventTypeID = 3)
            ORDER BY timestamp
        ''', (startDate.strftime('%Y-%m-%d %H:%M:%S'), endDate.strftime('%Y-%m-%d %H:%M:%S')))

        data = cursor.fetchall()
        cursor.close()

        if not data:
            self.clearASDayChart()
            noDataLabel = QLabel("No Data")
            noDataLabel.setAlignment(Qt.AlignCenter)
            self.ASDayChart.addWidget(noDataLabel)
            self.DATotalLabel.setText(f"On {selectedDate.toString('MMMM d')}, you were\nactive for a total of 0h 0m")
        else:
            timestamps = [datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in data]
            sessions = self.calculateActiveSessions(timestamps)
            self.plotTimelineChart(sessions)

            # Calculate and format the total active time
            totalActiveTime = self.calculateTotalActiveTime(sessions)
            formattedTime = self.formatActiveTime(totalActiveTime)

            self.DATotalLabel.setText(f"On {selectedDate.toString('MMMM d')}, you were\nactive for a total of {formattedTime}")

    # Clears the data in the active session timeline chart so new data can be displayed
    def clearASDayChart(self):
        for i in reversed(range(self.ASDayChart.count())):
            widget = self.ASDayChart.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    # Calculates and returns the active session start and end times
    def calculateActiveSessions(self, timestamps):
        sessions = []
        sessionStart = timestamps[0]

        for i in range(1, len(timestamps)):
            if (timestamps[i] - timestamps[i - 1]).seconds > 900:  # 15 minutes
                sessions.append((sessionStart, timestamps[i - 1]))
                sessionStart = timestamps[i]

        sessions.append((sessionStart, timestamps[-1]))
        return sessions

    # Plots the active session times on a timeline chart
    def plotTimelineChart(self, sessions):
        self.clearASDayChart()

        canvas = MplCanvas(self, width=10, height=2, dpi=100)
        ax = canvas.axes

        for start, end in sessions:
            ax.plot([start, end], [1, 1], color='#00FF7D', linewidth=16, solid_capstyle='butt')

        # Chart customization
        ax.set_xlim(sessions[0][0].replace(hour=0, minute=0, second=0, microsecond=0), sessions[0][0].replace(hour=23, minute=59, second=59, microsecond=999999))
        ax.set_ylim(0.5, 1.5)
        ax.yaxis.set_visible(False)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        annot = ax.annotate(
            "", 
            xy=(0, 0), 
            xytext=(20, 20), 
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="black", ec="white"),
            arrowprops=dict(arrowstyle="-", color="white")
        )
        annot.set_visible(False)
        annot.set_color("white")  
        
        # Handles annotations
        def updateAnnot(start, end):
            midpoint = start + (end - start) / 2
            annot.xy = (midpoint, 1)
            text = f"{start.strftime('%I:%M%p')} to {end.strftime('%I:%M%p')}"
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.4)

            if midpoint.hour >= 0 and midpoint.hour < 8:
                annot.set_position((10, 20))
            elif midpoint.hour >= 8 and midpoint.hour < 16:
                annot.set_position((-10, 20))
            else:
                annot.set_position((-110, 20))

        # Handles hovering over data to view annotations
        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for line in ax.get_lines():
                    cont, _ = line.contains(event)
                    if cont:
                        start, end = line.get_xdata()
                        updateAnnot(start, end)
                        annot.set_visible(True)
                        canvas.draw_idle()
                        break
                else:
                    if vis:
                        annot.set_visible(False)
                        canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", hover)
        canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=-0.4)

        canvas.figure.patch.set_facecolor('black')
        ax.set_facecolor('black')

        self.ASDayChart.addWidget(canvas)
        canvas.draw()
    
    # Gets the total active time in a day
    def calculateTotalActiveTime(self, sessions):
        totalActiveTime = sum((end - start).seconds for start, end in sessions)
        return totalActiveTime

    # Formats the total active time to look better
    def formatActiveTime(self, totalSeconds):
        hours, remainder = divmod(totalSeconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"
        
    # Chooses a random key and handles the random key section
    def randomizeKey(self):
        self.lifetimeLongestDurations = getLifetimeLongestDurations(self.conn)
        excludedKeys = {'mouseleft', 'mouseright', 'mousemiddle', 'scrollup', 'scrolldown'}
        allKeys = [key for key in self.lifetimeLongestDurations.keys() if key not in excludedKeys]
        if allKeys:
            randomKey = random.choice(allKeys)
            formattedKey = self.formatKeyName(randomKey)
            self.RandomKey.setText(formattedKey)
            shiftedKey = self.getShiftedKey(randomKey)
            self.RandomKeyShifted.setText(shiftedKey)
            self.updateRandomKeyStats(randomKey)

    # Makes key names look better
    def formatKeyName(self, key):
        if key.isalpha() and len(key) == 1:
            return key
        elif key == 'capslock':
            return 'Caps Lock'
        elif key in {'left', 'up', 'down', 'right'}:
            return key.capitalize() + ' Arrow'
        else:
            return key.capitalize()

    # Gets the random key and returns it when it is pressed while holding shift
    def getShiftedKey(self, key):
        shiftMap = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%', '6': '^',
            '7': '&', '8': '*', '9': '(', '0': ')', '-': '_', '=': '+',
            '[': '{', ']': '}', '\\': '|', ';': ':', "'": '"', ',': '<',
            '.': '>', '/': '?'
        }

        if key.isalpha() and len(key) == 1:
            return key.upper()
        elif key in shiftMap:
            return shiftMap[key]
        else:
            return 'N/A'

    # Updates the information of the random key
    def updateRandomKeyStats(self, key):
        totalCounts = getTotalCounts(self.conn)
        longestDurations = getLifetimeLongestDurations(self.conn)
        keyCount = totalCounts.get(key, 0)
        longestDuration = longestDurations.get(key, 0)

        excludedKeys = {'mouseleft', 'mouseright', 'mousemiddle', 'scrollup', 'scrolldown', 'mouseposition', 'mousedistance'}
        filteredTotalCounts = {k: v for k, v in totalCounts.items() if k not in excludedKeys}

        totalInputs = getTotalKeyInputs(filteredTotalCounts)
        percentOfTotal = (keyCount / totalInputs) * 100 if totalInputs > 0 else 0

        # Calculate the rank of the key
        sortedKeys = sorted(filteredTotalCounts.items(), key=lambda item: item[1], reverse=True)
        keyRank = next((index + 1 for index, (k, count) in enumerate(sortedKeys) if k == key), None)

        # Sets the labels
        self.TotalPresses.setText(f"{keyCount}")
        self.LongestTimeHeld.setText(f"{longestDuration:.2f} seconds")
        self.PercentOfTotal.setText(f"{percentOfTotal:.2f}%")
        self.RandomKeyRank.setText(f"#{keyRank}")
        
    # Handles the key heatmap colors
    def getColorFromScheme(self, scheme, intensity):
        color = QColor()
        if scheme == 'greenToRedScheme':
            color.setHsvF(0.33 - 0.33 * intensity, 1, 1)  # Green to Red
        elif scheme == 'greenScheme':
            hue = 0.40 - 0.10 * intensity  # Adjust hue for the desired range
            saturation = 1  # Adjust saturation for the desired range
            value = 0.3 + 0.7 * intensity  # Adjust value for the desired range
            color.setHsvF(hue, saturation, value)
        return color
        
    # Updates the key heatmap
    def updateKeyHeatmap(self, totalCounts):
        keyWidgetMap = {
            'a': self.AKey, 'b': self.BKey, 'c': self.CKey, 'd': self.DKey,
            'e': self.EKey, 'f': self.FKey, 'g': self.GKey, 'h': self.HKey,
            'i': self.IKey, 'j': self.JKey, 'k': self.KKey, 'l': self.LKey,
            'm': self.MKey, 'n': self.NKey, 'o': self.OKey, 'p': self.PKey,
            'q': self.QKey, 'r': self.RKey, 's': self.SKey, 't': self.TKey,
            'u': self.UKey, 'v': self.VKey, 'w': self.WKey, 'x': self.XKey,
            'y': self.YKey, 'z': self.ZKey, '1': self.OneKey, '2': self.TwoKey,
            '3': self.ThreeKey, '4': self.FourKey, '5': self.FiveKey, '6': self.SixKey,
            '7': self.SevenKey, '8': self.EightKey, '9': self.NineKey, '0': self.ZeroKey,
            'enter': self.EnterKey, 'space': self.SpaceKey, 'backspace': self.BackspaceKey,
            'tab': self.TabKey, 'capslock': self.CapslockKey, 'lshift': self.LShiftKey,
            'rshift': self.RShiftKey, 'ctrl': self.CtrlKey, 'alt': self.AltKey, 'win': self.WinKey,
            'left': self.LeftArrowKey, 'up': self.UpArrowKey, 'right': self.RightArrowKey,
            'down': self.DownArrowKey, 'esc': self.EscKey, ';': self.SemicolonKey,
            '=': self.EqualsKey, ',': self.CommaKey, '-': self.MinusKey,
            '.': self.PeriodKey, '/': self.ForwardslashKey, '\\': self.BackslashKey,
            "'": self.ApostropheKey, '[': self.LBracketKey, ']': self.RBracketKey
        }

        keyCounts = {}
        for key in keyWidgetMap.keys():
            if key in ['lshift', 'rshift']:
                keyCounts[key] = totalCounts.get('shift', 0)
            else:
                keyCounts[key] = totalCounts.get(key, 0)

        # Apply logarithmic scale to key counts
        logKeyCounts = {key: math.log(count + 1) for key, count in keyCounts.items()}

        minLogCount = min(logKeyCounts.values())
        maxLogCount = max(logKeyCounts.values())

        for key, widget in keyWidgetMap.items():
            logCount = logKeyCounts[key]
            if maxLogCount > minLogCount:
                intensity = (logCount - minLogCount) / (maxLogCount - minLogCount)
            else:
                intensity = 0

            # Calculate the color based on intensity
            color = self.getColorFromScheme(self.colorScheme, intensity)

            # Convert QColor to RGBA with opacity 0.85
            r, g, b, _ = color.getRgb()
            rgbaColor = f'rgba({r}, {g}, {b}, 0.85)'

            # Preserve the existing styles and add background-color
            newStyle = f'background-color: {rgbaColor};'
            widget.setStyleSheet(f'{newStyle}')

    # Changes the color scheme of the keyboard heatmap when the button is pressed
    def toggleColorScheme(self, checked):
        stylesheet = self.styleSheet()
        if checked:
            self.colorScheme = 'greenToRedScheme'
            stylesheet = stylesheet.replace('background-color: qlineargradient(spread:pad, x1:0, y1:0.477682, x2:1, y2:0.472, stop:0 rgba(2, 67, 28, 255), stop:0.366086 rgba(1, 102, 0, 255), stop:0.692552 rgba(25, 157, 5, 255), stop:1 rgba(39, 219, 4, 255));', 'background-color: qlineargradient(spread:pad, x1:0.028, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 21, 255), stop:0.361111 rgba(249, 255, 0, 255), stop:0.638889 rgba(255, 255, 0, 255), stop:1 rgba(255, 0, 0, 255));')
        else:
            self.colorScheme = 'greenScheme'
            stylesheet = stylesheet.replace('background-color: qlineargradient(spread:pad, x1:0.028, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 21, 255), stop:0.361111 rgba(249, 255, 0, 255), stop:0.638889 rgba(255, 255, 0, 255), stop:1 rgba(255, 0, 0, 255));', 'background-color: qlineargradient(spread:pad, x1:0, y1:0.477682, x2:1, y2:0.472, stop:0 rgba(2, 67, 28, 255), stop:0.366086 rgba(1, 102, 0, 255), stop:0.692552 rgba(25, 157, 5, 255), stop:1 rgba(39, 219, 4, 255));')
        self.HeatLegend.setStyleSheet(stylesheet)
        self.updateKeyHeatmap(getTotalCounts(self.conn))

    # Changes the border radius on the keyboard heatmap when the button is pressed
    def toggleRoundedBorders(self, checked):
        stylesheet = self.HeatmapContainer.styleSheet()
        if checked:
            stylesheet = stylesheet.replace('border-radius: 0px;', 'border-radius: 5px;')
        else:
            stylesheet = stylesheet.replace('border-radius: 5px;', 'border-radius: 0px;')
        self.HeatmapContainer.setStyleSheet(stylesheet)

    # Toggles letter visibility on the keyboard heatmap when the button is pressed
    def toggleKeyTextVisibility(self, checked):
        stylesheet = self.HeatmapContainer.styleSheet()
        if checked:
            stylesheet = stylesheet.replace('color: transparent;', 'color: white;')
        else:
            stylesheet = stylesheet.replace('color: white;', 'color: transparent;')
        self.HeatmapContainer.setStyleSheet(stylesheet)

    # Toggles a darker overlay when the button is pressed
    def toggleHighContrast(self, checked):
        if checked:
            self.overlay.setWindowOpacity(1.2)
        else:
            self.overlay.setWindowOpacity(0.6)
            
    # Toggles animation when the button is pressed
    def toggleAnimation(self, checked):
        self.overlay.setAnimationEnabled(checked)
        
    # Toggles green (left click) dots on the overlay when the button is pressed
    def toggleGreenDots(self, checked):
        self.overlay.showGreenDots = checked

    # Toggles red (right click) dots on the overlay when the button is pressed
    def toggleRedDots(self, checked):
        self.overlay.showRedDots = checked

    # Toggles yellow (middle click) dots on the overlay when the button is pressed
    def toggleYellowDots(self, checked):
        self.overlay.showYellowDots = checked
        
    # Toggles a darker overlay when the button is pressed (mouse draw overlay)
    def toggleHighContrast2(self, checked):
        if checked:
            self.drawOverlay.setWindowOpacity(1.2)
        else:
            self.drawOverlay.setWindowOpacity(0.6)

    # Toggles animation when the button is pressed (mouse draw overlay)
    def toggleAnimation2(self, checked):
        self.drawOverlay.setAnimationEnabled(checked)

    # Toggles the size of the lines in the mouse draw overlay when the button is pressed
    def toggleLineWeight(self, checked):
        if checked:
            self.drawOverlay.setLineWeight(1)
        else:
            self.drawOverlay.setLineWeight(5)
            
    # Toggles the amount of lines in the mouse draw overlay when the button is pressed
    def toggleAmountOfHistory(self, checked):
        if checked:
            self.drawOverlay.setHistoryAmount(10000)
        else:
            self.drawOverlay.setHistoryAmount(2000)

    # Shows the mouse click overlay
    def showOverlay(self):
        self.overlay.showOverlay()
        
    # Shows the mouse draw overlay
    def showDrawOverlay(self):
        self.drawOverlay.showOverlay()
        
    # Handles app page changes by changing the page and highlighted button
    def changePage(self, index):
        self.Pages.setCurrentIndex(index)
        self.highlightButton(index)
        
    # Handles home page information page changes
    def showExplanationPage(self, index):
        self.HomePageExplanationsContainer.setCurrentIndex(index)

    # Highlights the selected page's respective button
    def highlightButton(self, index):
        for i, button in enumerate(self.buttons):
            if i == index:
                button.setStyleSheet(button.styleSheet().replace("background-color: transparent;", "background-color: #1F1F1F;"))
                button.setStyleSheet(button.styleSheet().replace("background-color: #1A1A1A;", "background-color: #1F1F1A;"))
            else:
                button.setStyleSheet(button.styleSheet().replace("background-color: #1F1F1F;", "background-color: transparent;"))
                button.setStyleSheet(button.styleSheet().replace("background-color: #1F1F1A;", "background-color: #1A1A1A;"))

    # Opens a help link for the application
    def openHelpLink(self):
        QDesktopServices.openUrl(QUrl("https://github.com/LukeBarcenas/MyPCStats?tab=readme-ov-file#help"))

    # Handles highlighting and changing the current index of the app's pages
    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress and source is self.HomeMouseButton:
            self.Pages.setCurrentIndex(1)
            self.highlightButton(1)
            return True
        elif event.type() == QEvent.MouseButtonPress and source is self.HomeKeyboardButton:
            self.Pages.setCurrentIndex(2)
            self.highlightButton(2)
            return True
        elif event.type() == QEvent.MouseButtonPress and source is self.HomeAnalyticsButton:
            self.Pages.setCurrentIndex(3)
            self.highlightButton(3)
            return True
        if event.type() == QEvent.MouseButtonPress and source == self.HelpHPText2:
            if event.button() == Qt.LeftButton:
                self.openAppFolder()
                return True

        return super(MainWindow, self).eventFilter(source, event)
    
    # Handler for manual refreshes
    def handleManualRefresh(self):
        self.updateAllPlots()
        self.ManualRefreshButton.setEnabled(False)
        self.manualRefreshTimer.start(5000)  # Disable the button for 5 seconds

    # Updates a ton of mouse stats
    def updateMouseCounts(self, totalCounts, longestDurations):
        # Updates total clicks
        totalClicks = sum(totalCounts.get(name, 0) for name in ['mouseleft', 'mouseright', 'mousemiddle'])
        self.TotalClicks.setText(f"{totalClicks}")
        
        # Updates total left clicks
        totalLeftClicks = totalCounts.get('mouseleft', 0)
        self.LCQS.setText(f"{totalLeftClicks}")
        
        # Updates total right clicks
        totalRightClicks = totalCounts.get('mouseright', 0)
        self.RCQS.setText(f"{totalRightClicks}")
        
        # Updates total middle clicks
        totalMiddleClicks = totalCounts.get('mousemiddle', 0)
        self.MMiddleQS.setText(f"{totalMiddleClicks}")
        
        # Updates total scrolls down
        totalScrollsDown = totalCounts.get('scrolldown', 0)
        self.SDQS.setText(f"{totalScrollsDown}")
        
        # Updates total scrolls up
        totalScrollsUp = totalCounts.get('scrollup', 0)
        self.SUQS.setText(f"{totalScrollsUp}")
        
        # Updates total scrolls
        totalScrolls = totalScrollsDown + totalScrollsUp
        self.ScrollTotal.setText(f"{totalScrolls} times.")
        self.ScrollPixels.setText(f"{totalScrolls * 80} Pixels")
        self.ScrollMiles.setText(f"{totalScrolls * 0.000621371:.3f} Miles")
        
        # Updates total mouse movements
        totalMoves = totalCounts.get('mouseposition', 0)
        self.MMoveQS.setText(f"{totalMoves}")

        # Updates total clicks in the last 24 hours
        clicksToday = getMouseClicksLast24Hours(self.conn)
        self.ClicksToday.setText(f"{clicksToday}")
        
        # Updates longest clicks
        longestClick = getLongestMouseClick(longestDurations)
        self.LongestClick.setText(f" {longestClick} Seconds ")
        
        # Updates most used mouse button
        favoriteMB = getMostUsedMouseButton(totalCounts)
        self.FavoriteMouseButton.setText(f"{favoriteMB}")
        
        # Updates mouse distances
        mouseDistanceMeters = totalCounts.get('mousedistance', 0)
        mouseDistances = (
            f"{mouseDistanceMeters * 3779.53:.0f}<br>"
            f"{mouseDistanceMeters * 3.28084:.2f}<br>"
            f"{mouseDistanceMeters * 0.000621371:.3f}<br>"
            f"{mouseDistanceMeters:.2f}<br>"
            f"{mouseDistanceMeters * 0.001:.2f}<br>"
            f"{mouseDistanceMeters * 1.057e-16:.7f}<br>"
        )
        self.MouseDistanceQS.setText(mouseDistances)
        
    # Updates a ton of keyboard stats
    def updateKeyboardCounts(self, totalCounts):
        # Updates the total inputs in the last 24 hours
        inputsToday = getKeyInputsLast24Hours(self.conn)
        self.InputsToday.setText(f"{inputsToday}")
        
        # Updates the most used special key
        favoriteSpecialKey = getFavoriteSpecialKey(totalCounts)
        self.FavoriteSpecialKey.setText(f"{favoriteSpecialKey}")
        
        # Updates the least used key
        leastUsedKey = getLeastUsedKey(totalCounts)
        self.LeastUsedKey.setText(f"{leastUsedKey}")

        # Updates the total keyboard inputs
        totalInputs = getTotalKeyInputs(totalCounts)
        self.TotalInputs.setText(f"{totalInputs}")
                
        # Updates the 5 most used letters
        top5Letters = getTop5Letters(totalCounts)
        for i, (letter, count) in enumerate(top5Letters, start=1):
            getattr(self, f"KeyRank{i}").setText(f"{letter}")
            getattr(self, f"KeyRank{i}Count").setText(f"{count}")
            
        # Updates the 5 least used letters
        bottom5Letters = getBottom5Letters(totalCounts)
        for i, (letter, count) in enumerate(bottom5Letters, start=1):
            getattr(self, f"BottomKeyRank{i}").setText(f"{letter}")
            getattr(self, f"BottomKeyRank{i}Count").setText(f"{count}")

        # Updates the total number of number inputs and their real total
        numberKeyInputs, realNumberKeyTotal = getNumberKeyInputs(totalCounts)
        self.NumberKeyInputs.setText(f"{numberKeyInputs}")
        self.RealNumberKeyTotal.setText(f"{realNumberKeyTotal}")
        
        # Updates the key heatmap
        self.updateKeyHeatmap(totalCounts)

    # Calls the functions that use total counts
    def updateAllTotals(self):
        totalCounts = getTotalCounts(self.conn)
        longestDurations = getLifetimeLongestDurations(self.conn)
        self.updateMouseCounts(totalCounts, longestDurations)
        self.updatePieChart(totalCounts)
        self.updateKeyboardCounts(totalCounts)
        self.updateKBPieChart(totalCounts)
        
    # Calls the functions that need to update plots more frequently
    def updateLivePlots(self):
        self.updateLivePlot()
        self.updateLiveKeyboardPlot()
        
    # Updates the active session information
    def updateActiveInfo(self):
        self.updateActiveSessionInfo()

    # Calls all of the functions that update plots
    def updateAllPlots(self):
        self.updateLivePlot()
        self.updateDayPlot()
        self.updateWeekPlot()
        self.updateMonthPlot()
        self.updateYearPlot()
        self.updateLiveKeyboardPlot()
        self.updateDayKeyboardPlot()
        self.updateWeekKeyboardPlot()
        self.updateMonthKeyboardPlot()
        self.updateYearKeyboardPlot()
        self.updateAvgDayInputsPlot()
        self.updateActiveSessionInfo()
        
    # Calls all of the functions that need to update plots less frequently
    def updateOtherPlots(self):
        self.updateDayPlot()
        self.updateWeekPlot()
        self.updateMonthPlot()
        self.updateYearPlot()
        self.updateDayKeyboardPlot()
        self.updateWeekKeyboardPlot()
        self.updateMonthKeyboardPlot()
        self.updateYearKeyboardPlot()
        self.updateAvgDayInputsPlot()

    # Updates a plot that shows mouse activity in the last hour
    def updateLivePlot(self):
        now = datetime.now()
        startTime = now - timedelta(hours=1)
        data = getMouseClicksBetweenTimes(self.conn, startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))
        
        self.liveCanvas.axes.cla()
        
        if data:
            timestamps, counts = zip(*data)
            dates = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamps]
            
            self.liveCanvas.axes.plot(dates, counts, label="Mouse Clicks", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.liveCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.liveCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                    transform=self.liveCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.liveCanvas.axes.set_xlim(startTime, now)
        
        self.liveCanvas.axes.set_xlabel("Time", color='#F0F0F0', fontsize=12, labelpad=8)
        self.liveCanvas.axes.set_ylabel("Number of Clicks", color='#F0F0F0', fontsize=12, labelpad=8)
        self.liveCanvas.axes.set_title("Live Mouse Clicks", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.liveCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
        self.liveCanvas.axes.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        self.liveCanvas.axes.tick_params(axis='x', colors='white')
        self.liveCanvas.axes.tick_params(axis='y', colors='white')
        
        self.liveCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.liveCanvas.axes.spines['top'].set_color('#263556')
        self.liveCanvas.axes.spines['right'].set_color('#263556')
        self.liveCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.liveCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.liveCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.liveCanvas.draw()

    # Updates a plot that shows mouse activity in the last 24 hours
    def updateDayPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=1)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d %H', timestamp) as hour, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
            GROUP BY hour
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.dayCanvas.axes.cla()
        
        if data:
            hours, counts = zip(*data)
            dates = [datetime.strptime(hour, '%Y-%m-%d %H') for hour in hours]
            
            self.dayCanvas.axes.plot(dates, counts, label="Mouse Clicks", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.dayCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.dayCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                    transform=self.dayCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.dayCanvas.axes.set_xlim(startTime, now)
        
        self.dayCanvas.axes.set_xlabel("Time", color='#F0F0F0', fontsize=12, labelpad=8)
        self.dayCanvas.axes.set_ylabel("Number of Clicks", color='#F0F0F0', fontsize=12, labelpad=8)
        self.dayCanvas.axes.set_title("Mouse Clicks in the Last 24 Hours", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.dayCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M%p'))
        self.dayCanvas.axes.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        self.dayCanvas.axes.tick_params(axis='x', colors='white')
        self.dayCanvas.axes.tick_params(axis='y', colors='white')
        
        self.dayCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.dayCanvas.axes.spines['top'].set_color('#263556')
        self.dayCanvas.axes.spines['right'].set_color('#263556')
        self.dayCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.dayCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.dayCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.dayCanvas.draw()

    # Updates a plot that shows mouse activity in the last 7 days
    def updateWeekPlot(self):
        now = datetime.now()
        startTime = now - timedelta(weeks=1)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
            GROUP BY day
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.weekCanvas.axes.cla()
        
        if data:
            days, counts = zip(*data)
            dates = [datetime.strptime(day, '%Y-%m-%d') for day in days]
            
            self.weekCanvas.axes.plot(dates, counts, label="Mouse Clicks", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.weekCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.weekCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                    transform=self.weekCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.weekCanvas.axes.set_xlim(startTime, now)
        
        self.weekCanvas.axes.set_xlabel("Date", color='#F0F0F0', fontsize=12, labelpad=8)
        self.weekCanvas.axes.set_ylabel("Number of Clicks", color='#F0F0F0', fontsize=12, labelpad=8)
        self.weekCanvas.axes.set_title("Mouse Clicks in the Last Week", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.weekCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.weekCanvas.axes.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        self.weekCanvas.axes.tick_params(axis='x', colors='white')
        self.weekCanvas.axes.tick_params(axis='y', colors='white')
        
        self.weekCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.weekCanvas.axes.spines['top'].set_color('#263556')
        self.weekCanvas.axes.spines['right'].set_color('#263556')
        self.weekCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.weekCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.weekCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.weekCanvas.draw()

    # Updates a plot that shows mouse activity in the last 30 days
    def updateMonthPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=30)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
            GROUP BY day
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.monthCanvas.axes.cla()
        
        if data:
            days, counts = zip(*data)
            dates = [datetime.strptime(day, '%Y-%m-%d') for day in days]
            
            self.monthCanvas.axes.plot(dates, counts, label="Mouse Clicks", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.monthCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.monthCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                    transform=self.monthCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.monthCanvas.axes.set_xlim(startTime, now)
        
        self.monthCanvas.axes.set_xlabel("Date", color='#F0F0F0', fontsize=12, labelpad=8)
        self.monthCanvas.axes.set_ylabel("Number of Clicks", color='#F0F0F0', fontsize=12, labelpad=8)
        self.monthCanvas.axes.set_title("Mouse Clicks in the Last Month", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.monthCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.monthCanvas.axes.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        self.monthCanvas.axes.tick_params(axis='x', colors='white')
        self.monthCanvas.axes.tick_params(axis='y', colors='white')
        
        self.monthCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.monthCanvas.axes.spines['top'].set_color('#263556')
        self.monthCanvas.axes.spines['right'].set_color('#263556')
        self.monthCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.monthCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.monthCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.monthCanvas.draw()

    # Updates a plot that shows mouse activity in the last 12 months
    def updateYearPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=365)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m', timestamp) as month, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND button IN ('mouseright', 'mouseleft', 'mousemiddle')
            GROUP BY month
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.yearCanvas.axes.cla()
        
        if data:
            months, counts = zip(*data)
            dates = [datetime.strptime(month, '%Y-%m') for month in months]
            
            self.yearCanvas.axes.plot(dates, counts, label="Mouse Clicks", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.yearCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.yearCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                    transform=self.yearCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.yearCanvas.axes.set_xlim(startTime, now)
        
        self.yearCanvas.axes.set_xlabel("Month", color='#F0F0F0', fontsize=12, labelpad=8)
        self.yearCanvas.axes.set_ylabel("Number of Clicks", color='#F0F0F0', fontsize=12, labelpad=8)
        self.yearCanvas.axes.set_title("Mouse Clicks in the Last Year", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.yearCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        self.yearCanvas.axes.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        self.yearCanvas.axes.tick_params(axis='x', colors='white')
        self.yearCanvas.axes.tick_params(axis='y', colors='white')
        
        self.yearCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.yearCanvas.axes.spines['top'].set_color('#263556')
        self.yearCanvas.axes.spines['right'].set_color('#263556')
        self.yearCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.yearCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.yearCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.yearCanvas.draw()
            
    # Updates a plot that shows keyboard activity in the last hour
    def updateLiveKeyboardPlot(self):
        now = datetime.now()
        startTime = now - timedelta(hours=1)
        data = getKeyboardInputsBetweenTimes(self.conn, startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))
        
        self.keyboardLiveCanvas.axes.cla()

        if data:
            timestamps, counts = zip(*data)
            dates = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamps]
            
            self.keyboardLiveCanvas.axes.plot(dates, counts, label="Keyboard Inputs", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.keyboardLiveCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.keyboardLiveCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.keyboardLiveCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.keyboardLiveCanvas.axes.set_xlim(startTime, now)
        
        self.keyboardLiveCanvas.axes.set_xlabel("Time", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardLiveCanvas.axes.set_ylabel("Number of Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardLiveCanvas.axes.set_title("Live Keyboard Inputs", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        
        self.keyboardLiveCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
        self.keyboardLiveCanvas.axes.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        
        self.keyboardLiveCanvas.axes.tick_params(axis='x', colors='white')
        self.keyboardLiveCanvas.axes.tick_params(axis='y', colors='white')
        
        self.keyboardLiveCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.keyboardLiveCanvas.axes.spines['top'].set_color('#263556')
        self.keyboardLiveCanvas.axes.spines['right'].set_color('#263556')
        self.keyboardLiveCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.keyboardLiveCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.keyboardLiveCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.keyboardLiveCanvas.draw()

    # Updates a plot that shows keyboard activity in the last 24 hours
    def updateDayKeyboardPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=1)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d %H', timestamp) as hour, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND eventTypeID = 1
            GROUP BY hour
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.keyboardDayCanvas.axes.cla()
        
        if data:
            hours, counts = zip(*data)
            dates = [datetime.strptime(hour, '%Y-%m-%d %H') for hour in hours]
            
            self.keyboardDayCanvas.axes.plot(dates, counts, label="Keyboard Inputs", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.keyboardDayCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.keyboardDayCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.keyboardDayCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.keyboardDayCanvas.axes.set_xlim(startTime, now)
        
        self.keyboardDayCanvas.axes.set_xlabel("Time", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardDayCanvas.axes.set_ylabel("Number of Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardDayCanvas.axes.set_title("Keyboard Inputs in the Last 24 Hours", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        
        self.keyboardDayCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M%p'))
        self.keyboardDayCanvas.axes.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        
        self.keyboardDayCanvas.axes.tick_params(axis='x', colors='white')
        self.keyboardDayCanvas.axes.tick_params(axis='y', colors='white')
        
        self.keyboardDayCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.keyboardDayCanvas.axes.spines['top'].set_color('#263556')
        self.keyboardDayCanvas.axes.spines['right'].set_color('#263556')
        self.keyboardDayCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.keyboardDayCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.keyboardDayCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.keyboardDayCanvas.draw()

    # Updates a plot that shows keyboard activity in the last 7 days
    def updateWeekKeyboardPlot(self):
        now = datetime.now()
        startTime = now - timedelta(weeks=1)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND eventTypeID = 1
            GROUP BY day
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.keyboardWeekCanvas.axes.cla()
        
        if data:
            days, counts = zip(*data)
            dates = [datetime.strptime(day, '%Y-%m-%d') for day in days]
            
            self.keyboardWeekCanvas.axes.plot(dates, counts, label="Keyboard Inputs", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.keyboardWeekCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.keyboardWeekCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.keyboardWeekCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.keyboardWeekCanvas.axes.set_xlim(startTime, now)
        
        self.keyboardWeekCanvas.axes.set_xlabel("Date", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardWeekCanvas.axes.set_ylabel("Number of Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardWeekCanvas.axes.set_title("Keyboard Inputs in the Last Week", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.keyboardWeekCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.keyboardWeekCanvas.axes.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        self.keyboardWeekCanvas.axes.tick_params(axis='x', colors='white')
        self.keyboardWeekCanvas.axes.tick_params(axis='y', colors='white')
        
        self.keyboardWeekCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.keyboardWeekCanvas.axes.spines['top'].set_color('#263556')
        self.keyboardWeekCanvas.axes.spines['right'].set_color('#263556')
        self.keyboardWeekCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.keyboardWeekCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.keyboardWeekCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.keyboardWeekCanvas.draw()

    # Updates a plot that shows keyboard activity in the last 30 days
    def updateMonthKeyboardPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=30)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND eventTypeID = 1
            GROUP BY day
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.keyboardMonthCanvas.axes.cla()
        
        if data:
            days, counts = zip(*data)
            dates = [datetime.strptime(day, '%Y-%m-%d') for day in days]
            
            self.keyboardMonthCanvas.axes.plot(dates, counts, label="Keyboard Inputs", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.keyboardMonthCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.keyboardMonthCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.keyboardMonthCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.keyboardMonthCanvas.axes.set_xlim(startTime, now)
        
        self.keyboardMonthCanvas.axes.set_xlabel("Date", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardMonthCanvas.axes.set_ylabel("Number of Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardMonthCanvas.axes.set_title("Keyboard Inputs in the Last Month", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.keyboardMonthCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.keyboardMonthCanvas.axes.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        self.keyboardMonthCanvas.axes.tick_params(axis='x', colors='white')
        self.keyboardMonthCanvas.axes.tick_params(axis='y', colors='white')
        
        self.keyboardMonthCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.keyboardMonthCanvas.axes.spines['top'].set_color('#263556')
        self.keyboardMonthCanvas.axes.spines['right'].set_color('#263556')
        self.keyboardMonthCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.keyboardMonthCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.keyboardMonthCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.keyboardMonthCanvas.draw()

    # Updates a plot that shows keyboard activity in the last 12 months
    def updateYearKeyboardPlot(self):
        now = datetime.now()
        startTime = now - timedelta(days=365)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m', timestamp) as month, COUNT(*)
            FROM events
            WHERE timestamp BETWEEN ? AND ?
            AND eventTypeID = 1
            GROUP BY month
        ''', (startTime.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
        
        data = cursor.fetchall()
        self.keyboardYearCanvas.axes.cla()
        
        if data:
            months, counts = zip(*data)
            dates = [datetime.strptime(month, '%Y-%m') for month in months]
            
            self.keyboardYearCanvas.axes.plot(dates, counts, label="Keyboard Inputs", color='#0FFF7D', marker='o', markersize=6, markevery=[-1])
            self.keyboardYearCanvas.axes.legend(facecolor='#F0F0F0', edgecolor='#171C30')
        else:
            self.keyboardYearCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.keyboardYearCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
            self.keyboardYearCanvas.axes.set_xlim(startTime, now)
        
        self.keyboardYearCanvas.axes.set_xlabel("Month", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardYearCanvas.axes.set_ylabel("Number of Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.keyboardYearCanvas.axes.set_title("Keyboard Inputs in the Last Year", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.keyboardYearCanvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        self.keyboardYearCanvas.axes.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        self.keyboardYearCanvas.axes.tick_params(axis='x', colors='white')
        self.keyboardYearCanvas.axes.tick_params(axis='y', colors='white')
        
        self.keyboardYearCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.keyboardYearCanvas.axes.spines['top'].set_color('#263556')
        self.keyboardYearCanvas.axes.spines['right'].set_color('#263556')
        self.keyboardYearCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.keyboardYearCanvas.axes.grid(color='#354B6A', linestyle='-', linewidth=0.5)
        self.keyboardYearCanvas.figure.subplots_adjust(top=0.88, bottom=0.15)
        
        self.keyboardYearCanvas.draw()

    # Updates a pie chart for mouse scrolls up vs. mouse scrolls down
    def updatePieChart(self, totalCounts):
        scrollUpTotal = totalCounts.get('scrollup', 0)
        scrollDownTotal = totalCounts.get('scrolldown', 0)
        
        totalScrolls = scrollUpTotal + scrollDownTotal
        
        if totalScrolls == 0:
            labels = ['No Scrolls']
            sizes = [100]
            colors = ['#404040']
            explode = (0,)
            
            self.pieCanvas.axes.cla()
            self.pieCanvas.axes.pie(sizes, explode=explode, labels=labels, colors=colors,
                                    shadow=True, startangle=140, textprops={'color':"white", 'fontsize': 15, 'fontweight': 'bold'})
            self.pieCanvas.axes.set_title("Scroll Up vs. Scroll Down", color='white', fontsize=32, fontweight='bold')
        else:
            labels = 'Scroll Up', 'Scroll Down'
            sizes = [scrollUpTotal, scrollDownTotal]
            colors = ['#0FFF7D', '#0F7DFF']
            explode = (0.1, 0)

            def format_autopct(pct, allvalues):
                absolute = int(pct/100.*sum(allvalues))
                return f"{absolute:,}\n({pct:.1f}%)"

            self.pieCanvas.axes.cla()
            self.pieCanvas.axes.pie(sizes, explode=explode, labels=labels, colors=colors, autopct=lambda pct: format_autopct(pct, sizes),
                                    shadow=True, startangle=140, textprops={'color':"white", 'fontsize': 15, 'fontweight': 'bold'})
            self.pieCanvas.axes.set_title("Scroll Up vs. Scroll Down", color='white', fontsize=32, fontweight='bold')
        
        self.pieCanvas.figure.subplots_adjust(top=0.86, bottom=0.02)
        self.pieCanvas.draw()
        
    # Updates a pie chart for spacebar inputs vs. backspace inputs
    def updateKBPieChart(self, totalCounts):
        spaceCount = totalCounts.get('space', 0)
        backspaceCount = totalCounts.get('backspace', 0)

        totalKeyPresses = spaceCount + backspaceCount

        if totalKeyPresses == 0:
            labels = ['No Inputs']
            sizes = [100]
            colors = ['#404040']
            explode = (0,)
            
            # Draw the "No Key Presses" pie chart
            self.kbPieCanvas.axes.cla()
            self.kbPieCanvas.axes.pie(sizes, explode=explode, labels=labels, colors=colors,
                                    shadow=True, startangle=140, textprops={'color': "white", 'fontsize': 15, 'fontweight': 'bold'})
            self.kbPieCanvas.axes.set_title("Space vs. Backspace", color='white', fontsize=32, fontweight='bold')
        else:
            labels = 'Space', 'Backspace'
            sizes = [spaceCount, backspaceCount]
            colors = ['#FF7D0F', '#7D0FFF']
            explode = (0.1, 0)

            def format_autopct(pct, allvalues):
                absolute = int(pct / 100. * sum(allvalues))
                return f"{absolute:,}\n({pct:.1f}%)"

            self.kbPieCanvas.axes.cla()
            self.kbPieCanvas.axes.pie(sizes, explode=explode, labels=labels, colors=colors, autopct=lambda pct: format_autopct(pct, sizes),
                                    shadow=True, startangle=140, textprops={'color': "white", 'fontsize': 15, 'fontweight': 'bold'})
            self.kbPieCanvas.axes.set_title("Space vs. Backspace", color='white', fontsize=32, fontweight='bold')
        
        self.kbPieCanvas.figure.subplots_adjust(top=0.86, bottom=0.02)
        self.kbPieCanvas.draw()
        
    # Updates a chart that shows average input activity every hour of the day
    def updateAvgDayInputsPlot(self):
        hourlyAverages = getAverageInputsPerHour(self.conn)

        self.avgDayInputsCanvas.axes.cla()
        
        # Check if all averages are zero
        if all(average == 0 for hour, average in hourlyAverages):
            self.MostActiveTime.setText("No data available for average activity.")
            self.avgDayInputsCanvas.axes.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center',
                                            transform=self.avgDayInputsCanvas.axes.transAxes, color='#F0F0F0', fontsize=15, fontweight='bold')
        else:
            hours, averages = zip(*hourlyAverages)
            mostActiveHour = max(hourlyAverages, key=lambda x: x[1])[0]

            def formatHour(hour):
                if hour == 0:
                    return "12AM"
                elif hour < 12:
                    return f"{hour}AM"
                elif hour == 12:
                    return "12PM"
                else:
                    return f"{hour-12}PM"

            formattedHour = formatHour(mostActiveHour)
            self.MostActiveTime.setText(f"On average, you are most active around {formattedHour}")

            self.avgDayInputsCanvas.axes.bar(hours, averages, color='#0FFF7D', width=0.75)
            self.avgDayInputsCanvas.axes.set_xticks(hours)
            self.avgDayInputsCanvas.axes.set_xticklabels([formatHour(hour) for hour in hours], rotation=45)
        
        self.avgDayInputsCanvas.axes.set_xlabel("Hour of Day", color='#F0F0F0', fontsize=12, labelpad=8)
        self.avgDayInputsCanvas.axes.set_ylabel("Average Inputs", color='#F0F0F0', fontsize=12, labelpad=8)
        self.avgDayInputsCanvas.axes.set_title("Average Input Usage Per Hour", color='#F0F0F0', fontsize=15, fontweight='bold', pad=12)
        self.avgDayInputsCanvas.axes.tick_params(axis='x', colors='white')
        self.avgDayInputsCanvas.axes.tick_params(axis='y', colors='white')
        
        self.avgDayInputsCanvas.axes.spines['bottom'].set_color('#F0F0F0')
        self.avgDayInputsCanvas.axes.spines['top'].set_color('#263556')
        self.avgDayInputsCanvas.axes.spines['right'].set_color('#263556')
        self.avgDayInputsCanvas.axes.spines['left'].set_color('#F0F0F0')
        
        self.avgDayInputsCanvas.figure.subplots_adjust(top=0.85, bottom=0.25)
        
        self.avgDayInputsCanvas.draw()

    # Handles updating the time of a current active session and the last active session
    def updateActiveSessionInfo(self):
        cursor = self.conn.cursor()
        
        # Get the latest keyboard or mouse event
        cursor.execute('''
            SELECT timestamp
            FROM events
            WHERE eventTypeID IN (1, 3)
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        latestEvent = cursor.fetchone()

        # Calculate the time difference from now to the latest event
        if latestEvent:
            latestEventTime = datetime.strptime(latestEvent[0], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            timeDifference = now - latestEventTime

            # Finds the start time of the current active session
            if timeDifference <= timedelta(minutes=15):
                sessionStartTime = self.findSessionStartTime(cursor, latestEventTime)
                sessionDuration = now - sessionStartTime
                minsAgo = int(sessionDuration.total_seconds() // 60)
                self.CASText.setText(f"Your current active session started <b>{minsAgo} minutes ago</b>.")
            else:
                self.CASText.setText("You are not currently in an active session.")
        else:
            self.CASText.setText("You are not currently in an active session.")

        self.updateLastActiveSession(cursor, latestEventTime if latestEvent else None)

        cursor.close()

    # Finds how long ago the user's current session started
    def findSessionStartTime(self, cursor, latestEventTime):
        cursor.execute('''
            SELECT timestamp
            FROM events
            WHERE eventTypeID IN (1, 3)
            AND timestamp <= ?
            ORDER BY timestamp DESC
        ''', (latestEventTime.strftime('%Y-%m-%d %H:%M:%S'),))
        events = cursor.fetchall()

        sessionStartTime = latestEventTime
        for i in range(len(events) - 1):
            currentEventTime = datetime.strptime(events[i][0], '%Y-%m-%d %H:%M:%S')
            previousEventTime = datetime.strptime(events[i+1][0], '%Y-%m-%d %H:%M:%S')
            if (currentEventTime - previousEventTime) > timedelta(minutes=15):
                break
            sessionStartTime = previousEventTime

        return sessionStartTime

    # Finds the start and end time of the previous active session
    def updateLastActiveSession(self, cursor, latestEventTime):
        if latestEventTime:
            cursor.execute('''
                SELECT timestamp
                FROM events
                WHERE eventTypeID IN (1, 3)
                AND timestamp <= ?
                ORDER BY timestamp DESC
            ''', (latestEventTime.strftime('%Y-%m-%d %H:%M:%S'),))
            events = cursor.fetchall()
            if events:
                for i in range(len(events) - 1):
                    currentEventTime = datetime.strptime(events[i][0], '%Y-%m-%d %H:%M:%S')
                    previousEventTime = datetime.strptime(events[i+1][0], '%Y-%m-%d %H:%M:%S')
                    if (currentEventTime - previousEventTime) > timedelta(minutes=15):
                        currentSessionStart = datetime.strptime(events[i][0], '%Y-%m-%d %H:%M:%S')
                        break
                else:
                    currentSessionStart = datetime.strptime(events[-1][0], '%Y-%m-%d %H:%M:%S')

                # Finds the last session before the current session
                cursor.execute('''
                    SELECT timestamp
                    FROM events
                    WHERE eventTypeID IN (1, 3)
                    AND timestamp < ?
                    ORDER BY timestamp DESC
                ''', (currentSessionStart.strftime('%Y-%m-%d %H:%M:%S'),))
                previousEvent = cursor.fetchall()

                if not previousEvent:
                    self.LASText.setText("Your last active session was not found.")
                    return

                lastSessionEnd = datetime.strptime(previousEvent[0][0], '%Y-%m-%d %H:%M:%S')
                for i in range(len(previousEvent) - 1):
                    currentEventTime = datetime.strptime(previousEvent[i][0], '%Y-%m-%d %H:%M:%S')
                    previousEventTime = datetime.strptime(previousEvent[i+1][0], '%Y-%m-%d %H:%M:%S')
                    if (currentEventTime - previousEventTime) > timedelta(minutes=15):
                        lastSessionStart = datetime.strptime(previousEvent[i][0], '%Y-%m-%d %H:%M:%S')
                        break
                else:
                    lastSessionStart = datetime.strptime(previousEvent[-1][0], '%Y-%m-%d %H:%M:%S')

                # Formats the times
                startDateStr = lastSessionStart.strftime('%b-%d')
                startTimeStr = lastSessionStart.strftime('%I:%M%p').lower().lstrip('0')
                endDateStr = lastSessionEnd.strftime('%b-%d')
                endTimeStr = lastSessionEnd.strftime('%I:%M%p').lower().lstrip('0')

                if startDateStr == endDateStr:
                    self.LASText.setText(f"Your last active session was from <b>{startDateStr} at {startTimeStr} to {endTimeStr}</b>.")
                else:
                    self.LASText.setText(f"Your last active session was from <b>{startDateStr} at {startTimeStr} to {endDateStr} at {endTimeStr}.</b>")
            else:
                self.LASText.setText("Your last active session was not found.")
        else:
            self.LASText.setText("Your last active session was not found.")
            
    # Close database when the app closes
    def closeDatabaseConnection(self):
        if self.conn:
            self.conn.close()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
