var app;

document.addEventListener("DOMContentLoaded", () => {
    app = new App();
});

class App {
    #agents = [];
    #messages = [];
    #selectedAgent = null;
    #createAgentModal;
    #settingsModal;

    constructor() {
        this.#init();
    }

    #init() {
        this.#createAgentModal = new CreateAgentModal(this.#onCreateAgent.bind(this));
        this.#settingsModal = new SettingsModal(this.#onDeleteAgent.bind(this));
        this.#addEventListeners();
        this.#loadAgents();
    }

    #addEventListeners() {
        let addAgentButton = document.getElementById("add-agent-btn");
        addAgentButton.addEventListener("click", this.#onAddAgentClick.bind(this));
        let sendMessageButton = document.getElementById("send-btn");
        sendMessageButton.addEventListener("click", this.#onSendMessageClick.bind(this));
        let settingsButton = document.getElementById("setting-btn");
        settingsButton.addEventListener("click", this.#onSettingsClick.bind(this));
    }

    #loadAgents() {
        fetch("/api/agents")
            .then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to load agents!");
                    return;
                }
                let agents = data["agents"];
                agents = agents.map(agent => AgentMapper.map(agent));
                agents.forEach(agent => {
                    this.#agents.push(agent);
                });
                if (agents.length > 0) {
                    this.#selectedAgent = agents[0];
                    this.#loadMessages(this.#selectedAgent.id);
                }
                this.#renderAgents();
                this.#renderMessages();
                this.#renderChatHeader();
            }).catch(error => {
                console.error("Failed to load agents!", error);
            });
    }

    #loadMessages(agentId) {
        let messages = MessagesPersistantStorage.load(agentId);
        this.#messages = messages;
    }

    #saveMessages() {
        if (this.#selectedAgent && this.#messages.length > 0) {
            MessagesPersistantStorage.save(this.#messages, this.#selectedAgent.id);
        }
    }

    #renderAgents() {
        if (this.#agents.length == 0) {
            return;
        }
        let agentsList = document.getElementById("agents-list");
        agentsList.innerHTML = "";
        this.#agents.forEach(agent => {
            agentsList.innerHTML += agent.renderHTML();
        });

        if (!this.#selectedAgent) {
            this.#selectedAgent = this.#agents[0];
        }
        this.#markAgentAsSelected(this.#selectedAgent);

        let agentContainers = document.getElementsByClassName("agent-container");
        for (let i = 0; i < agentContainers.length; i++) {
            agentContainers[i].addEventListener("click", this.#onAgentClick.bind(this));
        }
    }

    #markAgentAsSelected(agent) {
        if (!agent) {
            return;
        }
        let agentContainer = document.getElementById(`agent-container-${agent.id}`);
        if (agentContainer) {
            agentContainer.classList.add("active");
        }
    }

    #unmarkAgentAsSelected(agent) {
        if (!agent) {
            return;
        }
        let agentContainer = document.getElementById(`agent-container-${agent.id}`);
        if (agentContainer) {
            agentContainer.classList.remove("active");
        }
    }

    #renderChatHeader() {
        let chatHeaderTitle = document.getElementById("chat-header-title");
        let settingsButton = document.getElementById("setting-btn");
        if (this.#selectedAgent) {
            chatHeaderTitle.innerHTML = this.#selectedAgent.name;
            chatHeaderTitle.style.display = "block";
            settingsButton.style.display = "block";
        } else {
            chatHeaderTitle.style.display = "none";
            settingsButton.style.display = "none";
        }
    }

    #renderMessages() {
        let messagesContainer = document.getElementById("chat-list");
        messagesContainer.innerHTML = "";
        this.#messages.forEach(message => {
            messagesContainer.innerHTML += message.renderHTML();
        });
    }

    // Event handlers
    #onAgentClick(event) {
        let agentId = parseInt(event.currentTarget.id.split("-")[2]);
        let agent = this.#agents.find(agent => agent.id === agentId);
        if (agent && agent != this.#selectedAgent) {
            if (this.#selectedAgent) {
                this.#saveMessages();
            }
            this.#unmarkAgentAsSelected(this.#selectedAgent);
            this.#selectedAgent = agent;
            this.#markAgentAsSelected(this.#selectedAgent);
            this.#loadMessages(agent.id);
            this.#renderMessages();
            this.#renderChatHeader();
        }
    }

    #onAddAgentClick() {
        this.#createAgentModal.show();
    }

    #onSendMessageClick() {
        let chatInput = document.getElementById("chat-input");
        let body = chatInput.value;
        if (body == "") {
            return;
        }
        chatInput.value = "";
        let message = new OutgoingMessage(body, null);
        this.#messages.unshift(message);
        this.#saveMessages();
        this.#renderMessages();
        fetch(`/api/agents/${this.#selectedAgent.id}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(MessageMapper.toJSON(message))
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to send message!");
                    return;
                }
                let message = MessageMapper.map(data["message"]);
                this.#messages.unshift(message);
                this.#saveMessages();
                this.#renderMessages();
            }).catch(error => {
                console.error("Failed to send message!", error);
            });
    }

    #onSettingsClick() {
        this.#settingsModal.show(this.#selectedAgent);
    }

    // Create agent modal handlers
    #onCreateAgent(name, description) {
        let agent = new Agent(null, name, description);
        fetch("/api/agents", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(AgentMapper.toJSON(agent))
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to create agent!");
                    return;
                }
                let agent = AgentMapper.map(data["agent"]);
                this.#agents.push(agent);
                this.#renderAgents();
                this.#renderChatHeader();
            }).catch(error => {
                console.error("Failed to create agent!", error);
            });
    }

    // Settings modal handlers
    #onDeleteAgent(agentId) {
        fetch(`/api/agents/${agentId}`, {
            method: "DELETE"
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to delete agent!");
                    return;
                }
                let agent = this.#agents.find(agent => agent.id === agentId);
                if (agent) {
                    let index = this.#agents.indexOf(agent);
                    this.#agents.splice(index, 1);
                }
                if (this.#selectedAgent) {
                    this.#selectedAgent = null;
                    if (this.#agents.length > 0) {
                        this.#selectedAgent = this.#agents[0];
                        this.#loadMessages(this.#selectedAgent.id);
                    } else {
                        this.#messages = [];
                    }
                    this.#renderMessages();
                    this.#renderChatHeader();
                }
                this.#renderAgents();
            }).catch(error => {
                console.error("Failed to delete agent!", error);
            }).finally(() => {
                this.#settingsModal.hide();
            });
    }
}

class Agent {
    id;
    name;
    description;

    constructor(id, name, description) {
        this.id = id;
        this.name = name;
        this.description = description;
    }

    renderHTML() {
        return `
            <div class="agent-container" id="agent-container-${this.id}">
                <img class="agent-avatar" src="/static/images/agent_avatar.png"></img>
                <div class="agent-info-container">
                    <p class="agent-name">${this.name}</p>
                    <p class="agent-description">${this.description}</p>
                </div>
            </div>
        `;
    }
}

class AgentMapper {
    static map(data) {
        return new Agent(data.id, data.name, data.description);
    }

    static toJSON(agent) {
        return {
            name: agent.name,
            description: agent.description
        };
    }
}

class Message {
    body;
    senderId;

    constructor(body, senderId) {
        this.body = body;
        this.senderId = senderId;
    }
}

class IncomingMessage extends Message {
    constructor(body, senderId) {
        super(body, senderId);
    }

    renderHTML() {
        return `
            <div class="incomig-message-container">
                <div class="incoming-message-avatar">
                    <img src="/static/images/agent_avatar.png"></img>
                </div>
                <div class="incoming-message-bubble">
                    <p class="incoming-message-text">${this.body}</p>
                </div>
            </div>
        `;
    }
}

class OutgoingMessage extends Message {
    constructor(body, senderId) {
        super(body, senderId);
    }

    renderHTML() {
        return `
            <div class="outgoing-message-container">
                <div class="outgoing-message-bubble">
                    <p class="outgoing-message-text">${this.body}</p>
                </div>
            </div>
        `;
    }
}

class MessageMapper {
    static map(data) {
        if (data.agent_id) {
            return new IncomingMessage(data.body, data.agent_id);
        } else {
            return new OutgoingMessage(data.body, null);
        }
    }

    static toJSON(message) {
        return {
            body: message.body
        };
    }

    static toStorageJSON(message) {
        return {
            body: message.body,
            agent_id: message.senderId
        };
    }
}

class MessagesPersistantStorage {
    static save(messages, agentId) {
        let key = `agent-${agentId}-messages`;
        messages = messages.map(message => MessageMapper.toStorageJSON(message));
        localStorage.setItem(key, JSON.stringify(messages));
    }

    static load(agentId) {
        let key = `agent-${agentId}-messages`;
        let messages = localStorage.getItem(key);
        if (!messages) {
            return [];
        }
        return JSON.parse(messages).map(message => MessageMapper.map(message));
    }
}

class ContentItem {
    id;
    name;
    type;

    constructor(id, name, type) {
        this.id = id;
        this.name = name;
        this.type = type;
    }
}

class FileContentItem extends ContentItem {
    constructor(id, name, type) {
        super(id, name, type);
    }

    renderHTML() {
        return `
            <div class="content-item">
                <div class="content-item-picture">
                    <img src="/static/images/file_icon.png"></img>
                </div>
                <div class="content-item-name">
                    <p class="content-item-name-text">${this.name}</p>
                </div>
                <div class="content-item-delete">
                    <button class="btn-icon" id="content-item-delete-btn-${this.id}" value="${this.id}">
                        <img src="/static/images/delete_icon.png"></img>
                    </button>
                </div>
            </div>
        `;
    }
}

class WebsiteContentItem extends ContentItem {
    constructor(id, name, type) {
        super(id, name, type);
    }

    renderHTML() {
        return `
            <div class="content-item">
                <div class="content-item-picture">
                    <img src="/static/images/web_icon.png"></img>
                </div>
                <div class="content-item-name">
                    <p class="content-item-name-text">${this.name}</p>
                </div>
                <div class="content-item-delete">
                    <button class="btn-icon" id="content-item-delete-btn-${this.id}" value="${this.id}">
                        <img src="/static/images/delete_icon.png"></img>
                    </button>
                </div>
            </div>
        `;
    }
}

class ContentItemMapper {
    static map(data) {
        if (data.type == "webpage") {
            return new WebsiteContentItem(data.id, data.name, data.type);
        } else {
            return new FileContentItem(data.id, data.name, data.type);
        }
    }

    static toJSON(contentItem) {
        return {
            name: contentItem.name,
            type: contentItem.type
        };
    }
}

// Modal Views

class CreateAgentModal {
    modal;
    nameInput;
    descriptionInput;
    createButton;
    cancelButton;
    createCallback;

    constructor(createCallback) {
        this.createCallback = createCallback;
        this.#init();
    }

    #init() {
        this.modal = document.getElementById("create-agent-modal");
        this.createButton = document.getElementById("create-agent-create-btn");
        this.cancelButton = document.getElementById("create-agent-cancel-btn");
        this.nameInput = document.getElementById("create-agent-name-input");
        this.descriptionInput = document.getElementById("create-agent-description-input");

        this.#addEventListeners();
    }

    show() {
        this.modal.style.display = "flex";
        window.onclick = function (event) {
            if (event.target == this.modal) {
                this.hide();
            }
        }.bind(this);
    }

    hide() {
        this.modal.style.display = "none";
        window.onclick = null;
    }

    #addEventListeners() {
        this.createButton.addEventListener("click", this.#onCreateClick.bind(this));
        this.cancelButton.addEventListener("click", this.#onCancelClick.bind(this));
    }

    #onCreateClick() {
        let name = this.nameInput.value;
        let description = this.descriptionInput.value;
        if (name == "" || description == "") {
            return;
        }
        if (this.createCallback) {
            this.createCallback(name, description);
        }
    }

    #onCancelClick() {
        let modal = document.getElementById("create-agent-modal");
        modal.style.display = "none";
        window.onclick = null;
    }
}

class SettingsModal {
    modal;
    agent;
    deleteAgentCallback;
    nameText;
    descriptionText;
    deleteAgentButton;
    uploadFileButton;
    fileInput;
    uploadWebpageButton;
    webpageInput;
    contentItemsContainer;
    contentItems = [];

    constructor(deleteAgentCallback) {
        this.deleteAgentCallback = deleteAgentCallback;
        this.#init();
    }

    #init() {
        this.modal = document.getElementById("agent-settings-modal");
        this.nameText = document.getElementById("agent-settings-name-text");
        this.descriptionText = document.getElementById("agent-settings-description-text");
        this.deleteAgentButton = document.getElementById("agent-settings-delete-agent-btn");
        this.uploadFileButton = document.getElementById("add-file-btn");
        this.uploadWebpageButton = document.getElementById("add-website-btn");
        this.fileInput = document.getElementById("add-file-input");
        this.webpageInput = document.getElementById("add-website-input");
        this.contentItemsContainer = document.getElementById("content-items-container");

        this.#addEventListeners();
    }

    show(agent) {
        if (!agent) {
            return;
        }
        this.agent = agent;
        this.contentItems = [];
        this.nameText.innerHTML = this.agent.name;
        this.descriptionText.innerHTML = this.agent.description;
        this.fileInput.value = "";
        this.webpageInput.value = "";
        this.modal.style.display = "flex";
        this.#loadContentItems();
        window.onclick = function (event) {
            if (event.target == this.modal) {
                this.hide();
            }
        }.bind(this);
    }

    hide() {
        this.modal.style.display = "none";
        window.onclick = null;
    }

    #addEventListeners() {
        this.deleteAgentButton.addEventListener("click", this.#onDeleteAgentClick.bind(this));
        this.uploadFileButton.addEventListener("click", this.#onUploadFileClick.bind(this));
        this.uploadWebpageButton.addEventListener("click", this.#onUploadWebpageClick.bind(this));
    }

    #onDeleteAgentClick() {
        if (this.deleteAgentCallback) {
            this.deleteAgentCallback(this.agent.id);
        }
    }

    #onUploadFileClick() {
        let file = this.fileInput.files[0];
        if (!file) {
            return;
        }
        this.fileInput.value = "";
        let formData = new FormData();
        formData.append("file", file);
        fetch(`/api/agents/${this.agent.id}/file`, {
            method: "POST",
            body: formData
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to upload file!");
                    return;
                }
                let contentItem = ContentItemMapper.map(data["content"]);
                this.contentItems.push(contentItem);
                this.#renderContentItems(this.contentItems);
            }).catch(error => {
                console.error("Failed to upload file!", error);
            });
    }

    #onUploadWebpageClick() {
        let url = this.webpageInput.value;
        if (url == "") {
            return;
        }
        this.webpageInput.value = "";
        fetch(`/api/agents/${this.agent.id}/webpage`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                webpage_url: url
            })
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to upload webpage!");
                    return;
                }
                let contentItem = ContentItemMapper.map(data["content"]);
                this.contentItems.push(contentItem);
                this.#renderContentItems(this.contentItems);
            }).catch(error => {
                console.error("Failed to upload webpage!", error);
            });
    }

    #onDeleteContentItemClick(event) {
        let contentItemId = parseInt(event.currentTarget.value);
        fetch(`/api/agents/${this.agent.id}/content/${contentItemId}`, {
            method: "DELETE"
        }).then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to delete content item!");
                    return;
                }
                let contentItem = this.contentItems.find(contentItem => contentItem.id === contentItemId);
                if (contentItem) {
                    let index = this.contentItems.indexOf(contentItem);
                    this.contentItems.splice(index, 1);
                }
                this.#renderContentItems(this.contentItems);
            }).catch(error => {
                console.error("Failed to delete content item!", error);
            });
    }

    #renderContentItems(contentItems) {
        this.contentItemsContainer.innerHTML = "";
        contentItems.forEach(contentItem => {
            this.contentItemsContainer.innerHTML += contentItem.renderHTML();
            // Add event listener to delete button
            let deleteButton = document.getElementById(`content-item-delete-btn-${contentItem.id}`);
            deleteButton.addEventListener("click", this.#onDeleteContentItemClick.bind(this));
        });
    }

    #loadContentItems() {
        fetch(`/api/agents/${this.agent.id}/content`)
            .then(response => response.json())
            .then(data => {
                if (data["status"] != "success") {
                    console.error("Failed to load content items!");
                    return;
                }
                let contentItems = data["content"];
                contentItems = contentItems.map(contentItem => ContentItemMapper.map(contentItem));
                this.contentItems = contentItems
                this.#renderContentItems(contentItems);
            }).catch(error => {
                console.error("Failed to load content items!", error);
            });
    }
}