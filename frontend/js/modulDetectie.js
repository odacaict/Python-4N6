/**
 * Modul de detectare și analiză structuri de directoare
 * Python Forensics (p4n6) - Directory Detection Module
 * Versiune actualizată cu remedieri FAZA 1, 2, 3
 */

// Variabile globale pentru modul
let detectedStructure = null;
let detectedFiles = [];
let structurePreview = null;
let processedFilesCount = 0;
let totalFilesToProcess = 0;

// Constantă pentru mărimea maximă a fișierelor (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// Extensii Python valide
const PYTHON_EXTENSIONS = ['py', 'pyw', 'pyx', 'pyi', 'pyc', 'pyd', 'pyo'];
const VALID_EXTENSIONS = [...PYTHON_EXTENSIONS, 'txt', 'md', 'json', 'yml', 'yaml', 'cfg', 'ini', 'js', 'html', 'css', 'xml', 'toml', 'rst'];

// Referințe DOM
const directoryModal = document.getElementById('directoryModal');
const closeDirectoryModal = document.getElementById('closeDirectoryModal');
const cancelDirectoryLoad = document.getElementById('cancelDirectoryLoad');
const loadDirectoryBtn = document.getElementById('loadDirectoryStructure');
const dragDropZone = document.getElementById('dragDropZone');
const directoryInput = document.getElementById('directoryInput');
const filesInput = document.getElementById('filesInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const manualStructure = document.getElementById('manualStructure');
const parseManualStructure = document.getElementById('parseManualStructure');
const clearManualStructure = document.getElementById('clearManualStructure');
const structurePreviewDiv = document.getElementById('structurePreview');
const previewStats = document.getElementById('previewStats');
const previewTree = document.getElementById('previewTree');
const selectDirectory = document.getElementById('selectDirectory');
const selectFiles = document.getElementById('selectFiles');

// Tab-uri
const directoryTabs = document.querySelectorAll('.tab-btn');
const uploadTab = document.getElementById('uploadTab');
const manualTab = document.getElementById('manualTab');

// Event listeners pentru tab-uri
directoryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Actualizează butoanele
        directoryTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Actualizează conținutul
        if (targetTab === 'upload') {
            uploadTab.classList.remove('hidden');
            manualTab.classList.add('hidden');
        } else {
            uploadTab.classList.add('hidden');
            manualTab.classList.remove('hidden');
        }
    });
});

// Drag and drop events
dragDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dragDropZone.classList.add('drag-over');
});

dragDropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragDropZone.classList.remove('drag-over');
});

dragDropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dragDropZone.classList.remove('drag-over');
    
    const items = Array.from(e.dataTransfer.items);
    const files = [];
    
    for (const item of items) {
        if (item.kind === 'file') {
            const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : item.getAsFile();
            if (entry) {
                if (entry.isDirectory) {
                    await scanDirectory(entry, files);
                } else {
                    const file = item.getAsFile();
                    if (file && isValidFile(file)) {
                        files.push(file);
                    }
                }
            }
        }
    }
    
    if (files.length > 0) {
        processSelectedFiles(files, 'dropped');
    } else {
        showMsg('⚠️ Nu s-au găsit fișiere valide în selecția dvs.', "#ff2929");
    }
});

// Click events pentru selectare
selectDirectory.addEventListener('click', (e) => {
    e.stopPropagation();
    directoryInput.click();
});

selectFiles.addEventListener('click', (e) => {
    e.stopPropagation();
    filesInput.click();
});

directoryInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const files = Array.from(e.target.files);
        const validFiles = files.filter(file => isValidFile(file));
        if (validFiles.length > 0) {
            processSelectedFiles(validFiles, 'directory');
        } else {
            showMsg('⚠️ Nu s-au găsit fișiere valide în director!', "#ff2929");
        }
    }
});

filesInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const files = Array.from(e.target.files);
        const validFiles = files.filter(file => isValidFile(file));
        if (validFiles.length > 0) {
            processSelectedFiles(validFiles, 'files');
        } else {
            showMsg('⚠️ Nu s-au selectat fișiere valide!', "#ff2929");
        }
    }
});

// Procesare manuală
parseManualStructure.addEventListener('click', () => {
    const structureText = manualStructure.value.trim();
    if (!structureText) {
        showMsg('⚠️ Introduceți structura de directoare!', "#ff2929");
        return;
    }
    
    const structure = parseTreeStructure(structureText);
    if (structure && structure.files.length > 0) {
        detectedStructure = structure;
        detectedFiles = extractFilesFromStructure(structure);
        showStructurePreview();
        // FAZA 1.1 - Activare corectă a butonului
        loadDirectoryBtn.disabled = false;
        showMsg(`✅ Structură parsată: ${detectedFiles.length} fișiere detectate`, "#229966");
    } else {
        showMsg('⚠️ Nu s-au putut extrage fișiere din structura introdusă!', "#ff2929");
    }
});

clearManualStructure.addEventListener('click', () => {
    manualStructure.value = '';
    hideStructurePreview();
    loadDirectoryBtn.disabled = true;
    detectedStructure = null;
    detectedFiles = [];
});

// Funcții de scanare directoare
async function scanDirectory(entry, files, path = '') {
    if (entry.isFile) {
        const file = await new Promise(resolve => entry.file(resolve));
        if (isValidFile(file)) {
            file.path = path + file.name;
            files.push(file);
        }
    } else if (entry.isDirectory) {
        const reader = entry.createReader();
        let entries = [];
        let batch;
        
        // Citește toate intrările (poate fi nevoie de mai multe apeluri)
        do {
            batch = await new Promise(resolve => reader.readEntries(resolve));
            entries = entries.concat(batch);
        } while (batch.length > 0);
        
        for (const childEntry of entries) {
            await scanDirectory(childEntry, files, path + entry.name + '/');
        }
    }
}

// FAZA 3.1 - Validare completă fișiere
function isValidFile(file) {
    // Verifică extensia
    const ext = file.name.split('.').pop().toLowerCase();
    if (!VALID_EXTENSIONS.includes(ext)) {
        return false;
    }
    
    // Verifică mărimea
    if (file.size > MAX_FILE_SIZE) {
        console.warn(`Fișierul ${file.name} depășește limita de ${formatFileSize(MAX_FILE_SIZE)}`);
        return false;
    }
    
    return true;
}

// Procesare fișiere selectate
async function processSelectedFiles(files, source) {
    // Resetează variabilele
    detectedFiles = [];
    detectedStructure = null;
    processedFilesCount = 0;
    totalFilesToProcess = files.length;
    
    // Resetează și arată progresul
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = `Se procesează ${totalFilesToProcess} fișiere...`;
    
    // Dezactivează butonul temporar
    loadDirectoryBtn.disabled = true;
    
    // Filtrare fișiere valide
    const validFiles = files.filter(file => {
        if (!isValidFile(file)) {
            console.warn(`Fișier invalid sau prea mare: ${file.name}`);
            return false;
        }
        return true;
    });
    
    if (validFiles.length === 0) {
        showMsg('⚠️ Nu s-au găsit fișiere valide!', "#ff2929");
        uploadProgress.style.display = 'none';
        return;
    }
    
    // Construiește structura
    const structure = { name: 'root', type: 'folder', children: {}, files: [] };
    
    // Procesează fișierele în batch-uri pentru performanță
    const batchSize = 10;
    for (let i = 0; i < validFiles.length; i += batchSize) {
        const batch = validFiles.slice(i, i + batchSize);
        
        await Promise.all(batch.map(async (file) => {
            try {
                let content = '';
                
                // Citește conținutul pentru fișiere mici
                if (file.size < 1024 * 1024) { // Sub 1MB
                    content = await readFileContent(file);
                } else {
                    content = '[Fișier prea mare - conținutul nu a fost încărcat automat]';
                }
                
                const fileData = {
                    name: file.name,
                    path: file.webkitRelativePath || file.path || file.name,
                    size: file.size,
                    type: getFileType(file.name),
                    content: content
                };
                
                detectedFiles.push(fileData);
                
                // Adaugă în structură
                addFileToStructure(structure, fileData);
                
                // Actualizează progresul
                processedFilesCount++;
                const progress = (processedFilesCount / totalFilesToProcess) * 100;
                progressFill.style.width = progress + '%';
                progressText.textContent = `Procesate ${processedFilesCount} din ${totalFilesToProcess} fișiere`;
                
            } catch (error) {
                console.error(`Eroare la procesarea fișierului ${file.name}:`, error);
            }
        }));
        
        // Permite UI-ului să se actualizeze
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    // Salvează structura detectată
    detectedStructure = structure;
    
    // Finalizare
    progressText.textContent = `✅ Procesate ${validFiles.length} fișiere`;
    
    // Arată preview
    showStructurePreview();
    
    // FAZA 1.1 - Activează butonul doar dacă avem fișiere
    if (detectedFiles.length > 0) {
        loadDirectoryBtn.disabled = false;
        showMsg(`✅ ${detectedFiles.length} fișiere pregătite pentru încărcare`, "#229966");
    } else {
        loadDirectoryBtn.disabled = true;
        showMsg('⚠️ Nu s-au putut procesa fișierele!', "#ff2929");
    }
    
    // Ascunde progresul după 2 secunde
    setTimeout(() => {
        uploadProgress.style.display = 'none';
    }, 2000);
}

// Citire conținut fișier
function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

// Adaugă fișier în structură
function addFileToStructure(structure, fileData) {
    const pathParts = fileData.path.split('/').filter(p => p);
    let current = structure;
    
    // Navighează/creează structura de directoare
    for (let i = 0; i < pathParts.length - 1; i++) {
        const dirName = pathParts[i];
        if (!current.children[dirName]) {
            current.children[dirName] = {
                name: dirName,
                type: 'folder',
                children: {},
                files: []
            };
        }
        current = current.children[dirName];
    }
    
    // Adaugă fișierul
    current.files.push(fileData);
}

// FAZA 4.2 - Parsare structură text îmbunătățită
function parseTreeStructure(treeText) {
    const lines = treeText.split('\n').filter(line => line.trim());
    const root = { name: 'root', type: 'folder', children: {}, files: [] };
    
    if (lines.length === 0) {
        return root;
    }
    
    // Detectează tipul de indentare
    let indentChar = ' ';
    let indentSize = 4;
    
    // Găsește prima linie indentată pentru a detecta stilul
    for (const line of lines) {
        const leadingWhitespace = line.match(/^(\s+)/);
        if (leadingWhitespace) {
            const indent = leadingWhitespace[1];
            if (indent.includes('\t')) {
                indentChar = '\t';
                indentSize = 1;
            } else {
                // Calculează numărul de spații pentru un nivel
                const trimmed = line.trim();
                const level = lines.indexOf(line);
                if (level > 0) {
                    // Găsește prima diferență de indentare
                    for (let i = level - 1; i >= 0; i--) {
                        const prevIndent = lines[i].match(/^(\s*)/)[1].length;
                        const currIndent = indent.length;
                        if (currIndent > prevIndent && prevIndent >= 0) {
                            indentSize = currIndent - prevIndent;
                            break;
                        }
                    }
                }
            }
            break;
        }
    }
    
    const stack = [{ node: root, level: -1 }];
    
    lines.forEach(line => {
        // Calculează nivelul de indentare
        const leadingWhitespace = line.match(/^(\s*)/)[1];
        const level = indentChar === '\t' 
            ? leadingWhitespace.split('\t').length - 1
            : Math.floor(leadingWhitespace.length / indentSize);
        
        // Extrage numele (elimină caracterele de arbore)
        const trimmed = line.trim();
        const name = trimmed.replace(/[│├└─┬┐]/g, '').trim();
        if (!name) return;
        
        // Determină dacă e folder sau fișier
        const isFolder = name.endsWith('/') || name.endsWith('\\');
        const cleanName = isFolder ? name.slice(0, -1) : name;
        
        // Găsește părintele corect
        while (stack.length > 1 && stack[stack.length - 1].level >= level) {
            stack.pop();
        }
        
        const parent = stack[stack.length - 1].node;
        
        if (isFolder || !cleanName.includes('.')) {
            // Presupunem că e folder dacă nu are extensie
            const newFolder = {
                name: cleanName,
                type: 'folder',
                children: {},
                files: []
            };
            parent.children[cleanName] = newFolder;
            stack.push({ node: newFolder, level });
        } else {
            parent.files.push({
                name: cleanName,
                type: getFileType(cleanName),
                size: 0,
                content: ''
            });
        }
    });
    
    return root;
}

// Extrage fișiere din structură
function extractFilesFromStructure(node, path = '') {
    let files = [];
    
    // Adaugă fișierele din nodul curent
    node.files?.forEach(file => {
        files.push({
            ...file,
            path: path ? `${path}/${file.name}` : file.name
        });
    });
    
    // Procesează recursiv subdirectoarele
    Object.entries(node.children || {}).forEach(([name, child]) => {
        const childPath = path ? `${path}/${name}` : name;
        files = files.concat(extractFilesFromStructure(child, childPath));
    });
    
    return files;
}

// Determină tipul fișierului - FAZA 3.1 extins
function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const typeMap = {
        // Python files
        'py': 'python',
        'pyw': 'python',
        'pyx': 'python',
        'pyi': 'python',
        'pyc': 'python',
        'pyd': 'python',
        'pyo': 'python',
        // Web files
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'html': 'web',
        'htm': 'web',
        'css': 'web',
        'scss': 'web',
        'sass': 'web',
        // Config files
        'json': 'config',
        'yml': 'config',
        'yaml': 'config',
        'xml': 'config',
        'ini': 'config',
        'cfg': 'config',
        'toml': 'config',
        // Documentation
        'txt': 'text',
        'md': 'doc',
        'rst': 'doc',
        // Other
        'log': 'text',
        'sh': 'shell',
        'bat': 'batch'
    };
    return typeMap[ext] || 'other';
}

// Afișare preview structură
function showStructurePreview() {
    if (!detectedStructure || !detectedFiles || detectedFiles.length === 0) {
        hideStructurePreview();
        return;
    }
    
    structurePreviewDiv.style.display = 'block';
    
    // Statistici
    const pythonFiles = detectedFiles.filter(f => f.type === 'python');
    const totalSize = detectedFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    
    previewStats.innerHTML = `
        <div class="stat-item">
            <div class="stat-value">${detectedFiles.length}</div>
            <div class="stat-label">Total Fișiere</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${pythonFiles.length}</div>
            <div class="stat-label">Fișiere Python</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${countDirectories(detectedStructure)}</div>
            <div class="stat-label">Directoare</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${formatFileSize(totalSize)}</div>
            <div class="stat-label">Dimensiune Totală</div>
        </div>
    `;
    
    // Arbore
    previewTree.innerHTML = renderTreeHTML(detectedStructure);
    
    // Adaugă event listeners pentru expand/collapse
    previewTree.querySelectorAll('.folder-toggle').forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const folder = e.target.closest('.folder-item');
            folder.classList.toggle('collapsed');
        });
    });
}

// Ascunde preview
function hideStructurePreview() {
    structurePreviewDiv.style.display = 'none';
}

// Randare arbore HTML
function renderTreeHTML(node, level = 0) {
    let html = '';
    
    if (level === 0 && node.name === 'root') {
        // Pentru root, randează doar conținutul
        Object.entries(node.children).forEach(([name, child]) => {
            html += renderTreeHTML(child, level);
        });
        node.files.forEach(file => {
            html += renderFileHTML(file, level);
        });
    } else {
        // Pentru foldere normale
        html += `<div class="folder-item" style="margin-left: ${level * 20}px">
            <span class="folder-toggle">▼</span>
            <span class="folder-icon">📁</span>
            <span class="folder-name">${node.name}</span>
        </div>`;
        
        html += '<div class="folder-contents">';
        
        // Subdirectoare
        Object.entries(node.children || {}).forEach(([name, child]) => {
            html += renderTreeHTML(child, level + 1);
        });
        
        // Fișiere
        (node.files || []).forEach(file => {
            html += renderFileHTML(file, level + 1);
        });
        
        html += '</div>';
    }
    
    return html;
}

// Randare fișier HTML
function renderFileHTML(file, level) {
    const icons = {
        'python': '🐍',
        'javascript': '📜',
        'typescript': '📘',
        'web': '🌐',
        'config': '⚙️',
        'text': '📄',
        'doc': '📝',
        'shell': '🐚',
        'batch': '⚡',
        'other': '📎'
    };
    
    const icon = icons[file.type] || '📎';
    
    return `
        <div class="file-item ${file.type}" style="margin-left: ${level * 20}px">
            <span class="file-icon">${icon}</span>
            <span class="file-name">${file.name}</span>
            ${file.size ? `<span class="file-size">(${formatFileSize(file.size)})</span>` : ''}
        </div>
    `;
}

// Numără directoarele
function countDirectories(node) {
    let count = Object.keys(node.children || {}).length;
    
    Object.values(node.children || {}).forEach(child => {
        count += countDirectories(child);
    });
    
    return count;
}

// Formatare dimensiune fișier
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Încărcare structură în aplicație
loadDirectoryBtn.addEventListener('click', async () => {
    // FAZA 1.1 - Verificare suplimentară
    if (!detectedStructure || !detectedFiles || detectedFiles.length === 0) {
        showMsg('⚠️ Nu există o structură validă de încărcat!', "#ff2929");
        loadDirectoryBtn.disabled = true;
        return;
    }
    
    showMsg('📁 Se încarcă structura de directoare...', "#229966");
    
    // Dezactivează butonul pentru a preveni click-uri multiple
    loadDirectoryBtn.disabled = true;
    
    try {
        // Trimite structura la backend
        const response = await fetch('http://localhost:5000/save_directory_structure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                structure: detectedStructure,
                files: detectedFiles
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'ok') {
            // Salvează ID-ul structurii
            window.currentStructureId = result.structure_id;
            window.currentDirectoryStructure = detectedStructure;
            
            // Afișează file explorer
            showFileExplorer(detectedStructure, detectedFiles);
            
            // Procesează entry points
            if (result.entry_points && result.entry_points.length > 0) {
                const mainEntry = result.entry_points.find(ep => 
                    ['main.py', 'app.py', 'run.py', '__main__.py'].includes(ep.name)
                ) || result.entry_points[0];
                
                // Încarcă automat ca script principal
                await loadEntryPointAsMain(mainEntry);
            }
            
            showMsg(`✅ Structură încărcată: ${result.total_files} fișiere, ${result.python_files} Python`, "#229966");
            
            // Închide modalul
            directoryModal.classList.add('hidden');
            
            // Activează butonul de analiză dacă există
            const analyzeBtn = document.getElementById('analyzeDirectory');
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
            }
            
            // Resetează pentru o nouă încărcare
            detectedStructure = null;
            detectedFiles = [];
            hideStructurePreview();
            
        } else {
            showMsg('❌ Eroare la încărcarea structurii: ' + (result.message || 'Eroare necunoscută'), "#ff2929");
            // Re-activează butonul în caz de eroare
            loadDirectoryBtn.disabled = false;
        }
        
    } catch (err) {
        showMsg('❌ Eroare la comunicarea cu serverul!', "#ff2929");
        console.error('Eroare:', err);
        // Re-activează butonul în caz de eroare
        loadDirectoryBtn.disabled = false;
    }
});

// Afișare file explorer
function showFileExplorer(structure, files) {
    // Verifică dacă există deja un explorer și îl elimină
    const existingExplorer = document.querySelector('.file-explorer');
    if (existingExplorer) {
        existingExplorer.remove();
    }
    
    const explorer = document.createElement('div');
    explorer.className = 'file-explorer';
    explorer.innerHTML = `
        <div class="explorer-header">
            <h3>📁 Explorer Proiect</h3>
            <button class="close-explorer" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="explorer-content">
            ${renderExplorerTree(structure)}
        </div>
        <div class="explorer-actions">
            <button class="analyze-directory-btn" onclick="analyzeDirectoryStructure()">
                🔍 Analizează Structura Completă
            </button>
        </div>
    `;
    
    document.body.appendChild(explorer);
    
    // Event listeners pentru fișiere
    explorer.querySelectorAll('.file-tree-item.file').forEach(item => {
        item.addEventListener('click', async (e) => {
            e.stopPropagation();
            const fileName = item.dataset.filename;
            const filePath = item.dataset.path;
            
            // Găsește fișierul în lista de fișiere
            const fileData = files.find(f => f.path === filePath || f.name === fileName);
            
            if (fileData && fileData.type === 'python') {
                // Încarcă ca script secundar
                const file = new File([fileData.content || ''], fileName, { type: 'text/plain' });
                await handleFileUpload(file, false);
            }
        });
    });
    
    // Event listeners pentru foldere
    explorer.querySelectorAll('.folder-toggle').forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const item = e.target.closest('.file-tree-item');
            item.classList.toggle('collapsed');
            toggle.textContent = item.classList.contains('collapsed') ? '▶' : '▼';
        });
    });
}

// Randare arbore pentru explorer
function renderExplorerTree(node, level = 0, path = '') {
    let html = '';
    
    if (level === 0 && node.name === 'root') {
        // Pentru root, randează doar conținutul
        Object.entries(node.children).forEach(([name, child]) => {
            html += renderExplorerTree(child, level, name);
        });
        node.files.forEach(file => {
            html += renderExplorerFile(file, level, path);
        });
    } else {
        // Pentru foldere normale
        const currentPath = path;
        html += `
            <div class="file-tree-item folder" style="padding-left: ${level * 15}px">
                <span class="folder-toggle">▼</span>
                <span class="file-tree-icon">📁</span>
                <span class="file-tree-name">${node.name}</span>
            </div>
        `;
        
        html += '<div class="folder-children">';
        
        // Subdirectoare
        Object.entries(node.children || {}).forEach(([name, child]) => {
            const childPath = currentPath ? `${currentPath}/${name}` : name;
            html += renderExplorerTree(child, level + 1, childPath);
        });
        
        // Fișiere
        (node.files || []).forEach(file => {
            html += renderExplorerFile(file, level + 1, currentPath);
        });
        
        html += '</div>';
    }
    
    return html;
}

// Randare fișier pentru explorer
function renderExplorerFile(file, level, parentPath) {
    const icons = {
        'python': '🐍',
        'javascript': '📜',
        'typescript': '📘',
        'web': '🌐',
        'config': '⚙️',
        'text': '📄',
        'doc': '📝',
        'shell': '🐚',
        'batch': '⚡',
        'other': '📎'
    };
    
    const icon = icons[file.type] || '📎';
    const fullPath = parentPath ? `${parentPath}/${file.name}` : file.name;
    const clickable = file.type === 'python' ? 'clickable' : '';
    const title = file.type === 'python' ? 'Click pentru a încărca ca script secundar' : file.name;
    
    return `
        <div class="file-tree-item file ${file.type} ${clickable}" 
             style="padding-left: ${(level + 1) * 15}px"
             data-filename="${file.name}"
             data-path="${fullPath}"
             title="${title}">
            <span class="file-tree-icon">${icon}</span>
            <span class="file-tree-name">${file.name}</span>
        </div>
    `;
}

// Încarcă entry point ca script principal
async function loadEntryPointAsMain(entryPoint) {
    try {
        const response = await fetch('http://localhost:5000/get_file_content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                structure_id: window.currentStructureId,
                file_path: entryPoint.path
            })
        });
        
        const data = await response.json();
        if (data.status === 'ok' && data.file) {
            // Creează un obiect File pentru compatibilitate
            const file = new File([data.file.content], data.file.name, { type: 'text/plain' });
            await handleFileUpload(file, true);
            showMsg(`✅ Script principal "${data.file.name}" încărcat automat`, "#229966");
        }
    } catch (err) {
        console.error('Eroare la încărcarea entry point:', err);
    }
}

// Analizare structură completă
window.analyzeDirectoryStructure = async function() {
    if (!window.currentStructureId) {
        showMsg('⚠️ Nu există o structură încărcată!', "#ff2929");
        return;
    }
    
    showMsg('🔍 Se analizează structura de directoare...', "#229966");
    
    try {
        const response = await fetch('http://localhost:5000/analyze_directory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                structure_id: window.currentStructureId,
                options: {
                    deep_analysis: true
                }
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            window.directoryAnalysis = data.analysis;
            
            // Afișează rezultatele analizei
            showDirectoryAnalysisResults(data.analysis);
            
            showMsg(`✅ Analiză completă: ${data.analysis.files_analyzed} fișiere procesate!`, "#229966");
        } else {
            showMsg('❌ Eroare la analiză: ' + data.message, "#ff2929");
        }
    } catch (err) {
        showMsg('❌ Eroare de comunicare cu serverul!', "#ff2929");
        console.error(err);
    }
};

// Afișare rezultate analiză directoare
function showDirectoryAnalysisResults(analysis) {
    // Verifică dacă există deja un modal de analiză și îl elimină
    const existingModal = document.querySelector('.directory-analysis-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.className = 'modal directory-analysis-modal';
    modal.innerHTML = `
        <div class="modal-content analysis-content">
            <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>📊 Rezultate Analiză Directoare</h2>
            
            <div class="analysis-section">
                <h3>📈 Statistici Generale</h3>
                <div class="analysis-stats">
                    <div class="stat">
                        <span class="stat-label">Fișiere analizate:</span>
                        <span class="stat-value">${analysis.files_analyzed}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total funcții:</span>
                        <span class="stat-value">${analysis.total_functions}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total clase:</span>
                        <span class="stat-value">${analysis.total_classes}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total linii:</span>
                        <span class="stat-value">${analysis.total_lines}</span>
                    </div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>🎯 Puncte de Intrare</h3>
                <ul class="entry-points-list">
                    ${analysis.entry_points.map(ep => `
                        <li>
                            <span class="entry-icon">▶️</span>
                            <span class="entry-name">${ep.name}</span>
                            <span class="entry-type">(${ep.type})</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
            
            <div class="analysis-section">
                <h3>🔗 Graf de Dependențe</h3>
                <div class="dependencies-summary">
                    ${Object.entries(analysis.import_graph).map(([file, deps]) => `
                        <div class="dep-item">
                            <strong>${file}</strong>
                            ${deps.imports.length > 0 ? 
                                `<br>↳ importă: ${deps.imports.join(', ')}` : 
                                '<br>↳ nu importă alte module locale'}
                            ${deps.imported_by.length > 0 ? 
                                `<br>↳ importat de: ${deps.imported_by.join(', ')}` : 
                                ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>⚠️ Complexitate</h3>
                <div class="complexity-list">
                    ${Object.entries(analysis.complexity_metrics)
                        .filter(([_, metrics]) => metrics.max > 10)
                        .map(([file, metrics]) => `
                            <div class="complexity-item">
                                <strong>${file}</strong>
                                <span class="complexity-badge ${metrics.max > 20 ? 'high' : 'medium'}">
                                    Max: ${metrics.max}
                                </span>
                            </div>
                        `).join('') || '<p>Nu au fost detectate funcții cu complexitate ridicată.</p>'}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

// Event listener pentru închiderea modalului de încărcare
if (closeDirectoryModal) {
    closeDirectoryModal.addEventListener('click', () => {
        directoryModal.classList.add('hidden');
    });
}

if (cancelDirectoryLoad) {
    cancelDirectoryLoad.addEventListener('click', () => {
        directoryModal.classList.add('hidden');
        // Resetează starea
        detectedStructure = null;
        detectedFiles = [];
        hideStructurePreview();
        loadDirectoryBtn.disabled = true;
    });
}

// Export funcții globale pentru compatibilitate
window.showFileExplorer = showFileExplorer;
window.loadEntryPointAsMain = loadEntryPointAsMain;