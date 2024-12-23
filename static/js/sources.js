class SourcesHandler {
    constructor() {
        document.body.addEventListener('ws-message', this.handleWebSocketMessge.bind(this));
    }

    handleWebSocketMessge(event) {
        const data = JSON.parse(event.detail.message);
        if (data.type == "sources_update"){
            this.updateSources(data)
        }
    }

    updateSources(data) {
        const knowledgeContent = document.createElement('div');
        if (data.knowledge_sources.length == 0){
            knowledgeContent.innerHTML = `
                <p class="text-gray-500 text-center">No knowledge base entries found</p>
            `
        }
        else {
            data.knowledge_sources.forEach(source => {
                knowledgeContent.innerHTML += this.createKnowledgeSourceHTML(source);
            });
        }
        document.getElementById('knowledge-content').innerHTML = knowledgeContent.innerHTML;

        this.updateActiveTab()
    } 

    createKnowledgeSourceHTML(source) {
        return `
            <div class="mb-4 border-b border-gray-200 pb-4">
                <h4 class="font-semibold text-lg">${this.escapeHTML(source.title)}</h4>
                <p class="mt-1">${this.escapeHTML(source.content_preview)}</p>
                <a href="${this.escapeHTML(source.source_link)}" 
                   class="inline-block mt-2 text-blue-500 hover:text-blue-700"
                   target="_blank" rel="noopener noreferrer">
                    Source Link
                </a>
            </div>
        `;
    }

    updateActiveTab() {
        const activeTab = document.querySelector('#tab-doctors').classList.contains('bg-white') ? 
            'doctors-content' : 'knowledge-content';
        document.getElementById('tab-content').innerHTML = 
            document.getElementById(activeTab).innerHTML;
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    handleTabSwitch(tabId) {
        const contentId = tabId === 'tab-doctors' ? 'doctors-content' : 'knowledge-content';
        document.getElementById('tab-content').innerHTML = 
            document.getElementById(contentId).innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.sourcesHandler = new SourcesHandler();
});