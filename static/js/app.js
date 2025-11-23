let pollInterval;

async function startPolling(gameId) {
    updateGameState(gameId);
    pollInterval = setInterval(() => updateGameState(gameId), 2000);
}

async function updateGameState(gameId) {
    try {
        const res = await fetch(`/api/game/${gameId}/state`);
        if (!res.ok) throw new Error('Failed to fetch state');
        const state = await res.json();
        renderGame(state);
    } catch (err) {
        console.error(err);
    }
}

function renderGame(state) {
    // Update Header
    document.getElementById('round-display').textContent = state.round;

    // Update Shotgun
    document.getElementById('live-count').textContent = state.shotgun.live_shells;
    document.getElementById('blank-count').textContent = state.shotgun.blank_shells;
    document.getElementById('sawed-status').textContent = state.shotgun.is_sawed_off ? "SAWED-OFF" : "NORMAL";
    if (state.shotgun.is_sawed_off) {
        document.getElementById('sawed-status').style.color = "#ff3333";
    } else {
        document.getElementById('sawed-status').style.color = "#e0e0e0";
    }

    // Update Players
    const container = document.getElementById('players-container');
    container.innerHTML = '';

    state.players.forEach(p => {
        const isCurrent = p.id === state.current_player_id;
        const card = document.createElement('div');
        card.className = `player-card ${isCurrent ? 'active' : ''}`;
        if (p.lives <= 0) card.classList.add('dead');

        const itemsHtml = p.items.map(i => `<span class="item-tag">${i}</span>`).join('');
        const livesIcon = '⚡'.repeat(p.lives);

        card.innerHTML = `
            <div class="player-header">
                <span class="name">${p.name} ${isCurrent ? '(TURN)' : ''}</span>
                <span class="lives">${livesIcon}</span>
            </div>
            <div class="player-details">
                <div class="items-list">${itemsHtml || '<span style="color:#555">No Items</span>'}</div>
                ${p.is_skipped ? '<div style="color:orange; margin-top:5px">[HANDCUFFED]</div>' : ''}
            </div>
        `;
        container.appendChild(card);
    });

    // Update Console
    const currentPlayer = state.players.find(p => p.id === state.current_player_id);
    document.getElementById('current-turn-display').textContent =
        `CURRENT TURN: ${currentPlayer.name} (ID: ${currentPlayer.id})`;

    // Update Logs
    const logContainer = document.getElementById('game-log');
    logContainer.innerHTML = '';
    state.logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="timestamp">[${log.timestamp}]</span> <span class="log-msg">${log.message}</span>`;
        logContainer.appendChild(entry);
    });
    // Scroll to bottom
    logContainer.scrollTop = logContainer.scrollHeight;

    // Update Action Buttons
    updateControls(state);
}

async function sendMessage() {
    const input = document.getElementById('admin-message');
    const msg = input.value;
    if (!msg) return;

    try {
        await fetch(`/api/game/${GAME_ID}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        input.value = '';
        updateGameState(GAME_ID);
    } catch (err) { console.error(err); }
}

async function terminateGame() {
    if (!confirm("WARNING: This will forcibly end the game session. Continue?")) return;
    try {
        await fetch(`/api/game/${GAME_ID}/terminate`, { method: 'POST' });
        updateGameState(GAME_ID);
    } catch (err) { console.error(err); }
}

function updateControls(state) {
    const shootContainer = document.getElementById('shoot-targets');
    const itemContainer = document.getElementById('item-buttons');

    shootContainer.innerHTML = '';
    itemContainer.innerHTML = '';

    // Shoot Buttons (Target all living players)
    state.players.forEach(p => {
        if (p.lives > 0) {
            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.textContent = p.id === state.current_player_id ? 'SELF' : `PLAYER ${p.id}`;
            btn.onclick = () => sendAction(GAME_ID, 'shoot', { target_id: p.id });
            shootContainer.appendChild(btn);
        }
    });

    // Item Buttons (Based on current player's inventory)
    const currentPlayer = state.players.find(p => p.id === state.current_player_id);
    if (currentPlayer && currentPlayer.items) {
        const uniqueItems = [...new Set(currentPlayer.items)];
        uniqueItems.forEach(item => {
            const btn = document.createElement('button');
            btn.className = 'btn item-btn';
            btn.textContent = item;
            btn.onclick = () => sendAction(GAME_ID, 'use', { item_name: item });
            itemContainer.appendChild(btn);
        });
    }
}

async function sendAction(gameId, action, payload = {}) {
    try {
        const fullPayload = { action, ...payload };
        const res = await fetch(`/api/game/${gameId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(fullPayload)
        });
        const result = await res.json();
        if (result.success) {
            updateGameState(gameId); // Immediate update
        } else {
            alert(`Action Failed: ${result.message}`);
        }
    } catch (err) {
        console.error(err);
        alert('Communication Error');
    }
}

async function resetGame() {
    if (!confirm("Are you sure you want to reset this session?")) return;
    try {
        await fetch(`/api/game/${GAME_ID}/reset`, { method: 'POST' });
        updateGameState(GAME_ID);
    } catch (err) {
        console.error(err);
    }
}
