// Global variables
let scanData = [];

// DOM Elements
const scanButton = document.getElementById('scanButton');
const exportButton = document.getElementById('exportButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsContainer = document.getElementById('resultsContainer');
const statsContainer = document.getElementById('statsContainer');
const resultsTableBody = document.getElementById('resultsTableBody');
const alertContainer = document.getElementById('alertContainer');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeIcon.classList.remove('bi-moon-fill');
        themeIcon.classList.add('bi-sun-fill');
    }
}

// Toggle theme
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');

    if (document.body.classList.contains('dark-theme')) {
        themeIcon.classList.remove('bi-moon-fill');
        themeIcon.classList.add('bi-sun-fill');
        localStorage.setItem('theme', 'dark');
    } else {
        themeIcon.classList.remove('bi-sun-fill');
        themeIcon.classList.add('bi-moon-fill');
        localStorage.setItem('theme', 'light');
    }
});

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.appendChild(alertDiv);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Show loading state
function showLoading() {
    scanButton.disabled = true;
    exportButton.disabled = true;
    loadingSpinner.style.display = 'block';
    resultsContainer.style.display = 'none';
    statsContainer.style.display = 'none';
}

// Hide loading state
function hideLoading() {
    scanButton.disabled = false;
    loadingSpinner.style.display = 'none';
}

// Update statistics
function updateStatistics(totalEntries, regionsScanned) {
    // Count unique VPCs
    const uniqueVpcs = new Set(scanData.map(item => item.vpc_id)).size;

    document.getElementById('totalEntries').textContent = totalEntries;
    document.getElementById('uniqueVpcs').textContent = uniqueVpcs;
    document.getElementById('regionsScanned').textContent = regionsScanned;

    statsContainer.style.display = 'block';
}

// Populate results table
function populateTable(data) {
    resultsTableBody.innerHTML = '';

    if (data.length === 0) {
        resultsTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    No VPCs or Subnets found in any region.
                </td>
            </tr>
        `;
        return;
    }

    data.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.region || '-'}</td>
            <td><code>${item.vpc_id || '-'}</code></td>
            <td>${item.vpc_name || '-'}</td>
            <td><code>${item.vpc_cidr || '-'}</code></td>
            <td><code>${item.subnet_id || '-'}</code></td>
            <td>${item.subnet_name || '-'}</td>
            <td><code>${item.subnet_cidr || '-'}</code></td>
        `;

        // Add subtle animation
        row.style.animation = `fadeIn 0.3s ease ${index * 0.02}s`;
        resultsTableBody.appendChild(row);
    });

    resultsContainer.style.display = 'block';
}

// Scan AWS Infrastructure
scanButton.addEventListener('click', async () => {
    try {
        showLoading();
        showAlert('Starting AWS infrastructure scan...', 'info');

        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            scanData = result.data;
            populateTable(scanData);
            updateStatistics(result.total_entries, result.regions_scanned);
            exportButton.disabled = false;

            showAlert(
                `Scan completed successfully! Found ${result.total_entries} entries across ${result.regions_scanned} regions.`,
                'success'
            );
        } else {
            showAlert(`Error: ${result.error}`, 'danger');
        }
    } catch (error) {
        showAlert(`Failed to scan AWS infrastructure: ${error.message}`, 'danger');
        console.error('Scan error:', error);
    } finally {
        hideLoading();
    }
});

// Export to CSV
exportButton.addEventListener('click', async () => {
    try {
        exportButton.disabled = true;
        showAlert('Generating CSV report...', 'info');

        const response = await fetch('/api/export');

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aws_vpc_subnet_report_${new Date().getTime()}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showAlert('CSV report downloaded successfully!', 'success');
        } else {
            const error = await response.json();
            showAlert(`Export failed: ${error.error}`, 'danger');
        }
    } catch (error) {
        showAlert(`Failed to export CSV: ${error.message}`, 'danger');
        console.error('Export error:', error);
    } finally {
        exportButton.disabled = false;
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    console.log('AWS VPC & Subnet Extraction Tool loaded successfully');
});

// Add CSS animation for table rows
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
