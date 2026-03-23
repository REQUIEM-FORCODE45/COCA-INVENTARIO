class InventoryApp {
    constructor() {
        this.data = [];
        this.filteredData = [];

        this.uploadScreen = document.getElementById('upload-screen');
        this.gridScreen = document.getElementById('grid-screen');
        this.fileInventario = document.getElementById('file-inventario');
        this.filePlantilla = document.getElementById('file-plantilla');
        this.fileInventarioName = document.getElementById('file-inventario-name');
        this.filePlantillaName = document.getElementById('file-plantilla-name');
        this.btnProcess = document.getElementById('btn-process');
        this.uploadError = document.getElementById('upload-error');
        this.dataStatus = document.getElementById('data-status');

        this.searchInput = document.getElementById('search');
        this.filterColumn = document.getElementById('filter-column');
        this.tableBody = document.getElementById('table-body');
        this.totalCount = document.getElementById('total-count');

        this.init();
    }

    init() {
        this.bindEvents();
        this.checkFilesStatus();
    }

    bindEvents() {
        this.fileInventario.addEventListener('change', (e) => this.handleFileSelect(e, 'inventario'));
        this.filePlantilla.addEventListener('change', (e) => this.handleFileSelect(e, 'plantilla'));
        this.btnProcess.addEventListener('click', () => this.uploadFiles());
        document.getElementById('btn-refresh').addEventListener('click', () => this.clearFiles());
        this.searchInput.addEventListener('input', () => this.filter());
        this.filterColumn.addEventListener('change', () => this.filter());
        document.getElementById('filter-diff-real').addEventListener('change', () => this.filter());
    }

    async checkFilesStatus() {
        try {
            const response = await fetch('/api/files/status');
            const result = await response.json();
            
            if (result.has_files) {
                this.dataStatus.textContent = `📁 Archivos cargados (${result.fecha})`;
                this.dataStatus.style.color = '#27ae60';
                await this.loadData();
            } else {
                this.dataStatus.textContent = '';
                this.showUploadScreen();
            }
        } catch (e) {
            this.showUploadScreen();
        }
    }

    handleFileSelect(e, type) {
        const file = e.target.files[0];
        if (file) {
            const nameEl = type === 'inventario' ? this.fileInventarioName : this.filePlantillaName;
            nameEl.textContent = file.name;
        }
        this.checkFilesReady();
    }

    checkFilesReady() {
        const ready = this.fileInventario.files.length > 0 && this.filePlantilla.files.length > 0;
        this.btnProcess.disabled = !ready;
    }

    async uploadFiles() {
        this.uploadError.style.display = 'none';

        try {
            this.btnProcess.disabled = true;
            this.btnProcess.textContent = 'Subiendo...';

            const formData = new FormData();
            formData.append('inventario', this.fileInventario.files[0]);
            formData.append('plantilla', this.filePlantilla.files[0]);

            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Error al subir archivos');
            }

            await this.loadData();
        } catch (error) {
            this.uploadError.textContent = `Error: ${error.message}`;
            this.uploadError.style.display = 'block';
        } finally {
            this.btnProcess.disabled = false;
            this.btnProcess.textContent = 'Procesar Archivos';
        }
    }

    async loadData() {
        try {
            this.tableBody.innerHTML = `<tr><td colspan="14" class="loading">Cargando datos...</td></tr>`;
            
            const response = await fetch('/api/inventario');
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Error al cargar datos');
            }

            this.data = result.data;
            this.filteredData = [...this.data];
            this.showGridScreen();
        } catch (error) {
            this.tableBody.innerHTML = `<tr><td colspan="14" class="loading">Error: ${error.message}</td></tr>`;
            this.showGridScreen();
        }
    }

    async clearFiles() {
        if (!confirm('¿Borrar archivos actuales y cargar nuevos?')) return;
        
        try {
            await fetch('/api/files/clear', { method: 'POST' });
        } catch (e) {}
        
        this.fileInventario.value = '';
        this.filePlantilla.value = '';
        this.fileInventarioName.textContent = '';
        this.filePlantillaName.textContent = '';
        this.btnProcess.disabled = true;
        this.dataStatus.textContent = '';
        this.data = [];
        this.showUploadScreen();
    }

    showUploadScreen() {
        this.uploadScreen.style.display = 'block';
        this.gridScreen.style.display = 'none';
    }

    showGridScreen() {
        this.uploadScreen.style.display = 'none';
        this.gridScreen.style.display = 'block';
        this.render();
    }

    filter() {
        const search = this.searchInput.value.toLowerCase().trim();
        const column = this.filterColumn.value;
        const diffRealFilter = document.getElementById('filter-diff-real').value;

        this.filteredData = this.data.filter(item => {
            if (search) {
                if (column === 'all') {
                    if (!(item.codigo && item.codigo.toLowerCase().includes(search)) &&
                        !(item.nombre && item.nombre.toLowerCase().includes(search))) {
                        return false;
                    }
                } else {
                    if (!(item[column] && item[column].toLowerCase().includes(search))) {
                        return false;
                    }
                }
            }

            if (diffRealFilter !== 'all') {
                const diffU = item.diferencias_reales.unidades;
                const diffSU = item.diferencias_reales.subunidades;
                const totalDiff = diffU + diffSU;

                if (diffRealFilter === 'positive' && totalDiff <= 0) return false;
                if (diffRealFilter === 'negative' && totalDiff >= 0) return false;
            }

            return true;
        });

        this.render();
    }

    render() {
        if (this.filteredData.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="14" class="loading">No hay resultados</td></tr>`;
        } else {
            this.tableBody.innerHTML = this.filteredData.map(item => `
                <tr>
                    <td>${item.codigo || ''}</td>
                    <td>${item.nombre || ''}</td>
                    <td>${item.teorico.unidades}</td>
                    <td>${item.teorico.subunidades}</td>
                    <td>${item.fisico.unidades}</td>
                    <td>${item.fisico.subunidades}</td>
                    <td class="piso-real-col">${item.piso_real.unidades}</td>
                    <td class="piso-real-col">${item.piso_real.subunidades}</td>
                    <td class="${this.getDiferenciaClass(item.diferencias.unidades)}">${item.diferencias.unidades}</td>
                    <td class="${this.getDiferenciaClass(item.diferencias.subunidades)}">${item.diferencias.subunidades}</td>
                    <td class="diferencias-reales-col ${this.getDiferenciaClass(item.diferencias_reales.unidades)}">${item.diferencias_reales.unidades}</td>
                    <td class="diferencias-reales-col ${this.getDiferenciaClass(item.diferencias_reales.subunidades)}">${item.diferencias_reales.subunidades}</td>
                    <td class="liquida-col ${this.getDiferenciaClass(item.ajuste_liquido.unidades)}">${item.ajuste_liquido.unidades}</td>
                    <td class="liquida-col ${this.getDiferenciaClass(item.ajuste_liquido.subunidades)}">${item.ajuste_liquido.subunidades}</td>
                </tr>
            `).join('');
        }
        this.totalCount.textContent = `Total: ${this.filteredData.length} registros`;
    }

    getDiferenciaClass(value) {
        if (value > 0) return 'diferencia-positiva';
        if (value < 0) return 'diferencia-negativa';
        return '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new InventoryApp();
});
