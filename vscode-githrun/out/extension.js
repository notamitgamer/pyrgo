"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const cp = require("child_process");
// 1. Activation Event
function activate(context) {
    console.log('Githrun extension is now active!');
    // Check if githrun CLI is installed
    checkGithrunInstallation();
    // Register the CodeLens Provider
    const docSelector = [
        { language: 'markdown', scheme: 'file' },
        { language: 'python', scheme: 'file' },
        { language: 'plaintext', scheme: 'file' }
    ];
    const codeLensProvider = new GithrunCodeLensProvider();
    context.subscriptions.push(vscode.languages.registerCodeLensProvider(docSelector, codeLensProvider));
    // --- REGISTER COMMANDS ---
    // Command 1: Run from CodeLens (Clicking the button)
    context.subscriptions.push(vscode.commands.registerCommand('githrun.runUrl', (url) => {
        runGithrun(url);
    }));
    // Command 2: Install CLI
    context.subscriptions.push(vscode.commands.registerCommand('githrun.installCli', () => {
        installGithrun();
    }));
    // Command 3: Run from Input Box (Ctrl+Shift+P)
    context.subscriptions.push(vscode.commands.registerCommand('githrun.runInput', () => {
        runFromInput();
    }));
    // Command 4: Run Current Selection
    context.subscriptions.push(vscode.commands.registerCommand('githrun.runSelection', () => {
        runSelection();
    }));
}
// 2. The CodeLens Provider (The "Scanner")
class GithrunCodeLensProvider {
    constructor() {
        // Regex to find GitHub/Gist URLs ending in .py
        this.regex = /https:\/\/(gist\.)?github\.com\/[\w\-\.\/]+\.py/g;
    }
    provideCodeLenses(document) {
        const text = document.getText();
        const lenses = [];
        let match;
        // Loop through all matches in the file
        while ((match = this.regex.exec(text)) !== null) {
            const url = match[0];
            const startPos = document.positionAt(match.index);
            const endPos = document.positionAt(match.index + url.length);
            const range = new vscode.Range(startPos, endPos);
            // Create the "Run" button
            const cmd = {
                title: "$(play) Run with Githrun", // The text user sees
                tooltip: "Execute this script remotely",
                command: "githrun.runUrl",
                arguments: [url]
            };
            lenses.push(new vscode.CodeLens(range, cmd));
        }
        return lenses;
    }
}
// 3. The Runner Logic
function runGithrun(url) {
    if (!url) {
        return;
    }
    // Get config for auto-install flag
    const config = vscode.workspace.getConfiguration('githrun');
    const autoInstall = config.get('autoInstallDeps') ? ' --auto-install' : '';
    // Create or show terminal
    const terminalName = 'Githrun';
    // Explicitly type 't' as a vscode.Terminal
    let terminal = vscode.window.terminals.find((t) => t.name === terminalName);
    if (!terminal) {
        terminal = vscode.window.createTerminal(terminalName);
    }
    terminal.show();
    // Use the CLI command you built in python!
    terminal.sendText(`githrun run ${url}${autoInstall}`);
}
// Helper: Run from Input Box
async function runFromInput() {
    const url = await vscode.window.showInputBox({
        placeHolder: "https://github.com/username/repo/blob/main/script.py",
        prompt: "Enter a GitHub URL or Gist to run with Githrun"
    });
    if (url) {
        runGithrun(url.trim());
    }
}
// Helper: Run from Selection
function runSelection() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage("No active text editor found.");
        return;
    }
    const selection = editor.document.getText(editor.selection);
    if (!selection) {
        vscode.window.showInformationMessage("Please highlight a GitHub URL first.");
        return;
    }
    // Basic validation
    const trimmed = selection.trim();
    if (trimmed.startsWith("http")) {
        runGithrun(trimmed);
    }
    else {
        vscode.window.showWarningMessage("The selected text does not look like a URL.");
    }
}
// 4. Installation Helper
function checkGithrunInstallation() {
    // Check version to verify installation
    cp.exec('githrun --version', (err, stdout) => {
        // Regex looks for standard version patterns like 1.0.0, 0.2, v1.0 etc.
        // It allows for "githrun version 1.0.0" or just "1.0.0"
        const versionMatch = stdout && stdout.match(/(\d+\.\d+(\.\d+)?)/);
        if (err || !versionMatch) {
            console.log('Githrun CLI check failed:', err ? err.message : 'No version number in stdout');
            vscode.window.showWarningMessage("Githrun CLI is not detected. Install it to run remote scripts?", "Install Now").then((selection) => {
                if (selection === "Install Now") {
                    installGithrun();
                }
            });
        }
        else {
            console.log(`Githrun CLI detected: ${versionMatch[0]}`);
        }
    });
}
function installGithrun() {
    const terminal = vscode.window.createTerminal("Install Githrun");
    terminal.show();
    terminal.sendText("pip install githrun");
    vscode.window.showInformationMessage("Installing Githrun... Try running the script once finished.");
}
function deactivate() { }
//# sourceMappingURL=extension.js.map