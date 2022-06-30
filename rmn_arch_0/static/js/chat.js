const ACTIVE = 'active';
const DSP_NONE = 'dsp-none';
const UNREAD = 'unread';
const ERROR_MSG = 'Network error, please try again later';
const CHAT_NEW = 'chat_new';
const CHAT_MSG = 'chat_message';
const CHAT_READ = 'chat_read';


/**
 * Add given class_ if comp_func evaluate to true for all children of parent
 * @param {Object} parent parent element
 * @param {string} class_ class to be added/removed
 * @param {Object} comp_func function that takes one arguement, child element of parent
 *                              must return a boolean, decides whether class_is added
 */
const toggle_child_class = (parent, class_, comp_func) => {
    for (let child of parent.children) {
        if (comp_func(child)) {
            child.classList.add(class_);
        } else {
            child.classList.remove(class_);
        }
    }
};


/**
 * Individual ChatRoom
 * @param {Object} elem HTML emement of the room
 * @param {Object} chat parent chat object
 */
const ChatRoom = class {
    constructor(elem, chat) {
        this.chat = chat;
        this.id = elem.id;
        this.room = elem;
        this.content = undefined;
        if (elem.getAttribute('data-new-convo')) {
            this.new = true;
            this.init_content();
        } else {
            this.new = false;
        }
        this.chat.user_info_cache[elem.getAttribute('data-username')] = {
            img_url: elem.querySelector('img').src,
            name: elem.querySelector('strong').innerHTML,
        };

        this.room.addEventListener('click', () => this.room_click_handler(), false);
    }

    /**
     * Initialize ChatRoom content and attach apporiate event listeners
     * Requires the content element already present
     */
    init_content() {
        this.content = document.getElementById(`${this.id}_content`);
        this.msgs = this.content.querySelector('.msgs-room-msgs');
        this.input = this.content.querySelector('textarea');
        this.send = this.content.querySelector('button');
        this.input.addEventListener(
            'keydown',
            (event) => this.input_handler(event),
            false,
        );
        this.send.addEventListener(
            'click',
            () => this.send_handler(),
            false,
        );
    }

    /**
     * Change parent chat to not ready, display error message
     * TODO better handle error
     */
    error() {
        if (this.input)
            this.input.value = ERROR_MSG;
        this.chat.ready = false;
    }

    /**
     * Clink the send button if enter is pressed
     * @param {Object} event HTML keydown event
     */
    input_handler(event) {
        if (event.keyCode === 13) {  // enter, return
            event.preventDefault();
            this.send.click();
        }
    }

    /**
     * Send CHAT_READ mesage through websocket, to update last_view status
     */
    msg_read() {
        if (!this.chat.ready)
            return;
        this.chat.ws.send(JSON.stringify({
            from: this.chat.username,
            to: this.id,
            type: CHAT_READ,
            body: "read",
        }));
    }

    /**
     * Send the chat message with apporiate type (CHAT_NEW or CHAT_MSG)
     * if websocket is ready and message is not empty
     */
    async send_handler() {
        if (!this.chat.ready || this.input.value.length === 0)
            return;
        // this.chat.ready = false; // is this necessary?
        this.scroll_to_bottom();
        this.chat.ws.send(JSON.stringify({
            from: this.chat.username,
            to: this.id,
            type: this.new ? CHAT_NEW : CHAT_MSG,
            body: this.input.value,
        }));
        this.input.value = '';
        // this.chat.ready = true;
    }

    /**
     * Handles when user clicking on a ChatRoom
     *      toggles ACTIVE and UNREAD status
     *      initialize the chat cotent if not done already
     *      scroll to the bottom of the chat
     */
    async room_click_handler() {
        toggle_child_class(this.room.parentElement, ACTIVE, (child) => child === this.room);
        this.room.classList.remove(UNREAD);
        this.msg_read();
        if (this.content === undefined) {
            let res = await fetch(
                window.dj_data.urls.chat.chat_content.replace(window.dj_data.url_key, this.id));
            if (!res.ok)
                return this.error();

            const content = document.createElement('div');
            content.innerHTML = await res.text();
            this.chat.room_container.append(content);
            content.replaceWith(...content.childNodes);
            this.init_content();
        }
        toggle_child_class(this.content.parentElement, DSP_NONE, (child) => child !== this.content);
        this.scroll_to_bottom();
    }

    /**
     * Handle new message being send to this ChatRoom
     *      add the message to content if content is initialized
     *      only scroll to bottom if already at bottom
     * @param {Object} content websocket message content
     */
    onmessage(content) {
        this.new = false;
        if (this.content) {
            let scroll = (this.msgs.scrollTop === (this.msgs.scrollHeight - this.msgs.offsetHeight));
            this.build_msg(content);
            if (scroll)
                this.scroll_to_bottom();

            if (this.content.classList.contains(DSP_NONE))
                this.room.classList.add(UNREAD);
            else
                this.msg_read();
        }
        this.room.querySelector('.msg-room-latest').innerHTML = content.body;
        this.chat.room_list.prepend(this.room);
    }

    build_msg(content) {
        const msg = document.createElement('div');
        msg.innerHTML = `
            <div class="msgs-room-msg${(content.from === this.chat.username) ? ' self' : ''}">
                <img src="${this.chat.user_info_cache[content.from].img_url}"
                    alt="Profile Image for ${this.chat.user_info_cache[content.from].name}" class="img-circle m-profile-img">
                <span class="msgs-text">${content.body}</span>
            </div>
        `;
        this.msgs.append(msg);
        msg.replaceWith(...msg.childNodes);
    }

    scroll_to_bottom() {
        this.msgs.scrollTop = (this.msgs.scrollHeight - this.msgs.offsetHeight);
    }
};


/**
 * Chat room, contains websocket connection and ChatRooms
 */
const Chat = class {
    constructor() {
        this.ready = false;
        this.timeout = 500;
        this.connect();
        this.username = JSON.parse(document.getElementById('username').textContent);
        this.user_info_cache = {};
        this.user_info_cache[this.username] = {
            img_url: document.getElementById('profile_image').src,
            name: 'yourself',
        };
        this.room_list = document.getElementById('room_list');
        this.room_container = document.getElementById('room_container');
        this.rooms = {};
        for (let room of this.room_list.children) {
            this.rooms[room.id] = new ChatRoom(room, this);
            if (room.matches(`.${ACTIVE}`))
                room.click();
        }
        if (this.room_list.querySelector(`.${ACTIVE}`) === null
            && this.room_list.children.length !== 0)
            this.room_list.children[0].click();
    }

    /**
     * Wrap websocket connection logic to facilate reconnection
     */
    connect() {
        this.ws = new WebSocket(
            `${window.location.protocol === 'https:' ? 'wss://' : 'ws://'}${window.location.host}/ws/messages/`
        );

        this.ws.onmessage = (event) => {
            const content = JSON.parse(event.data);
            if (!('from' in content) ||
                !('to' in content) ||
                !('type' in content) ||
                !('body' in content))
                return; // ignore if the msg is malformed
            if (!(content.to in this.rooms)) {
                this.build_msgs_room(content);
                this.rooms[content.to] = new ChatRoom(document.getElementById(content.to), this);
            }
            this.rooms[content.to].onmessage(content);
        };

        this.ws.onerror = (err) => {
            console.error('Socket encountered error: ', err.message, 'Closing socket');
            this.ws.close();
        };

        this.ws.onclose = (event) => {
            console.log(`Socket is closed. Reconnect will be attempted in ${this.timeout}ms`, event.reason);
            this.ready = false;
            this.ws = undefined;
            setTimeout(() => this.connect(), this.timeout += this.timeout);
        };

        this.ws.onopen = () => {
            this.ready = true;
            this.timeout = 500;
            let active_room = this.room_list.querySelector(`.${ACTIVE}`);
            if (active_room)
                this.rooms[active_room.id].msg_read();
        };
    }

    /**
     * Builds a new ChatRoom base on websocket message
     * @param {Object} content websocket message content
     */
    build_msgs_room(content) {
        const room = document.createElement('div');
        room.innerHTML = `
            <div class="msgs-room ${UNREAD}" id="${content.to}"
                data-username="${content.user_info.username}">
                <img src="${content.user_info.img_url}" alt="Profile Image for ${content.user_info.name}"
                    class="img-circle m-profile-img">
                <div class="msgs-room-summary">
                    <strong>${content.user_info.name}</strong>
                    <div class="msg-room-latest"></div>
                </div>
            </div>
        `;
        this.room_list.append(room);
        room.replaceWith(...room.childNodes);
    }
};


const chat = new Chat();
