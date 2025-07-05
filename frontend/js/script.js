// ========== VARIABILE GLOBALE ==========
let canvas, ctx;
let board = document.getElementById('board');
let miniatures = [];
let connections = [];
let isDragging = false;
let draggedElement = null;
let selectedPin = null;
let selectedConnection = null;
let mainScriptData = null;
let mainScriptFile = null;
let offsetX, offsetY;
let connectionCounter = 0;
let isPanning = false;
let panStartX, panStartY;
let boardOffsetX = 0, boardOffsetY = 0;
let zoomLevel = 1;
let pinSelectionMode = false;
let firstPin = null;
let addingConnection = false;
let tempLine = null;
let lastClickedMini = null;
let fileToMiniMap = new Map();
let MINIATURE_BASE_SIZE = 130;

// Cache pentru date
let scriptsData = new Map();
let connectionData = new Map();

// Cache pentru editări
let editedFiles = new Map();

// FAZA 2.3 - Variabile pentru optimizare performanță
let redrawTimeout = null;
let lastRedrawTime = 0;
const REDRAW_DEBOUNCE_MS = 16; // ~60 FPS

// Mod IDE
let ideMode = false;

// Structura de directoare
let currentDirectoryStructure = null;
let currentStructureId = null;
let directoryAnalysis = null;

// ========== CONFIGURARE INIȚIALĂ ==========
window.onload = function() {
    canvas = document.getElementById('connectionCanvas');
    ctx = canvas.getContext('2d');
    
    // Setează dimensiunea canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Evenimente mouse pentru canvas
    canvas.addEventListener('mousedown', handleCanvasMouseDown);
    canvas.addEventListener('mousemove', handleCanvasMouseMove); 
    canvas.addEventListener('mouseup', handleCanvasMouseUp);
    canvas.addEventListener('wheel', handleCanvasWheel);
    
    // Evenimente pentru board
    board.addEventListener('dragover', allowDrop);
    board.addEventListener('drop', handleDrop);
    
    // Verifică sesiunea existentă
    checkExistingSession();
    
    console.log('Python Forensics (p4n6) - Platformă de analiză inițializată');
};

// ========== FUNCȚII UTILITATE ==========
function resizeCanvas() {
    canvas.width = board.offsetWidth;
    canvas.height = board.offsetHeight;
    redrawConnectionsOptimized();
}

function showMsg(msg, color = "#229966") {
    const messageElement = document.getElementById('uploadMessage');
    messageElement.style.display = 'block';
    messageElement.innerText = msg;
    messageElement.style.backgroundColor = color;
    
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 3500);
}

function getRandomPosition() {
    const margin = 50;
    const boardRect = board.getBoundingClientRect();
    const x = margin + Math.random() * (boardRect.width - 200 - margin);
    const y = margin + Math.random() * (boardRect.height - 200 - margin);
    return { x, y };
}

// FAZA 2.2 - Funcție pentru validare coordonate
function validatePosition(x, y) {
    const boardRect = board.getBoundingClientRect();
    const margin = 10;
    const miniSize = MINIATURE_BASE_SIZE;
    
    // Asigură că miniatura rămâne în board
    const validX = Math.max(margin, Math.min(x, boardRect.width - miniSize - margin));
    const validY = Math.max(margin, Math.min(y, boardRect.height - miniSize - margin));
    
    return { x: validX, y: validY };
}

function adjustMiniatureSize() {
    const miniCount = miniatures.length;
    let newSize = MINIATURE_BASE_SIZE;
    
    if (miniCount > 10) newSize = 110;
    if (miniCount > 20) newSize = 90;
    if (miniCount > 40) newSize = 75;
    
    document.querySelectorAll('.miniature').forEach(mini => {
        mini.style.width = newSize + 'px';
        mini.style.height = newSize + 'px';
    });
}

// ========== GESTIONARE FIȘIERE ==========
async function handleFileUpload(file, isMainScript = false) {
    if (!file.name.endsWith('.py')) {
        showMsg('⚠️ Vă rugăm să selectați doar fișiere Python (.py)', "#ff2929");
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async function(e) {
        const content = e.target.result;
        const fileName = file.name;
        
        // Salvează în cache
        scriptsData.set(fileName, content);
        
        if (isMainScript) {
            mainScriptFile = file;
            mainScriptData = content;
            showMainScriptPreview(fileName, content);
            analyzeScript(fileName, content, true);
            
            // Trimite la backend
            const numeFaraExt = fileName.replace(/\.py$/, '');
            try {
                await fetch('http://localhost:5000/set_principal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        filename: numeFaraExt,
                        content: content
                    })
                });
                
                showMsg(`✅ Script principal "${fileName}" încărcat cu succes!`, "#229966");
            } catch (err) {
                showMsg('⚠️ Eroare la comunicarea cu serverul!', "#ff2929");
            }
        } else {
            createMiniature(file, content);
            analyzeScript(fileName, content, false);
            
            // Trimite la backend
            try {
                await fetch('http://localhost:5000/add_secundar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: fileName,
                        content: content
                    })
                });
                
                showMsg(`✅ Script secundar "${fileName}" adăugat!`, "#229966");
            } catch (err) {
                showMsg('⚠️ Eroare la comunicarea cu serverul!', "#ff2929");
            }
        }
    };
    reader.readAsText(file);
}

function showMainScriptPreview(fileName, content) {
    const container = document.getElementById('mainScriptContainer');
    container.innerHTML = `
        <div class="script-info">
            <span class="script-icon">📄</span>
            <span class="script-name">${fileName}</span>
        </div>
        <pre class="main-script-preview">${content.substring(0, 200)}...</pre>
    `;
    
    // FAZA 1.2 - Salvează date pentru analiză
    container.dataset.analysis = JSON.stringify({});
}

// ========== ANALIZĂ SCRIPTURI ==========
async function analyzeScript(fileName, content, isMainScript) {
    try {
        const response = await fetch('http://localhost:5000/analyze_imports', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                content: content,
                filename: fileName
            })
        });
        
        const data = await response.json();
        
        if (isMainScript) {
            // Salvează analiza pentru scriptul principal
            const container = document.getElementById('mainScriptContainer');
            if (container) {
                container.dataset.analysis = JSON.stringify(data.analysis || {});
            }
        } else {
            // Găsește miniatura corespunzătoare
            const miniature = Array.from(document.querySelectorAll('.miniature'))
                .find(m => m.querySelector('.filename').textContent === fileName);
            
            if (miniature && data.analysis) {
                // Adaugă indicator pentru tipul de script
                addScriptTypeIndicator(miniature, data.analysis.script_type);
                
                // Salvează analiza
                miniature.dataset.analysis = JSON.stringify(data.analysis);
                
                // Verifică conexiuni
                if (data.imports && !isMainScript && mainScriptFile) {
                    createConnection(mainScriptFile.name, fileName, data.entities);
                }
            }
        }
        
    } catch (err) {
        console.error('Eroare la analiza script:', err);
    }
}

function addScriptTypeIndicator(miniature, scriptType) {
    const existing = miniature.querySelector('.script-type-indicator');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.className = 'script-type-indicator';
    
    const typeIcons = {
        'Server Flask': '🌶️',
        'Server FastAPI': '⚡',
        'Aplicație Django': '🎯',
        'Suite de teste': '🧪',
        'Machine Learning': '🤖',
        'Analiză de date': '📊',
        'Web Scraper': '🕷️',
        'Aplicație GUI': '🖼️',
        'Aplicație CLI': '💻',
        'Script executabil': '▶️',
        'Modul Python': '📦'
    };
    
    indicator.textContent = typeIcons[scriptType] || '📄';
    indicator.title = scriptType;
    
    miniature.appendChild(indicator);
}

// ========== CREARE MINIATURI ==========
function createMiniature(file, content) {
    const position = getRandomPosition();
    const miniature = document.createElement('div');
    miniature.className = 'miniature';
    miniature.style.left = position.x + 'px';
    miniature.style.top = position.y + 'px';
    miniature.dataset.filename = file.name;
    
    // Conținut miniatură
    miniature.innerHTML = `
        <div class="pin"></div>
        <div class="magnify" onclick="magnifyScript('${file.name}')">🔍</div>
        <div class="edit-btn" onclick="openEditor('${file.name}')">✏️</div>
        <div class="filename">${file.name}</div>
        <pre class="preview">${content.substring(0, 150)}...</pre>
    `;
    
    // Evenimente drag
    miniature.draggable = true;
    miniature.addEventListener('dragstart', handleDragStart);
    miniature.addEventListener('dragend', handleDragEnd);
    
    // Click pe pin
    const pin = miniature.querySelector('.pin');
    pin.addEventListener('click', handlePinClick);
    
    board.appendChild(miniature);
    miniatures.push(miniature);
    fileToMiniMap.set(file.name, miniature);
    
    adjustMiniatureSize();
}

// ========== DRAG & DROP ==========
function handleDragStart(e) {
    isDragging = true;
    draggedElement = e.target;
    const rect = draggedElement.getBoundingClientRect();
    const boardRect = board.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    isDragging = false;
    draggedElement = null;
}

function allowDrop(e) {
    e.preventDefault();
}

// FAZA 2.2 - Validare poziție la drop
function handleDrop(e) {
    e.preventDefault();
    
    if (draggedElement && draggedElement.classList.contains('miniature')) {
        const boardRect = board.getBoundingClientRect();
        const x = e.clientX - boardRect.left - offsetX;
        const y = e.clientY - boardRect.top - offsetY;
        
        // Validează poziția
        const validPos = validatePosition(x, y);
        
        draggedElement.style.left = validPos.x + 'px';
        draggedElement.style.top = validPos.y + 'px';
        
        redrawConnectionsOptimized();
    }
}

// ========== CONEXIUNI ==========
function createConnection(mainFile, secondaryFile, entities) {
    const connection = {
        id: ++connectionCounter,
        main: mainFile,
        secondary: secondaryFile,
        entities: entities || { functions: [], classes: [] }
    };
    
    connections.push(connection);
    connectionData.set(connection.id, connection);
    
    // Adaugă clasa pentru script care importă main
    const miniature = fileToMiniMap.get(secondaryFile);
    if (miniature) {
        miniature.classList.add('imports-main');
    }
    
    redrawConnectionsOptimized();
}

// FAZA 2.3 - Optimizare redraw cu debouncing
function redrawConnectionsOptimized() {
    // Cancel redraw anterior dacă există
    if (redrawTimeout) {
        clearTimeout(redrawTimeout);
    }
    
    const now = Date.now();
    const timeSinceLastRedraw = now - lastRedrawTime;
    
    if (timeSinceLastRedraw >= REDRAW_DEBOUNCE_MS) {
        // Redraw imediat dacă a trecut suficient timp
        redrawConnections();
        lastRedrawTime = now;
    } else {
        // Programează redraw pentru mai târziu
        redrawTimeout = setTimeout(() => {
            redrawConnections();
            lastRedrawTime = Date.now();
        }, REDRAW_DEBOUNCE_MS);
    }
}

function redrawConnections() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // FAZA 2.2 - Verifică doar conexiunile vizibile
    const canvasRect = canvas.getBoundingClientRect();
    
    connections.forEach(conn => {
        if (isConnectionVisible(conn, canvasRect)) {
            drawConnection(conn);
        }
    });
    
    // Desenează linia temporară dacă există
    if (tempLine) {
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(tempLine.startX, tempLine.startY);
        ctx.lineTo(tempLine.endX, tempLine.endY);
        ctx.stroke();
        ctx.setLineDash([]);
    }
}

// FAZA 2.2 - Verifică dacă conexiunea este vizibilă
function isConnectionVisible(connection, canvasRect) {
    const mainMini = document.querySelector('#mainScriptContainer');
    const secondaryMini = fileToMiniMap.get(connection.secondary);
    
    if (!mainMini || !secondaryMini) return false;
    
    const mainRect = mainMini.getBoundingClientRect();
    const secondaryRect = secondaryMini.getBoundingClientRect();
    
    // Verifică dacă cel puțin un capăt este vizibil
    const mainVisible = (
        mainRect.right >= canvasRect.left &&
        mainRect.left <= canvasRect.right &&
        mainRect.bottom >= canvasRect.top &&
        mainRect.top <= canvasRect.bottom
    );
    
    const secondaryVisible = (
        secondaryRect.right >= canvasRect.left &&
        secondaryRect.left <= canvasRect.right &&
        secondaryRect.bottom >= canvasRect.top &&
        secondaryRect.top <= canvasRect.bottom
    );
    
    return mainVisible || secondaryVisible;
}

function drawConnection(connection) {
    const mainMini = document.querySelector('#mainScriptContainer');
    const secondaryMini = fileToMiniMap.get(connection.secondary);
    
    if (!mainMini || !secondaryMini) return;
    
    const mainRect = mainMini.getBoundingClientRect();
    const secondaryRect = secondaryMini.getBoundingClientRect();
    const canvasRect = canvas.getBoundingClientRect();
    
    const startX = mainRect.right - canvasRect.left;
    const startY = mainRect.top + mainRect.height / 2 - canvasRect.top;
    const endX = secondaryRect.left - canvasRect.left;
    const endY = secondaryRect.top + secondaryRect.height / 2 - canvasRect.top;
    
    // Desenează linia
    ctx.strokeStyle = connection === selectedConnection ? '#22aaff' : '#92ff68';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    
    // Curbă Bezier pentru conexiuni mai frumoase
    const cp1x = startX + (endX - startX) / 3;
    const cp1y = startY;
    const cp2x = endX - (endX - startX) / 3;
    const cp2y = endY;
    ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
    ctx.stroke();
    
    // Desenează săgeata
    drawArrow(ctx, cp2x, cp2y, endX, endY);
}

function drawArrow(ctx, fromX, fromY, toX, toY) {
    const headLength = 15;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(
        toX - headLength * Math.cos(angle - Math.PI / 6),
        toY - headLength * Math.sin(angle - Math.PI / 6)
    );
    ctx.lineTo(
        toX - headLength * Math.cos(angle + Math.PI / 6),
        toY - headLength * Math.sin(angle + Math.PI / 6)
    );
    ctx.closePath();
    ctx.fill();
}

// ========== EVENIMENTE CANVAS ==========
function handleCanvasMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (e.button === 1 || (e.button === 0 && e.ctrlKey)) {
        // Pan cu middle click sau Ctrl+click
        isPanning = true;
        panStartX = e.clientX;
        panStartY = e.clientY;
        canvas.style.cursor = 'grabbing';
        e.preventDefault();
    }
}

function handleCanvasMouseMove(e) {
    if (isPanning) {
        const dx = e.clientX - panStartX;
        const dy = e.clientY - panStartY;
        
        boardOffsetX += dx;
        boardOffsetY += dy;
        
        board.style.transform = `translate(${boardOffsetX}px, ${boardOffsetY}px) scale(${zoomLevel})`;
        
        panStartX = e.clientX;
        panStartY = e.clientY;
    } else if (addingConnection && firstPin) {
        // Actualizează linia temporară
        const rect = canvas.getBoundingClientRect();
        tempLine.endX = e.clientX - rect.left;
        tempLine.endY = e.clientY - rect.top;
        redrawConnectionsOptimized();
    }
}

function handleCanvasMouseUp(e) {
    isPanning = false;
    canvas.style.cursor = 'default';
}

function handleCanvasWheel(e) {
    if (e.ctrlKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        zoomLevel *= delta;
        zoomLevel = Math.max(0.3, Math.min(3, zoomLevel));
        
        board.style.transform = `translate(${boardOffsetX}px, ${boardOffsetY}px) scale(${zoomLevel})`;
    }
}

// ========== VIZUALIZARE ȘI EDITARE ==========
function magnifyScript(filename) {
    const content = scriptsData.get(filename) || 'Conținut indisponibil';
    const modal = document.getElementById('modal');
    const modalFilename = modal.querySelector('.modal-filename');
    const modalText = modal.querySelector('.modal-text');
    
    modalFilename.value = filename;
    modalText.textContent = content;
    
    // FAZA 1.2 - Curăță clasele reziduale
    modal.classList.remove('editor-mode');
    modal.classList.remove('hidden');
}

function openEditor(filename) {
    const content = editedFiles.get(filename) || scriptsData.get(filename) || '';
    const modal = document.getElementById('modal');
    
    // Configurează modal pentru mod editor
    modal.classList.add('editor-mode');
    
    const modalContent = modal.querySelector('.modal-content');
    modalContent.innerHTML = `
        <span class="close" id="closeModalEditor">&times;</span>
        <input type="text" class="modal-filename" value="${filename}" readonly>
        <textarea class="modal-editor" id="editorTextarea">${content}</textarea>
        <div class="editor-controls">
            <button class="editor-btn" onclick="saveEdit('${filename}')">💾 Salvează</button>
            <button class="editor-btn" onclick="cancelEdit()">❌ Anulează</button>
        </div>
    `;
    
    // FAZA 1.2 - Event listener specific pentru editor
    document.getElementById('closeModalEditor').onclick = () => {
        modal.classList.add('hidden');
        modal.classList.remove('editor-mode');
    };
    
    modal.classList.remove('hidden');
    
    // Focus pe editor
    document.getElementById('editorTextarea').focus();
}

async function saveEdit(filename) {
    const content = document.getElementById('editorTextarea').value;
    
    // FAZA 3.3 - Sincronizare cache
    editedFiles.set(filename, content);
    scriptsData.set(filename, content);
    
    // Marchează miniatura ca editată
    const miniature = fileToMiniMap.get(filename);
    if (miniature) {
        miniature.classList.add('edited-file');
        
        // Actualizează preview
        const preview = miniature.querySelector('.preview');
        if (preview) {
            preview.textContent = content.substring(0, 150) + '...';
        }
    }
    
    // Salvează în backend
    try {
        const response = await fetch('http://localhost:5000/save_session_edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: filename,
                content: content
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showMsg(`✅ Modificări salvate pentru ${filename}`, "#229966");
        } else {
            showMsg(`⚠️ ${data.message || 'Eroare la salvare'}`, "#ff2929");
        }
    } catch (err) {
        showMsg('❌ Eroare la salvarea modificărilor', "#ff2929");
    }
    
    // Închide modal
    const modal = document.getElementById('modal');
    modal.classList.add('hidden');
    modal.classList.remove('editor-mode');
    
    // Re-analizează dacă e necesar
    await analyzeScript(filename, content, filename === mainScriptFile?.name);
    
    // Actualizează conexiuni
    await updateConnectionsAfterEdit(filename);
}

function cancelEdit() {
    const modal = document.getElementById('modal');
    modal.classList.add('hidden');
    modal.classList.remove('editor-mode');
}

// ========== EVENIMENTE BUTOANE ==========
document.getElementById('loadMainScript').onclick = () => {
    document.getElementById('mainScriptInput').click();
};

document.getElementById('mainScriptInput').onchange = (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0], true);
    }
};

document.getElementById('loadScript').onclick = () => {
    document.getElementById('scriptInput').click();
};

document.getElementById('scriptInput').onchange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 100) {
        showMsg('⚠️ Maxim 100 de fișiere pot fi încărcate simultan!', "#ff2929");
        return;
    }
    files.forEach(file => handleFileUpload(file, false));
};

document.getElementById('clearBoard').onclick = () => {
    if (confirm('Sigur doriți să ștergeți toate elementele?')) {
        clearBoard();
    }
};

document.getElementById('startAnalysis').onclick = async () => {
    if (!mainScriptFile) {
        showMsg('⚠️ Vă rugăm să încărcați mai întâi un script principal!', "#ff2929");
        return;
    }
    
    showMsg('🔍 Analiză în desfășurare...', "#229966");
    
    // Generează raport
    await generateReport();
};

document.getElementById('addConnection').onclick = () => {
    if (!mainScriptFile) {
        showMsg('⚠️ Încărcați mai întâi un script principal!', "#ff2929");
        return;
    }
    
    addingConnection = true;
    firstPin = null;
    showMsg('📍 Selectați două pin-uri pentru a crea o conexiune', "#00c3ff");
};

document.getElementById('resetView').onclick = () => {
    boardOffsetX = 0;
    boardOffsetY = 0;
    zoomLevel = 1;
    board.style.transform = 'translate(0px, 0px) scale(1)';
    showMsg('🔄 Vizualizare resetată', "#229966");
};

document.getElementById('loadDirectoryStructure').onclick = () => {
    const modal = document.getElementById('directoryModal');
    modal.classList.remove('hidden');
};

// ========== EVENIMENTE PIN ==========
function handlePinClick(e) {
    e.stopPropagation();
    const pin = e.target;
    const miniature = pin.parentElement;
    
    if (addingConnection) {
        if (!firstPin) {
            firstPin = pin;
            miniature.classList.add('pin-selected');
            
            // Inițializează linia temporară
            const rect = pin.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();
            tempLine = {
                startX: rect.left + rect.width / 2 - canvasRect.left,
                startY: rect.top + rect.height / 2 - canvasRect.top,
                endX: rect.left + rect.width / 2 - canvasRect.left,
                endY: rect.top + rect.height / 2 - canvasRect.top
            };
        } else if (pin !== firstPin) {
            // Creează conexiune manuală
            const file1 = firstPin.parentElement.dataset.filename || mainScriptFile?.name;
            const file2 = miniature.dataset.filename;
            
            createConnection(file1, file2, { functions: [], classes: [] });
            
            // Reset
            firstPin.parentElement.classList.remove('pin-selected');
            firstPin = null;
            addingConnection = false;
            tempLine = null;
            
            showMsg('✅ Conexiune creată!', "#229966");
            redrawConnectionsOptimized();
        }
    }
}

// ========== RAPORTARE ==========
async function generateReport() {
    const raportBox = document.getElementById('raportBox');
    raportBox.innerHTML = 'Generare raport în curs...\n\n';
    
    try {
        // Colectează date despre analiză
        const analysisData = {
            mainScript: {
                name: mainScriptFile?.name,
                analysis: JSON.parse(document.querySelector('#mainScriptContainer').dataset.analysis || '{}')
            },
            secondaryScripts: [],
            connections: connections.map(conn => ({
                from: conn.main,
                to: conn.secondary,
                entities: conn.entities
            }))
        };
        
        // Adaugă scripturile secundare
        document.querySelectorAll('.miniature').forEach(mini => {
            const analysis = JSON.parse(mini.dataset.analysis || '{}');
            analysisData.secondaryScripts.push({
                name: mini.dataset.filename,
                analysis: analysis,
                imports_main: mini.classList.contains('imports-main')
            });
        });
        
        // Generează raport text
        let raport = '=== RAPORT ANALIZĂ PYTHON FORENSICS (p4n6) ===\n\n';
        raport += `📅 Data: ${new Date().toLocaleString('ro-RO')}\n`;
        raport += `📄 Script Principal: ${analysisData.mainScript.name}\n`;
        raport += `📁 Scripturi Secundare: ${analysisData.secondaryScripts.length}\n`;
        raport += `🔗 Conexiuni Detectate: ${analysisData.connections.length}\n\n`;
        
        raport += '=== DETALII SCRIPT PRINCIPAL ===\n';
        const mainAnalysis = analysisData.mainScript.analysis;
        if (mainAnalysis.script_type) {
            raport += `Tip: ${mainAnalysis.script_type}\n`;
        }
        if (mainAnalysis.functions?.length) {
            raport += `Funcții: ${mainAnalysis.functions.length}\n`;
            mainAnalysis.functions.slice(0, 5).forEach(f => {
                raport += `  - ${f.name} (complexitate: ${f.complexity || 1})\n`;
            });
        }
        if (mainAnalysis.classes?.length) {
            raport += `Clase: ${mainAnalysis.classes.length}\n`;
            mainAnalysis.classes.forEach(c => {
                raport += `  - ${c.name}\n`;
            });
        }
        
        raport += '\n=== SCRIPTURI SECUNDARE ===\n';
        analysisData.secondaryScripts.forEach(script => {
            raport += `\n📄 ${script.name}:\n`;
            raport += `  - Tip: ${script.analysis.script_type || 'Modul Python'}\n`;
            raport += `  - Importă scriptul principal: ${script.imports_main ? 'DA ✅' : 'NU ❌'}\n`;
            if (script.analysis.functions?.length) {
                raport += `  - Funcții: ${script.analysis.functions.length}\n`;
            }
            if (script.analysis.classes?.length) {
                raport += `  - Clase: ${script.analysis.classes.length}\n`;
            }
        });
        
        raport += '\n=== ANALIZA DEPENDENȚELOR ===\n';
        if (analysisData.connections.length > 0) {
            analysisData.connections.forEach(conn => {
                raport += `\n${conn.from} → ${conn.to}:\n`;
                if (conn.entities.functions?.length) {
                    raport += `  Funcții importate: ${conn.entities.functions.join(', ')}\n`;
                }
                if (conn.entities.classes?.length) {
                    raport += `  Clase importate: ${conn.entities.classes.join(', ')}\n`;
                }
            });
        } else {
            raport += 'Nu au fost detectate dependențe directe.\n';
        }
        
        raport += '\n=== RECOMANDĂRI ===\n';
        
        // Analiză complexitate
        const highComplexityFuncs = [];
        [analysisData.mainScript, ...analysisData.secondaryScripts].forEach(script => {
            script.analysis.functions?.forEach(f => {
                if (f.complexity > 10) {
                    highComplexityFuncs.push(`${script.name}:${f.name}`);
                }
            });
        });
        
        if (highComplexityFuncs.length > 0) {
            raport += `\n⚠️ Funcții cu complexitate ridicată (>10):\n`;
            highComplexityFuncs.forEach(f => raport += `  - ${f}\n`);
            raport += '  Recomandare: Considerați refactorizarea acestor funcții.\n';
        }
        
        // Verifică structura
        const totalFiles = analysisData.secondaryScripts.length + 1;
        if (totalFiles > 20) {
            raport += '\n⚠️ Proiect cu multe fișiere\n';
            raport += '  Recomandare: Considerați organizarea în pachete/module.\n';
        }
        
        raport += '\n=== FIN RAPORT ===';
        
        raportBox.textContent = raport;
        
    } catch (err) {
        raportBox.textContent = 'Eroare la generarea raportului: ' + err.message;
        console.error('Eroare:', err);
    }
}

// ========== FUNCȚII AUXILIARE ==========
function clearBoard() {
    // Șterge miniaturi
    miniatures.forEach(mini => mini.remove());
    miniatures = [];
    
    // Șterge conexiuni
    connections = [];
    connectionData.clear();
    
    // Șterge date
    scriptsData.clear();
    editedFiles.clear();
    fileToMiniMap.clear();
    
    // Reset variabile
    mainScriptFile = null;
    mainScriptData = null;
    connectionCounter = 0;
    
    // Curăță UI
    document.getElementById('mainScriptContainer').innerHTML = `
        <p class="placeholder-text">Niciun script principal încărcat</p>
    `;
    document.getElementById('raportBox').textContent = '';
    
    // Curăță canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    showMsg('🗑️ Board curățat!', "#229966");
}

async function checkExistingSession() {
    try {
        const response = await fetch('http://localhost:5000/get_session_edits');
        const data = await response.json();
        
        if (data.count > 0) {
            showMsg(`📂 ${data.count} fișiere editate în sesiune`, "#00c3ff");
        }
    } catch (err) {
        console.log('Nu s-a putut verifica sesiunea:', err);
    }
}

// FAZA 3.3 - Sincronizare îmbunătățită
async function updateConnectionsAfterEdit(filename) {
    // Re-verifică conexiunile după editare
    if (filename === mainScriptFile?.name) {
        // Dacă s-a editat scriptul principal, re-analizează toate conexiunile
        for (const mini of miniatures) {
            const secondaryFile = mini.dataset.filename;
            const content = scriptsData.get(secondaryFile);
            if (content) {
                await analyzeScript(secondaryFile, content, false);
            }
        }
    } else {
        // Dacă s-a editat un script secundar, verifică doar conexiunea lui
        const content = scriptsData.get(filename);
        if (content) {
            await analyzeScript(filename, content, false);
        }
    }
}

// ========== EXPORT FUNCȚII ==========
document.getElementById('exportWorkflow').onclick = async () => {
    if (!mainScriptFile) {
        showMsg('⚠️ Nu există date pentru export!', "#ff2929");
        return;
    }
    
    showMsg('📊 Generare workflow...', "#229966");
    
    try {
        // Pregătește datele pentru workflow
        const projectData = {
            project_name: mainScriptFile.name.replace('.py', ''),
            main_script: {
                name: mainScriptFile.name,
                analysis: JSON.parse(document.querySelector('#mainScriptContainer').dataset.analysis || '{}')
            },
            secondary_scripts: [],
            connections: connections.map(conn => ({
                from: conn.main,
                to: conn.secondary,
                entities: conn.entities
            })),
            metrics: {
                total_files: miniatures.length + 1,
                coupling_score: calculateCouplingScore()
            }
        };
        
        // Adaugă scripturile secundare
        document.querySelectorAll('.miniature').forEach(mini => {
            const analysis = JSON.parse(mini.dataset.analysis || '{}');
            projectData.secondary_scripts.push({
                name: mini.dataset.filename,
                analysis: analysis,
                imports_main: mini.classList.contains('imports-main')
            });
        });
        
        // Adaugă informații despre structura de directoare dacă există
        if (currentStructureId && directoryAnalysis) {
            projectData.directory_structure = {
                directories: directoryAnalysis.directories,
                total_files: directoryAnalysis.total_files,
                python_files: directoryAnalysis.files_analyzed,
                entry_points: directoryAnalysis.entry_points
            };
        }
        
        // Trimite la backend pentru generare
        const response = await fetch('http://localhost:5000/generate_workflow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        
        const result = await response.json();
        
        if (result.status === 'ok') {
            // Afișează workflow-ul în modal
            showWorkflowModal(result.workflow);
        } else {
            showMsg('❌ ' + (result.message || 'Eroare la generarea workflow'), "#ff2929");
        }
        
    } catch (err) {
        showMsg('❌ Eroare la generarea workflow!', "#ff2929");
        console.error(err);
    }
};

function calculateCouplingScore() {
    const totalPossible = miniatures.length * (miniatures.length - 1);
    const actualConnections = connections.length;
    
    if (totalPossible === 0) return 'low';
    
    const ratio = actualConnections / totalPossible;
    
    if (ratio < 0.1) return 'low';
    else if (ratio < 0.3) return 'medium';
    else if (ratio < 0.5) return 'high';
    else return 'very_high';
}

function showWorkflowModal(workflowContent) {
    const modal = document.getElementById('workflowModal');
    const workflowBody = document.getElementById('workflowBody');
    
    // Convertește markdown în HTML pentru afișare mai bună
    workflowBody.innerHTML = `<pre class="workflow-content">${workflowContent}</pre>`;
    
    modal.classList.remove('hidden');
}

// ========== EVENIMENTE MODALE ==========
// FAZA 1.2 - Fixare închidere modaluri
document.addEventListener('DOMContentLoaded', function() {
    // Modal principal
    const modal = document.getElementById('modal');
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.onclick = () => {
            modal.classList.add('hidden');
            // Curăță toate clasele posibile
            modal.classList.remove('editor-mode');
        };
    }
    
    // Modal raport
    const closeReportModal = document.getElementById('closeReportModal');
    if (closeReportModal) {
        closeReportModal.onclick = () => {
            document.getElementById('reportModal').classList.add('hidden');
        };
    }
    
    // Modal workflow
    const closeWorkflowModal = document.getElementById('closeWorkflowModal');
    if (closeWorkflowModal) {
        closeWorkflowModal.onclick = () => {
            document.getElementById('workflowModal').classList.add('hidden');
        };
    }
    
    // Export PDF
    const exportWorkflowPDF = document.getElementById('exportWorkflowPDF');
    if (exportWorkflowPDF) {
        exportWorkflowPDF.onclick = async () => {
            const workflowContent = document.querySelector('.workflow-content').textContent;
            
            try {
                const response = await fetch('http://localhost:5000/export_pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: workflowContent,
                        title: 'Python Forensics - Analiză Workflow'
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.status === 'ok') {
                    // Descarcă PDF-ul
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'python_forensics_workflow.pdf';
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    showMsg('✅ PDF exportat cu succes!', "#229966");
                } else {
                    showMsg(`⚠️ ${result.message || 'Eroare la exportul PDF'}`, "#ff2929");
                }
            } catch (err) {
                showMsg('❌ Eroare la exportul PDF!', "#ff2929");
                console.error(err);
            }
        };
    }
});

// Export funcții globale necesare
window.magnifyScript = magnifyScript;
window.openEditor = openEditor;
window.saveEdit = saveEdit;
window.cancelEdit = cancelEdit;
window.handleFileUpload = handleFileUpload;