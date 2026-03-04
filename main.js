const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios'); // We'll use this to check if server is up

let mainWindow;
let pythonProcess;

function startPythonProcess() {
    // Detect the correct python executable from our previously created venv_win
    const pyPath = path.join(__dirname, 'venv_win', 'Scripts', 'python.exe');

    console.log('Starting Python process at:', pyPath);

    pythonProcess = spawn(pyPath, ['app.py'], {
        cwd: __dirname,
        env: { ...process.env, FLASK_ENV: 'production' }
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });
}

async function checkServerReady() {
    const url = 'http://localhost:5000/login';
    let attempts = 0;
    const maxAttempts = 20;

    while (attempts < maxAttempts) {
        try {
            await axios.get(url);
            return true;
        } catch (e) {
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
    return false;
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        icon: path.join(__dirname, 'static', 'favicon.ico'), // Ensure static/favicon.ico exists or icon is removed
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        },
        autoHideMenuBar: true
    });

    mainWindow.loadURL('http://localhost:5000');

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

app.on('ready', async () => {
    startPythonProcess();

    // Wait for the server to be ready before showing the window
    const isReady = await checkServerReady();
    if (isReady) {
        createWindow();
    } else {
        console.error('Failed to start Python server in time.');
        app.quit();
    }
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    if (pythonProcess) {
        console.log('Killing Python process...');
        pythonProcess.kill();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});
