<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Code XR - Dynamic Data Dashboard</title>
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- PapaParse for CSV parsing -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>
  <!-- SheetJS for Excel (.xlsx, .xls) parsing -->
  <script src="https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js"></script>

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background-color: #cbd5e1;
      border-radius: 9999px;
    }
  </style>
</head>
<body class="bg-[#F4F7FE] text-slate-800 antialiased min-h-screen">

  <!-- Global Shared File Input for both upload buttons -->
  <input type="file" id="globalCsvFileInput" accept=".csv, .xlsx, .xls" class="hidden" onchange="handleFileUpload(event)">

  <div class="flex min-h-screen">
    
    <!-- ================= SIDEBAR ================= -->
    <aside class="w-64 bg-white border-r border-slate-200/80 p-5 flex flex-col justify-between hidden lg:flex shrink-0">
      <div>
        <div class="flex items-center gap-2.5 px-2 mb-8">
          <div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/30">
            <i data-lucide="layers" class="w-5 h-5"></i>
          </div>
          <span class="text-xl font-bold tracking-tight text-slate-900">Code XR</span>
        </div>

        <nav class="space-y-1">
          <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold bg-blue-50 text-blue-600 transition-all">
            <i data-lucide="layout-grid" class="w-4 h-4"></i> Overview
          </a>
          <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all">
            <i data-lucide="database" class="w-4 h-4"></i> Data Table
          </a>
          <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all">
            <i data-lucide="bar-chart-3" class="w-4 h-4"></i> Analytics
          </a>
          <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all">
            <i data-lucide="settings" class="w-4 h-4"></i> Settings
          </a>
        </nav>
      </div>

      <!-- Quick Upload Widget in Sidebar -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50/50 border border-blue-200/60 rounded-2xl p-4 text-center">
        <div class="w-10 h-10 mx-auto rounded-xl bg-blue-600 text-white flex items-center justify-center mb-2 shadow-sm">
          <i data-lucide="file-spreadsheet" class="w-5 h-5"></i>
        </div>
        <h4 class="text-xs font-bold text-slate-800">Custom Dataset</h4>
        <p class="text-[11px] text-slate-500 mt-1 mb-3">Upload your CSV or Excel file.</p>
        <button onclick="triggerFileInput()" class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all flex items-center justify-center gap-1.5 cursor-pointer">
          <i data-lucide="upload" class="w-3.5 h-3.5"></i> Select File
        </button>
      </div>
    </aside>

    <!-- ================= MAIN CONTENT ================= -->
    <main class="flex-1 flex flex-col overflow-y-auto custom-scrollbar">

      <!-- Header with Upload & File Name -->
      <header class="bg-white/80 backdrop-blur-md sticky top-0 z-30 border-b border-slate-200/80 px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h1 class="text-lg font-bold text-slate-900">Live Data Analytics</h1>
          <p class="text-xs text-slate-400" id="fileStatusLabel">Loaded: Default Sample Dataset</p>
        </div>

        <div class="flex items-center gap-3 w-full sm:w-auto">
          <!-- Top Upload Button -->
          <button onclick="triggerFileInput()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm shadow-blue-500/20 flex items-center gap-2 transition-all cursor-pointer">
            <i data-lucide="upload-cloud" class="w-4 h-4"></i> Upload File (.CSV / .XLSX)
          </button>
          
          <button onclick="resetDefaultData()" class="px-3 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-semibold rounded-xl transition-all cursor-pointer">
            Reset
          </button>
        </div>
      </header>

      <!-- Dashboard Body -->
      <div class="p-6 space-y-6 max-w-7xl mx-auto w-full">

        <!-- Dynamic Stat Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div class="bg-white rounded-2xl p-5 border border-slate-200/70 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Total Entries</span>
              <span class="p-2 bg-blue-50 text-blue-600 rounded-xl">
                <i data-lucide="layers" class="w-4 h-4"></i>
              </span>
            </div>
            <h3 class="text-2xl font-extrabold text-slate-900" id="cardTotalRows">0</h3>
            <p class="text-[11px] text-slate-400 mt-1">Filtered from uploaded records</p>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/70 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Total Value / Revenue</span>
              <span class="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                <i data-lucide="dollar-sign" class="w-4 h-4"></i>
              </span>
            </div>
            <h3 class="text-2xl font-extrabold text-slate-900" id="cardTotalAmount">$0</h3>
            <p class="text-[11px] text-emerald-600 mt-1 font-semibold" id="cardTotalSub">Sum of filtered amounts</p>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/70 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Average Transaction</span>
              <span class="p-2 bg-violet-50 text-violet-600 rounded-xl">
                <i data-lucide="trending-up" class="w-4 h-4"></i>
              </span>
            </div>
            <h3 class="text-2xl font-extrabold text-slate-900" id="cardAvgAmount">$0</h3>
            <p class="text-[11px] text-slate-400 mt-1">Mean per transaction</p>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/70 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Categories</span>
              <span class="p-2 bg-amber-50 text-amber-600 rounded-xl">
                <i data-lucide="pie-chart" class="w-4 h-4"></i>
              </span>
            </div>
            <h3 class="text-2xl font-extrabold text-slate-900" id="cardCategoryCount">0</h3>
            <p class="text-[11px] text-slate-400 mt-1">Unique segments</p>
          </div>

        </div>

        <!-- Dynamic Chart Area -->
        <div class="bg-white rounded-3xl p-6 border border-slate-200/70 shadow-sm">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 class="text-base font-bold text-slate-900">Category Breakdown</h3>
              <p class="text-xs text-slate-400">Auto-calculated from your uploaded file</p>
            </div>
          </div>
          <div class="h-64 w-full">
            <canvas id="categoryChart"></canvas>
          </div>
        </div>

        <!-- Data Filter & Table Container -->
        <div class="bg-white rounded-3xl p-6 border border-slate-200/70 shadow-sm space-y-4">
          
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 class="text-base font-bold text-slate-900">Data Records</h3>
              <p class="text-xs text-slate-400">Search and filter rows instantly</p>
            </div>

            <!-- Filters Toolbar -->
            <div class="flex flex-wrap items-center gap-2">
              
              <!-- Search Input -->
              <div class="relative w-48 sm:w-64">
                <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2"></i>
                <input type="text" id="searchInput" oninput="applyFilters()" placeholder="Search all fields..." class="w-full pl-9 pr-3 py-2 bg-slate-100 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 border border-transparent">
              </div>

              <!-- Category Dropdown Filter -->
              <select id="categoryFilter" onchange="applyFilters()" class="px-3 py-2 bg-slate-100 text-xs font-semibold rounded-xl text-slate-700 border border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
                <option value="ALL">All Categories</option>
              </select>

              <!-- Status Dropdown Filter -->
              <select id="statusFilter" onchange="applyFilters()" class="px-3 py-2 bg-slate-100 text-xs font-semibold rounded-xl text-slate-700 border border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
                <option value="ALL">All Status</option>
              </select>

            </div>
          </div>

          <!-- Responsive Table -->
          <div class="overflow-x-auto custom-scrollbar max-h-96">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="bg-slate-50 sticky top-0 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr id="tableHeaders">
                  <!-- Headers inserted dynamically -->
                </tr>
              </thead>
              <tbody id="tableBody" class="divide-y divide-slate-100 text-slate-700">
                <!-- Rows inserted dynamically -->
              </tbody>
            </table>
          </div>

          <div class="flex items-center justify-between pt-3 text-xs text-slate-500">
            <span id="recordCountLabel">Showing 0 entries</span>
          </div>

        </div>

      </div>
    </main>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    const sampleData = [
      { ID: "TX1001", Name: "Sofia Taylor", Category: "Subscription", Amount: 240, Status: "Completed", Date: "2026-03-01" },
      { ID: "TX1002", Name: "Alex Murphy", Category: "Cloud Hosting", Amount: 1250, Status: "Completed", Date: "2026-03-02" },
      { ID: "TX1003", Name: "John Doe", Category: "Marketing", Amount: 620, Status: "Pending", Date: "2026-03-03" },
      { ID: "TX1004", Name: "Elena Rostova", Category: "Design Assets", Amount: 180, Status: "Completed", Date: "2026-03-04" },
      { ID: "TX1005", Name: "Liam Smith", Category: "Marketing", Amount: 950, Status: "Failed", Date: "2026-03-05" },
      { ID: "TX1006", Name: "Emma Watson", Category: "Cloud Hosting", Amount: 2100, Status: "Completed", Date: "2026-03-06" },
      { ID: "TX1007", Name: "Lucas Gray", Category: "Consulting", Amount: 3400, Status: "Completed", Date: "2026-03-07" },
      { ID: "TX1008", Name: "Zoe Chen", Category: "Subscription", Amount: 490, Status: "Pending", Date: "2026-03-08" }
    ];

    let currentDataset = [...sampleData];
    let chartInstance = null;

    window.addEventListener('DOMContentLoaded', () => {
      lucide.createIcons();
      initChart();
      loadData(sampleData, "Default Sample Dataset");
    });

    // Trigger global file picker
    function triggerFileInput() {
      document.getElementById('globalCsvFileInput').click();
    }

    // Universal File Upload Handler (CSV & Excel)
    function handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const fileName = file.name.toLowerCase();

      if (fileName.endsWith('.csv')) {
        Papa.parse(file, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: function(results) {
            if (results.data && results.data.length > 0) {
              loadData(results.data, file.name);
            } else {
              alert("Uploaded CSV file me data nahi mila.");
            }
          },
          error: function(err) {
            alert("CSV Error: " + err.message);
          }
        });
      } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            const jsonResult = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

            if (jsonResult && jsonResult.length > 0) {
              loadData(jsonResult, file.name);
            } else {
              alert("Excel file empty hai ya format support nahi kar raha.");
            }
          } catch (err) {
            alert("Excel Error: " + err.message);
          }
        };
        reader.readAsArrayBuffer(file);
      } else {
        alert("Kripya sirf valid .csv, .xlsx ya .xls file select karein.");
      }
    }

    function resetDefaultData() {
      loadData(sampleData, "Default Sample Dataset");
      document.getElementById('globalCsvFileInput').value = "";
    }

    function loadData(data, sourceName) {
      currentDataset = data;
      document.getElementById('fileStatusLabel').innerText = "Loaded: " + sourceName;
      populateDropdownFilters();
      applyFilters();
    }

    function populateDropdownFilters() {
      const categorySelect = document.getElementById('categoryFilter');
      const statusSelect = document.getElementById('statusFilter');

      categorySelect.innerHTML = '<option value="ALL">All Categories</option>';
      statusSelect.innerHTML = '<option value="ALL">All Status</option>';

      const categories = new Set();
      const statuses = new Set();

      currentDataset.forEach(row => {
        const cat = row.Category || row.category || row.Department || row.Type;
        const st = row.Status || row.status || row.State;
        if (cat) categories.add(cat);
        if (st) statuses.add(st);
      });

      categories.forEach(c => {
        categorySelect.innerHTML += `<option value="${c}">${c}</option>`;
      });

      statuses.forEach(s => {
        statusSelect.innerHTML += `<option value="${s}">${s}</option>`;
      });
    }

    function applyFilters() {
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      const selectedCategory = document.getElementById('categoryFilter').value;
      const selectedStatus = document.getElementById('statusFilter').value;

      const filtered = currentDataset.filter(row => {
        const rowCategory = row.Category || row.category || row.Department || row.Type || "";
        if (selectedCategory !== "ALL" && String(rowCategory) !== selectedCategory) {
          return false;
        }

        const rowStatus = row.Status || row.status || row.State || "";
        if (selectedStatus !== "ALL" && String(rowStatus) !== selectedStatus) {
          return false;
        }

        if (query) {
          return Object.values(row).some(val => 
            val !== null && val !== undefined && String(val).toLowerCase().includes(query)
          );
        }

        return true;
      });

      renderTable(filtered);
      renderCards(filtered);
      updateChart(filtered);
    }

    function renderTable(data) {
      const headersContainer = document.getElementById('tableHeaders');
      const bodyContainer = document.getElementById('tableBody');
      const recordCountLabel = document.getElementById('recordCountLabel');

      headersContainer.innerHTML = '';
      bodyContainer.innerHTML = '';

      if (data.length === 0) {
        bodyContainer.innerHTML = `<tr><td colspan="100%" class="text-center py-8 text-slate-400">No matching records found.</td></tr>`;
        recordCountLabel.innerText = "Showing 0 entries";
        return;
      }

      const keys = Object.keys(data[0]);
      keys.forEach(k => {
        headersContainer.innerHTML += `<th class="px-4 py-3">${k}</th>`;
      });

      data.forEach(row => {
        let tr = `<tr class="hover:bg-slate-50/80 transition-colors">`;
        keys.forEach(k => {
          let val = row[k] ?? "-";
          
          if (k.toLowerCase() === 'status') {
            let badgeClass = "bg-slate-100 text-slate-700";
            const lower = String(val).toLowerCase();
            if (lower === 'completed' || lower === 'active' || lower === 'paid') badgeClass = "bg-emerald-50 text-emerald-600";
            else if (lower === 'pending') badgeClass = "bg-amber-50 text-amber-600";
            else if (lower === 'failed' || lower === 'cancelled') badgeClass = "bg-rose-50 text-rose-600";
            
            val = `<span class="px-2.5 py-1 rounded-full text-[11px] font-bold ${badgeClass}">${val}</span>`;
          } else if (k.toLowerCase() === 'amount' || k.toLowerCase() === 'price' || k.toLowerCase() === 'revenue') {
            const num = parseFloat(val);
            if (!isNaN(num)) val = `<span class="font-bold text-slate-900">$${num.toLocaleString()}</span>`;
          }

          tr += `<td class="px-4 py-3">${val}</td>`;
        });
        tr += `</tr>`;
        bodyContainer.innerHTML += tr;
      });

      recordCountLabel.innerText = `Showing ${data.length} of ${currentDataset.length} entries`;
    }

    function renderCards(data) {
      document.getElementById('cardTotalRows').innerText = data.length.toLocaleString();

      let totalAmount = 0;
      let validAmountCount = 0;
      const categoriesSet = new Set();

      data.forEach(row => {
        const amountKey = Object.keys(row).find(k => /amount|price|revenue|total|cost|val/i.test(k));
        if (amountKey) {
          const num = parseFloat(row[amountKey]);
          if (!isNaN(num)) {
            totalAmount += num;
            validAmountCount++;
          }
        }

        const cat = row.Category || row.category || row.Department || row.Type;
        if (cat) categoriesSet.add(cat);
      });

      const avgAmount = validAmountCount > 0 ? (totalAmount / validAmountCount) : 0;

      document.getElementById('cardTotalAmount').innerText = '$' + totalAmount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
      document.getElementById('cardAvgAmount').innerText = '$' + avgAmount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
      document.getElementById('cardCategoryCount').innerText = categoriesSet.size;
    }

    function initChart() {
      const ctx = document.getElementById('categoryChart').getContext('2d');
      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [{
            label: 'Total Value ($)',
            data: [],
            backgroundColor: '#2563EB',
            borderRadius: 8,
            barThickness: 32
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: { grid: { display: false } },
            y: { 
              grid: { color: '#F1F5F9' },
              ticks: { callback: v => '$' + v }
            }
          }
        }
      });
    }

    function updateChart(data) {
      if (!chartInstance) return;

      const categoryTotals = {};
      
      data.forEach(row => {
        const cat = row.Category || row.category || row.Department || row.Type || "Uncategorized";
        const amountKey = Object.keys(row).find(k => /amount|price|revenue|total|cost|val/i.test(k));
        let num = 0;
        if (amountKey) {
          num = parseFloat(row[amountKey]) || 0;
        } else {
          num = 1;
        }

        categoryTotals[cat] = (categoryTotals[cat] || 0) + num;
      });

      chartInstance.data.labels = Object.keys(categoryTotals);
      chartInstance.data.datasets[0].data = Object.values(categoryTotals);
      chartInstance.update();
    }
  </script>
</body>
</html>
