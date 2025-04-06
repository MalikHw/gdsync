# GD Sync - Geometry Dash Data Sync Tool

GD Sync is a tool designed to sync your Geometry Dash data (levels, progress, etc.) between your Android device and your PC (Linux). With GD Sync, you can easily transfer your Geometry Dash data back and forth, ensuring that your progress is always up-to-date on both platforms.

## Screenshots

### Push Mode
![Push Screenshot](Screenshot_2025-04-06_15-42-10.png)

### Pull Mode
![Pull Screenshot](Screenshot_2025-04-06_15-42-22.png)

### Success Dialog
![Success Screenshot](Screenshot_2025-04-06_15-42-33.png)


## Features

- Only when the phone has Geode this works
- Sync Geometry Dash user data (levels and progress) between your Android device and Linux PC.
- Supports both pushing (PC → Phone) and pulling (Phone → PC) data.
- Easy-to-use interface (GUI).

## Building!

just clone this repo and do a simple

```
chmod +x build.sh
./build.sh
```

## Installation

### For Linux (via PPA) (WIP, NOT WORKING RIGHT NOW)

To install GD Sync on your Linux machine, follow these steps:

`sudo add-apt-repository ppa:malikhw47/ppa`

then

`sudo apt update`

then

`sudo apt-get install gd-sync`

### For Linux via deb file

just go to the releases page and get the .deb file lol


**Android Device**: You need an Android device with USB Debugging enabled. To enable USB Debugging:

    Go to *Settings* → *About Phone* → Tap on *Build Number* multiple times to unlock *Developer Options.*

    Go to *Developer Options* → *Enable USB Debugging.*
