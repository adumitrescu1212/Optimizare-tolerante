import streamlit as st
import numpy as np
import pandas as pd
import requests
import time
from agent_tester import AgentTester
from agent_proiectant import AgentProiectant
from model_matematic import functia_de_joc, valori_nominale

st.set_page_config(page_title="Optimizare Tolerante DD", page_icon="⚙️", layout="wide")

# ---------- Dictionar traduceri ----------
LANG = {
    'ro': {
        'tab1': "🏠 Acasa", 'tab2': "📊 Optimizare", 'tab3': "📈 Grafice",
        'tab4': "📖 Despre", 'tab5': "📐 Matematica",
        'params': "⚡ Parametri",
        'alpha': "Alpha (memorie fractionara)",
        'alpha_help': "0.1 = memorie lunga | 1.0 = memorie scurta",
        'delta': "Delta (pas ajustare)",
        'delta_help': "Cat de mult se modifica tolerantele la fiecare pas",
        'tol': "Toleranta initiala (mm)",
        'tol_help': "Toate cele 6 cote pornesc cu aceasta valoare",
        'run': "▶️ Ruleaza optimizarea",
        'wait': "Configureaza parametrii in panoul din stanga si apasa **Ruleaza optimizarea**.",
        'defect': "🔴 DEFECT la cota",
        'ok': "🟢 OK",
        'conv': "✅ CONVERGENTA atinsa in",
        'iterations': "Iteratii totale",
        'cost_opt': "Cost optim",
        'cost_init': "Cost initial",
        'tol_header': "Tolerante optime",
        'mc_header': "🎲 Simulare Monte Carlo",
        'mc_samples': "Esantioane",
        'mc_defects': "Defecte gasite",
        'mc_prob': "Probabilitate de defect",
        'mc_dist': "Distributie",
        'comp_header': "📊 Comparatie cu metodele clasice",
        'export': "📥 Exporta rezultatele (CSV)",
        'grafice_warn': "⚠️ Ruleaza mai intai optimizarea din tab-ul Optimizare.",
        'history': "📋 Istoricul complet al iteratiilor",
        'chart_cost': "Evolutia costului",
        'chart_beta': "Dinamica Beta",
        'chart_joc': "Evolutia jocului minim",
        'cap_cost': "Costul creste pe masura ce tolerantele sunt stranse. Un cost mai mic = fabricatie mai ieftina.",
        'cap_beta': "Beta reflecta starea neuronului fractionar. ~0.85 = sistem alert (strange agresiv). ~0.15 = sistem stabil (ajustari fine).",
        'cap_joc': "Jocul minim evolueaza de la negativ (interferenta) spre zero. Pozitiv = ansamblul functioneaza.",
        'joc_label': "Joc =",
        'cote': ['Diametru stift', 'Diametru gaura', 'DistX baza', 'DistY baza', 'DistX capac', 'DistY capac'],
    },
    'en': {
        'tab1': "🏠 Home", 'tab2': "📊 Optimization", 'tab3': "📈 Charts",
        'tab4': "📖 About", 'tab5': "📐 Mathematics",
        'params': "⚡ Parameters",
        'alpha': "Alpha (fractional memory)",
        'alpha_help': "0.1 = long memory | 1.0 = short memory",
        'delta': "Delta (adjustment step)",
        'delta_help': "How much tolerances change at each step",
        'tol': "Initial tolerance (mm)",
        'tol_help': "All 6 dimensions start with this value",
        'run': "▶️ Run Optimization",
        'wait': "Set parameters in the left panel and press **Run Optimization**.",
        'defect': "🔴 DEFECT at dimension",
        'ok': "🟢 OK",
        'conv': "✅ CONVERGENCE reached in",
        'iterations': "Total Iterations",
        'cost_opt': "Optimal Cost",
        'cost_init': "Initial Cost",
        'tol_header': "Optimal Tolerances",
        'mc_header': "🎲 Monte Carlo Simulation",
        'mc_samples': "Samples",
        'mc_defects': "Defects Found",
        'mc_prob': "Defect Probability",
        'mc_dist': "Distribution",
        'comp_header': "📊 Comparison with Classical Methods",
        'export': "📥 Export Results (CSV)",
        'grafice_warn': "⚠️ Run the optimization first from the Optimization tab.",
        'history': "📋 Complete Iteration History",
        'chart_cost': "Cost Evolution",
        'chart_beta': "Beta Dynamics",
        'chart_joc': "Gap Evolution",
        'cap_cost': "Cost increases as tolerances are tightened. Lower = cheaper manufacturing.",
        'cap_beta': "Beta reflects the fractional neuron state. ~0.85 = alert (tightens aggressively). ~0.15 = stable (fine adjustments).",
        'cap_joc': "Gap evolves from negative (interference) towards zero. Positive = assembly works.",
        'joc_label': "Gap =",
        'cote': ['Pin Diameter', 'Hole Diameter', 'DistX base', 'DistY base', 'DistX cover', 'DistY cover'],
    }
}

# ---------- Initializare ----------
if 'lang' not in st.session_state:
    st.session_state.lang = 'ro'
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

t = LANG[st.session_state.lang]

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("""
    <style>
        div[data-testid="stHorizontalBlock"] button {
            padding: 2px 8px !important;
            font-size: 12px !important;
            min-height: 0px !important;
            height: auto !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("RO", use_container_width=True, key="btn_ro"):
            st.session_state.lang = 'ro'
    with col2:
        if st.button("EN", use_container_width=True, key="btn_en"):
            st.session_state.lang = 'en'
    with col3:
        theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        if st.button(theme_icon, use_container_width=True, key="btn_theme"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
    
    st.divider()
    st.header(t['params'])
    
    alpha = st.slider(t['alpha'], 0.10, 1.00, 0.70, 0.05, help=t['alpha_help'])
    delta = st.slider(t['delta'], 0.01, 0.50, 0.20, 0.01, help=t['delta_help'])
    tol_init = st.slider(t['tol'], 0.010, 1.000, 0.500, 0.005, help=t['tol_help'])
    
    st.divider()
    run = st.button(t['run'], type="primary", use_container_width=True)
    mod_rapid = st.checkbox("⚡ Mod rapid", value=False, 
                            help="Optimizare fara animatie. Rezultate instant.")
# ---------- Dark theme ----------
if st.session_state.theme == 'dark':
    st.markdown("""
    <style>
        .stApp { background-color: #0e1117 !important; color: #fafafa !important; }
        div[style*="background: #f8f9fa"] { background-color: #1a1c23 !important; border-color: #2d3139 !important; }
        div[style*="background: #f0f4ff"] { background-color: #1a1c23 !important; border-color: #2d3139 !important; }
        div[style*="background: linear-gradient"] { opacity: 0.9; }
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
        .stMarkdown li, .stMarkdown strong { color: #e0e0e0 !important; }
        div[style*="background: linear-gradient"] p,
        div[style*="background: linear-gradient"] strong { color: white !important; }
        div[data-testid="stMetric"] { background-color: #1a1c23 !important; }
        div[data-testid="stMetric"] label { color: #999 !important; }
        div[data-testid="stMetric"] div { color: #fafafa !important; }
        blockquote { background-color: #1a1c23 !important; border-left: 4px solid #667eea !important; color: #e0e0e0 !important; }
        .stDataFrame > div > div { background-color: #1a1c23 !important; }
        div[data-testid="stAlert"] { background-color: #1a1c23 !important; }
        .stTabs [data-baseweb="tab-list"] { background-color: #1a1c23 !important; }
        .stTabs [aria-selected="true"] { background-color: #2d3139 !important; color: #fafafa !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------- CSS tab-uri ----------
# ---------- CSS modern ----------
st.markdown("""
<style>
    /* Font modern */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Tab-uri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: white;
        border-radius: 12px;
        padding: 6px;
        border: 1px solid rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 6px 18px;
        font-size: 15px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 8px rgba(102,126,234,0.12);
    }
    
    /* Carduri */
    div[style*="background: #f8f9fa"] {
        background: white !important;
        border: 1px solid rgba(0,0,0,0.06) !important;
        border-radius: 12px !important;
        transition: box-shadow 0.3s ease !important;
    }
    div[style*="background: #f8f9fa"]:hover {
        box-shadow: 0 4px 16px rgba(102,126,234,0.08) !important;
    }
    
    /* Buton principal */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(102,126,234,0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Metrici */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid rgba(0,0,0,0.06) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    
    /* Tabele */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid rgba(0,0,0,0.06) !important;
    }
    
    /* Background */
    .stApp {
        background: #f8f9fa !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: white !important;
        border-right: 1px solid rgba(0,0,0,0.06) !important;
    }
</style>
""", unsafe_allow_html=True)
# ---------- Tab-uri ----------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    t['tab1'], t['tab2'], t['tab3'], t['tab4'], t['tab5'], "💬 Asistent AI"
])

# ================================================================
# TAB 1: ACASA
# ================================================================
with tab1:
    if st.session_state.lang == 'ro':
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="font-size: 2.2rem; margin-bottom: 0.5rem;">⚙️ Sistem Multi-Agent cu Neuron Fractionar</h1>
            <p style="font-size: 1.1rem; color: #666;">Optimizarea tolerantelor pentru ansambluri mecanice</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="display: flex; justify-content: center;">
            <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/ansamblu.gif" width="700">
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin: 20px 0;">
            <p style="font-size: 0.95rem; line-height: 1.6; margin: 0; text-align: center;">
            Acest proiect propune o <strong>metoda noua</strong> de optimizare a tolerantelor,
            bazata pe o <strong>arhitectura multi-agent adversiala</strong> cu <strong>neuron fractionar</strong>.
            Doi agenti software interactioneaza iterativ pentru a gasi
            <strong>cel mai ieftin set de tolerante</strong> care garanteaza functionalitatea.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="font-size: 2.2rem; margin-bottom: 0.5rem;">⚙️ Multi-Agent System with Fractional Neuron</h1>
            <p style="font-size: 1.1rem; color: #666;">Tolerance Optimization for Mechanical Assemblies</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="display: flex; justify-content: center;">
            <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/ansamblu.gif" width="700">
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin: 20px 0;">
            <p style="font-size: 0.95rem; line-height: 1.6; margin: 0; text-align: center;">
            This project proposes a <strong>novel method</strong> for dimensional tolerance optimization,
            based on an <strong>adversarial multi-agent architecture</strong> with a <strong>fractional neuron</strong>.
            Two software agents interact iteratively to find the
            <strong>cheapest tolerance set</strong> that guarantees assembly functionality.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #667eea;">2</h2>
            <p style="margin: 5px 0 0 0; color: #555;">Agenti software autonomi</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #764ba2;">64</h2>
            <p style="margin: 5px 0 0 0; color: #555;">Colturi verificate exhaustiv</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #e74c3c;">< 1s</h2>
            <p style="margin: 5px 0 0 0; color: #555;">Timp de executie</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.lang == 'ro':
            st.markdown("""
            ### 🔴 Problema
            In fabricatia mecanica, **tolerantele dimensionale** reprezinta un compromis fundamental:
            - **Tolerante stranse** garanteaza asamblarea, dar costa foarte mult
            - **Tolerante largi** sunt economice, dar risca rebuturi
            Metodele traditionale trateaza optimizarea si analiza ca procese separate.
            """)
        else:
            st.markdown("""
            ### 🔴 The Problem
            In mechanical manufacturing, **dimensional tolerances** represent a fundamental trade-off:
            - **Tight tolerances** guarantee assembly but are very expensive
            - **Wide tolerances** are economical but risk defects
            Traditional methods treat optimization and analysis as separate processes.
            """)
    with col2:
        if st.session_state.lang == 'ro':
            st.markdown("""
            ### 🟢 Solutia noastra
            Un **sistem multi-agent** cu doi roboti software care invata unul de la celalalt:
            - **🔵 Proiectantul** vrea tolerante cat mai largi (cost minim)
            - **🔴 Testerul** ataca fiecare propunere, cautand vulnerabilitati
            - **🧠 Neuronul fractionar** controleaza adaptiv agresivitatea
            """)
        else:
            st.markdown("""
            ### 🟢 Our Solution
            A **multi-agent system** with two software robots that learn from each other:
            - **🔵 The Designer** wants tolerances as wide as possible
            - **🔴 The Tester** attacks each proposal, searching for vulnerabilities
            - **🧠 The Fractional Neuron** adaptively controls aggressiveness
            """)
    
    st.divider()
    
    if st.session_state.lang == 'ro':
        st.markdown("### 🔬 Domenii de cercetare implicate")
    else:
        st.markdown("### 🔬 Research Areas Involved")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown("**🤖 Inteligenta artificiala**\nSisteme multi-agent")
    with col2: st.markdown("**📐 Calcul fractionar**\nDerivata Grunwald-Letnikov")
    with col3: st.markdown("**⚡ Optimizare**\nCercetari operationale")
    with col4: st.markdown("**🔧 Inginerie mecanica**\nSolidWorks CAD")
    
    st.divider()
    
    if st.session_state.lang == 'ro':
        st.markdown("""
        <div style="background: rgba(128, 128, 128, 0.08); border-radius: 8px; padding: 20px 25px; margin-top: 10px;">
            <p style="font-size: 1.05rem; margin: 0 0 10px 0;"><strong>Procedura de utilizare a sistemului</strong></p>
            <p style="margin: 4px 0; font-size: 0.95rem;">1. Configurati parametrii <strong>Alpha</strong>, <strong>Delta</strong> si <strong>Toleranta initiala</strong> in panoul lateral.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">2. Accesati tab-ul <strong>Optimizare</strong> si actionati butonul <strong>Ruleaza optimizarea</strong>.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">3. Analizati rezultatele: tolerante optime, simulare Monte Carlo, comparatii cu metodele clasice.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">4. Consultati tab-ul <strong>Matematica</strong> pentru fundamentarea teoretica a fiecarui modul.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(128, 128, 128, 0.08); border-radius: 8px; padding: 20px 25px; margin-top: 10px;">
            <p style="font-size: 1.05rem; margin: 0 0 10px 0;"><strong>System Usage Procedure</strong></p>
            <p style="margin: 4px 0; font-size: 0.95rem;">1. Configure parameters <strong>Alpha</strong>, <strong>Delta</strong>, and <strong>Initial Tolerance</strong> in the side panel.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">2. Go to the <strong>Optimization</strong> tab and press <strong>Run Optimization</strong>.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">3. Analyze the results: optimal tolerances, Monte Carlo simulation, comparisons with classical methods.</p>
            <p style="margin: 4px 0; font-size: 0.95rem;">4. Consult the <strong>Mathematics</strong> tab for the theoretical foundation of each module.</p>
        </div>
        """, unsafe_allow_html=True)

# ================================================================
# TAB 2: OPTIMIZARE
# ================================================================
with tab2:
    st.title(t['tab2'])
    
    if run:
        tolerante_init = np.full(6, tol_init)
                # ---------- Combinatia critica INITIALA ----------
        st.divider()
        st.header("🔍 " + ("Combinatia critica INAINTE de optimizare" if st.session_state.lang == 'ro' else "Critical Combination BEFORE optimization"))
        
        tester_init = AgentTester(alpha=alpha, max_iteratii=500)
        rez_init, X_init, cota_init = tester_init.ataca(np.full(6, tol_init))
        joc_init, _, _ = functia_de_joc(X_init)
        
        df_critic_init = pd.DataFrame({
            ('Cota' if st.session_state.lang == 'ro' else 'Dimension'): t['cote'],
            ('Valoare nominala' if st.session_state.lang == 'ro' else 'Nominal Value'): valori_nominale,
            ('Valoare critica' if st.session_state.lang == 'ro' else 'Critical Value'): np.round(X_init, 5),
            ('Abatere' if st.session_state.lang == 'ro' else 'Deviation'): np.round(X_init - valori_nominale, 5),
            ('Directie' if st.session_state.lang == 'ro' else 'Direction'): [
                'Maxim' if X_init[i] > valori_nominale[i] else 'Minim' for i in range(6)
            ]
        })
        st.dataframe(df_critic_init, use_container_width=True, hide_index=True)
        
        if st.session_state.lang == 'ro':
            st.markdown(
                "> **Pentru validare CAD:** Acestea sunt valorile care trebuie introduse in SolidWorks "
                f"pentru a reproduce interferenta. Jocul cu aceste valori este **{joc_init:.4f} mm** "
                "(puternic negativ → interferenta vizibila)."
            )
        else:
            st.markdown(
                "> **For CAD validation:** These are the values to enter in SolidWorks "
                f"to reproduce the interference. The gap with these values is **{joc_init:.4f} mm** "
                "(strongly negative → visible interference)."
            )
        
        st.divider()
        st.header("⏳ " + ("Optimizare in curs..." if st.session_state.lang == 'ro' else "Optimization in progress..."))
        proiectant = AgentProiectant(valori_nominale, tolerante_init, delta=delta)
        tester = AgentTester(alpha=alpha, max_iteratii=500)
        
        c1, c2, c3 = st.columns(3)
        m_iter = c1.empty()
        m_cost = c2.empty()
        m_beta = c3.empty()
        
        # Container pentru arena luptei
        arena = st.empty()
        
        istoric = []
        fara_defect = 0
        iteratii = 0
        total_defecte = 0
        total_ok = 0
        
        for it in range(300):
            iteratii = it + 1
            tolerante = proiectant.propune_tolerante()
            cost = proiectant.calculeaza_cost()
            rezultat, X_worst, cota = tester.ataca(tolerante)
            beta = tester.get_beta()
            joc, _, _ = functia_de_joc(X_worst)
            
            istoric.append({
                'Iterație': iteratii, 'Rezultat': rezultat, 'Beta': round(beta, 3),
                'Cost': round(cost, 2), 'Joc (mm)': round(joc, 4),
                'Cotă vinovată': cota + 1 if cota is not None else '-'
            })
            
            m_iter.metric(t['iterations'], f"{iteratii}", 
                         help="Numarul curent de iteratii. Sistemul se opreste dupa 2 iteratii consecutive fara defecte (convergenta).")
            m_cost.metric(t['cost_opt'], f"{cost:.2f}", 
                         help="Costul total al tolerantelor. Formula: Cost = suma(1/toleranta). Mai mic = fabricatie mai ieftina.")
            m_beta.metric("Beta", f"{beta:.3f}", 
                         help="Factorul de agresivitate al neuronului fractionar. ~0.85 = sistem alert (strange agresiv). ~0.15 = sistem relaxat (ajustari fine).")
            
            # Calcul proporție pentru bară
            if rezultat == "DEFECT":
                total_defecte += 1
                fara_defect = 0
                proiectant.primeste_raport(True, cota, beta)
                culoare = "#ffc107"
                actiune = f"strange toleranta la cota {cota+1}"
            else:
                total_ok += 1
                fara_defect += 1
                culoare = "#28a745"
                actiune = "incearca sa largeasca tolerantele"
            
            # Arena luptei - Doi Roboti
            if not mod_rapid:
                if st.session_state.lang == 'ro':
                    arena.markdown(f"""
                    <div style="border: 1px solid #e0e0e0; border-radius: 16px; padding: 25px; background: linear-gradient(135deg, #fafafa, #f0f0f0); margin: 10px 0; text-align: center;">
                        <h4 style="margin: 0 0 20px 0; color: #555; font-weight: 600;">Confruntarea Agentilor — Iteratia {iteratii}</h4>
                        <div style="display: flex; justify-content: space-around; align-items: center;">
                            <div style="text-align: center;">
                                <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/robot_rosu.gif" 
                                     width="{110 if rezultat == 'DEFECT' else 85}" 
                                     style="transition: all 0.3s ease;
                                            filter: drop-shadow(0 0 {20 if rezultat == 'DEFECT' else 5}px {'#ffc107' if rezultat == 'DEFECT' else '#ccc'});
                                            opacity: {1 if rezultat == 'DEFECT' else 0.5};">
                                <strong style="color: #e74c3c;">Testerul</strong><br>
                                <small style="color: #888;">Beta: {beta:.3f}</small><br>
                                <small style="color: #888;">Joc: {joc:.4f} mm</small>
                            </div>
                            <div style="font-size: 2rem; font-weight: bold; color: {culoare};">
                                VS
                            </div>
                            <div style="text-align: center;">
                                <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/robot_albastru.gif" 
                                     width="{110 if rezultat == 'OK' else 85}" 
                                     style="transition: all 0.3s ease;
                                            filter: drop-shadow(0 0 {20 if rezultat == 'OK' else 5}px {'#28a745' if rezultat == 'OK' else '#ccc'});
                                            opacity: {1 if rezultat == 'OK' else 0.5};">
                                <strong style="color: #667eea;">Proiectantul</strong><br>
                                <small style="color: #888;">Cost: {cost:.2f}</small><br>
                                <small style="color: #888;">{actiune}</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    arena.markdown(f"""
                    <div style="border: 1px solid #e0e0e0; border-radius: 16px; padding: 25px; background: linear-gradient(135deg, #fafafa, #f0f0f0); margin: 10px 0; text-align: center;">
                        <h4 style="margin: 0 0 20px 0; color: #555; font-weight: 600;">Agent Confrontation — Iteration {iteratii}</h4>
                        <div style="display: flex; justify-content: space-around; align-items: center;">
                            <div style="text-align: center;">
                                <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/robot_rosu.gif" 
                                     width="{110 if rezultat == 'DEFECT' else 85}" 
                                     style="transition: all 0.3s ease;
                                            filter: drop-shadow(0 0 {20 if rezultat == 'DEFECT' else 5}px {'#ffc107' if rezultat == 'DEFECT' else '#ccc'});
                                            opacity: {1 if rezultat == 'DEFECT' else 0.5};">
                                <strong style="color: #e74c3c;">Tester</strong><br>
                                <small style="color: #888;">Beta: {beta:.3f}</small><br>
                                <small style="color: #888;">Gap: {joc:.4f} mm</small>
                            </div>
                            <div style="font-size: 2rem; font-weight: bold; color: {culoare};">
                                VS
                            </div>
                            <div style="text-align: center;">
                                <img src="https://raw.githubusercontent.com/adumitrescu1212/optimizare-tolerante/main/robot_albastru.gif" 
                                     width="{110 if rezultat == 'OK' else 85}" 
                                     style="transition: all 0.3s ease;
                                            filter: drop-shadow(0 0 {20 if rezultat == 'OK' else 5}px {'#28a745' if rezultat == 'OK' else '#ccc'});
                                            opacity: {1 if rezultat == 'OK' else 0.5};">
                                <strong style="color: #667eea;">Designer</strong><br>
                                <small style="color: #888;">Cost: {cost:.2f}</small><br>
                                <small style="color: #888;">{actiune}</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                arena.markdown(f"**Iteratia {iteratii}: {rezultat}** | Joc = {joc:.4f} mm | Beta = {beta:.3f} | Cost = {cost:.2f}")
            
            if not mod_rapid:
                time.sleep(0.8)
            
            if fara_defect >= 2:
                break
            
            if rezultat == "OK":
                cota_mod = proiectant.primeste_raport(False, None, beta)
                if cota_mod is not False:
                    tol_noi = proiectant.propune_tolerante()
                    rez2, _, _ = tester.ataca(tol_noi)
                    if rez2 == "DEFECT":
                        proiectant.confirma_esec(cota_mod)
                        fara_defect = 0
        
        st.session_state['istoric'] = istoric
        st.session_state['proiectant'] = proiectant
        st.session_state['iteratii'] = iteratii
        
        st.divider()
        st.header("📊 " + ("Rezultate finale" if st.session_state.lang == 'ro' else "Final Results"))
        c1, c2, c3 = st.columns(3)
        c1.metric(t['iterations'], f"{iteratii}")
        c2.metric(t['cost_opt'], f"{proiectant.calculeaza_cost():.2f}")
        c3.metric(t['cost_init'], f"{np.sum(1.0/(tolerante_init + 1e-9)):.2f}")
        
        if st.session_state.lang == 'ro':
            st.markdown(f"> **Interpretare:** Sistemul a convergit in **{iteratii} iteratii**. Costul a crescut de la **{np.sum(1.0/(tolerante_init + 1e-9)):.2f}** la **{proiectant.calculeaza_cost():.2f}**. Aceasta este frontiera de fezabilitate.")
        else:
            st.markdown(f"> **Interpretation:** Converged in **{iteratii} iterations**. Cost increased from **{np.sum(1.0/(tolerante_init + 1e-9)):.2f}** to **{proiectant.calculeaza_cost():.2f}**.")
        
        st.subheader(t['tol_header'])
        df_tol = pd.DataFrame({
            ('Cotă' if st.session_state.lang == 'ro' else 'Dimension'): t['cote'],
            ('Val. nominală (mm)' if st.session_state.lang == 'ro' else 'Nominal (mm)'): valori_nominale,
            ('Toleranță optimă (±mm)' if st.session_state.lang == 'ro' else 'Optimal (±mm)'): np.round(proiectant.propune_tolerante(), 5),
        })
        st.dataframe(df_tol, use_container_width=True, hide_index=True)
        
        st.divider()
        st.header(t['mc_header'])
        
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.6;">
                <strong>Ce face aceasta simulare?</strong> Sistemul a garantat deja (prin verificarea celor 64 de colturi) 
                ca <strong>niciuna</strong> dintre combinatiile extreme nu produce interferenta. 
                Dar in productia reala, majoritatea pieselor ies aproape de valorile nominale, nu la extreme. 
                Monte Carlo simuleaza <strong>5000 de scenarii realiste</strong> si estimeaza 
                probabilitatea de defect in conditii reale de fabricatie. 
                Un rezultat de 0% confirma ca tolerantele optime sunt sigure.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.6;">
                <strong>What does this simulation do?</strong> The system has already guaranteed (by checking all 64 corners) 
                that <strong>none</strong> of the extreme combinations causes interference. 
                But in real production, most parts come out near nominal values, not at extremes. 
                Monte Carlo simulates <strong>5000 realistic scenarios</strong> (normal distribution) and estimates 
                the defect probability under real manufacturing conditions. 
                A 0% result confirms the optimal tolerances are safe.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        tol_opt = proiectant.propune_tolerante()
        n_mc, defecte_mc = 5000, 0
        for _ in range(n_mc):
            X_mc = np.random.normal(loc=valori_nominale, scale=tol_opt/3)
            X_mc = np.clip(X_mc, valori_nominale - tol_opt, valori_nominale + tol_opt)
            if functia_de_joc(X_mc)[0] <= 0:
                defecte_mc += 1
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t['mc_samples'], f"{n_mc:,}")
        c2.metric(t['mc_defects'], f"{defecte_mc}")
        c3.metric(t['mc_prob'], f"{100*defecte_mc/n_mc:.3f}%")
        c4.metric(t['mc_dist'], "Normala", help="Distributia normala (Gaussiana) centrata pe valoarea nominala, cu σ = toleranta/3.")
        
        st.divider()
        st.header(t['comp_header'])
        df_comp = pd.DataFrame({
            ('Metoda' if st.session_state.lang == 'ro' else 'Method'): ['Sistem Multi-Agent', 'Worst-Case', 'Monte Carlo'],
            'Cost': [f"{proiectant.calculeaza_cost():.2f}", "∞", "~180"],
            ('Evaluări' if st.session_state.lang == 'ro' else 'Evaluations'): [f"~{iteratii * 64:,}", "1", "10,000+"],
            ('Garanție' if st.session_state.lang == 'ro' else 'Guarantee'): ['Absolută', 'Absolută', 'Statistică'],
        })
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        
         # ---------- Combinația critică ----------
        st.divider()
        st.header("🔍 " + ("Combinația critică" if st.session_state.lang == 'ro' else "Critical Combination"))
        
        tester2 = AgentTester(alpha=alpha, max_iteratii=500)
        rezultat_crit, X_crit, cota_crit = tester2.ataca(proiectant.propune_tolerante())
        joc_crit, j1, j2 = functia_de_joc(X_crit)
        
        df_critic = pd.DataFrame({
            ('Cotă' if st.session_state.lang == 'ro' else 'Dimension'): t['cote'],
            ('Valoare nominală' if st.session_state.lang == 'ro' else 'Nominal Value'): valori_nominale,
            ('Valoare critică' if st.session_state.lang == 'ro' else 'Critical Value'): np.round(X_crit, 5),
            ('Abatere' if st.session_state.lang == 'ro' else 'Deviation'): np.round(X_crit - valori_nominale, 5),
            ('Direcție' if st.session_state.lang == 'ro' else 'Direction'): [
                'Maxim' if X_crit[i] > valori_nominale[i] else 'Minim' for i in range(6)
            ]
        })
        st.dataframe(df_critic, use_container_width=True, hide_index=True)
        
        if st.session_state.lang == 'ro':
            st.markdown(f"""
            <div style="background: rgba(128,128,128,0.06); border-radius: 8px; padding: 15px; margin-top: 10px;">
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.6;">
                <strong>Interpretare:</strong> Jocul minim teoretic este <strong>{joc_crit:.4f} mm</strong>. 
                Valorile negative indica interferenta (defect). Coloana <strong>Directie</strong> specifica 
                daca dimensiunea trebuie sa fie la <strong>Maxim</strong> (peste valoarea nominala) 
                sau la <strong>Minim</strong> (sub valoarea nominala) pentru a provoca aceasta interferenta.
                Aceste valori se introduc in SolidWorks pentru validarea experimentala.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(128,128,128,0.06); border-radius: 8px; padding: 15px; margin-top: 10px;">
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.6;">
                <strong>Interpretation:</strong> The theoretical minimum gap is <strong>{joc_crit:.4f} mm</strong>. 
                Negative values indicate interference (defect). The <strong>Direction</strong> column specifies 
                whether the dimension should be at <strong>Maximum</strong> (above nominal) 
                or <strong>Minimum</strong> (below nominal) to cause this interference.
                These values are entered in SolidWorks for experimental validation.
                </p>
            </div>
            """, unsafe_allow_html=True)
        csv = pd.DataFrame(istoric).to_csv(index=False).encode('utf-8')
        st.download_button(t['export'], csv, 'istoric_optimizare.csv', 'text/csv')
    
        st.success("👈 " + ("Mergi la tab-ul Grafice." if st.session_state.lang == 'ro' else "Go to Charts tab."))
    else:
        st.info(t['wait'])
# ================================================================
# TAB 3: GRAFICE
# ================================================================
with tab3:
    st.title("📈 " + ("Grafice" if st.session_state.lang == 'ro' else "Charts"))
    if 'istoric' not in st.session_state or st.session_state['istoric'] is None:
        st.warning(t['grafice_warn'])
    else:
        df = pd.DataFrame(st.session_state['istoric'])
        
        # Ghid de citire
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                <p style="font-size: 1rem; line-height: 1.7; margin: 0;">
                <strong>📋 Cum citesti aceste date?</strong><br>
                Tabelul de mai jos contine <strong>istoricul complet al optimizarii</strong>. Fiecare rand reprezinta o iteratie.
                Coloana <strong>Rezultat</strong> arata daca Testerul a gasit un defect (DEFECT) sau nu (OK).
                Coloana <strong>Beta</strong> arata starea neuronului fractionar.
                Coloana <strong>Cost</strong> este costul tolerantelor.
                Coloana <strong>Joc</strong> este distanta minima dintre stift si gaura.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                <p style="font-size: 1rem; line-height: 1.7; margin: 0;">
                <strong>📋 How to read this data?</strong><br>
                The table below contains the <strong>complete optimization history</strong>.
                <strong>Result</strong> shows DEFECT or OK.
                <strong>Beta</strong> shows the fractional neuron state.
                <strong>Cost</strong> is the tolerance cost.
                <strong>Gap</strong> is the minimum distance between pin and hole.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader(t['history'])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.markdown("### 📈 " + ("Evolutia pe parcursul optimizarii" if st.session_state.lang == 'ro' else "Evolution During Optimization"))
        
        tg1, tg2, tg3 = st.tabs([t['chart_cost'], t['chart_beta'], t['chart_joc']])
        
        with tg1:
            # Grafic Cost - linie cu culoare
            st.line_chart(df, x='Iterație', y='Cost', height=400, color='#667eea')
            
            # Statistici
            c1, c2, c3 = st.columns(3)
            c1.metric("Minim", f"{df['Cost'].min():.2f}")
            c2.metric("Maxim", f"{df['Cost'].max():.2f}")
            c3.metric("Final", f"{df['Cost'].iloc[-1]:.2f}")
            
            if st.session_state.lang == 'ro':
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🔵 Cum interpretam:</strong> Costul porneste de la o valoare mica (tolerante largi = ieftin) 
                    si <strong>creste pe masura ce sistemul strange tolerantele</strong> pentru a elimina defectele.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🔵 How to interpret:</strong> Cost starts low and 
                    <strong>increases as the system tightens tolerances</strong> to eliminate defects.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with tg2:
            # Grafic Beta - linie cu culoare
            st.line_chart(df, x='Iterație', y='Beta', height=400, color='#e74c3c')
            
            # Statistici
            c1, c2, c3 = st.columns(3)
            c1.metric("Minim", f"{df['Beta'].min():.3f}")
            c2.metric("Maxim", f"{df['Beta'].max():.3f}")
            c3.metric("Final", f"{df['Beta'].iloc[-1]:.3f}")
            
            if st.session_state.lang == 'ro':
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🔴 Cum interpretam:</strong> Beta reflecta <strong>starea neuronului fractionar</strong>.
                    Ramane ridicat (~0.85) in faza de defecte, apoi <strong>scade brusc</strong> cand sistemul se relaxeaza.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🔴 How to interpret:</strong> Beta reflects the <strong>fractional neuron state</strong>.
                    Stays high (~0.85) during defects, then <strong>drops sharply</strong> when the system relaxes.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with tg3:
            # Grafic Joc - linie cu culoare
            st.line_chart(df, x='Iterație', y='Joc (mm)', height=400, color='#28a745')
            
            # Statistici
            c1, c2, c3 = st.columns(3)
            c1.metric("Minim", f"{df['Joc (mm)'].min():.4f} mm")
            c2.metric("Maxim", f"{df['Joc (mm)'].max():.4f} mm")
            c3.metric("Final", f"{df['Joc (mm)'].iloc[-1]:.4f} mm")
            
            if st.session_state.lang == 'ro':
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🟢 Cum interpretam:</strong> Jocul porneste <strong>puternic negativ</strong> (interferenta majora)
                    si creste spre zero. Cand jocul devine pozitiv, ansamblul functioneaza corect.
                    Sistemul gaseste exact <strong>frontiera de fezabilitate</strong> — punctul optim.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(128,128,128,0.05); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <p style="font-size: 0.95rem; line-height: 1.6; margin: 0;">
                    <strong>🟢 How to interpret:</strong> The gap starts <strong>strongly negative</strong>
                    and rises toward zero. When the gap becomes positive, the assembly works correctly.
                    The system finds exactly the <strong>feasibility boundary</strong> — the optimal point.
                    </p>
                </div>
                """, unsafe_allow_html=True)
# ================================================================
# TAB 4: DESPRE
# ================================================================
with tab4:
    st.title("📖 " + ("Despre proiect" if st.session_state.lang == 'ro' else "About the Project"))
    
    if st.session_state.lang == 'ro':
        st.markdown("""
        ### 🎯 Ce este acest proiect?
        
        Acest proiect reprezinta un **sistem inteligent de optimizare a tolerantelor** pentru ansambluri mecanice,
        dezvoltat la intersectia dintre **inteligenta artificiala**, **ingineria mecanica** si **calculul fractionar**.
        
        Sistemul utilizeaza o **arhitectura multi-agent** in care doi agenti software — un Proiectant si un Tester —
        interactioneaza iterativ pentru a gasi automat cel mai ieftin set de tolerante care garanteaza functionalitatea
        unui ansamblu mecanic.
        
        ---
        
        ### 🔥 Ce ne-a motivat?
        
        In ingineria mecanica, **toleranțarea** este o provocare fundamentala. Pe de o parte, tolerantele stranse
        garanteaza calitatea dar cresc exploziv costurile de fabricatie. Pe de alta parte, tolerantele largi reduc
        costurile dar risca sa produca piese care nu se potrivesc.
        
        Metodele traditionale (Worst-Case, Monte Carlo, algoritmi genetici) trateaza optimizarea si analiza ca
        **procese separate**. Am vrut sa cream un sistem care sa le **integreze dinamic**, permitand celor doi
        agenti sa invete unul de la celalalt in timp real.
        
        ---
        
        ### ✨ Elemente de originalitate
        
        1. **Abordare adversiala pentru tolerante** — In literatura de specialitate, optimizarea tolerantelor
        utilizeaza predominant algoritmi genetici sau metode deterministe. Utilizarea unui sistem multi-agent
        cu dinamica adversiala (un agent propune, celalalt ataca) este o **abordare noua** in acest domeniu.
        
        2. **Neuron fractionar ca manager de risc** — Am introdus un neuron cu dinamica fractionara, bazat
        pe derivata **Grunwald-Letnikov**, care actioneaza ca un **controler adaptiv** al ratei de ajustare.
        Memoria lunga oferita de calculul fractionar permite sistemului sa fie agresiv in faza de corectie
        si precaut in faza de optimizare fina.
        
        3. **Garantie matematica absoluta** — Am demonstrat o **teorema de localizare a minimului** care
        stabileste ca cel mai rau caz se gaseste intotdeauna la unul dintre cele 64 de colturi ale domeniului
        de toleranta. Aceasta elimina necesitatea metodelor iterative si ofera **siguranta absoluta** ca
        niciun defect nu scapa nedetectat.
        
        4. **Flux complet pe resurse minime** — Intregul sistem este implementat in **Python** (open-source)
        si validat pe un model CAD real in **SolidWorks Student** (licenta educationala gratuita), demonstrand
        ca o analiza avansata a tolerantelor poate fi realizata fara investitii in software comercial.
        
        ---
        
        ### 🏗️ Cum functioneaza — pe scurt
        
        **🔵 Agentul Proiectant** porneste cu tolerante foarte largi (cost minim) si le ajusteaza pe baza
        feedback-ului. Cand Testerul gaseste un defect, Proiectantul strange toleranta la cota respectiva.
        Cand totul e in regula, incearca sa largeasca tolerantele pentru a reduce costul.
        
        **🔴 Agentul Tester** verifica fiecare set de tolerante testand **toate cele 64 de combinatii extreme**
        posibile. Aceasta ofera o garantie matematica absoluta: daca Testerul spune OK, atunci nu exista
        nicio combinatie de dimensiuni in domeniul de toleranta care sa produca interferenta.
        
        **🧠 Neuronul fractionar** controleaza **cat de agresiv** se fac ajustarile. Are memorie lunga asupra
        istoricului interactiunii: cand Testerul gaseste constant defecte, neuronul e "stresat" (Beta ~0.85)
        si Proiectantul strange agresiv. Cand sistemul se stabilizeaza, neuronul se relaxeaza (Beta ~0.15)
        si ajustarile devin fine si precise.
        
        ---
        
        ### 🎯 Rezultatul
        
        Sistemul produce **tolerantele optime** — cel mai ieftin set care garanteaza ca piesele se vor asambla
        corect, indiferent de variatiile dimensionale inerente fabricatiei. Convergenta se atinge in aproximativ
        100–110 iteratii (sub o secunda pe un laptop standard).
        """)
    else:
        st.markdown("""
        ### 🎯 What is this project?
        
        This project represents an **intelligent tolerance optimization system** for mechanical assemblies,
        developed at the intersection of **artificial intelligence**, **mechanical engineering**, and
        **fractional calculus**.
        
        The system uses a **multi-agent architecture** where two software agents — a Designer and a Tester —
        interact iteratively to automatically find the cheapest tolerance set that guarantees the functionality
        of a mechanical assembly.
        
        ---
        
        ### 🔥 What motivated us?
        
        In mechanical engineering, **tolerancing** is a fundamental challenge. Tight tolerances guarantee
        quality but explosively increase manufacturing costs. Wide tolerances reduce costs but risk
        producing parts that don't fit together.
        
        Traditional methods (Worst-Case, Monte Carlo, genetic algorithms) treat optimization and analysis
        as **separate processes**. We wanted to create a system that **dynamically integrates** them,
        allowing the two agents to learn from each other in real time.
        
        ---
        
        ### ✨ Original Contributions
        
        1. **Adversarial approach for tolerances** — Using a multi-agent system with adversarial dynamics
        (one agent proposes, the other attacks) is a **novel approach** in tolerance optimization, where
        genetic algorithms and deterministic methods dominate.
        
        2. **Fractional neuron as risk manager** — We introduced a neuron with fractional dynamics, based
        on the **Grunwald-Letnikov** derivative, acting as an **adaptive controller** of the adjustment rate.
        The long memory provided by fractional calculus allows the system to be aggressive in the correction
        phase and cautious in the fine-tuning phase.
        
        3. **Absolute mathematical guarantee** — We proved a **corner localization theorem** establishing
        that the worst case is always at one of the 64 vertices of the tolerance domain. This eliminates
        the need for iterative methods and provides **absolute certainty** that no defect escapes detection.
        
        4. **Complete low-cost workflow** — The entire system is implemented in **Python** (open-source)
        and validated on a real CAD model in **SolidWorks Student** (free educational license), demonstrating
        that advanced tolerance analysis can be performed without investment in commercial software.
        
        ---
        
        ### 🏗️ How It Works — in brief
        
        **🔵 The Designer Agent** starts with very wide tolerances (minimum cost) and adjusts them based on
        feedback. When the Tester finds a defect, the Designer tightens the tolerance for that dimension.
        When everything is fine, it tries to widen tolerances to reduce cost.
        
        **🔴 The Tester Agent** checks each tolerance set by testing **all 64 extreme combinations**.
        This provides an absolute mathematical guarantee: if the Tester says OK, there is no dimension
        combination within the tolerance domain that produces interference.
        
        **🧠 The Fractional Neuron** controls **how aggressive** the adjustments are. It has long memory
        of the interaction history: when the Tester consistently finds defects, the neuron is "stressed"
        (Beta ~0.85) and the Designer tightens aggressively. When the system stabilizes, the neuron
        relaxes (Beta ~0.15) and adjustments become fine and precise.
        
        ---
        
        ### 🎯 The Result
        
        The system produces the **optimal tolerances** — the cheapest set that guarantees the parts will
        assemble correctly, regardless of manufacturing variations. Convergence is reached in approximately
        100–110 iterations (under one second on a standard laptop).
        """)
# ================================================================
# TAB 5: MATEMATICA
# ================================================================
with tab5:
    st.title("📐 " + ("Breviat teoretic" if st.session_state.lang == 'ro' else "Theoretical Brief"))
    
    if st.session_state.lang == 'ro':
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin-bottom: 25px;">
            <p style="font-size: 1rem; line-height: 1.6; margin: 0;">
            Acest breviar contine <strong>fundamentele matematice</strong> pe care se bazeaza intregul sistem.
            Fiecare sectiune prezinta <strong>conceptul teoretic</strong>, <strong>formulele corespunzatoare</strong>
            si <strong>modulul Python</strong> in care este implementat.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin-bottom: 25px;">
            <p style="font-size: 1rem; line-height: 1.6; margin: 0;">
            This brief contains the <strong>mathematical foundations</strong> underlying the entire system.
            Each section presents the <strong>theoretical concept</strong>, <strong>corresponding formulas</strong>,
            and the <strong>Python module</strong> where it is implemented.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    tm1, tm2, tm3, tm4, tm5, tm6, tm7, tm8 = st.tabs([
        "1. " + ("Functia de joc" if st.session_state.lang == 'ro' else "Gap Function"),
        "2. " + ("Gradientul analitic" if st.session_state.lang == 'ro' else "Analytical Gradient"),
        "3. " + ("Subgradientul" if st.session_state.lang == 'ro' else "Subgradient"),
        "4. " + ("Teorema colturilor" if st.session_state.lang == 'ro' else "Corner Theorem"),
        "5. " + ("Neuronul fractionar" if st.session_state.lang == 'ro' else "Fractional Neuron"),
        "6. " + ("Cuantificarea incertitudinii" if st.session_state.lang == 'ro' else "Uncertainty Quantification"),
        "7. " + ("Functia de cost" if st.session_state.lang == 'ro' else "Cost Function"),
        "8. " + ("Convergenta" if st.session_state.lang == 'ro' else "Convergence")
    ])
    
    # ---------- TAB 5.1 ----------
    with tm1:
        st.markdown("### 1. " + ("Functia de joc" if st.session_state.lang == 'ro' else "The Gap Function"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Determinarea matematica a conditiei de asamblare corecta pentru o pereche stift-gaura.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Definitie.** Pentru o pereche stift-gaura, fie $R_s$ raza stiftului, $R_g$ raza gaurii si $d = \\|S - G\\|$ distanta euclidiana dintre centrele lor. **Jocul** este:")
            st.latex(r"J = R_g - R_s - d")
            st.markdown("**Demonstratie.** Doua cercuri sunt disjuncte daca $d > R_s + R_g$ sau $d < |R_s - R_g|$. Pentru asamblare, stiftul trebuie sa fie **complet interior** gaurii ($R_g > R_s$). Conditia: $d + R_s < R_g$, adica $R_g - R_s - d > 0$.")
            st.markdown("**Functia globala de joc:**")
            st.latex(r"f(X) = \min(J_1(X), J_2(X))")
            st.markdown("**Criteriul de asamblare:** Ansamblul functioneaza *daca si numai daca* $f(X) > 0$.")
            st.markdown("**Exprimare explicita:**")
            st.latex(r"f(X) = \frac{x_2 - x_1}{2} - \sqrt{(x_3 - x_5)^2 + (x_4 - x_6)^2}")
            st.markdown("""
            <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
                <strong>💻 Implementare:</strong> <code>model_matematic.py</code> → functia <code>functia_de_joc(X)</code>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Mathematical determination of the correct assembly condition for a pin-hole pair.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"J = R_g - R_s - d")
            st.latex(r"f(X) = \min(J_1(X), J_2(X))")
            st.latex(r"f(X) = \frac{x_2 - x_1}{2} - \sqrt{(x_3 - x_5)^2 + (x_4 - x_6)^2}")
            st.markdown("""
            <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
                <strong>💻 Implementation:</strong> <code>model_matematic.py</code> → function <code>functia_de_joc(X)</code>
            </div>
            """, unsafe_allow_html=True)
    
    # ---------- TAB 5.2 ----------
    with tm2:
        st.markdown("### 2. " + ("Gradientul analitic" if st.session_state.lang == 'ro' else "Analytical Gradient"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Identificarea cotelor cu cel mai mare impact asupra jocului.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"\nabla f(X) = \begin{bmatrix} -\frac{1}{2} & +\frac{1}{2} & -\frac{x_3-x_5}{d} & -\frac{x_4-x_6}{d} & +\frac{x_3-x_5}{d} & +\frac{x_4-x_6}{d} \end{bmatrix}^T")
            st.markdown("$-1/2$ pentru stift → mai gros = joc mai mic. $+1/2$ pentru gaura → mai mare = joc mai mare.")
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Identifying dimensions with greatest impact on the gap.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"\nabla f(X) = \begin{bmatrix} -\frac{1}{2} & +\frac{1}{2} & -\frac{x_3-x_5}{d} & -\frac{x_4-x_6}{d} & +\frac{x_3-x_5}{d} & +\frac{x_4-x_6}{d} \end{bmatrix}^T")
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>model_matematic.py</code> → <code>calculeaza_subgradient(X)</code>
        </div>
        """, unsafe_allow_html=True)
    
             # ---------- TAB 5.3: SUBGRADIENTUL ----------
    with tm3:
        st.markdown("### 3. " + ("Subgradientul" if st.session_state.lang == 'ro' else "Subgradient"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            **Problema:** Functia $f(X) = \\min(J_1, J_2)$ nu este diferentiabila cand $J_1 = J_2$.
            
            **Solutia:** Subgradientul (Rockafellar, 1970). Subdiferentiala lui $f$ in $X$ este:
            """)
            st.latex(r"\partial f(X) = \text{conv}\{\nabla J_i(X) : i \in \mathcal{A}(X)\}")
            st.markdown("""
            unde $\\mathcal{A}(X)$ = functiile care ating minimul in $X$.
            
            **Cazul 1:** Un singur $J_i$ activ → gradientul sau.
            **Cazul 2:** $J_1 = J_2$ → orice combinatie convexa a gradientilor.
            **Cand $d=0$:** Regularizare $d \\leftarrow \\max(d, 10^{-8})$.
            """)
        else:
            st.markdown("""
            **Problem:** $f(X) = \\min(J_1, J_2)$ is non-differentiable when $J_1 = J_2$.
            
            **Solution:** Subgradient (Rockafellar, 1970). The subdifferential of $f$ at $X$ is:
            """)
            st.latex(r"\partial f(X) = \text{conv}\{\nabla J_i(X) : i \in \mathcal{A}(X)\}")
            st.markdown("""
            where $\\mathcal{A}(X)$ = active functions at $X$.
            
            **Case 1:** Single active $J_i$ → its gradient.
            **Case 2:** $J_1 = J_2$ → any convex combination of gradients.
            **When $d=0$:** Regularize $d \\leftarrow \\max(d, 10^{-8})$.
            """)
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>model_matematic.py</code> → <code>calculeaza_subgradient(X)</code>
        </div>
        """, unsafe_allow_html=True)
        
    # ---------- TAB 5.4: TEOREMA COLTURILOR ----------
    with tm4:
        st.markdown("### 4. " + ("Teorema de localizare a minimului" if st.session_state.lang == 'ro' else "Corner Localization Theorem"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Garantarea matematica a gasirii celui mai rau caz fara metode iterative.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Enunt.** Fie $D(T)$ domeniul de toleranta si $\\mathcal{V}(T)$ multimea celor $2^6 = 64$ varfuri. Atunci:")
            st.latex(r"\min_{X \in D(T)} f(X) = \min_{X \in \mathcal{V}(T)} f(X)")
            st.markdown("""
            **Demonstratie.**
            - **Pasul 1:** $x_1$ apare cu $-1/2$. Pentru a minimiza $f$, maximizam $x_1$ si minimizam $x_2$.
            - **Pasul 2:** $g(u,v) = \\sqrt{u^2+v^2}$ este convexa. Maximul pe un dreptunghi e la varfuri (Rockafellar, 1970).
            - **Concluzie:** Minimul global se atinge la unul din cele 64 de varfuri.
            
            **Implicatie practica:** Enumerarea exhaustiva ofera **garantia absoluta** in sub 1 ms.
            """)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Mathematical guarantee of finding the worst case without iterative methods.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"\min_{X \in D(T)} f(X) = \min_{X \in \mathcal{V}(T)} f(X)")
            st.markdown("""
            **Proof.** $x_1$ with $-1/2$ → maximize $x_1$, minimize $x_2$. $g(u,v)=\\sqrt{u^2+v^2}$ is convex → max at vertices (Rockafellar, 1970).
            **Conclusion:** Global minimum at one of 64 vertices.
            """)
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>agent_tester.py</code> → metoda <code>ataca()</code> — 64 de masti binare
        </div>
        """, unsafe_allow_html=True)
    
    # ---------- TAB 5.5: NEURONUL FRACTIONAR ----------
    with tm5:
        st.markdown("### 5. " + ("Neuronul fractionar" if st.session_state.lang == 'ro' else "Fractional Neuron"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Controlul adaptiv al ajustarilor folosind memoria lunga a calculului fractionar.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Derivata Grunwald-Letnikov:**")
            st.latex(r"D^{\alpha} y(t) = \lim_{h \to 0} \frac{1}{h^{\alpha}} \sum_{j=0}^{\infty} (-1)^j \binom{\alpha}{j} y(t - jh)")
            st.markdown("Ponderile $|w_j|$ descresc **algebric** (ca $j^{-\\alpha-1}$) — memorie lunga.")
            st.markdown("**Implementare discreta.** Semnal: $y(t) = +1$ (DEFECT) sau $-1$ (OK).")
            st.latex(r"u(t) = \sum_{j=0}^{19} w_j \cdot y(t-j), \quad \beta(t) = \frac{1}{1 + e^{-u(t)}} \in (0, 1)")
            st.markdown("**Rol:** $\\beta \\to 1$ = agresiv (strange tare). $\\beta \\to 0$ = precaut (ajustari fine).")
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Adaptive control using long memory from fractional calculus.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"D^{\alpha} y(t) = \lim_{h \to 0} \frac{1}{h^{\alpha}} \sum_{j=0}^{\infty} (-1)^j \binom{\alpha}{j} y(t - jh)")
            st.latex(r"u(t) = \sum_{j=0}^{19} w_j \cdot y(t-j), \quad \beta(t) = \frac{1}{1 + e^{-u(t)}}")
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>neuron_fractionar.py</code> → clasa <code>NeuronFractionar</code> (~30 linii)
        </div>
        """, unsafe_allow_html=True)
    
       # ---------- TAB 5.6: CUANTIFICAREA INCERTITUDINII ----------
    with tm6:
        st.markdown("### 6. " + ("Cuantificarea incertitudinii" if st.session_state.lang == 'ro' else "Uncertainty Quantification"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Dupa optimizare, stim ca ansamblul functioneaza garantat. Dar care este probabilitatea
                reala de defect intr-un scenariu de productie? Cuantificarea incertitudinii (UQ) raspunde la aceasta intrebare.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### Modelul stochastic al procesului de fabricatie")
            st.markdown("""
            Fiecare dimensiune $x_i$ este modelata ca o variabila aleatoare **normala** (Gaussiana), centrata pe valoarea nominala.
            Aceasta este ipoteza standard in ingineria calitatii, justificata de doua argumente:
            """)
            st.latex(r"x_i \sim \mathcal{N}(x_i^{\text{nom}}, \sigma_i^2), \quad \sigma_i = \frac{t_i}{3}")
            st.markdown("""
            **Justificare teoretica — Teorema limitei centrale (Feller, 1971):** O dimensiune fabricata este rezultatul cumulat
            al numerosi factori independenti: vibratii, uzura sculei, variatii de temperatura. Conform teoremei limitei centrale,
            suma unui numar mare de variabile aleatoare independente tinde catre o distributie normala, indiferent de
            distributia factorilor individuali.
            
            **Justificare practica — Six Sigma (Pyzdek & Keller, 2014):** Regula celor $3\\sigma$ stipuleaza ca intervalul
            $[\\mu - 3\\sigma, \\mu + 3\\sigma]$ contine $99.73\\%$ din piesele produse. Definirea tolerantei ca $t_i = 3\\sigma_i$
            este conventia industriala standard.
            """)
            
            st.markdown("### Estimarea Monte Carlo a probabilitatii de defect")
            st.markdown("""
            Probabilitatea de defect pentru un vector de tolerante $T$ este:
            """)
            st.latex(r"P_{\text{defect}}(T) = \mathbb{P}_{X \sim \mathcal{D}(T)}\left[ f(X) \leq 0 \right]")
            st.markdown("""
            Intrucat aceasta integrala nu poate fi calculata analitic (din cauza complexitatii functiei $f$),
            o estimam prin simulare Monte Carlo:
            """)
            st.latex(r"\hat{P}_{\text{defect}} = \frac{1}{N} \sum_{k=1}^{N} \mathbf{1}_{\{f(X_k) \leq 0\}}")
            st.markdown("""
            unde $X_1, \\dots, X_N$ sunt $N$ esantioane independente din distributia normala $\\mathcal{D}(T)$,
            iar $\\mathbf{1}_{\\{f(X_k) \\leq 0\\}}$ este functia indicator (1 daca apare defect, 0 altfel).
            
            **Proprietati statistice:** $\\hat{P}_{\\text{defect}}$ este un estimator **nedeplasat** (expected value = valoarea reala)
            si **convergent** (devine mai precis pe masura ce $N$ creste). Varianta estimatorului este:
            """)
            st.latex(r"\text{Var}(\hat{P}_{\text{defect}}) = \frac{P_{\text{defect}}(1-P_{\text{defect}})}{N} \leq \frac{1}{4N}")
            st.markdown("""
            Pentru $N = 5.000$ (cat folosim in aplicatie), eroarea standard este sub $0.007$ (0.7 puncte procentuale).
            """)
            
            st.markdown("### Integrarea UQ in sistemul nostru")
            st.markdown("""
            Cuantificarea incertitudinii apare in **doua puncte** distincte ale sistemului:
            
            **1. In bucla de optimizare (online):** La fiecare iteratie, dupa ce Testerul gaseste cel mai rau caz
            (prin enumerarea celor 64 de colturi), se ruleaza un mini Monte Carlo pentru a estima $P_{\\text{defect}}$
            asociat tolerantelor curente. Aceasta ofera o metrica cantitativa a riscului in timp real.
            
            **2. La finalul optimizarii (offline):** Se ruleaza un Monte Carlo complet ($N = 5.000$) pe tolerantele optime,
            pentru validare si comparatie cu metodele traditionale.
            
            **Noutatea abordarii:** Spre deosebire de metodele traditionale unde UQ este un pas separat (post-optimizare),
            in sistemul nostru UQ-ul este **integrat in bucla de feedback**. Estimarea riscului ghideaza direct deciziile
            Agentului Proiectant prin factorul $\\beta$, creand o sinergie intre optimizare si cuantificarea incertitudinii.
            """)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> After optimization, we know the assembly works. But what is the real defect
                probability in a production scenario? Uncertainty Quantification (UQ) answers this question.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### Stochastic Manufacturing Model")
            st.markdown("""
            Each dimension $x_i$ is modeled as a **normal** (Gaussian) random variable centered on the nominal value.
            This is the standard assumption in quality engineering, justified by two arguments:
            """)
            st.latex(r"x_i \sim \mathcal{N}(x_i^{\text{nom}}, \sigma_i^2), \quad \sigma_i = \frac{t_i}{3}")
            st.markdown("""
            **Theoretical justification — Central Limit Theorem (Feller, 1971):** A manufactured dimension results from
            many independent factors: vibrations, tool wear, temperature variations. The CLT states that the sum tends
            toward a normal distribution.
            
            **Practical justification — Six Sigma (Pyzdek & Keller, 2014):** The $3\\sigma$ rule states that
            $[\\mu - 3\\sigma, \\mu + 3\\sigma]$ contains $99.73\\%$ of produced parts. Defining tolerance as
            $t_i = 3\\sigma_i$ is the standard industrial convention.
            """)
            
            st.markdown("### Monte Carlo Estimation of Defect Probability")
            st.markdown("""
            The defect probability for a tolerance vector $T$ is:
            """)
            st.latex(r"P_{\text{defect}}(T) = \mathbb{P}_{X \sim \mathcal{D}(T)}\left[ f(X) \leq 0 \right]")
            st.markdown("""
            Since this integral cannot be computed analytically, we estimate it via Monte Carlo simulation:
            """)
            st.latex(r"\hat{P}_{\text{defect}} = \frac{1}{N} \sum_{k=1}^{N} \mathbf{1}_{\{f(X_k) \leq 0\}}")
            st.markdown("""
            where $X_1, \\dots, X_N$ are $N$ independent samples from $\\mathcal{D}(T)$.
            
            **Statistical properties:** $\\hat{P}_{\\text{defect}}$ is **unbiased** and **consistent**.
            Its variance is bounded by $1/(4N)$. For $N = 5.000$, the standard error is below $0.007$.
            """)
            
            st.markdown("### UQ Integration in Our System")
            st.markdown("""
            Uncertainty quantification appears in **two points** of the system:
            
            **1. In the optimization loop (online):** At each iteration, after the Tester finds the worst case
            (by enumerating the 64 corners), a mini Monte Carlo estimates $P_{\\text{defect}}$ for current tolerances.
            
            **2. After optimization (offline):** A full Monte Carlo ($N = 5.000$) runs on the optimal tolerances
            for validation and comparison with traditional methods.
            
            **Novelty:** Unlike traditional methods where UQ is a separate post-optimization step, our system
            **integrates UQ into the feedback loop**. Risk estimation directly guides the Designer Agent's decisions
            through the $\\beta$ factor, creating synergy between optimization and uncertainty quantification.
            """)
        
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>np.random.normal(loc=nom, scale=t/3)</code> in aplicatia Streamlit (tab-ul Optimizare)
        </div>
        """, unsafe_allow_html=True)
    
    # ---------- TAB 5.7: FUNCTIA DE COST ----------
    with tm7:
        st.markdown("### 7. " + ("Functia de cost si regula de ajustare" if st.session_state.lang == 'ro' else "Cost Function and Adjustment Rule"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Modelarea costului de fabricatie si definirea regulii de ajustare.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Functia de cost:**")
            st.latex(r"\text{Cost}(T) = \sum_{i=1}^{6} \frac{1}{t_i}")
            st.markdown("**Justificare:** Costul creste invers proportional cu precizia (Singh et al., 2009).")
            st.markdown("**Regula de ajustare — pas relativ:**")
            st.markdown("- **Strangere:** $t_i \\leftarrow t_i / (1 + \\delta_{\\text{efectiv}})$")
            st.markdown("- **Largire:** $t_i \\leftarrow t_i \\times (1 + \\delta_{\\text{efectiv}})$")
            st.markdown("cu $\\delta_{\\text{efectiv}} = \\beta \\cdot \\delta$, $\\delta = 0.2$.")
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Modeling manufacturing cost and defining the adjustment rule.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"\text{Cost}(T) = \sum_{i=1}^{6} \frac{1}{t_i}")
            st.markdown("- **Tightening:** $t_i \\leftarrow t_i / (1 + \\delta_{\\text{effective}})$")
            st.markdown("- **Widening:** $t_i \\leftarrow t_i \\times (1 + \\delta_{\\text{effective}})$")
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>agent_proiectant.py</code> → metoda <code>primeste_raport()</code>
        </div>
        """, unsafe_allow_html=True)
    
    # ---------- TAB 5.8: CONVERGENTA ----------
    with tm8:
        st.markdown("### 8. " + ("Convergenta sistemului" if st.session_state.lang == 'ro' else "System Convergence"))
        if st.session_state.lang == 'ro':
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Obiectiv:</strong> Stabilirea conditiilor in care sistemul a atins solutia optima.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            **Criteriul de convergenta:**
            1. **Calitate:** $f(X) > -0.01$ mm pentru toate cele 64 de colturi
            2. **Stabilitate:** 2 iteratii consecutive OK
            
            **Demonstratia convergentei:**
            - **Monotonitatea strangerii:** $t_j \\leftarrow t_j/(1+\\delta) < t_j$
            - **Finitudinea explorarii:** Maxim 6 esecuri de largire
            - **Marginirea inferioara:** $t_{\\min} = 0.01$ mm
            - **Neuronul fractionar:** $\\beta$ scade brusc la tranzitie
            
            **Garantia oferita:** **Absoluta** — niciuna din cele 64 de combinatii nu produce interferenta.
            """)
        else:
            st.markdown("""
            <div style="background: rgba(128,128,128,0.06); border-radius: 10px; padding: 20px; margin: 15px 0;">
                <p style="font-size: 1rem; line-height: 1.7;">
                <strong>Objective:</strong> Establishing conditions for optimal solution.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            **Convergence Criterion:**
            1. **Quality:** $f(X) > -0.01$ mm for all 64 corners
            2. **Stability:** 2 consecutive OK iterations
            **Guarantee:** **Absolute** — none of the 64 combinations produces interference.
            """)
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border-left: 3px solid #667eea; border-radius: 0 8px 8px 0; padding: 10px 15px; margin-top: 15px;">
            <strong>💻 Implementare:</strong> <code>principal.py</code> → bucla principala
        </div>
        """, unsafe_allow_html=True)

# ================================================================
# TAB 6: ASISTENT AI
# ================================================================
with tab6:
    st.title("💬 Asistent AI")
    
    if st.session_state.lang == 'ro':
        st.markdown("Pune orice intrebare despre acest proiect.")
    else:
        st.markdown("Ask anything about this project.")
    
    intrebare = st.text_input(
        "Intrebarea ta:" if st.session_state.lang == 'ro' else "Your question:",
        placeholder="Ex: Ce este Beta?" if st.session_state.lang == 'ro' else "E.g.: What is Beta?"
    )
    
    if intrebare:
        with st.spinner("Se genereaza raspunsul..." if st.session_state.lang == 'ro' else "Generating answer..."):
            context = """
            Tu esti un asistent AI pentru un proiect de cercetare despre optimizarea tolerantelor.
            Sistem multi-agent cu neuron fractionar.
            Doi agenti: Proiectantul si Testerul.
            64 de colturi verificate exhaustiv. Garantie matematica absoluta.
            Raspunde scurt, clar, in limba intrebarii.
            """
            
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": st.secrets["GEMINI_API_KEY"]
            }
            
            payload = {
                "contents": [{"parts": [{"text": context + "\n\nIntrebare: " + intrebare}]}]
            }
            
            raspuns_api = requests.post(url, json=payload, headers=headers)
            
            if raspuns_api.status_code == 200:
                raspuns = raspuns_api.json()['candidates'][0]['content']['parts'][0]['text']
                st.markdown(raspuns)
            else:
                st.error(f"Eroare API: {raspuns_api.status_code}")
                st.write(raspuns_api.text[:300])
