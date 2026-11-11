import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Fleet Operations Command Center",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit ke default margins aur header ko hide karne ke liye CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0rem !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

html_code = """<!DOCTYPE html>
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
    const { useState, useMemo, useEffect } = React;

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
      const initial = (name || 'C').charAt(0).toUpperCase();
      return (
        <div className="w-5 h-5 rounded-md bg-wine-800 border border-wine-500/30 flex items-center justify-center shrink-0" title={name}>
          <span className="text
