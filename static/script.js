const socket = io();
let myGroup = null;

// Generate 36 Tiles on Load
const grid = document.getElementById('grid');
for (let i = 1; i <= 36; i++) {
    let div = document.createElement('div');
    div.id = `topic-${i}`;
    div.className = 'tile';
    div.innerHTML = `Topic ${i} <br><span id="status-${i}">Available</span>`;
    div.onclick = () => selectTopic(i);
    grid.appendChild(div);
}

// 1. Enter Dashboard
function enterDashboard() {
    const input = document.getElementById('group-input').value;
    const error = document.getElementById('login-error');
    
    if (input < 1 || input > 35 || input === "") {
        error.innerText = "Please enter a valid Group Number (1-35)";
        return;
    }
    
    myGroup = input;
    document.getElementById('display-group').innerText = `Group ${myGroup}`;
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('dashboard-screen').classList.remove('hidden');
}

// 2. Select Topic
function selectTopic(topicNum) {
    if (!myGroup) return;
    socket.emit('select_topic', { group_number: myGroup, topic_number: topicNum });
}

// --- SOCKET LISTENERS ---

// Initial Load: Color the grid based on DB state
socket.on('initial_state', (topics) => {
    topics.forEach(t => {
        if (t.group_number) {
            markTaken(t.topic_number, t.group_number);
        }
    });
});

// Real-time Update: Someone picked a topic
socket.on('update_tile', (data) => {
    markTaken(data.topic_number, data.group_number);
});

// Reset Event: Clear board
socket.on('reset_event', () => {
    for (let i = 1; i <= 36; i++) {
        let tile = document.getElementById(`topic-${i}`);
        tile.className = 'tile'; // Remove 'taken' class
        document.getElementById(`status-${i}`).innerText = "Available";
    }
    alert("System has been reset by Admin.");
});

// Error Handling
socket.on('error_message', (data) => {
    alert(data.msg);
});

// Helper to update UI
function markTaken(topicNum, groupNum) {
    let tile = document.getElementById(`topic-${topicNum}`);
    let status = document.getElementById(`status-${topicNum}`);
    
    tile.classList.add('taken');
    
    if (groupNum == myGroup) {
        tile.classList.add('taken-by-me');
        status.innerText = "Selected by YOU";
    } else {
        status.innerText = `Taken by Group ${groupNum}`;
    }
}

// Admin Functions
function toggleAdmin() {
    document.getElementById('admin-modal').classList.toggle('hidden');
}

function resetSystem() {
    const password = document.getElementById('admin-pass').value;
    fetch('/reset', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ password: password })
    })
    .then(res => res.json())
    .then(data => {
        if(!data.success) alert(data.message);
        toggleAdmin();
    });
}