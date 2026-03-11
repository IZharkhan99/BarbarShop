const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios'); // We'll use this to check if server is up

let mainWindow;
let pythonProcess;

function startPythonProcess() {
    let pyPath;
    let args = [];
    let cwd = __dirname;

    if (app.isPackaged) {
        // Production: Path within the packaged app
        if (process.platform === 'darwin') {
            // Mac App Bundle: Contents/Resources/backend/barbershop_backend
            pyPath = path.join(process.resourcesPath, 'backend', 'barbershop_backend');
        } else {
            // Windows: resources/backend/barbershop_backend.exe
            pyPath = path.join(process.resourcesPath, 'backend', 'barbershop_backend.exe');
        }
        // No args needed since it's a bundled executable
        args = [];
        cwd = path.join(process.resourcesPath, 'backend');
    } else {
        // Development
        if (process.platform === 'win32') {
            pyPath = path.join(__dirname, 'venv_win', 'Scripts', 'python.exe');
        } else {
            pyPath = path.join(__dirname, 'venv', 'bin', 'python');
        }
        args = ['app.py'];
        cwd = __dirname;
    }

    console.log('Starting Python process at:', pyPath);

    const userDataPath = app.getPath('userData');
    
    pythonProcess = spawn(pyPath, args, {
        cwd: cwd,
        env: { 
            ...process.env, 
            FLASK_ENV: 'production', 
            PYTHONIOENCODING: 'utf-8',
            BARBERSHOP_DATA: userDataPath
        }
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
    const iconPath = app.isPackaged
        ? path.join(process.resourcesPath, 'AlShahidLogo.jpeg')
        : path.join(__dirname, 'AlShahidLogo.jpeg');

    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        icon: iconPath,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        },
        autoHideMenuBar: true
    });

    mainWindow.loadURL('http://localhost:5000');
    mainWindow.maximize();
    mainWindow.show();
    mainWindow.focus();

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
