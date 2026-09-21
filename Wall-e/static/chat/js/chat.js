/* ========================================================================
   Wall-e — ChatGPT-clone interactive JS
   ======================================================================== */

class ChatApp {
    constructor(config) {
        this.conversationId = config.conversationId;
        this.csrfToken = config.csrfToken;

        // Cache DOM elements
        this.$input       = document.getElementById('message-input');
        this.$sendBtn     = document.getElementById('send-btn');
        this.$form        = document.getElementById('message-form');
        this.$messages    = document.getElementById('messages-container');
        this.$typing      = document.getElementById('typing-indicator');

        this.isSending    = false;
        this.init();
    }

    /* ===== Initialization ===== */
    init() {
        if (!this.$input || !this.$form) return;

        // Auto-resize textarea
        this.$input.addEventListener('input', () => this._onInput());

        // Submit via form or Enter key
        this.$form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        this.$input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Focus input on page load
        setTimeout(() => this.$input.focus(), 100);
    }

    _onInput() {
        // Auto-resize the textarea
        this.$input.style.height = 'auto';
        this.$input.style.height = Math.min(this.$input.scrollHeight, 120) + 'px';

        // Enable / disable the send button
        const hasText = this.$input.value.trim().length > 0;
        this.$sendBtn.disabled = !hasText || this.isSending;
    }

    /* ===== Messaging ===== */
    async sendMessage() {
        const message = this.$input.value.trim();
        if (!message || this.isSending) return;

        this.isSending = true;
        this.$sendBtn.disabled = true;
        this.$input.value = '';
        this._onInput(); // update button state

        // Render user message immediately
        this.addMessage('user', message);

        // Show typing indicator
        this.showTyping(true);

        try {
            const response = await fetch(`/chat/${this.conversationId}/send/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken':    this.csrfToken,
                    'Content-Type':   'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: `message=${encodeURIComponent(message)}`,
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.addMessage('assistant', data.response || '(no reply)');
        } catch (err) {
            this.addMessage('assistant',
                `Sorry, I ran into an error: ${err.message}`);
        } finally {
            this.isSending = false;
            this._onInput();
            this.showTyping(false);
            this.$input.focus();
        }
    }

    /* ===== Rendering helpers ===== */
    addMessage(role, content) {
        const wrapper = document.createElement('div');
        wrapper.className = `message ${role}`;
        wrapper.innerHTML = `
            <div class="avatar">${role === 'assistant' ? '🤖' : '👤'}</div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;
        this.$messages.appendChild(wrapper);
        this.scrollToBottom();
    }

    showTyping(show) {
        if (!this.$typing) return;
        this.$typing.classList.toggle('show', show);
        if (show) this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.$messages) {
            this.$messages.scrollTop = this.$messages.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

/* ===== Auto-init ===== */
document.addEventListener('DOMContentLoaded', () => {
    if (window.WALL_E_CONFIG) {
        new ChatApp(window.WALL_E_CONFIG);
    }
});