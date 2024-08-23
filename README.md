<p>
  <img src="docs/images/myPCStatsBanner.png" alt="MyPCStats Logo" width="100%">
</p>

#### Quick Links
- [Overview](#overview)
- [Features](#features)
- [Download](#download)
- [Help](#help)

## Overview
MyPCStats lets you track your lifetime computer inputs with new ways to view your keyboard and mouse input data.

## Features
MyPCStats is launching with a variety of different ways to view your computer activity. From mouse and keyboard input statistics to data analytics, you can view all of your input activity in one place.

#### Mouse
View your overall mouse input statistics on the Mouse Summary page. This holds convenient information, such as click totals, mouse movement totals, and more.

<p align="center">
  <img src="docs/images/mouseSummary.png" alt="Mouse Summary Page" width="80%">
</p>

---

The Scroll Up vs. Scroll Down pie chart shows a simple representation of how often you scroll up compared to scrolling down.

<p align="center">
  <img src="docs/images/scrollPieChart.png" alt="Mouse Scrolling Pie Chart" width="80%">
</p>

---

Fill up your screen with color by using the 24 hour click map, an overlay that shows you your last 24 hours of click history with colored dots. There are 5 different toggle buttons to change the way the data is displayed:

- **High Contrast:** the button with the 2 circles with a lined cross section makes the overlay darker, allowing easier viewing of the dots.
- **Animation:** Toggles the animation of drawing each dot individually.
- **Green Dot:** The green dots signify left click inputs from the mouse, and the green dot button can be used to turn them off or on.
- **Red Dot:** The red dots signify the right click inputs from the mouse, and the red dot button is used to turn them on or off.
- **Yellow Dot:** The yellow dot is for middle click inputs and the button toggles them on or off.

Press the esc button to leave the overlay.

<p align="center">
  <img src="docs/images/mouseClickDrawGIF.gif" alt="Mouse Click Overlay" width="80%">
</p>

---

View your mouse movement history with the move map, an overlay that shows your previous 2,000 (or 10,000) mouse movements. This overlay has 4 different toggle options:

- **High Contrast:** the button with the 2 circles with a lined cross section makes the overlay darker, allowing easier viewing of the dots.
- **Animation:** Toggles the animation of drawing the lines.
- **Line Thickness:** Changes the line thickness of the lines drawn from thick to thin.
- **Movement History Amount:** Changes the amount of recent mouse movements shown between 2,000 and 10,000.

Press the esc button to leave the overlay.

<p align="center">
  <img src="docs/images/mouseMoveDrawGIF.gif" alt="Mouse Movement Overlay" width="80%">
</p>

<hr>

#### Keyboard
See your summary of keyboard inputs on the Keyboard Summary page. This page has convenient keyboard input information, such as keyboard input totals, most used letters, and other insightful features.

<p align="center">
  <img src="docs/images/keyboardSummary.png" alt="Keyboard Summary Page" width="80%">
</p>

---

The Keyboard Heatmap is a depiction of your keyboard interaction history, showing the most used keys as red hot points and least used keys as green points. This overlay has 3 toggleable buttons:

- **View Letters Button:** Allows you to toggle the appearence of the letters and key names on the keyboard for better visibility.
- **Rounded Corners:** Toggles rounded or sharp corners on each key.
- **Color Scheme:** Changes the colors of the heatmap from the traditional green-to-red to a dark-to-light green scheme akin to the colors of the app.

<p align="center">
  <img src="docs/images/keyboardHeatmap.png" alt="Keyboard Heatmap Page" width="80%">
</p>

---

View the feud between space and backspace on the Space vs. Backspace pie chart.

<p align="center">
  <img src="docs/images/spaceVsBackspace.png" alt="Space vs Backspace Pie Chart" width="80%">
</p>

---

View various statistics of random keys with the Random Key Stats page. By clicking on either of the die, a random key on the keyboard is selected, and various details about it are shown.

<p align="center">
  <img src="docs/images/randomKeyStats.png" alt="Random Key Stats Page" width="80%">
</p>

<hr>

#### Analytics

The Input Summary Page presents a graph of average inputs throughout the day, telling you your most active computer usage hours.

<p align="center">
  <img src="docs/images/avgInputSummary.png" alt="Average Input Summary Page" width="80%">
</p>

---

The Mouse Click History plot has 5 settings to display your history of mouse inputs:

- **Live:** Last hour.
- **Day:** Last 24 hours.
- **Week:** Last 7 days.
- **Month:** Last 30 days.
- **Year:** last 12 months.

Depicted below is an example of the "Month" plot.

<p align="center">
  <img src="docs/images/mouseInputHistory.png" alt="Mouse Input History Page" width="80%">
</p>

---

Just like the Mouse Click History plot, the Keyboard Input History Plot has 5 settings to display your history of keyboard inputs:

- **Live:** Last hour.
- **Day:** Last 24 hours.
- **Week:** Last 7 days.
- **Month:** Last 30 days.
- **Year:** last 12 months.

Depicted below is an example of the "Month" plot.

<p align="center">
  <img src="docs/images/keyboardInputHistory.png" alt="Keyboard History Page" width="80%">
</p>

---

The active sessions page is an experimental way to see your typicsl computer actity. It uses your past keyboard and mouse inputs to infer the times you were active on your computer. On the Active Sessions page, there are various points of interest:

- **Current Session:** Tells you when your current active session started.
- **Last Active Session:** Displays your last active session on your computer.
- **Daily Activity Calendar:** Allows you to change the date and to view your activity on that day.
- **Daily Activity Plot:** Shows a 24 hour graph of periods when you were active on your computer. Hovering over the data allows for deeper analysis of usage times.

<p align="center">
  <img src="docs/images/activeSessions.png" alt="Active Sessions Page" width="80%">
</p>

<hr>

## Download
[Download the latest version of MyPCStats](https://github.com/LukeBarcenas/MyPCStats/releases/latest) - Get the latest version here.

#### Step 1
Head to the latest release page (linked above) and download the latest release by clicking on the 'MyPCStatsInstaller.exe' link in the assets section of the page.

#### Step 2
Open the installer and follow the install instructions. You should now be set up with MyPCStats!
Open the installer and follow the install instructions. You should now be set up with MyPCStats!

## Help
#### Data not being collected?
1. In the MyPCStats app, go to the homepage in the help section or the settings and click the link to open the application's folder. 
2. Head to the 'scripts' folder and double click 'PCStatsCollector'. Now, stats should start being collected. 

#### How do I collect data without manually starting PCStatsCollector every time?
This option is now available in the installer, but If you want to manually set up automatic data collection, follow these steps:

1. <b>Press Win+r and type "shell:startup", press enter</b> (This is the startup folder, you will add a shortcut of 'PCStatsCollector' into this folder).
2. <b>Head to your MyPCStats application folder and click the 'scripts' folder.</b> (To easily access, use the home help page or settings page in the 'MyPCStats' app)
3. <b>Right-click 'PCStatsCollector' and select the option 'Create shortcut'</b> (on Windows 11, press 'Show more options'->'Create shortcut').
4. <b>Drag the shortcut into your startup folder.</b> You should now be set up with automatic data collection at every startup!

#### How do I keep my data after every update?
The installer automatically avoids deleting your database if it already exists, but it is suggested to make a copy of your database just in case. Old databases will work unless a major database overhaul occurs.

##### Still not working or found a new bug? Report it to the Issues page, and I'll get to it as soon as possible.
