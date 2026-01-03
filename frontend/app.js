// Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// Global state
let sessionId = null;
let isRecording = false;
let mediaRecorder = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    loadEquipmentList();
    setupEventListeners();
    checkSystemHealth();
});

// Setup event listeners
function setupEventListeners() {
    const messageInput = document.getElementById('messageInput');
    
    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    
    // Send on Enter (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Session Management
async function initializeSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/session/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionId = data.session_id;
            console.log('Session created:', sessionId);
        } else {
            console.error('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        showError('Failed to initialize session. Please refresh the page.');
    }
}

// Chat Functions
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Show loading indicator
    const loadingId = addLoadingMessage();
    
    // Get settings
    const includePlantData = document.getElementById('includePlantData').checked;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
                include_plant_data: includePlantData
            })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoadingMessage(loadingId);
        
        if (data.success) {
            addMessageToChat('bot', data.response);
        } else {
            addMessageToChat('bot', `Error: ${data.error}`);
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        console.error('Error sending message:', error);
        addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
    }
}

function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${formatMessage(content)}
            <div class="message-timestamp">${timestamp}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(content) {
    // Convert markdown-like formatting to HTML
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert numbered lists
    content = content.replace(/(\d+\.\s.*?)(\n|$)/g, '<li>$1</li>');
    if (content.includes('<li>')) {
        content = '<ol>' + content + '</ol>';
    }
    
    // Convert bullet points
    content = content.replace(/[-•]\s(.*?)(\n|$)/g, '<li>$1</li>');
    if (content.includes('<li>') && !content.includes('<ol>')) {
        content = '<ul>' + content + '</ul>';
    }
    
    // Convert line breaks
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

function addLoadingMessage() {
    const chatMessages = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message bot-message';
    
    loadingDiv.innerHTML = `
        <div class="loading-message">
            <span>Thinking</span>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return loadingId;
}

function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

function fillMessage(text) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = text;
    messageInput.focus();
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    <p>Chat cleared. How can I assist you?</p>
                </div>
            </div>
        `;
        
        // Create new session
        initializeSession();
    }
}

// Equipment Functions
async function loadEquipmentList() {
    const equipmentList = document.getElementById('equipment-list');
    
    try {
        const response = await fetch(`${API_BASE_URL}/equipment`);
        const data = await response.json();
        
        if (data.success && data.equipment.length > 0) {
            equipmentList.innerHTML = '';
            
            data.equipment.forEach(equipment => {
                const card = createEquipmentCard(equipment);
                equipmentList.appendChild(card);
            });
        } else {
            equipmentList.innerHTML = '<p class="loading">No equipment found</p>';
        }
    } catch (error) {
        console.error('Error loading equipment:', error);
        equipmentList.innerHTML = '<p class="loading">Error loading equipment</p>';
    }
}

function createEquipmentCard(equipment) {
    const card = document.createElement('div');
    card.className = `equipment-card status-${equipment.status}`;
    card.onclick = () => showEquipmentDetails(equipment.id);
    
    card.innerHTML = `
        <h4>${equipment.name}</h4>
        <p>${equipment.location}</p>
        <span class="equipment-status ${equipment.status}">
            ${equipment.status.toUpperCase()}
        </span>
    `;
    
    return card;
}

async function showEquipmentDetails(equipmentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/equipment/${equipmentId}`);
        const data = await response.json();
        
        if (data.success) {
            const equipment = data.equipment;
            displayEquipmentModal(equipment);
        }
    } catch (error) {
        console.error('Error fetching equipment details:', error);
        showError('Failed to load equipment details');
    }
}

function displayEquipmentModal(equipment) {
    const modalBody = document.getElementById('modalBody');
    
    let alertsHtml = '';
    if (equipment.status.alerts && equipment.status.alerts.length > 0) {
        alertsHtml = '<div class="detail-section"><h4>Active Alerts</h4>';
        equipment.status.alerts.forEach(alert => {
            alertsHtml += `
                <div class="detail-item">
                    <span class="alert-badge ${alert.severity}">${alert.severity.toUpperCase()}</span>
                    <span>${alert.message}</span>
                </div>
            `;
        });
        alertsHtml += '</div>';
    }
    
    let maintenanceHtml = '';
    if (equipment.maintenance_history && equipment.maintenance_history.length > 0) {
        maintenanceHtml = '<div class="detail-section"><h4>Recent Maintenance</h4>';
        equipment.maintenance_history.slice(0, 3).forEach(record => {
            maintenanceHtml += `
                <div class="detail-item">
                    <div>
                        <div class="detail-label">${record.date}</div>
                        <div>${record.description}</div>
                    </div>
                    <span class="detail-value">${record.duration_hours}h</span>
                </div>
            `;
        });
        maintenanceHtml += '</div>';
    }
    
    modalBody.innerHTML = `
        <h2>${equipment.info.name}</h2>
        <p class="text-secondary mb-2">${equipment.info.location}</p>
        
        <div class="equipment-details">
            <div class="detail-section">
                <h4>Equipment Info</h4>
                <div class="detail-item">
                    <span class="detail-label">Type</span>
                    <span class="detail-value">${equipment.info.type}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status</span>
                    <span class="equipment-status ${equipment.info.status}">
                        ${equipment.info.status.toUpperCase()}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Last Maintenance</span>
                    <span class="detail-value">${equipment.info.last_maintenance}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Sensor Data</h4>
                <div class="detail-item">
                    <span class="detail-label">Temperature</span>
                    <span class="detail-value">${equipment.sensor_data.temperature.toFixed(1)}°C</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Vibration</span>
                    <span class="detail-value">${equipment.sensor_data.vibration.toFixed(2)} mm/s</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Pressure</span>
                    <span class="detail-value">${equipment.sensor_data.pressure.toFixed(1)} bar</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Power</span>
                    <span class="detail-value">${equipment.sensor_data.power_consumption.toFixed(0)} kW</span>
                </div>
            </div>
        </div>
        
        ${alertsHtml}
        ${maintenanceHtml}
        
        <button class="btn btn-primary mt-2" onclick="askAboutEquipment('${equipment.info.name}')">
            Ask about this equipment
        </button>
    `;
    
    document.getElementById('modal').style.display = 'block';
}

function askAboutEquipment(equipmentName) {
    closeModal();
    const messageInput = document.getElementById('messageInput');
    messageInput.value = `Tell me about ${equipmentName} status and any issues`;
    messageInput.focus();
}

// Voice Functions
async function toggleVoiceInput() {
    const voiceBtn = document.getElementById('voiceBtn');
    const enableVoice = document.getElementById('enableVoice').checked;
    
    if (!enableVoice) {
        showError('Please enable voice input in settings first');
        return;
    }
    
    if (!isRecording) {
        startRecording();
        voiceBtn.classList.add('active');
        voiceBtn.textContent = 'Stop';
        isRecording = true;
    } else {
        stopRecording();
        voiceBtn.classList.remove('active');
        voiceBtn.textContent = 'Voice';
        isRecording = false;
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendAudioToServer(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        addMessageToChat('bot', 'Listening... Click the microphone again to stop.');
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        showError('Could not access microphone. Please check permissions.');
        isRecording = false;
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch(`${API_BASE_URL}/voice/speech-to-text`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        removeLoadingMessage(loadingId);
        
        if (data.success && data.text) {
            document.getElementById('messageInput').value = data.text;
            addMessageToChat('bot', `I heard: "${data.text}"`);
        } else {
            addMessageToChat('bot', 'Sorry, I could not understand the audio. Please try again.');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        console.error('Error with speech-to-text:', error);
        showError('Failed to process audio');
    }
}

// Modal Functions
function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
    }
};

// Utility Functions
async function loadSOPs() {
    const modalBody = document.getElementById('modalBody');
    try {
        const response = await fetch(`${API_BASE_URL}/sops/count`);
        const data = await response.json();
        
        modalBody.innerHTML = `
            <h2>SOP Management</h2>
            <p>Manage Standard Operating Procedures for the maintenance assistant.</p>
            
            <div class="detail-section mt-2">
                <h4>Current Status</h4>
                <div class="detail-item">
                    <span class="detail-label">Loaded Documents</span>
                    <span class="detail-value">${data.document_count || 0} chunks</span>
                </div>
            </div>
            
            <div class="mt-2">
                <h4>Upload New SOP</h4>
                <input type="file" id="sopFile" accept=".pdf" class="mt-1">
                <button class="btn btn-primary mt-1" onclick="uploadSOP()">Upload</button>
            </div>
            
            <div class="mt-2">
                <button class="btn btn-secondary" onclick="reloadSOPs()">Reload All SOPs</button>
            </div>
        `;
        
        document.getElementById('modal').style.display = 'block';
    } catch (error) {
        console.error('Error loading SOP info:', error);
    }
}

async function uploadSOP() {
    const fileInput = document.getElementById('sopFile');
    const file = fileInput.files[0];
    if (!file) {
        showError('Please select a PDF file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/sops/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('SOP uploaded successfully!');
            loadSOPs();
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error uploading SOP:', error);
        showError('Failed to upload SOP');
    }
}

async function reloadSOPs() {
    try {
        const response = await fetch(`${API_BASE_URL}/sops/reload`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`SOPs reloaded! ${data.document_count} chunks loaded.`);
            closeModal();
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error reloading SOPs:', error);
        showError('Failed to reload SOPs');
    }
}

async function showStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        if (data.success) {
            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = `
                <h2>System Statistics</h2>
                
                <div class="equipment-details mt-2">
                    <div class="detail-section">
                        <h4>Sessions</h4>
                        <div class="detail-item">
                            <span class="detail-label">Active Sessions</span>
                            <span class="detail-value">${data.stats.active_sessions}</span>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Knowledge Base</h4>
                        <div class="detail-item">
                            <span class="detail-label">SOP Documents</span>
                            <span class="detail-value">${data.stats.sop_documents}</span>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Equipment</h4>
                        <div class="detail-item">
                            <span class="detail-label">Total Equipment</span>
                            <span class="detail-value">${data.stats.equipment_count}</span>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('modal').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showError('Failed to load statistics');
    }
}

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        const statusElement = document.querySelector('.status span:last-child');
        const statusDot = document.querySelector('.status-dot');
        
        if (data.status === 'healthy') {
            statusElement.textContent = 'Connected';
            statusDot.style.backgroundColor = 'var(--success-color)';
        } else {
            statusElement.textContent = 'Issues Detected';
            statusDot.style.backgroundColor = 'var(--warning-color)';
        }
    } catch (error) {
        const statusElement = document.querySelector('.status span:last-child');
        const statusDot = document.querySelector('.status-dot');
        statusElement.textContent = 'Disconnected';
        statusDot.style.backgroundColor = 'var(--danger-color)';
    }
}

function showError(message) {
    addMessageToChat('bot', `${message}`);
}

// Refresh equipment list every 30 seconds
setInterval(loadEquipmentList, 30000);
// Check health every 60 seconds
setInterval(checkSystemHealth, 60000);