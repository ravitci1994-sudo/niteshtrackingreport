<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Fleet Operations Command Center</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- React 18 & Babel Standalone -->
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <!-- Framer Motion Standalone -->
  <script src="https://unpkg.com/framer-motion@10.16.4/dist/framer-motion.js"></script>

  <!-- SheetJS (XLSX) for Dynamic Excel Parsing -->
  <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    body {
      background: radial-gradient(circle at 50% -15%, #3d0812 0%, #150307 45%, #080103 100%);
      min-height: 100vh;
      color: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .glass-panel {
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }
    .active-nav-pill {
      background: linear-gradient(90deg, #e11d48 0%, #dc2626 100%);
      box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.55);
    }
    /* Scrollbars */
    ::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.25);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(244, 63, 94, 0.3);
      border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(244, 63, 94, 0.6);
    }
    .custom-scroll::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }
    .custom-scroll::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.02);
    }
    .custom-scroll::-webkit-scrollbar-thumb {
      background: rgba(244, 63, 94, 0.4);
      border-radius: 4px;
    }
  </style>
</head>
<body class="selection:bg-rose-500 selection:text-white">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect, useMemo } = React;
    const { motion, AnimatePresence } = window.Motion || window.framerMotion || {
      motion: {
        div: "div",
        button: "button",
        tr: "tr",
        span: "span",
        label: "label"
      },
      AnimatePresence: ({ children }) => children
    };

    const INITIAL_RECORDS = [
      { id: "TRP-9021", date: "2026-11-10", vehicle: "DL-01-AB-1234", client: "Amazon India", staff: "Ramesh Kumar", route: "Delhi Hub ➔ Mumbai Port", status: "In-Transit", isDelay: false, remarks: "Shipment moving as scheduled" },
      { id: "TRP-9022", date: "2026-11-09", vehicle: "MH-04-CD-5678", client: "Flipkart Wholesale", staff: "Suresh Patil", route: "Pune DC ➔ Bengaluru DC", status: "Trip Closed", isDelay: false, remarks: "Delivered on-time with clean POD" },
      { id: "TRP-9023", date: "2026-11-08", vehicle: "HR-26-EE-9901", client: "Reliance Retail", staff: "Vikram Singh", route: "Gurugram ➔ Jaipur Depot", status: "Delay Closed", isDelay: true, remarks: "Heavy highway traffic jam and toll gridlock" },
      { id: "TRP-9024", date: "2026-11-08", vehicle: "KA-05-FF-4321", client: "Amazon India", staff: "Anand Rao", route: "Bengaluru Hub ➔ Chennai Port", status: "Delay Closed", isDelay: true, remarks: "Single driver duty hours expired; rest required" },
      { id: "TRP-9025", date: "2026-10-25", vehicle: "GJ-01-GG-7788", client: "Tata Consumer", staff: "Jignesh Patel", route: "Ahmedabad ➔ Surat Yard", status: "Trip Closed", isDelay: false, remarks: "Completed on-time" },
      { id: "TRP-9026", date: "2026-10-22", vehicle: "UP-14-HH-3344", client: "Flipkart Wholesale", staff: "Mohan Verma", route: "Noida Plant ➔ Kanpur Depot", status: "Delay Closed", isDelay: true, remarks: "Breakdown: Clutch wire snapped on express route" },
      { id: "TRP-9027", date: "2026-11-05", vehicle: "TN-02-JJ-6655", client: "Reliance Retail", staff: "Karthik Raja", route: "Chennai Hub ➔ Hyderabad", status: "In-Transit", isDelay: true, remarks: "Driver issue: medical emergency replacement requested" },
      { id: "TRP-9028", date: "2026-09-18", vehicle: "WB-02-KK-1122", client: "Tata Consumer", staff: "Subhash Roy", route: "Kolkata Hub ➔ Patna Terminal", status: "Trip Closed", isDelay: false, remarks: "POD received" },
      { id: "TRP-9029", date: "2026-11-09", vehicle: "MH-12-PQ-8899", client: "BlueDart Express", staff: "Sunil Verma", route: "Mumbai ➔ Ahmedabad", status: "Delay Closed", isDelay: true, remarks: "Client warehouse dock unloading congestion" },
      { id: "TRP-9030", date: "2026-11-07", vehicle: "DL-04-RR-3344", client: "Delhivery Crossdock", staff: "Mohit Pandey", route: "Delhi Hub ➔ Lucknow", status: "Delay Closed", isDelay: true, remarks: "" }
    ];

    function FleetDashboard() {
      const [activeTab, setActiveTab] = useState("overall");
      const [trips, setTrips] = useState(INITIAL_RECORDS);

      // Filters for Day Wise Arrival
      const [filterDate, setFilterDate] = useState("");
      const [filterClient, setFilterClient] = useState("");
      const [filterStaff, setFilterStaff] = useState("");

      // Mobile sidebar toggle state
      const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

      // Calendar popup states
      const [isCalendarOpen, setIsCalendarOpen] = useState(false);
      const [calYear, setCalYear] = useState(2026);
      const [calMonth, setCalMonth] = useState(10); // November

      // AI Delay Category Filter
      const [aiCategoryFilter, setAiCategoryFilter] = useState("all");
      const [isAiGenerating, setIsAiGenerating] = useState(false);
      const [aiPlanOutput, setAiPlanOutput] = useState("");

      useEffect(() => {
        if (window.lucide) {
          window.lucide.createIcons();
        }
      }, [activeTab, trips, isCalendarOpen, aiCategoryFilter, aiPlanOutput, isMobileMenuOpen]);

      // Handle Excel Upload
      const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (evt) => {
          try {
            const data = new Uint8Array(evt.target.result);
            const workbook = XLSX.read(data, { type: "array" });
            const sheet = workbook.Sheets[workbook.SheetNames[0]];
            const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });

            const parsed = json.map((row, idx) => {
              const keys = Object.keys(row);
              const getVal = (pattern, fallback) => {
                const found = keys.find(k => pattern.test(k));
                return found !== undefined && row[found] !== "" ? String(row[found]).trim() : fallback;
              };

              let rawDate = getVal(/date|close|closing|dispatch|arrival/i, "2026-11-10");
              if (typeof row["Closing Date"] === "number") {
                const utcDays = Math.floor(row["Closing Date"] - 25569);
                rawDate = new Date(utcDays * 86400 * 1000).toISOString().split("T")[0];
              }

              const status = getVal(/status|state|trip status/i, "Trip Closed");
              const isDelay = /delay|late/i.test(status) || /yes|delay/i.test(getVal(/delay/i, ""));
              const remarks = getVal(/remark|reason|comment|notes/i, "");

              return {
                id: getVal(/trip|id|lr/i, `TRP-${1000 + idx}`),
                date: rawDate,
                vehicle: getVal(/vehicle|truck|lorry/i, `VEH-${2000 + idx}`),
                client: getVal(/client|customer|account|party/i, "General Client"),
                staff: getVal(/staff|driver|pilot/i, "Assigned Staff"),
                route: getVal(/route|corridor|from.*to/i, "Direct Corridor"),
                status: status,
                isDelay: isDelay,
                remarks: remarks
              };
            });

            if (parsed.length > 0) {
              setTrips(parsed);
            }
          } catch (err) {
            console.error("Error reading Excel", err);
          }
        };
        reader.readAsArrayBuffer(file);
      };

      // Metrics Counts
      const totalTrips = trips.length;
      const inTransitCount = trips.filter(t => t.status === "In-Transit").length;
      const closedCount = trips.filter(t => t.status === "Trip Closed" && !t.isDelay).length;
      const delayClosedCount = trips.filter(t => t.isDelay).length;

      // Aggregations
      const clientStats = useMemo(() => {
        const map = {};
        trips.forEach(t => {
          if (!map[t.client]) map[t.client] = { name: t.client, total: 0, closed: 0, delayed: 0 };
          map[t.client].total += 1;
          if (t.status === "Trip Closed" && !t.isDelay) map[t.client].closed += 1;
          if (t.isDelay) map[t.client].delayed += 1;
        });
        return Object.values(map).map(c => ({
          ...c,
          sla: c.total ? Math.round(((c.total - c.delayed) / c.total) * 100) : 100
        }));
      }, [trips]);

      const staffStats = useMemo(() => {
        const map = {};
        trips.forEach(t => {
          if (!map[t.staff]) map[t.staff] = { name: t.staff, total: 0, closed: 0, delayed: 0 };
          map[t.staff].total += 1;
          if (t.status === "Trip Closed" && !t.isDelay) map[t.staff].closed += 1;
          if (t.isDelay) map[t.staff].delayed += 1;
        });
        return Object.values(map).map(s => ({
          ...s,
          sla: s.total ? Math.round(((s.total - s.delayed) / s.total) * 100) : 100
        }));
      }, [trips]);

      const routeStats = useMemo(() => {
        const map = {};
        trips.forEach(t => {
          if (!map[t.route]) map[t.route] = { name: t.route, total: 0, closed: 0, delayed: 0 };
          map[t.route].total += 1;
          if (t.status === "Trip Closed" && !t.isDelay) map[t.route].closed += 1;
          if (t.isDelay) map[t.route].delayed += 1;
        });
        return Object.values(map).map(r => ({
          ...r,
          sla: r.total ? Math.round(((r.total - r.delayed) / r.total) * 100) : 100
        }));
      }, [trips]);

      // Day Wise Filtered Trips
      const dayWiseTrips = useMemo(() => {
        return trips.filter(t => {
          if (filterDate && t.date !== filterDate) return false;
          if (filterClient && t.client !== filterClient) return false;
          if (filterStaff && t.staff !== filterStaff) return false;
          return true;
        });
      }, [trips, filterDate, filterClient, filterStaff]);

      // Only Delay Trips
      const delayedTrips = useMemo(() => trips.filter(t => t.isDelay), [trips]);

      // AI Delay Classifier Function
      const classifyDelay = (remarks) => {
        const text = (remarks || "").toLowerCase();
        if (!text.trim()) {
          return {
            category: "Unexplained",
            action: "Issue show-cause notice & demand driver explanation",
            badgeColor: "bg-rose-500/15 text-rose-300 border-rose-500/30",
            icon: "help-circle"
          };
        }
        if (text.includes("breakdown") || text.includes("tyre") || text.includes("engine") || text.includes("puncture") || text.includes("clutch") || text.includes("repair")) {
          return {
            category: "Breakdown",
            action: "Deploy nearest authorized roadside mechanic & tow assistance",
            badgeColor: "bg-red-500/15 text-red-300 border-red-500/30",
            icon: "wrench"
          };
        }
        if (text.includes("driver") && (text.includes("issue") || text.includes("emergency") || text.includes("sick") || text.includes("leave") || text.includes("absent"))) {
          return {
            category: "Driver Issue",
            action: "Mobilize backup relief driver from hub roster immediately",
            badgeColor: "bg-amber-500/15 text-amber-300 border-amber-500/30",
            icon: "user-x"
          };
        }
        if (text.includes("traffic") || text.includes("toll") || text.includes("jam") || text.includes("congestion") || text.includes("highway") || text.includes("route blocked")) {
          return {
            category: "Traffic Jam",
            action: "Reroute via bypass corridor & alert destination dock supervisor",
            badgeColor: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
            icon: "navigation"
          };
        }
        if (text.includes("single driver") || text.includes("rest") || text.includes("fatigue") || text.includes("hours") || text.includes("sleep")) {
          return {
            category: "Single Driver Fatigue",
            action: "Verify mandatory 6-hr rest log; assign dual-driver protocol for trips >450km",
            badgeColor: "bg-purple-500/15 text-purple-300 border-purple-500/30",
            icon: "moon"
          };
        }
        if (text.includes("dock") || text.includes("unloading") || text.includes("loading") || text.includes("warehouse") || text.includes("gate") || text.includes("holding")) {
          return {
            category: "Dock Jam",
            action: "Escalate with client logistics team for priority dock bay allocation",
            badgeColor: "bg-blue-500/15 text-blue-300 border-blue-500/30",
            icon: "anchor"
          };
        }
        return {
          category: "Operational Delay",
          action: "Review telemetry log and audit transit timeline",
          badgeColor: "bg-rose-500/10 text-rose-300 border-rose-500/20",
          icon: "alert-triangle"
        };
      };

      // Categorized AI review list
      const aiDelayRecords = useMemo(() => {
        return delayedTrips.map(trip => {
          const classification = classifyDelay(trip.remarks);
          return {
            ...trip,
            classification
          };
        });
      }, [delayedTrips]);

      // Category breakdown counts
      const aiCategoryCounts = useMemo(() => {
        const counts = {
          Breakdown: 0,
          "Driver Issue": 0,
          "Traffic Jam": 0,
          "Single Driver Fatigue": 0,
          "Dock Jam": 0,
          Unexplained: 0
        };
        aiDelayRecords.forEach(r => {
          if (counts[r.classification.category] !== undefined) {
            counts[r.classification.category]++;
          }
        });
        return counts;
      }, [aiDelayRecords]);

      const filteredAiRecords = useMemo(() => {
        if (aiCategoryFilter === "all") return aiDelayRecords;
        return aiDelayRecords.filter(r => r.classification.category === aiCategoryFilter);
      }, [aiDelayRecords, aiCategoryFilter]);

      // Action Plan Generator simulation
      const handleGenerateAiPlan = () => {
        setIsAiGenerating(true);
        setTimeout(() => {
          const breakdownCount = aiCategoryCounts["Breakdown"] || 0;
          const driverCount = aiCategoryCounts["Driver Issue"] || 0;
          const trafficCount = aiCategoryCounts["Traffic Jam"] || 0;
          const singleDriverCount = aiCategoryCounts["Single Driver Fatigue"] || 0;
          const dockCount = aiCategoryCounts["Dock Jam"] || 0;
          const unexplainedCount = aiCategoryCounts["Unexplained"] || 0;

          const breakdownVehicles = aiDelayRecords
            .filter(r => r.classification.category === 'Breakdown')
            .map(r => r.vehicle)
            .join(", ") || "No current units";

          const planLines = [
            "🚨 AUTOMATED AI DISPATCH DIRECTIVE | GENERATED FOR " + new Date().toLocaleTimeString(),
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "1. MECHANICAL & ROAD REPAIRS (" + breakdownCount + " Vehicles)",
            "   ➔ Priority: Immediate emergency dispatch to " + breakdownVehicles + ". Authorize highway roadside vendor PO.",
            "",
            "2. DRIVER ALLOCATION & FATIGUE (" + (driverCount + singleDriverCount) + " Vehicles)",
            "   ➔ Action: Single-driver routes (>450km) show recurring rest stops. Mandate 2-driver staffing on Delhi-Mumbai & Pune-Bengaluru line-hauls.",
            "",
            "3. TRAFFIC & DOCK CONGESTION (" + (trafficCount + dockCount) + " Vehicles)",
            "   ➔ Directive: Advance notification to client receivers (Amazon/Reliance) to reserve dock bays 2 hours before gate arrival.",
            "",
            "4. COMPLIANCE AUDIT (" + unexplainedCount + " Vehicles without remarks)",
            "   ➔ Immediate action required: Mandatory incident reports demanded from drivers with 0 explanation tags."
          ];

          setAiPlanOutput(planLines.join("\n"));
          setIsAiGenerating(false);
        }, 500);
      };

      // Calendar helpers
      const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
      ];

      const calendarDays = useMemo(() => {
        const firstDay = new Date(calYear, calMonth, 1).getDay();
        const totalDays = new Date(calYear, calMonth + 1, 0).getDate();
        const startOffset = (firstDay + 6) % 7; // Mon start
        const days = [];
        for (let i = 0; i < startOffset; i++) days.push(null);
        for (let d = 1; d <= totalDays; d++) {
          const mStr = String(calMonth + 1).padStart(2, '0');
          const dStr = String(d).padStart(2, '0');
          const dateString = `${calYear}-${mStr}-${dStr}`;
          const hasRecords = trips.some(t => t.date === dateString);
          days.push({ day: d, dateString, hasRecords });
        }
        return days;
      }, [calYear, calMonth, trips]);

      // Company Logo Helper
      const renderCompanyLogo = (clientName) => {
        const name = (clientName || "").toLowerCase();
        if (name.includes("amazon")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#131921] border border-amber-500/30 flex items-center justify-center shrink-0" title="Amazon India">
              <span className="text-[10px] font-black text-amber-400">a</span>
            </div>
          );
        }
        if (name.includes("flipkart")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#2874f0] flex items-center justify-center shrink-0 shadow-sm" title="Flipkart Wholesale">
              <span className="text-[10px] font-black text-[#ffe500] italic">f</span>
            </div>
          );
        }
        if (name.includes("reliance")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#d8232a] flex items-center justify-center shrink-0 shadow-sm" title="Reliance Retail">
              <span className="text-[9px] font-black text-white">R</span>
            </div>
          );
        }
        if (name.includes("tata")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#0f2c59] border border-blue-400/40 flex items-center justify-center shrink-0" title="Tata Consumer">
              <span className="text-[7px] font-extrabold text-blue-200 tracking-tighter">TATA</span>
            </div>
          );
        }
        if (name.includes("bluedart")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#002b66] border border-cyan-400/30 flex items-center justify-center shrink-0" title="BlueDart Express">
              <span className="text-[8px] font-black text-cyan-300">BD</span>
            </div>
          );
        }
        if (name.includes("delhivery")) {
          return (
            <div className="w-5 h-5 rounded-md bg-[#b71c1c] flex items-center justify-center shrink-0" title="Delhivery Crossdock">
              <span className="text-[9px] font-black text-white">D</span>
            </div>
          );
        }
        return (
          <div className="w-5 h-5 rounded-md bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-300 shrink-0 text-[9px] font-bold">
            {clientName.charAt(0) || "C"}
          </div>
        );
      };

      const navItems = [
        { id: "overall", label: "Over All Performance", icon: "activity" },
        { id: "client", label: "Client Wise Performance", icon: "briefcase" },
        { id: "staff", label: "Staff Wise Performance", icon: "user" },
        { id: "daywise", label: "Day Wise Arrival Report", icon: "calendar" },
        { id: "delay", label: "Only Delay Arrival Report", icon: "alert-triangle" },
        { id: "ai_review", label: "AI Delay Review", icon: "bot" }
      ];

      return (
        <div className="min-h-screen flex flex-col md:flex-row antialiased overflow-x-hidden">

          {/* ================= MOBILE HEADER (< md screens) ================= */}
          <div className="md:hidden bg-[#120306]/95 border-b border-white/10 px-4 py-3 flex items-center justify-between sticky top-0 z-40 backdrop-blur-xl">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-rose-600 to-red-600 flex items-center justify-center shadow-md shadow-rose-950/80 shrink-0">
                <i data-lucide="shield" className="w-4 h-4 text-white"></i>
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-xs text-white tracking-tight">FLEET CONTROL</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">V5</span>
                </div>
                <p className="text-[10px] text-white/40">Logistics Mobile Center</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-xl bg-white/5 border border-white/10 text-white flex items-center justify-center focus:outline-none"
            >
              <i data-lucide={isMobileMenuOpen ? "x" : "menu"} className="w-4 h-4 text-rose-400"></i>
            </button>
          </div>

          {/* Mobile Drawer Navigation */}
          <AnimatePresence>
            {isMobileMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="md:hidden bg-[#150307] border-b border-white/10 px-4 py-3 space-y-1.5 z-30"
              >
                {navItems.map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setActiveTab(item.id);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                        isActive ? "bg-rose-600 text-white font-bold" : "text-white/70 hover:text-white hover:bg-white/5"
                      }`}
                    >
                      <i data-lucide={item.icon} className={`w-4 h-4 ${isActive ? 'text-white' : 'text-rose-400'}`}></i>
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Mobile Quick-Scroll Tab Strip */}
          <div className="md:hidden bg-[#0d0104] px-3 py-2 border-b border-white/5 overflow-x-auto flex items-center gap-2 custom-scroll">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-1.5 rounded-full text-[11px] font-semibold whitespace-nowrap transition shrink-0 ${
                    isActive ? "bg-rose-600 text-white shadow-sm" : "bg-white/5 text-white/60 hover:text-white"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          {/* ================= COMPACT LAPTOP/DESKTOP SIDEBAR (w-56) ================= */}
          <aside className="hidden md:flex md:w-56 bg-[#120306] border-r border-white/5 p-3.5 flex-col justify-between shrink-0 min-h-screen sticky top-0 h-screen">
            <div className="space-y-4">

              {/* Brand Header */}
              <div className="flex items-center gap-2.5 px-1 pt-1">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-rose-600 to-red-600 flex items-center justify-center shadow-md shadow-rose-950/80 shrink-0">
                  <i data-lucide="shield" className="w-4 h-4 text-white"></i>
                </div>
                <div className="truncate">
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-xs text-white tracking-tight">FLEET CONTROL</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">V5</span>
                  </div>
                  <p className="text-[10px] text-white/40 truncate">Logistics Command Center</p>
                </div>
              </div>

              {/* Nav Navigation Items */}
              <nav className="space-y-1.5 pt-2 relative">
                {navItems.map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <motion.button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-[11px] font-semibold transition-colors duration-150 relative z-10 ${
                        isActive ? "text-white font-bold" : "text-white/60 hover:text-white hover:bg-white/5"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 truncate z-10">
                        <i data-lucide={item.icon} className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-white' : 'text-rose-400'}`}></i>
                        <span className="truncate">{item.label}</span>
                      </div>

                      {isActive && (
                        <>
                          <motion.div
                            layoutId="activeNavBackground"
                            className="absolute inset-0 rounded-xl active-nav-pill -z-0"
                            transition={{ type: "spring", stiffness: 350, damping: 30 }}
                          />
                          <span className="w-1 h-3 bg-white rounded-full shadow-sm shrink-0 ml-1 z-10"></span>
                        </>
                      )}
                    </motion.button>
                  );
                })}
              </nav>

            </div>

            {/* Bottom Meta Status */}
            <div className="pt-3 border-t border-white/5">
              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center gap-2 text-[10px] text-white/50">
                <i data-lucide="file-spreadsheet" className="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <div className="overflow-hidden">
                  <p className="text-[9px] uppercase font-bold text-white/30 tracking-wider">Live Telemetry</p>
                  <p className="text-white/80 font-mono text-[10px] truncate">{trips.length} Dispatches Synced</p>
                </div>
              </div>
            </div>
          </aside>

          {/* ================= RIGHT WORKSPACE ================= */}
          <main className="flex-1 p-3.5 sm:p-5 md:p-7 overflow-y-auto space-y-4 sm:space-y-5">

            {/* BORDERLESS TOP BAR (NO CARD CONTAINER FOR TITLE) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
              <div>
                <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white capitalize">
                  {navItems.find(i => i.id === activeTab)?.label}
                </h2>
                <p className="text-[11px] sm:text-xs text-white/40 mt-0.5">Live operational telemetry & dispatch management</p>
              </div>

              {/* Upload & Sample buttons ONLY visible on Over All Performance */}
              {activeTab === "overall" && (
                <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap sm:flex-nowrap">
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => {
                      setTrips(INITIAL_RECORDS);
                      setFilterDate("");
                      setFilterClient("");
                      setFilterStaff("");
                    }}
                    className="px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 text-white text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    <i data-lucide="sparkles" className="w-3.5 h-3.5 text-amber-400"></i>
                    <span>Load Sample</span>
                  </motion.button>

                  <motion.label
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    className="cursor-pointer px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-rose-950/80 transition"
                  >
                    <i data-lucide="upload-cloud" className="w-3.5 h-3.5 text-white"></i>
                    <span>Upload Excel File</span>
                    <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} className="hidden" />
                  </motion.label>
                </div>
              )}
            </div>

            {/* Content Views */}
            <AnimatePresence mode="wait">

              {/* TAB 1: OVER ALL PERFORMANCE */}
              {activeTab === "overall" && (
                <motion.div
                  key="overall-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-4 sm:space-y-5"
                >
                  {/* SLEEK STATS: 2x2 ON MOBILE, INLINE ROW ON LAPTOP/DESKTOP */}
                  <div className="grid grid-cols-2 md:flex md:flex-wrap md:items-center md:justify-between gap-3 sm:gap-4 py-2 px-1 border-b border-white/5">
                    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 p-2 sm:p-0 bg-white/[0.02] sm:bg-transparent rounded-xl border border-white/5 sm:border-0">
                      <span className="text-2xl sm:text-3xl font-black text-white tracking-tight">{totalTrips}</span>
                      <div>
                        <p className="text-[10px] sm:text-[11px] font-bold text-white/70 uppercase tracking-wider">Total Fleet Trips</p>
                        <p className="text-[9px] sm:text-[10px] text-white/40 hidden sm:block">Total active recorded dispatches</p>
                      </div>
                    </div>

                    <div className="hidden md:block h-8 w-px bg-white/10"></div>

                    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 p-2 sm:p-0 bg-white/[0.02] sm:bg-transparent rounded-xl border border-white/5 sm:border-0">
                      <span className="text-2xl sm:text-3xl font-black text-blue-400 tracking-tight">{inTransitCount}</span>
                      <div>
                        <p className="text-[10px] sm:text-[11px] font-bold text-blue-400/90 uppercase tracking-wider">In-Transit Vehicle</p>
                        <p className="text-[9px] sm:text-[10px] text-white/40 hidden sm:block">Active line-haul movements</p>
                      </div>
                    </div>

                    <div className="hidden md:block h-8 w-px bg-white/10"></div>

                    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 p-2 sm:p-0 bg-white/[0.02] sm:bg-transparent rounded-xl border border-white/5 sm:border-0">
                      <span className="text-2xl sm:text-3xl font-black text-emerald-400 tracking-tight">{closedCount}</span>
                      <div>
                        <p className="text-[10px] sm:text-[11px] font-bold text-emerald-400/90 uppercase tracking-wider">Trip Closed</p>
                        <p className="text-[9px] sm:text-[10px] text-white/40 hidden sm:block">Completed on-time dispatches</p>
                      </div>
                    </div>

                    <div className="hidden md:block h-8 w-px bg-white/10"></div>

                    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 p-2 sm:p-0 bg-white/[0.02] sm:bg-transparent rounded-xl border border-white/5 sm:border-0">
                      <span className="text-2xl sm:text-3xl font-black text-rose-400 tracking-tight">{delayClosedCount}</span>
                      <div>
                        <p className="text-[10px] sm:text-[11px] font-bold text-rose-400/90 uppercase tracking-wider">Delay Closed</p>
                        <p className="text-[9px] sm:text-[10px] text-white/40 hidden sm:block">Delayed exception completions</p>
                      </div>
                    </div>
                  </div>

                  {/* 1. Client Wise Performance Report (NO In-Transit Column) */}
                  <div className="glass-panel p-3 sm:p-4 rounded-2xl space-y-2.5">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="briefcase" className="w-3.5 h-3.5 text-rose-400"></i>
                        <span>Client Wise Performance Report</span>
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono font-semibold">
                        {clientStats.length} Accounts Active
                      </span>
                    </div>

                    <div className="overflow-x-auto custom-scroll">
                      <table className="w-full text-left text-[11px] whitespace-nowrap">
                        <thead>
                          <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                            <th className="py-2 px-3">Client Name</th>
                            <th className="py-2 px-3 text-center">Total Trips</th>
                            <th className="py-2 px-3 text-center">Trip Closed</th>
                            <th className="py-2 px-3 text-center">Delay Closed</th>
                            <th className="py-2 px-3">On-Time SLA %</th>
                            <th className="py-2 px-3 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {clientStats.map((c, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                              <td className="py-2 px-3 font-semibold text-white flex items-center gap-2">
                                {renderCompanyLogo(c.name)}
                                <span>{c.name}</span>
                              </td>
                              <td className="py-2 px-3 text-center font-bold text-white font-mono">{c.total}</td>
                              <td className="py-2 px-3 text-center font-semibold text-emerald-400 font-mono">{c.closed}</td>
                              <td className="py-2 px-3 text-center font-semibold text-rose-400 font-mono">{c.delayed}</td>
                              <td className="py-2 px-3">
                                <div className="flex items-center gap-2.5">
                                  <div className="w-16 sm:w-24 bg-white/10 h-1.5 rounded-full overflow-hidden">
                                    <div
                                      style={{ width: `${c.sla}%` }}
                                      className={`h-full rounded-full ${
                                        c.sla >= 90 ? 'bg-gradient-to-r from-emerald-500 to-teal-400' :
                                        c.sla >= 60 ? 'bg-gradient-to-r from-amber-500 to-orange-400' :
                                        'bg-gradient-to-r from-rose-600 to-red-500'
                                      }`}
                                    />
                                  </div>
                                  <span className={`font-mono font-bold text-[10px] ${
                                    c.sla >= 90 ? 'text-emerald-400' :
                                    c.sla >= 60 ? 'text-amber-400' :
                                    'text-rose-400'
                                  }`}>
                                    {c.sla}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold border ${
                                  c.sla >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                  c.sla >= 60 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                  'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                }`}>
                                  {c.sla >= 90 ? 'Compliant' : c.sla >= 60 ? 'Moderate' : 'At Risk'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 2. Staff Wise Performance Report (NO In-Transit Column) */}
                  <div className="glass-panel p-3 sm:p-4 rounded-2xl space-y-2.5">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="user" className="w-3.5 h-3.5 text-rose-400"></i>
                        <span>Staff Wise Performance Report</span>
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono font-semibold">
                        {staffStats.length} Personnel
                      </span>
                    </div>

                    <div className="overflow-x-auto custom-scroll">
                      <table className="w-full text-left text-[11px] whitespace-nowrap">
                        <thead>
                          <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                            <th className="py-2 px-3">Staff / Driver</th>
                            <th className="py-2 px-3 text-center">Total Assigned</th>
                            <th className="py-2 px-3 text-center">Trip Closed</th>
                            <th className="py-2 px-3 text-center">Delay Closed</th>
                            <th className="py-2 px-3">On-Time SLA %</th>
                            <th className="py-2 px-3 text-right">Rating</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {staffStats.map((s, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                              <td className="py-2 px-3 font-semibold text-white flex items-center gap-2">
                                <div className="w-5 h-5 rounded-md bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                                  <i data-lucide="user" className="w-3 h-3"></i>
                                </div>
                                <span>{s.name}</span>
                              </td>
                              <td className="py-2 px-3 text-center font-bold text-white font-mono">{s.total}</td>
                              <td className="py-2 px-3 text-center font-semibold text-emerald-400 font-mono">{s.closed}</td>
                              <td className="py-2 px-3 text-center font-semibold text-rose-400 font-mono">{s.delayed}</td>
                              <td className="py-2 px-3">
                                <div className="flex items-center gap-2.5">
                                  <div className="w-16 sm:w-24 bg-white/10 h-1.5 rounded-full overflow-hidden">
                                    <div
                                      style={{ width: `${s.sla}%` }}
                                      className={`h-full rounded-full ${
                                        s.sla >= 90 ? 'bg-gradient-to-r from-emerald-500 to-teal-400' :
                                        s.sla >= 60 ? 'bg-gradient-to-r from-amber-500 to-orange-400' :
                                        'bg-gradient-to-r from-rose-600 to-red-500'
                                      }`}
                                    />
                                  </div>
                                  <span className={`font-mono font-bold text-[10px] ${
                                    s.sla >= 90 ? 'text-emerald-400' :
                                    s.sla >= 60 ? 'text-amber-400' :
                                    'text-rose-400'
                                  }`}>
                                    {s.sla}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold border ${
                                  s.sla >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                  s.sla >= 60 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                  'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                }`}>
                                  {s.sla >= 90 ? 'Top Pilot' : s.sla >= 60 ? 'Satisfactory' : 'Needs Review'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 3. Route Wise Performance Report (NO In-Transit Column) */}
                  <div className="glass-panel p-3 sm:p-4 rounded-2xl space-y-2.5">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="map-pin" className="w-3.5 h-3.5 text-rose-400"></i>
                        <span>Route Wise Performance Report</span>
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono font-semibold">
                        {routeStats.length} Corridors
                      </span>
                    </div>

                    <div className="overflow-x-auto custom-scroll">
                      <table className="w-full text-left text-[11px] whitespace-nowrap">
                        <thead>
                          <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                            <th className="py-2 px-3">Route / Corridor</th>
                            <th className="py-2 px-3 text-center">Total Dispatches</th>
                            <th className="py-2 px-3 text-center">Trip Closed</th>
                            <th className="py-2 px-3 text-center">Delay Closed</th>
                            <th className="py-2 px-3">Corridor SLA %</th>
                            <th className="py-2 px-3 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {routeStats.map((r, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                              <td className="py-2 px-3 font-semibold text-white flex items-center gap-2">
                                <div className="w-5 h-5 rounded-md bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                                  <i data-lucide="corner-down-right" className="w-3 h-3"></i>
                                </div>
                                <span>{r.name}</span>
                              </td>
                              <td className="py-2 px-3 text-center font-bold text-white font-mono">{r.total}</td>
                              <td className="py-2 px-3 text-center font-semibold text-emerald-400 font-mono">{r.closed}</td>
                              <td className="py-2 px-3 text-center font-semibold text-rose-400 font-mono">{r.delayed}</td>
                              <td className="py-2 px-3">
                                <div className="flex items-center gap-2.5">
                                  <div className="w-16 sm:w-24 bg-white/10 h-1.5 rounded-full overflow-hidden">
                                    <div
                                      style={{ width: `${r.sla}%` }}
                                      className={`h-full rounded-full ${
                                        r.sla >= 90 ? 'bg-gradient-to-r from-emerald-500 to-teal-400' :
                                        r.sla >= 60 ? 'bg-gradient-to-r from-amber-500 to-orange-400' :
                                        'bg-gradient-to-r from-rose-600 to-red-500'
                                      }`}
                                    />
                                  </div>
                                  <span className={`font-mono font-bold text-[10px] ${
                                    r.sla >= 90 ? 'text-emerald-400' :
                                    r.sla >= 60 ? 'text-amber-400' :
                                    'text-rose-400'
                                  }`}>
                                    {r.sla}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold border ${
                                  r.sla >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                  r.sla >= 60 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                  'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                }`}>
                                  {r.sla >= 90 ? 'Optimal' : r.sla >= 60 ? 'Congested' : 'Bottleneck'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </motion.div>
              )}

              {/* TAB 2: CLIENT WISE PERFORMANCE */}
              {activeTab === "client" && (
                <motion.div
                  key="client-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="glass-panel p-3.5 sm:p-5 rounded-2xl space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">Client Portfolio Compliance</h3>
                      <p className="text-[11px] sm:text-xs text-white/40">Detailed accounts breakdown, SLA compliance, and closed shipment volume</p>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
                      {clientStats.length} Accounts
                    </span>
                  </div>

                  <div className="overflow-x-auto custom-scroll">
                    <table className="w-full text-left text-xs whitespace-nowrap">
                      <thead>
                        <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                          <th className="py-2.5 px-3">Client</th>
                          <th className="py-2.5 px-3 text-center">Total Trips</th>
                          <th className="py-2.5 px-3 text-center">Trip Closed</th>
                          <th className="py-2.5 px-3 text-center">Delay Closed</th>
                          <th className="py-2.5 px-3">SLA Compliance</th>
                          <th className="py-2.5 px-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {clientStats.map((c, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-2">
                              {renderCompanyLogo(c.name)}
                              <span>{c.name}</span>
                            </td>
                            <td className="py-2.5 px-3 text-center font-bold text-white font-mono">{c.total}</td>
                            <td className="py-2.5 px-3 text-center font-semibold text-emerald-400 font-mono">{c.closed}</td>
                            <td className="py-2.5 px-3 text-center font-semibold text-rose-400 font-mono">{c.delayed}</td>
                            <td className="py-2.5 px-3">
                              <span className="font-bold text-rose-400 font-mono">{c.sla}% SLA</span>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                                c.sla >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                'bg-rose-500/10 text-rose-400 border-rose-500/20'
                              }`}>
                                {c.sla >= 90 ? 'Compliant' : 'Needs Review'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}

              {/* TAB 3: STAFF WISE PERFORMANCE */}
              {activeTab === "staff" && (
                <motion.div
                  key="staff-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="glass-panel p-3.5 sm:p-5 rounded-2xl space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">Staff / Driver Operational Ledger</h3>
                      <p className="text-[11px] sm:text-xs text-white/40">Assignment volumes, closed clean shipments, and driver compliance</p>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
                      {staffStats.length} Drivers
                    </span>
                  </div>

                  <div className="overflow-x-auto custom-scroll">
                    <table className="w-full text-left text-xs whitespace-nowrap">
                      <thead>
                        <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                          <th className="py-2.5 px-3">Staff / Driver</th>
                          <th className="py-2.5 px-3 text-center">Total Assigned</th>
                          <th className="py-2.5 px-3 text-center">Trip Closed</th>
                          <th className="py-2.5 px-3 text-center">Delay Closed</th>
                          <th className="py-2.5 px-3">Driver SLA %</th>
                          <th className="py-2.5 px-3 text-right">Rating</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {staffStats.map((s, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-2">
                              <i data-lucide="user" className="w-3.5 h-3.5 text-rose-400"></i>
                              <span>{s.name}</span>
                            </td>
                            <td className="py-2.5 px-3 text-center font-bold text-white font-mono">{s.total}</td>
                            <td className="py-2.5 px-3 text-center font-semibold text-emerald-400 font-mono">{s.closed}</td>
                            <td className="py-2.5 px-3 text-center font-semibold text-rose-400 font-mono">{s.delayed}</td>
                            <td className="py-2.5 px-3">
                              <span className="font-bold text-rose-400 font-mono">{s.sla}% SLA</span>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                                s.sla >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              }`}>
                                {s.sla >= 90 ? 'Top Pilot' : 'Satisfactory'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}

              {/* TAB 4: DAY WISE ARRIVAL REPORT */}
              {activeTab === "daywise" && (
                <motion.div
                  key="daywise-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="glass-panel p-3.5 sm:p-5 rounded-2xl space-y-4"
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-white">Day Wise Arrival Chronology</h3>
                      <p className="text-[11px] sm:text-xs text-white/40">Chronological vehicle arrivals with calendar date, client, and staff selectors</p>
                    </div>

                    {/* Filter Controls Row */}
                    <div className="flex flex-wrap items-center gap-2">

                      {/* 1. Compact Interactive Calendar Pop-up */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setIsCalendarOpen(!isCalendarOpen)}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition shadow-md ${
                            filterDate
                              ? "bg-rose-500/20 border-rose-500 text-rose-200"
                              : "bg-[#1f050b] hover:bg-[#28070e] border-rose-500/30 text-white"
                          }`}
                        >
                          <i data-lucide="calendar" className="w-3.5 h-3.5 text-rose-400"></i>
                          <span>{filterDate || "Select Date"}</span>
                          <i data-lucide={isCalendarOpen ? "chevron-up" : "chevron-down"} className="w-3 h-3 text-white/50"></i>
                        </button>

                        {/* Dropdown Calendar (w-60 compact, touch friendly) */}
                        <AnimatePresence>
                          {isCalendarOpen && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.95, y: -5 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.95, y: -5 }}
                              transition={{ duration: 0.15 }}
                              className="absolute left-0 sm:left-auto sm:right-0 top-10 z-50 w-60 p-3 rounded-2xl bg-[#190308]/98 backdrop-blur-2xl border border-rose-500/30 shadow-2xl shadow-black/95 space-y-2"
                            >
                              {/* Month Nav */}
                              <div className="flex items-center justify-between">
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (calMonth === 0) { setCalMonth(11); setCalYear(y => y - 1); }
                                    else { setCalMonth(m => m - 1); }
                                  }}
                                  className="w-5 h-5 rounded bg-white/5 hover:bg-rose-500/20 text-white flex items-center justify-center transition"
                                >
                                  <i data-lucide="chevron-left" className="w-3 h-3"></i>
                                </button>
                                <span className="text-[11px] font-bold text-white">
                                  {monthNames[calMonth]} {calYear}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (calMonth === 11) { setCalMonth(0); setCalYear(y => y + 1); }
                                    else { setCalMonth(m => m + 1); }
                                  }}
                                  className="w-5 h-5 rounded bg-white/5 hover:bg-rose-500/20 text-white flex items-center justify-center transition"
                                >
                                  <i data-lucide="chevron-right" className="w-3 h-3"></i>
                                </button>
                              </div>

                              {/* Days Header */}
                              <div className="grid grid-cols-7 gap-0.5 text-center text-[9px] font-bold text-rose-300/60 uppercase">
                                <span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span><span>Su</span>
                              </div>

                              {/* Days Grid */}
                              <div className="grid grid-cols-7 gap-0.5 text-center">
                                {calendarDays.map((item, idx) => {
                                  if (!item) return <div key={`empty-${idx}`} className="h-5 w-5"></div>;
                                  const isSelected = filterDate === item.dateString;
                                  return (
                                    <button
                                      key={item.dateString}
                                      type="button"
                                      onClick={() => {
                                        setFilterDate(item.dateString);
                                        setIsCalendarOpen(false);
                                      }}
                                      className={`h-5 w-5 mx-auto rounded text-[10px] font-medium flex items-center justify-center transition ${
                                        isSelected
                                          ? "bg-rose-600 text-white font-bold"
                                          : item.hasRecords
                                          ? "bg-rose-500/15 text-rose-200 hover:bg-rose-500/30 font-semibold"
                                          : "text-white/40 hover:text-white"
                                      }`}
                                    >
                                      {item.day}
                                    </button>
                                  );
                                })}
                              </div>

                              {/* Clear / Close Bottom Buttons */}
                              <div className="flex items-center justify-between pt-1 border-t border-white/10 text-[10px]">
                                <button
                                  type="button"
                                  onClick={() => { setFilterDate(""); setIsCalendarOpen(false); }}
                                  className="text-white/40 hover:text-rose-400 transition"
                                >
                                  Clear Date
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setIsCalendarOpen(false)}
                                  className="px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-white font-semibold transition"
                                >
                                  Close
                                </button>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      {/* 2. Client Filter Dropdown Button */}
                      <div className="relative">
                        <select
                          value={filterClient}
                          onChange={(e) => setFilterClient(e.target.value)}
                          className="bg-[#1f050b] hover:bg-[#28070e] border border-rose-500/30 text-white text-xs font-semibold px-2.5 py-1.5 rounded-xl outline-none transition cursor-pointer max-w-[130px] sm:max-w-none truncate"
                        >
                          <option value="">All Clients</option>
                          {clientStats.map(c => (
                            <option key={c.name} value={c.name}>{c.name}</option>
                          ))}
                        </select>
                      </div>

                      {/* 3. Staff Filter Dropdown Button */}
                      <div className="relative">
                        <select
                          value={filterStaff}
                          onChange={(e) => setFilterStaff(e.target.value)}
                          className="bg-[#1f050b] hover:bg-[#28070e] border border-rose-500/30 text-white text-xs font-semibold px-2.5 py-1.5 rounded-xl outline-none transition cursor-pointer max-w-[130px] sm:max-w-none truncate"
                        >
                          <option value="">All Staff / Drivers</option>
                          {staffStats.map(s => (
                            <option key={s.name} value={s.name}>{s.name}</option>
                          ))}
                        </select>
                      </div>

                      {/* Reset All Filters Button */}
                      {(filterDate || filterClient || filterStaff) && (
                        <button
                          type="button"
                          onClick={() => {
                            setFilterDate("");
                            setFilterClient("");
                            setFilterStaff("");
                          }}
                          className="px-2.5 py-1.5 rounded-xl bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/40 text-xs font-semibold flex items-center gap-1 transition"
                        >
                          <i data-lucide="rotate-ccw" className="w-3 h-3"></i>
                          <span>Reset</span>
                        </button>
                      )}

                    </div>
                  </div>

                  {/* Clean Arrival Table with NO Arrival Date Column */}
                  <div className="overflow-x-auto custom-scroll">
                    <table className="w-full text-left text-xs whitespace-nowrap">
                      <thead>
                        <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                          <th className="py-2.5 px-3">Vehicle No</th>
                          <th className="py-2.5 px-3">Client</th>
                          <th className="py-2.5 px-3">Staff / Driver</th>
                          <th className="py-2.5 px-3">Route</th>
                          <th className="py-2.5 px-3">Arrival Status</th>
                          <th className="py-2.5 px-3">Remarks</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {dayWiseTrips.map((t, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-2.5 px-3 font-mono font-bold text-white">{t.vehicle}</td>
                            <td className="py-2.5 px-3 font-semibold text-white/90 flex items-center gap-2">
                              {renderCompanyLogo(t.client)}
                              <span>{t.client}</span>
                            </td>
                            <td className="py-2.5 px-3 text-white/75">{t.staff}</td>
                            <td className="py-2.5 px-3 text-white/80">{t.route}</td>
                            <td className="py-2.5 px-3">
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                                t.status === "In-Transit" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                                t.isDelay ? "bg-rose-500/10 text-rose-400 border-rose-500/20" :
                                "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              }`}>
                                {t.status}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-white/60">
                              {t.remarks || <span className="text-white/20 italic">None</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}

              {/* TAB 5: ONLY DELAY ARRIVAL REPORT */}
              {activeTab === "delay" && (
                <motion.div
                  key="delay-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="glass-panel p-3.5 sm:p-5 rounded-2xl space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="alert-triangle" className="w-3.5 h-3.5 text-rose-400"></i>
                        <span>Only Delay Arrival Exception Report</span>
                      </h3>
                      <p className="text-[11px] sm:text-xs text-white/40">Isolates delayed dispatches and highlights unexplained delays without remarks</p>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold font-mono">
                      {delayedTrips.length} Delayed Units
                    </span>
                  </div>

                  <div className="overflow-x-auto custom-scroll">
                    <table className="w-full text-left text-xs whitespace-nowrap">
                      <thead>
                        <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                          <th className="py-2.5 px-3">Vehicle No</th>
                          <th className="py-2.5 px-3">Client</th>
                          <th className="py-2.5 px-3">Staff / Driver</th>
                          <th className="py-2.5 px-3">Corridor</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Delay Justification</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {delayedTrips.map((t, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-2.5 px-3 font-mono font-bold text-rose-400">{t.vehicle}</td>
                            <td className="py-2.5 px-3 text-white/90 flex items-center gap-2">
                              {renderCompanyLogo(t.client)}
                              <span>{t.client}</span>
                            </td>
                            <td className="py-2.5 px-3 text-white/75">{t.staff}</td>
                            <td className="py-2.5 px-3 text-white/80">{t.route}</td>
                            <td className="py-2.5 px-3">
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                {t.status}
                              </span>
                            </td>
                            <td className="py-2.5 px-3">
                              {t.remarks ? (
                                <span className="text-white/80">{t.remarks}</span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] font-bold">
                                  <i data-lucide="alert-circle" className="w-3 h-3 text-rose-400"></i>
                                  Delay w/o Remarks ⚠️
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}

              {/* TAB 6: AI DELAY REVIEW (DIRECT OPERATIONAL ACTION DIRECTIVES) */}
              {activeTab === "ai_review" && (
                <motion.div
                  key="ai-review-tab"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-4"
                >
                  {/* AI Review Header with Generate Action Plan Button */}
                  <div className="glass-panel p-3.5 sm:p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="bot" className="w-4 h-4 text-rose-400"></i>
                        <span>AI Delay Review & Action Intelligence</span>
                      </h3>
                      <p className="text-[11px] sm:text-xs text-white/40">Analyzes delay remarks and generates immediate operational interventions</p>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={handleGenerateAiPlan}
                      disabled={isAiGenerating}
                      className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-rose-950/80 transition shrink-0"
                    >
                      <i data-lucide="sparkles" className={`w-3.5 h-3.5 ${isAiGenerating ? 'animate-spin' : 'text-amber-300'}`}></i>
                      <span>{isAiGenerating ? "Synthesizing Directives..." : "Generate AI Action Plan"}</span>
                    </motion.button>
                  </div>

                  {/* AI Generated Action Plan Output Box (if generated) */}
                  {aiPlanOutput && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="p-3.5 sm:p-4 rounded-2xl bg-gradient-to-br from-rose-950/60 to-black/80 border border-rose-500/40 shadow-xl space-y-2 font-mono text-xs text-rose-100"
                    >
                      <div className="flex items-center justify-between border-b border-rose-500/30 pb-2">
                        <span className="font-bold flex items-center gap-1.5 text-white text-[11px] sm:text-xs">
                          <i data-lucide="check-circle" className="w-3.5 h-3.5 text-emerald-400"></i>
                          Operational Response Plan Ready
                        </span>
                        <button
                          type="button"
                          onClick={() => setAiPlanOutput("")}
                          className="text-white/40 hover:text-white"
                        >
                          <i data-lucide="x" className="w-3.5 h-3.5"></i>
                        </button>
                      </div>
                      <pre className="whitespace-pre-wrap leading-relaxed text-[10px] sm:text-[11px] text-white/90 custom-scroll overflow-x-auto">
                        {aiPlanOutput}
                      </pre>
                    </motion.div>
                  )}

                  {/* Root Cause Category Filters */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                    {[
                      { key: "Breakdown", label: "Breakdowns", count: aiCategoryCounts["Breakdown"], icon: "wrench", color: "text-red-400" },
                      { key: "Driver Issue", label: "Driver Issues", count: aiCategoryCounts["Driver Issue"], icon: "user-x", color: "text-amber-400" },
                      { key: "Traffic Jam", label: "Traffic Jams", count: aiCategoryCounts["Traffic Jam"], icon: "navigation", color: "text-yellow-400" },
                      { key: "Single Driver Fatigue", label: "Driver Rest", count: aiCategoryCounts["Single Driver Fatigue"], icon: "moon", color: "text-purple-400" },
                      { key: "Dock Jam", label: "Dock Holds", count: aiCategoryCounts["Dock Jam"], icon: "anchor", color: "text-blue-400" },
                      { key: "Unexplained", label: "No Remarks", count: aiCategoryCounts["Unexplained"], icon: "help-circle", color: "text-rose-400" }
                    ].map(cat => {
                      const isSelected = aiCategoryFilter === cat.key;
                      return (
                        <button
                          key={cat.key}
                          type="button"
                          onClick={() => setAiCategoryFilter(isSelected ? "all" : cat.key)}
                          className={`p-2.5 rounded-xl border text-left transition ${
                            isSelected
                              ? "bg-rose-500/25 border-rose-500 shadow-md shadow-rose-950/60"
                              : "bg-white/[0.02] border-white/5 hover:border-white/20"
                          }`}
                        >
                          <div className="flex items-center justify-between text-white/40 text-[10px]">
                            <span className="truncate font-semibold">{cat.label}</span>
                            <i data-lucide={cat.icon} className={`w-3 h-3 ${cat.color}`}></i>
                          </div>
                          <div className="text-base sm:text-lg font-black text-white mt-1">{cat.count}</div>
                        </button>
                      );
                    })}
                  </div>

                  {/* AI Classified Action Items Table */}
                  <div className="glass-panel p-3 sm:p-4 rounded-2xl space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">Actionable Intervention Matrix</span>
                        {aiCategoryFilter !== "all" && (
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                            Filtered: {aiCategoryFilter}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-white/40">
                        {filteredAiRecords.length} vehicles requiring operational action
                      </span>
                    </div>

                    <div className="overflow-x-auto custom-scroll">
                      <table className="w-full text-left text-xs whitespace-nowrap">
                        <thead>
                          <tr className="border-b border-white/10 text-white/40 uppercase tracking-wider text-[10px]">
                            <th className="py-2.5 px-3">Vehicle No</th>
                            <th className="py-2.5 px-3">Client</th>
                            <th className="py-2.5 px-3">Driver / Staff</th>
                            <th className="py-2.5 px-3">Identified Root Cause</th>
                            <th className="py-2.5 px-3">Delay Remarks</th>
                            <th className="py-2.5 px-3">Prescribed Action / Directive</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {filteredAiRecords.map((item, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02]">
                              <td className="py-2.5 px-3 font-mono font-bold text-rose-400">{item.vehicle}</td>
                              <td className="py-2.5 px-3 font-semibold text-white/90 flex items-center gap-1.5">
                                {renderCompanyLogo(item.client)}
                                <span>{item.client}</span>
                              </td>
                              <td className="py-2.5 px-3 text-white/80">{item.staff}</td>
                              <td className="py-2.5 px-3">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${item.classification.badgeColor}`}>
                                  {item.classification.category}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-white/70 max-w-xs truncate">
                                {item.remarks ? item.remarks : <span className="text-rose-400 font-bold italic">Missing Remarks ⚠️</span>}
                              </td>
                              <td className="py-2.5 px-3 text-emerald-300 font-medium">
                                <div className="flex items-center gap-1.5">
                                  <i data-lucide="arrow-right-circle" className="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                                  <span>{item.classification.action}</span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </motion.div>
              )}

            </AnimatePresence>

          </main>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById("root")).render(<FleetDashboard />);
  </script>
</body>
</html>
