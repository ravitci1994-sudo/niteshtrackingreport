<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Fleet Operations Command Center</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- SheetJS (xlsx parser) -->
  <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

  <!-- React 18 & ReactDOM -->
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>

  <!-- Babel Standalone for JSX -->
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <!-- Framer Motion -->
  <script src="https://unpkg.com/framer-motion@10.16.4/dist/framer-motion.js"></script>

  <!-- Inter Font -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace'],
          },
          colors: {
            wine: {
              950: '#080103',
              900: '#140207',
              850: '#1d030b',
              800: '#2a0510',
              750: '#3d0818',
              700: '#540c21',
              600: '#7e1333',
              500: '#ab1c47',
              400: '#e12d61',
              300: '#f45b86',
            }
          }
        }
      }
    };
  </script>

  <style>
    body {
      background: radial-gradient(circle at 15% 15%, #2a0510 0%, #0d0105 50%, #050002 100%);
      color: #fce7ef;
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Custom Slim Scrollbars */
    ::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(10, 2, 5, 0.6);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(225, 45, 97, 0.25);
      border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(225, 45, 97, 0.5);
    }

    .glass-panel {
      background: linear-gradient(135deg, rgba(35, 4, 13, 0.72) 0%, rgba(16, 2, 7, 0.88) 100%);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(244, 91, 134, 0.12);
    }

    .glass-nav-active {
      background: linear-gradient(90deg, #e12d61 0%, #b81444 100%);
      box-shadow: 0 4px 20px rgba(225, 45, 97, 0.45);
    }

    .glass-input {
      background: rgba(20, 2, 8, 0.75);
      border: 1px solid rgba(244, 91, 134, 0.2);
    }
    .glass-input:focus {
      border-color: #f45b86;
      outline: none;
      box-shadow: 0 0 0 2px rgba(244, 91, 134, 0.25);
    }
  </style>
</head>
<body class="selection:bg-wine-500 selection:text-white antialiased">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useMemo, useEffect, useRef } = React;
    const { motion, AnimatePresence } = window.Motion || window.framerMotion || {
      motion: {
        div: (props) => <div {...props}>{props.children}</div>,
        button: (props) => <button {...props}>{props.children}</button>,
      },
      AnimatePresence: ({ children }) => <>{children}</>
    };

    // Client Brand Logo helper with official brand accents
    const ClientBrandBadge = ({ name }) => {
      const lower = (name || '').toLowerCase();
      if (lower.includes('amazon')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#131921] border border-amber-500/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-[#FF9900] font-black text-[10px] leading-none font-sans">a</span>
          </div>
        );
      }
      if (lower.includes('flipkart')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#2874F0] border border-blue-400/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-[#FFE500] italic font-black text-[10px] leading-none">f</span>
          </div>
        );
      }
      if (lower.includes('reliance')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#C8102E] border border-red-400/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-white font-extrabold text-[10px] leading-none">R</span>
          </div>
        );
      }
      if (lower.includes('tata')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#0F4C81] border border-sky-400/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-white font-black text-[7px] tracking-tighter leading-none">TATA</span>
          </div>
        );
      }
      if (lower.includes('bluedart') || lower.includes('blue dart')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#001489] border border-blue-400/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-[#00B4D8] font-black text-[8px] tracking-tight leading-none">BD</span>
          </div>
        );
      }
      if (lower.includes('delhivery')) {
        return (
          <div className="w-5 h-5 rounded-md bg-[#B31942] border border-rose-400/40 flex items-center justify-center shrink-0 shadow-sm" title={name}>
            <span className="text-white font-black text-[9px] leading-none">D</span>
          </div>
        );
      }
      // Fallback initial
      const initial = (name || 'C').charAt(0).toUpperCase();
      return (
        <div className="w-5 h-5 rounded-md bg-wine-800 border border-wine-500/30 flex items-center justify-center shrink-0" title={name}>
          <span className="text-wine-300 font-bold text-[9px]">{initial}</span>
        </div>
      );
    };

    // Default Sample Logistics Fleet Data
    const INITIAL_RECORDS = [
      { id: 'TRP-9021', date: '2026-11-10', vehicleNo: 'DL-01-AB-1234', client: 'Amazon India', staff: 'Ramesh Kumar', route: 'Delhi Hub → Mumbai Sort', status: 'Trip Closed', remarks: 'Delayed at NH48 toll barrier' },
      { id: 'TRP-9022', date: '2026-11-09', vehicleNo: 'MH-04-CD-5678', client: 'Flipkart Wholesale', staff: 'Suresh Patil', route: 'Pune DC → Bengaluru WH', status: 'Trip Closed', remarks: 'Severe heavy rain & traffic jam' },
      { id: 'TRP-9023', date: '2026-11-08', vehicleNo: 'HR-26-EE-9901', client: 'Reliance Retail', staff: 'Vikram Singh', route: 'Gurugram → Jaipur DC', status: 'Trip Closed', remarks: 'Vehicle tyre breakdown at Rewari' },
      { id: 'TRP-9024', date: '2026-11-08', vehicleNo: 'KA-05-FF-4321', client: 'Amazon India', staff: 'Anand Rao', route: 'Bengaluru Hub → Chennai Yard', status: 'In-Transit', remarks: 'Single driver mandatory rest pause' },
      { id: 'TRP-9025', date: '2026-10-25', vehicleNo: 'GJ-01-GG-7788', client: 'Tata Consumer', staff: 'Jignesh Patel', route: 'Ahmedabad → Surat Plant', status: 'Trip Closed', remarks: 'Delivered seamlessly on schedule' },
      { id: 'TRP-9026', date: '2026-10-22', vehicleNo: 'UP-14-HH-3344', client: 'Flipkart Wholesale', staff: 'Mohan Verma', route: 'Noida Plant → Kanpur DC', status: 'Trip Closed', remarks: 'Mechanical radiator coolant leak' },
      { id: 'TRP-9027', date: '2026-11-05', vehicleNo: 'TN-02-JJ-6655', client: 'Reliance Retail', staff: 'Karthik Raja', route: 'Chennai Hub → Madurai DC', status: 'Trip Closed', remarks: 'Driver sickness delay during haul' },
      { id: 'TRP-9028', date: '2026-09-18', vehicleNo: 'WB-02-KK-1122', client: 'Tata Consumer', staff: 'Subhash Roy', route: 'Kolkata Hub → Patna Hub', status: 'Trip Closed', remarks: 'On schedule line haul handover' },
      { id: 'TRP-9029', date: '2026-11-07', vehicleNo: 'DL-01-LM-9944', client: 'BlueDart Express', staff: 'Mohit Pandey', route: 'Delhi Hub → Lucknow Sorting', status: 'Trip Closed', remarks: 'Unloading dock traffic congestion' },
      { id: 'TRP-9030', date: '2026-11-10', vehicleNo: 'HR-55-XY-8811', client: 'Delhivery Crossdock', staff: 'Kuldeep Gill', route: 'Sonipat DC → Ludhiana TC', status: 'Trip Closed', remarks: 'On time standard transit' },
    ];

    function App() {
      const [records, setRecords] = useState(INITIAL_RECORDS);
      const [activeTab, setActiveTab] = useState('overall'); // overall, client, staff, arrival, delay, ai_review
      const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

      // Arrival Filters
      const [selectedDate, setSelectedDate] = useState('2026-11-10');
      const [showCalendar, setShowCalendar] = useState(false);
      const [selectedClientFilter, setSelectedClientFilter] = useState('');
      const [selectedStaffFilter, setSelectedStaffFilter] = useState('');
      const [calMonth, setCalMonth] = useState(10); // 0-indexed: 10 = Nov
      const [calYear, setCalYear] = useState(2026);

      // AI Delay Review Filter
      const [aiDelayCategory, setAiDelayCategory] = useState('ALL');
      const [aiGenerating, setAiGenerating] = useState(false);
      const [aiReportOutput, setAiReportOutput] = useState(null);

      // Re-trigger Lucide icons when DOM / tab updates
      useEffect(() => {
        if (window.lucide) {
          window.lucide.createIcons();
        }
      }, [activeTab, selectedDate, showCalendar, mobileMenuOpen, aiDelayCategory, aiReportOutput]);

      // Parse uploaded Excel File
      const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (evt) => {
          try {
            const data = new Uint8Array(evt.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const json = XLSX.utils.sheet_to_json(sheet, { defval: '' });

            if (json.length === 0) {
              alert('Sheet is empty');
              return;
            }

            const mapped = json.map((row, idx) => {
              const keys = Object.keys(row);
              const findKey = (candidates) => {
                const found = keys.find(k => candidates.some(c => k.toLowerCase().includes(c)));
                return found ? row[found] : '';
              };

              const rawDate = findKey(['arrival date', 'closing date', 'close date', 'trip date', 'date', 'arrival']);
              let formattedDate = '2026-11-10';
              if (rawDate) {
                if (typeof rawDate === 'number') {
                  const d = new Date(Math.round((rawDate - 25569) * 86400 * 1000));
                  formattedDate = d.toISOString().split('T')[0];
                } else {
                  const parsed = new Date(rawDate);
                  if (!isNaN(parsed)) {
                    formattedDate = parsed.toISOString().split('T')[0];
                  } else {
                    formattedDate = String(rawDate).trim().slice(0, 10);
                  }
                }
              }

              const statusVal = String(findKey(['status', 'trip status', 'arrival status']) || 'Trip Closed').trim();
              const delayRemarks = String(findKey(['delay remarks', 'remarks', 'reason', 'delay reason', 'comment']) || '').trim();

              return {
                id: String(findKey(['trip id', 'tripid', 'trip_id', 'id']) || `TRP-${9000 + idx}`),
                date: formattedDate,
                vehicleNo: String(findKey(['vehicle no', 'vehicleno', 'truck', 'vehicle']) || `DL-01-XX-${1000 + idx}`).toUpperCase(),
                client: String(findKey(['client', 'client name', 'customer', 'account']) || 'General Client').trim(),
                staff: String(findKey(['staff', 'driver', 'pilot', 'driver name', 'staff name']) || 'Fleet Driver').trim(),
                route: String(findKey(['route', 'corridor', 'lane', 'source-dest']) || 'Origin → Destination').trim(),
                status: statusVal,
                remarks: delayRemarks || (statusVal.toLowerCase().includes('delay') ? 'Delayed arrival recorded' : 'On-time movement')
              };
            });

            setRecords(mapped);
            if (mapped.length > 0) {
              setSelectedDate(mapped[0].date);
            }
          } catch (err) {
            console.error('Failed to parse Excel file', err);
            alert('Error parsing Excel file. Please ensure valid format (.xlsx or .xls).');
          }
        };
        reader.readAsArrayBuffer(file);
      };

      // Aggregated Metrics Calculations
      const metrics = useMemo(() => {
        const total = records.length;
        const inTransit = records.filter(r => r.status.toLowerCase().includes('transit')).length;
        
        // Delay logic: has delay remarks or remarks not containing 'seamless' / 'on schedule' / 'on time'
        const delayed = records.filter(r => {
          const rem = (r.remarks || '').toLowerCase();
          const st = (r.status || '').toLowerCase();
          return st.includes('delay') || rem.includes('delay') || rem.includes('breakdown') || rem.includes('jam') || rem.includes('leak') || rem.includes('rest') || rem.includes('congestion') || rem.includes('sickness');
        }).length;

        const closed = records.filter(r => r.status.toLowerCase().includes('closed') && !r.status.toLowerCase().includes('delay')).length;

        return { total, inTransit, closed, delayed };
      }, [records]);

      // Client Performance Aggregation
      const clientStats = useMemo(() => {
        const map = {};
        records.forEach(r => {
          const client = r.client || 'Unknown Client';
          if (!map[client]) {
            map[client] = { name: client, total: 0, closed: 0, delayed: 0 };
          }
          map[client].total += 1;
          const rem = (r.remarks || '').toLowerCase();
          const isDelayed = r.status.toLowerCase().includes('delay') || rem.includes('delay') || rem.includes('breakdown') || rem.includes('jam') || rem.includes('leak') || rem.includes('rest') || rem.includes('congestion');
          if (isDelayed) {
            map[client].delayed += 1;
          } else if (r.status.toLowerCase().includes('closed')) {
            map[client].closed += 1;
          }
        });

        return Object.values(map).map(c => {
          const onTimeRate = c.total > 0 ? Math.round(((c.total - c.delayed) / c.total) * 100) : 100;
          return {
            ...c,
            sla: Math.max(0, onTimeRate),
            status: onTimeRate >= 85 ? 'Compliant' : onTimeRate >= 60 ? 'Moderate' : 'At Risk'
          };
        }).sort((a, b) => b.total - a.total);
      }, [records]);

      // Staff Performance Aggregation
      const staffStats = useMemo(() => {
        const map = {};
        records.forEach(r => {
          const staff = r.staff || 'Unknown Staff';
          if (!map[staff]) {
            map[staff] = { name: staff, total: 0, closed: 0, delayed: 0 };
          }
          map[staff].total += 1;
          const rem = (r.remarks || '').toLowerCase();
          const isDelayed = r.status.toLowerCase().includes('delay') || rem.includes('delay') || rem.includes('breakdown') || rem.includes('jam') || rem.includes('leak') || rem.includes('rest') || rem.includes('congestion');
          if (isDelayed) {
            map[staff].delayed += 1;
          } else if (r.status.toLowerCase().includes('closed')) {
            map[staff].closed += 1;
          }
        });

        return Object.values(map).map(s => {
          const onTimeRate = s.total > 0 ? Math.round(((s.total - s.delayed) / s.total) * 100) : 100;
          return {
            ...s,
            sla: Math.max(0, onTimeRate),
            status: onTimeRate >= 85 ? 'Top Pilot' : onTimeRate >= 60 ? 'Satisfactory' : 'Needs Review'
          };
        }).sort((a, b) => b.total - a.total);
      }, [records]);

      // Route Performance Aggregation
      const routeStats = useMemo(() => {
        const map = {};
        records.forEach(r => {
          const route = r.route || 'Unknown Corridor';
          if (!map[route]) {
            map[route] = { name: route, total: 0, closed: 0, delayed: 0 };
          }
          map[route].total += 1;
          const rem = (r.remarks || '').toLowerCase();
          const isDelayed = r.status.toLowerCase().includes('delay') || rem.includes('delay') || rem.includes('breakdown') || rem.includes('jam') || rem.includes('leak') || rem.includes('rest') || rem.includes('congestion');
          if (isDelayed) {
            map[route].delayed += 1;
          } else if (r.status.toLowerCase().includes('closed')) {
            map[route].closed += 1;
          }
        });

        return Object.values(map).map(rt => {
          const onTimeRate = rt.total > 0 ? Math.round(((rt.total - rt.delayed) / rt.total) * 100) : 100;
          return {
            ...rt,
            sla: Math.max(0, onTimeRate),
            status: onTimeRate >= 85 ? 'Optimal' : onTimeRate >= 60 ? 'Congested' : 'Bottleneck'
          };
        }).sort((a, b) => b.total - a.total);
      }, [records]);

      // Filtered records for Day Wise Arrival
      const filteredArrivals = useMemo(() => {
        return records.filter(r => {
          const matchDate = !selectedDate || r.date === selectedDate;
          const matchClient = !selectedClientFilter || r.client === selectedClientFilter;
          const matchStaff = !selectedStaffFilter || r.staff === selectedStaffFilter;
          return matchDate && matchClient && matchStaff;
        });
      }, [records, selectedDate, selectedClientFilter, selectedStaffFilter]);

      // Only Delayed records
      const delayedRecords = useMemo(() => {
        return records.filter(r => {
          const rem = (r.remarks || '').toLowerCase();
          const st = (r.status || '').toLowerCase();
          return st.includes('delay') || rem.includes('delay') || rem.includes('breakdown') || rem.includes('jam') || rem.includes('leak') || rem.includes('rest') || rem.includes('congestion') || rem.includes('sickness');
        });
      }, [records]);

      // Categorize Delayed vehicles for AI Review
      const categorizedDelays = useMemo(() => {
        return delayedRecords.map(r => {
          const rem = (r.remarks || '').toLowerCase();
          let category = 'Other Delay';
          let actionRequired = 'Investigate corridor timeline with local supervisor';

          if (rem.includes('breakdown') || rem.includes('leak') || rem.includes('tyre') || rem.includes('mechanical') || rem.includes('coolant')) {
            category = 'Breakdown';
            actionRequired = 'Deploy emergency mobile mechanic & arrange towing relief';
          } else if (rem.includes('driver sickness') || rem.includes('driver issue') || rem.includes('driver absence')) {
            category = 'Driver Issue';
            actionRequired = 'Summon backup standby pilot & collect driver medical note';
          } else if (rem.includes('traffic') || rem.includes('toll') || rem.includes('nh48') || rem.includes('jam') || rem.includes('rain')) {
            category = 'Traffic Jam';
            actionRequired = 'Issue bypass highway diversion GPS coordinates via control tower';
          } else if (rem.includes('single driver') || rem.includes('rest') || rem.includes('fatigue')) {
            category = 'Single Driver';
            actionRequired = 'Enforce 45-min mandatory log & schedule twin-driver crew for >400km';
          } else if (rem.includes('dock') || rem.includes('unloading') || rem.includes('congestion') || rem.includes('wh')) {
            category = 'Dock Jam';
            actionRequired = 'Escalate with client WH dock coordinator to authorize fast-track bay';
          }

          return { ...r, category, actionRequired };
        });
      }, [delayedRecords]);

      const filteredAiDelays = useMemo(() => {
        if (aiDelayCategory === 'ALL') return categorizedDelays;
        return categorizedDelays.filter(d => d.category === aiDelayCategory);
      }, [categorizedDelays, aiDelayCategory]);

      // Available unique clients & staff for dropdown filters
      const uniqueClients = useMemo(() => Array.from(new Set(records.map(r => r.client))).filter(Boolean), [records]);
      const uniqueStaff = useMemo(() => Array.from(new Set(records.map(r => r.staff))).filter(Boolean), [records]);

      // Calendar month days calculation
      const daysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
      const firstDayOffset = (year, month) => new Date(year, month, 1).getDay(); // 0 = Sun

      const calendarDays = useMemo(() => {
        const days = [];
        const totalDays = daysInMonth(calYear, calMonth);
        const offset = firstDayOffset(calYear, calMonth);
        const adjustedOffset = offset === 0 ? 6 : offset - 1; // Mon = 0

        for (let i = 0; i < adjustedOffset; i++) {
          days.push(null);
        }
        for (let d = 1; d <= totalDays; d++) {
          const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
          days.push({ day: d, dateStr });
        }
        return days;
      }, [calYear, calMonth]);

      // Mock AI Action Generation
      const handleGenerateAiReport = () => {
        setAiGenerating(true);
        setTimeout(() => {
          setAiGenerating(false);
          setAiReportOutput({
            summary: `Automated analysis completed across ${delayedRecords.length} delayed operations. Critical friction identified in Rewari corridor and NH48 toll junction.`,
            criticalFlags: [
              'High frequency breakdown on Haryana/Rajasthan freight corridor (DL/HR vehicles). Recommend mandatory fleet radiator & tyre pressure inspections prior to departure.',
              'Single Driver regulations breached on long hauls exceeding 500km (KA-05-FF-4321). Enforce dual-pilot rosters for all south-bound transit.',
              'Flipkart & Reliance retail delivery docks experiencing 3.2 hr average handover turnarounds. Issue formal dock bay reservation notices to client hub managers.'
            ],
            immediateOrders: [
              'Action Order #1: Route vehicle HR-26-EE-9901 to nearest authorized workshop for suspension check.',
              'Action Order #2: Issue automated driver changeover alert for Bangalore-Chennai corridor.',
              'Action Order #3: Apply contractual grace period waivers for NH48 toll choke points.'
            ]
          });
        }, 800);
      };

      return (
        <div className="flex flex-col md:flex-row min-h-screen text-slate-100">
          
          {/* MOBILE TOP BAR (< md) */}
          <div className="md:hidden glass-panel border-b border-wine-500/20 px-4 py-3 flex items-center justify-between sticky top-0 z-50">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-rose-500 to-wine-600 flex items-center justify-center shadow-lg shadow-rose-900/40">
                <i data-lucide="shield" className="w-4 h-4 text-white"></i>
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <span className="font-extrabold text-xs tracking-wider text-white">FLEET CONTROL</span>
                  <span className="px-1.5 py-0.2 text-[8px] font-bold rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">V5</span>
                </div>
                <p className="text-[9px] text-wine-300/70 font-mono tracking-tight">Logistics Command Center</p>
              </div>
            </div>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-lg bg-wine-800/80 border border-wine-500/30 text-rose-300 hover:text-white"
            >
              <i data-lucide={mobileMenuOpen ? "x" : "menu"} className="w-5 h-5"></i>
            </button>
          </div>

          {/* MOBILE EXPANDABLE DRAWER */}
          {mobileMenuOpen && (
            <div className="md:hidden fixed inset-x-0 top-14 bottom-0 bg-wine-950/95 backdrop-blur-xl z-40 p-4 flex flex-col space-y-2 border-b border-rose-500/20">
              {[
                { id: 'overall', label: 'Over All Performance', icon: 'activity' },
                { id: 'client', label: 'Client Wise Performance', icon: 'briefcase' },
                { id: 'staff', label: 'Staff Wise Performance', icon: 'user' },
                { id: 'arrival', label: 'Day Wise Arrival Report', icon: 'calendar' },
                { id: 'delay', label: 'Only Delay Arrival Report', icon: 'alert-triangle' },
                { id: 'ai_review', label: 'AI Delay Review', icon: 'bot' },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setMobileMenuOpen(false); }}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    activeTab === tab.id ? 'glass-nav-active text-white' : 'text-slate-300 hover:bg-wine-900/60'
                  }`}
                >
                  <i data-lucide={tab.icon} className="w-4 h-4 shrink-0"></i>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* COMPACT DESKTOP SIDEBAR (w-56) */}
          <aside className="hidden md:flex md:w-56 glass-panel border-r border-wine-500/20 p-3.5 flex-col shrink-0 justify-between">
            <div className="space-y-5">
              {/* BRAND HEADER */}
              <div className="flex items-center space-x-2.5 px-1 py-1">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-rose-500 to-wine-600 flex items-center justify-center shadow-lg shadow-rose-900/40">
                  <i data-lucide="shield" className="w-4 h-4 text-white"></i>
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="font-extrabold text-xs tracking-wider text-white">FLEET CONTROL</span>
                    <span className="px-1 py-0.2 text-[8px] font-bold rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">V5</span>
                  </div>
                  <p className="text-[9px] text-wine-300/70 font-mono tracking-tight">Logistics Command Center</p>
                </div>
              </div>

              {/* NAV ITEMS */}
              <nav className="space-y-1">
                {[
                  { id: 'overall', label: 'Over All Performance', icon: 'activity' },
                  { id: 'client', label: 'Client Wise Performance', icon: 'briefcase' },
                  { id: 'staff', label: 'Staff Wise Performance', icon: 'user' },
                  { id: 'arrival', label: 'Day Wise Arrival Report', icon: 'calendar' },
                  { id: 'delay', label: 'Only Delay Arrival Report', icon: 'alert-triangle' },
                  { id: 'ai_review', label: 'AI Delay Review', icon: 'bot' },
                ].map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`relative w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-[11px] font-semibold transition-all ${
                        isActive
                          ? 'glass-nav-active text-white'
                          : 'text-slate-300 hover:text-white hover:bg-wine-900/60'
                      }`}
                    >
                      <i data-lucide={item.icon} className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-white' : 'text-rose-300/70'}`}></i>
                      <span className="truncate">{item.label}</span>
                      {isActive && (
                        <span className="absolute right-2 w-1 h-3 rounded-full bg-white/90 shadow-sm" />
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* SIDEBAR FOOTER */}
            <div className="pt-3 border-t border-wine-500/20 text-[10px] text-wine-300/60 font-mono flex items-center justify-between px-1">
              <span>ACTIVE SYSTEM</span>
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span className="text-emerald-400 font-semibold">LIVE</span>
              </span>
            </div>
          </aside>

          {/* MAIN WORKSPACE CONTENT */}
          <main className="flex-1 p-3 md:p-6 space-y-4 max-w-7xl mx-auto w-full">
            
            {/* CLEAN BORDERLESS TOP BAR (NO CARD) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-wine-500/20">
              <div>
                <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                  {activeTab === 'overall' && 'Over All Performance'}
                  {activeTab === 'client' && 'Client Wise Performance Report'}
                  {activeTab === 'staff' && 'Staff Wise Performance Report'}
                  {activeTab === 'arrival' && 'Day Wise Arrival Chronology'}
                  {activeTab === 'delay' && 'Only Delay Arrival Exceptions'}
                  {activeTab === 'ai_review' && 'AI Operational Delay Review'}
                </h1>
                <p className="text-[11px] text-wine-200/60 font-mono">
                  Real-time operational telemetry, SLA compliance, and dispatch management
                </p>
              </div>

              {/* FILE UPLOAD CONTROLS (Over All Performance only) */}
              {activeTab === 'overall' && (
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => setRecords(INITIAL_RECORDS)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-wine-900/80 hover:bg-wine-800 border border-wine-500/30 text-rose-200 text-xs font-semibold transition shadow-sm"
                  >
                    <i data-lucide="rotate-ccw" className="w-3.5 h-3.5"></i>
                    <span>Load Sample</span>
                  </button>

                  <label className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-rose-500 to-wine-600 hover:from-rose-400 hover:to-wine-500 text-white text-xs font-bold shadow-md shadow-rose-900/30 cursor-pointer transition">
                    <i data-lucide="upload" className="w-3.5 h-3.5"></i>
                    <span>Upload Excel File</span>
                    <input
                      type="file"
                      accept=".xlsx, .xls"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                </div>
              )}
            </div>

            {/* HORIZONTAL INLINE METRICS (NO CARDS - ONLY NUMBERS & LABELS) */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 py-2 px-1">
              <div className="flex items-baseline space-x-2 border-l-2 border-white/20 pl-3">
                <span className="text-2xl md:text-3xl font-black text-white font-mono">{metrics.total}</span>
                <div>
                  <div className="text-[10px] md:text-xs font-bold text-slate-300 uppercase tracking-wider">Total Fleet Trips</div>
                  <div className="text-[9px] text-wine-200/50 hidden sm:block">Total active recorded dispatches</div>
                </div>
              </div>

              <div className="flex items-baseline space-x-2 border-l-2 border-blue-500/40 pl-3">
                <span className="text-2xl md:text-3xl font-black text-blue-400 font-mono">{metrics.inTransit}</span>
                <div>
                  <div className="text-[10px] md:text-xs font-bold text-slate-300 uppercase tracking-wider">In-Transit Vehicle</div>
                  <div className="text-[9px] text-wine-200/50 hidden sm:block">Active line-haul movements</div>
                </div>
              </div>

              <div className="flex items-baseline space-x-2 border-l-2 border-emerald-500/40 pl-3">
                <span className="text-2xl md:text-3xl font-black text-emerald-400 font-mono">{metrics.closed}</span>
                <div>
                  <div className="text-[10px] md:text-xs font-bold text-slate-300 uppercase tracking-wider">Trip Closed</div>
                  <div className="text-[9px] text-wine-200/50 hidden sm:block">Completed on-time dispatches</div>
                </div>
              </div>

              <div className="flex items-baseline space-x-2 border-l-2 border-rose-500/40 pl-3">
                <span className="text-2xl md:text-3xl font-black text-rose-400 font-mono">{metrics.delayed}</span>
                <div>
                  <div className="text-[10px] md:text-xs font-bold text-slate-300 uppercase tracking-wider">Delay Closed</div>
                  <div className="text-[9px] text-wine-200/50 hidden sm:block">Delayed exception completions</div>
                </div>
              </div>
            </div>

            {/* TAB 1: OVER ALL PERFORMANCE */}
            {activeTab === 'overall' && (
              <div className="space-y-4">
                
                {/* 1. Client Wise Performance Table */}
                <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                        <i data-lucide="briefcase" className="w-3.5 h-3.5"></i>
                      </div>
                      <div>
                        <h2 className="text-xs font-bold text-white tracking-wide">Client Wise Performance Report</h2>
                        <p className="text-[10px] text-wine-200/50 font-mono">Aggregated dispatches, completions, delays, and SLA compliance</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-wine-800/80 text-rose-300 border border-wine-500/30">
                      {clientStats.length} Accounts Active
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                          <th className="py-2 px-3">Client Name</th>
                          <th className="py-2 px-3 text-center">Total Trips</th>
                          <th className="py-2 px-3 text-center text-emerald-400">Trip Closed</th>
                          <th className="py-2 px-3 text-center text-rose-400">Delay Closed</th>
                          <th className="py-2 px-3">On-Time SLA %</th>
                          <th className="py-2 px-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-wine-500/10">
                        {clientStats.map((c, i) => (
                          <tr key={i} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 flex items-center space-x-2">
                              <ClientBrandBadge name={c.name} />
                              <span className="font-semibold text-white">{c.name}</span>
                            </td>
                            <td className="py-2 px-3 text-center font-mono font-bold">{c.total}</td>
                            <td className="py-2 px-3 text-center font-mono text-emerald-400 font-bold">{c.closed}</td>
                            <td className="py-2 px-3 text-center font-mono text-rose-400 font-bold">{c.delayed}</td>
                            <td className="py-2 px-3">
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-wine-950 rounded-full h-1 overflow-hidden border border-wine-500/20">
                                  <div
                                    className={`h-full rounded-full ${
                                      c.sla >= 80 ? 'bg-emerald-400' : c.sla >= 50 ? 'bg-amber-400' : 'bg-rose-500'
                                    }`}
                                    style={{ width: `${c.sla}%` }}
                                  ></div>
                                </div>
                                <span className="font-mono text-[10px] text-slate-300">{c.sla}%</span>
                              </div>
                            </td>
                            <td className="py-2 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                c.status === 'Compliant'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : c.status === 'Moderate'
                                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}>
                                {c.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 2. Staff Wise Performance Table */}
                <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                        <i data-lucide="user" className="w-3.5 h-3.5"></i>
                      </div>
                      <div>
                        <h2 className="text-xs font-bold text-white tracking-wide">Staff Wise Performance Report</h2>
                        <p className="text-[10px] text-wine-200/50 font-mono">Pilot assignments, trip closures, delay flags, and rating</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-wine-800/80 text-rose-300 border border-wine-500/30">
                      {staffStats.length} Drivers Recorded
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                          <th className="py-2 px-3">Staff / Driver</th>
                          <th className="py-2 px-3 text-center">Total Assigned</th>
                          <th className="py-2 px-3 text-center text-emerald-400">Trip Closed</th>
                          <th className="py-2 px-3 text-center text-rose-400">Delay Closed</th>
                          <th className="py-2 px-3">On-Time SLA %</th>
                          <th className="py-2 px-3 text-right">Rating</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-wine-500/10">
                        {staffStats.map((s, i) => (
                          <tr key={i} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 font-semibold text-white">{s.name}</td>
                            <td className="py-2 px-3 text-center font-mono font-bold">{s.total}</td>
                            <td className="py-2 px-3 text-center font-mono text-emerald-400 font-bold">{s.closed}</td>
                            <td className="py-2 px-3 text-center font-mono text-rose-400 font-bold">{s.delayed}</td>
                            <td className="py-2 px-3">
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-wine-950 rounded-full h-1 overflow-hidden border border-wine-500/20">
                                  <div
                                    className={`h-full rounded-full ${
                                      s.sla >= 80 ? 'bg-emerald-400' : s.sla >= 50 ? 'bg-amber-400' : 'bg-rose-500'
                                    }`}
                                    style={{ width: `${s.sla}%` }}
                                  ></div>
                                </div>
                                <span className="font-mono text-[10px] text-slate-300">{s.sla}%</span>
                              </div>
                            </td>
                            <td className="py-2 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                s.status === 'Top Pilot'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : s.status === 'Satisfactory'
                                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}>
                                {s.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 3. Route Wise Performance Table */}
                <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                        <i data-lucide="map-pin" className="w-3.5 h-3.5"></i>
                      </div>
                      <div>
                        <h2 className="text-xs font-bold text-white tracking-wide">Route Wise Performance Report</h2>
                        <p className="text-[10px] text-wine-200/50 font-mono">Transit corridor dispatches, choke points, and throughput</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-wine-800/80 text-rose-300 border border-wine-500/30">
                      {routeStats.length} Corridors
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                          <th className="py-2 px-3">Route / Corridor</th>
                          <th className="py-2 px-3 text-center">Total Dispatches</th>
                          <th className="py-2 px-3 text-center text-emerald-400">Trip Closed</th>
                          <th className="py-2 px-3 text-center text-rose-400">Delay Closed</th>
                          <th className="py-2 px-3">Corridor SLA %</th>
                          <th className="py-2 px-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-wine-500/10">
                        {routeStats.map((r, i) => (
                          <tr key={i} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 font-semibold text-white font-mono">{r.name}</td>
                            <td className="py-2 px-3 text-center font-mono font-bold">{r.total}</td>
                            <td className="py-2 px-3 text-center font-mono text-emerald-400 font-bold">{r.closed}</td>
                            <td className="py-2 px-3 text-center font-mono text-rose-400 font-bold">{r.delayed}</td>
                            <td className="py-2 px-3">
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-wine-950 rounded-full h-1 overflow-hidden border border-wine-500/20">
                                  <div
                                    className={`h-full rounded-full ${
                                      r.sla >= 80 ? 'bg-emerald-400' : r.sla >= 50 ? 'bg-amber-400' : 'bg-rose-500'
                                    }`}
                                    style={{ width: `${r.sla}%` }}
                                  ></div>
                                </div>
                                <span className="font-mono text-[10px] text-slate-300">{r.sla}%</span>
                              </div>
                            </td>
                            <td className="py-2 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                r.status === 'Optimal'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : r.status === 'Congested'
                                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}>
                                {r.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            )}

            {/* TAB 2: CLIENT WISE PERFORMANCE (DEDICATED) */}
            {activeTab === 'client' && (
              <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                      <i data-lucide="briefcase" className="w-3.5 h-3.5"></i>
                    </div>
                    <div>
                      <h2 className="text-xs font-bold text-white tracking-wide">Client Wise Performance Report</h2>
                      <p className="text-[10px] text-wine-200/50 font-mono">Aggregated dispatches, completions, delays, and SLA compliance</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-wine-800/80 text-rose-300 border border-wine-500/30">
                    {clientStats.length} Accounts
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                        <th className="py-2 px-3">Client Name</th>
                        <th className="py-2 px-3 text-center">Total Trips</th>
                        <th className="py-2 px-3 text-center text-emerald-400">Trip Closed</th>
                        <th className="py-2 px-3 text-center text-rose-400">Delay Closed</th>
                        <th className="py-2 px-3">On-Time SLA %</th>
                        <th className="py-2 px-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-wine-500/10">
                      {clientStats.map((c, i) => (
                        <tr key={i} className="hover:bg-wine-900/30 transition">
                          <td className="py-2 px-3 flex items-center space-x-2">
                            <ClientBrandBadge name={c.name} />
                            <span className="font-semibold text-white">{c.name}</span>
                          </td>
                          <td className="py-2 px-3 text-center font-mono font-bold">{c.total}</td>
                          <td className="py-2 px-3 text-center font-mono text-emerald-400 font-bold">{c.closed}</td>
                          <td className="py-2 px-3 text-center font-mono text-rose-400 font-bold">{c.delayed}</td>
                          <td className="py-2 px-3">
                            <div className="flex items-center space-x-2">
                              <div className="w-20 bg-wine-950 rounded-full h-1 overflow-hidden border border-wine-500/20">
                                <div
                                  className={`h-full rounded-full ${
                                    c.sla >= 80 ? 'bg-emerald-400' : c.sla >= 50 ? 'bg-amber-400' : 'bg-rose-500'
                                  }`}
                                  style={{ width: `${c.sla}%` }}
                                ></div>
                              </div>
                              <span className="font-mono text-[10px] text-slate-300">{c.sla}%</span>
                            </div>
                          </td>
                          <td className="py-2 px-3 text-right">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                              c.status === 'Compliant'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : c.status === 'Moderate'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                              {c.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: STAFF WISE PERFORMANCE (DEDICATED) */}
            {activeTab === 'staff' && (
              <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                      <i data-lucide="user" className="w-3.5 h-3.5"></i>
                    </div>
                    <div>
                      <h2 className="text-xs font-bold text-white tracking-wide">Staff Wise Performance Report</h2>
                      <p className="text-[10px] text-wine-200/50 font-mono">Pilot assignments, completions, delays, and performance rating</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-wine-800/80 text-rose-300 border border-wine-500/30">
                    {staffStats.length} Staff
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                        <th className="py-2 px-3">Staff / Driver</th>
                        <th className="py-2 px-3 text-center">Total Assigned</th>
                        <th className="py-2 px-3 text-center text-emerald-400">Trip Closed</th>
                        <th className="py-2 px-3 text-center text-rose-400">Delay Closed</th>
                        <th className="py-2 px-3">On-Time SLA %</th>
                        <th className="py-2 px-3 text-right">Rating</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-wine-500/10">
                      {staffStats.map((s, i) => (
                        <tr key={i} className="hover:bg-wine-900/30 transition">
                          <td className="py-2 px-3 font-semibold text-white">{s.name}</td>
                          <td className="py-2 px-3 text-center font-mono font-bold">{s.total}</td>
                          <td className="py-2 px-3 text-center font-mono text-emerald-400 font-bold">{s.closed}</td>
                          <td className="py-2 px-3 text-center font-mono text-rose-400 font-bold">{s.delayed}</td>
                          <td className="py-2 px-3">
                            <div className="flex items-center space-x-2">
                              <div className="w-20 bg-wine-950 rounded-full h-1 overflow-hidden border border-wine-500/20">
                                <div
                                  className={`h-full rounded-full ${
                                    s.sla >= 80 ? 'bg-emerald-400' : s.sla >= 50 ? 'bg-amber-400' : 'bg-rose-500'
                                  }`}
                                  style={{ width: `${s.sla}%` }}
                                ></div>
                              </div>
                              <span className="font-mono text-[10px] text-slate-300">{s.sla}%</span>
                            </div>
                          </td>
                          <td className="py-2 px-3 text-right">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                              s.status === 'Top Pilot'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : s.status === 'Satisfactory'
                                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                              {s.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 4: DAY WISE ARRIVAL REPORT */}
            {activeTab === 'arrival' && (
              <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-4">
                
                {/* FILTERS TOOLBAR */}
                <div className="flex flex-wrap items-center justify-between gap-2.5 pb-2 border-b border-wine-500/20">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-wine-800/80 border border-wine-500/30 flex items-center justify-center text-rose-300">
                      <i data-lucide="calendar" className="w-3.5 h-3.5"></i>
                    </div>
                    <div>
                      <h2 className="text-xs font-bold text-white tracking-wide">Day Wise Arrival Chronology</h2>
                      <p className="text-[10px] text-wine-200/50 font-mono">Daily arrival logs with interactive calendar and entity filters</p>
                    </div>
                  </div>

                  {/* FILTER CONTROLS */}
                  <div className="flex flex-wrap items-center gap-2">
                    
                    {/* CLIENT FILTER BUTTON */}
                    <div className="relative">
                      <select
                        value={selectedClientFilter}
                        onChange={(e) => setSelectedClientFilter(e.target.value)}
                        className="glass-input text-[11px] font-semibold text-rose-200 rounded-lg px-2.5 py-1.5 focus:outline-none cursor-pointer"
                      >
                        <option value="" className="bg-wine-950 text-slate-300">All Clients</option>
                        {uniqueClients.map((cl, idx) => (
                          <option key={idx} value={cl} className="bg-wine-950 text-slate-200">{cl}</option>
                        ))}
                      </select>
                    </div>

                    {/* STAFF FILTER BUTTON */}
                    <div className="relative">
                      <select
                        value={selectedStaffFilter}
                        onChange={(e) => setSelectedStaffFilter(e.target.value)}
                        className="glass-input text-[11px] font-semibold text-rose-200 rounded-lg px-2.5 py-1.5 focus:outline-none cursor-pointer"
                      >
                        <option value="" className="bg-wine-950 text-slate-300">All Staff / Drivers</option>
                        {uniqueStaff.map((st, idx) => (
                          <option key={idx} value={st} className="bg-wine-950 text-slate-200">{st}</option>
                        ))}
                      </select>
                    </div>

                    {/* COMPACT CALENDAR TRIGGER BUTTON */}
                    <div className="relative">
                      <button
                        onClick={() => setShowCalendar(!showCalendar)}
                        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-wine-900/90 border border-wine-500/30 text-rose-200 text-xs font-mono font-semibold hover:border-rose-400 transition"
                      >
                        <i data-lucide="calendar" className="w-3.5 h-3.5 text-rose-400"></i>
                        <span>{selectedDate || 'Select Date'}</span>
                        <i data-lucide="chevron-down" className="w-3 h-3 text-wine-300"></i>
                      </button>

                      {/* COMPACT POP-UP CALENDAR */}
                      {showCalendar && (
                        <div className="absolute right-0 mt-2 z-50 w-60 glass-panel rounded-xl p-3 border border-rose-500/30 shadow-2xl space-y-2">
                          <div className="flex items-center justify-between text-xs font-bold text-white">
                            <button
                              onClick={() => {
                                if (calMonth === 0) { setCalMonth(11); setCalYear(calYear - 1); }
                                else { setCalMonth(calMonth - 1); }
                              }}
                              className="p-1 rounded hover:bg-wine-800 text-wine-300 hover:text-white"
                            >
                              <i data-lucide="chevron-left" className="w-3.5 h-3.5"></i>
                            </button>
                            <span className="font-mono text-[11px]">
                              {["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][calMonth]} {calYear}
                            </span>
                            <button
                              onClick={() => {
                                if (calMonth === 11) { setCalMonth(0); setCalYear(calYear + 1); }
                                else { setCalMonth(calMonth + 1); }
                              }}
                              className="p-1 rounded hover:bg-wine-800 text-wine-300 hover:text-white"
                            >
                              <i data-lucide="chevron-right" className="w-3.5 h-3.5"></i>
                            </button>
                          </div>

                          {/* WEEKDAYS */}
                          <div className="grid grid-cols-7 text-center text-[9px] font-bold text-wine-300/60 font-mono">
                            <span>MO</span><span>TU</span><span>WE</span><span>TH</span><span>FR</span><span>SA</span><span>SU</span>
                          </div>

                          {/* DAYS GRID */}
                          <div className="grid grid-cols-7 gap-1">
                            {calendarDays.map((item, idx) => {
                              if (!item) return <div key={idx} className="h-6 w-6"></div>;
                              const isSelected = selectedDate === item.dateStr;
                              return (
                                <button
                                  key={idx}
                                  onClick={() => {
                                    setSelectedDate(item.dateStr);
                                    setShowCalendar(false);
                                  }}
                                  className={`h-6 w-6 rounded text-[10px] font-mono flex items-center justify-center transition ${
                                    isSelected
                                      ? 'bg-rose-500 text-white font-bold shadow-md shadow-rose-900/50'
                                      : 'hover:bg-wine-800 text-slate-300'
                                  }`}
                                >
                                  {item.day}
                                </button>
                              );
                            })}
                          </div>

                          {/* FOOTER ACTIONS */}
                          <div className="pt-2 border-t border-wine-500/20 flex items-center justify-between text-[10px]">
                            <button
                              onClick={() => { setSelectedDate(''); setShowCalendar(false); }}
                              className="text-rose-300 hover:text-white font-mono"
                            >
                              Clear Date
                            </button>
                            <button
                              onClick={() => setShowCalendar(false)}
                              className="text-slate-400 hover:text-white font-mono"
                            >
                              Close
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* RESET FILTERS BUTTON */}
                    {(selectedDate || selectedClientFilter || selectedStaffFilter) && (
                      <button
                        onClick={() => {
                          setSelectedDate('');
                          setSelectedClientFilter('');
                          setSelectedStaffFilter('');
                        }}
                        className="p-1.5 rounded-lg bg-wine-800/60 hover:bg-wine-700 text-rose-300 hover:text-white transition"
                        title="Reset Filters"
                      >
                        <i data-lucide="x" className="w-3.5 h-3.5"></i>
                      </button>
                    )}

                  </div>
                </div>

                {/* TABLE (NO ARRIVAL DATE COLUMN) */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                        <th className="py-2 px-3">Vehicle No</th>
                        <th className="py-2 px-3">Client</th>
                        <th className="py-2 px-3">Staff / Driver</th>
                        <th className="py-2 px-3">Route</th>
                        <th className="py-2 px-3">Arrival Status</th>
                        <th className="py-2 px-3">Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-wine-500/10">
                      {filteredArrivals.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-8 text-center text-wine-300/60 font-mono">
                            No vehicles matching the selected filters.
                          </td>
                        </tr>
                      ) : (
                        filteredArrivals.map((row, idx) => (
                          <tr key={idx} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 font-mono font-bold text-white tracking-wide">{row.vehicleNo}</td>
                            <td className="py-2 px-3 flex items-center space-x-2">
                              <ClientBrandBadge name={row.client} />
                              <span className="font-semibold text-slate-200">{row.client}</span>
                            </td>
                            <td className="py-2 px-3 text-slate-300">{row.staff}</td>
                            <td className="py-2 px-3 font-mono text-[10px] text-wine-200/80">{row.route}</td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                row.status.toLowerCase().includes('closed')
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                              }`}>
                                {row.status}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-wine-200/70 text-[10px] italic">{row.remarks}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

              </div>
            )}

            {/* TAB 5: ONLY DELAY ARRIVAL REPORT */}
            {activeTab === 'delay' && (
              <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
                      <i data-lucide="alert-triangle" className="w-3.5 h-3.5"></i>
                    </div>
                    <div>
                      <h2 className="text-xs font-bold text-white tracking-wide">Only Delay Arrival Exceptions</h2>
                      <p className="text-[10px] text-wine-200/50 font-mono">Isolated trip delays requiring operational remediation</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold">
                    {delayedRecords.length} Exceptions
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                        <th className="py-2 px-3">Trip ID</th>
                        <th className="py-2 px-3">Vehicle No</th>
                        <th className="py-2 px-3">Client</th>
                        <th className="py-2 px-3">Staff / Driver</th>
                        <th className="py-2 px-3">Route</th>
                        <th className="py-2 px-3 text-rose-400">Delay Reason / Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-wine-500/10">
                      {delayedRecords.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-8 text-center text-emerald-400 font-mono">
                            Zero delays reported. All fleet dispatches are running on schedule.
                          </td>
                        </tr>
                      ) : (
                        delayedRecords.map((d, i) => (
                          <tr key={i} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 font-mono text-wine-300/80">{d.id}</td>
                            <td className="py-2 px-3 font-mono font-bold text-white">{d.vehicleNo}</td>
                            <td className="py-2 px-3 flex items-center space-x-2">
                              <ClientBrandBadge name={d.client} />
                              <span className="font-semibold text-slate-200">{d.client}</span>
                            </td>
                            <td className="py-2 px-3 text-slate-300">{d.staff}</td>
                            <td className="py-2 px-3 font-mono text-[10px] text-wine-200/80">{d.route}</td>
                            <td className="py-2 px-3">
                              <span className="inline-block px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-[10px]">
                                {d.remarks}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 6: AI DELAY REVIEW & ROOT CAUSE ACTION PLAN */}
            {activeTab === 'ai_review' && (
              <div className="space-y-4">
                
                {/* CATEGORY FILTER CHIPS */}
                <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-300">
                        <i data-lucide="bot" className="w-3.5 h-3.5"></i>
                      </div>
                      <div>
                        <h2 className="text-xs font-bold text-white tracking-wide">Root Cause Delay Categorization</h2>
                        <p className="text-[10px] text-wine-200/50 font-mono">Remediation directives based on mechanical, driver, and highway issues</p>
                      </div>
                    </div>

                    <button
                      onClick={handleGenerateAiReport}
                      disabled={aiGenerating}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-rose-500 to-wine-600 hover:from-rose-400 hover:to-wine-500 text-white text-xs font-bold shadow-md shadow-rose-900/30 cursor-pointer transition shrink-0"
                    >
                      <i data-lucide={aiGenerating ? "loader" : "sparkles"} className={`w-3.5 h-3.5 ${aiGenerating ? 'animate-spin' : ''}`}></i>
                      <span>{aiGenerating ? 'Analyzing Remarks...' : 'Generate AI Action Plan'}</span>
                    </button>
                  </div>

                  {/* PILL FILTERS */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-2">
                    {[
                      { id: 'ALL', label: 'All Delays' },
                      { id: 'Breakdown', label: 'Breakdown / Mechanical' },
                      { id: 'Driver Issue', label: 'Driver Issue / Absence' },
                      { id: 'Traffic Jam', label: 'Traffic Jam / Highway' },
                      { id: 'Single Driver', label: 'Single Driver Fatigue' },
                      { id: 'Dock Jam', label: 'Dock Congestion' },
                    ].map(cat => {
                      const count = cat.id === 'ALL'
                        ? categorizedDelays.length
                        : categorizedDelays.filter(c => c.category === cat.id).length;
                      const isActive = aiDelayCategory === cat.id;
                      return (
                        <button
                          key={cat.id}
                          onClick={() => setAiDelayCategory(cat.id)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold transition flex items-center space-x-1.5 ${
                            isActive
                              ? 'bg-rose-500 text-white shadow-sm'
                              : 'bg-wine-900/70 text-slate-300 hover:text-white border border-wine-500/20'
                          }`}
                        >
                          <span>{cat.label}</span>
                          <span className={`px-1 rounded text-[9px] font-mono ${isActive ? 'bg-white/20' : 'bg-wine-800'}`}>
                            {count}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* AI EXECUTIVE BRIEFING (GENERATED) */}
                {aiReportOutput && (
                  <div className="glass-panel rounded-2xl p-4 border border-rose-500/40 bg-gradient-to-br from-rose-950/40 via-wine-950/80 to-black space-y-3">
                    <div className="flex items-center space-x-2 text-rose-300 text-xs font-bold">
                      <i data-lucide="zap" className="w-4 h-4 text-amber-400"></i>
                      <span>AI Operational Directive & Immediate Orders</span>
                    </div>

                    <p className="text-xs text-slate-200 leading-relaxed font-sans">
                      {aiReportOutput.summary}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                      <div className="space-y-1.5 bg-black/40 p-3 rounded-xl border border-wine-500/20">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-rose-300">Operational Bottlenecks</div>
                        <ul className="space-y-1 text-[11px] text-slate-300 list-disc list-inside">
                          {aiReportOutput.criticalFlags.map((flag, idx) => (
                            <li key={idx} className="leading-snug">{flag}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="space-y-1.5 bg-black/40 p-3 rounded-xl border border-emerald-500/20">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Immediate Action Dispatches</div>
                        <ul className="space-y-1 text-[11px] text-slate-300 list-disc list-inside">
                          {aiReportOutput.immediateOrders.map((ord, idx) => (
                            <li key={idx} className="leading-snug">{ord}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* ACTION REQUIRED TABLE */}
                <div className="glass-panel rounded-2xl p-4 border border-wine-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white tracking-wide">Vehicle Delay Remediations</h3>
                    <span className="text-[10px] font-mono text-wine-300/60">Showing {filteredAiDelays.length} vehicles</span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-wine-500/20 text-[10px] text-wine-200/60 uppercase tracking-wider">
                          <th className="py-2 px-3">Vehicle No</th>
                          <th className="py-2 px-3">Client</th>
                          <th className="py-2 px-3">Category</th>
                          <th className="py-2 px-3">Delay Remarks</th>
                          <th className="py-2 px-3 text-rose-300 font-bold">Action Required</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-wine-500/10">
                        {filteredAiDelays.map((v, i) => (
                          <tr key={i} className="hover:bg-wine-900/30 transition">
                            <td className="py-2 px-3 font-mono font-bold text-white">{v.vehicleNo}</td>
                            <td className="py-2 px-3 flex items-center space-x-2">
                              <ClientBrandBadge name={v.client} />
                              <span className="font-semibold text-slate-200">{v.client}</span>
                            </td>
                            <td className="py-2 px-3">
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                {v.category}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-wine-200/70 text-[10px] italic">{v.remarks}</td>
                            <td className="py-2 px-3">
                              <span className="text-emerald-400 font-medium text-[10px] flex items-center space-x-1">
                                <i data-lucide="arrow-right" className="w-3 h-3 shrink-0"></i>
                                <span>{v.actionRequired}</span>
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            )}

          </main>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
