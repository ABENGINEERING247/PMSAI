import io
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

APP_TITLE = "PMS AI — Predictive Maintenance System"
DB_PATH = Path("pms_ai_history.db")

# Cute Anime-style Innocent Boy Avatar for ALI & Chotu
ALI_ANIME_AVATAR = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png"

st.set_page_config(
    page_title="PMS AI — Drone & Autonomous Platform Maintenance",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------- Avionics Dark Theme & Anime Animations --------
st.markdown(f"""
<style>
:root {{ 
    --navy: #0a192f; 
    --card-bg: #112240; 
    --blue: #087cf0; 
    --cyan: #12c7ed; 
    --danger: #ff4b4b; 
    --warning: #ffb703; 
    --success: #28a745;
    --text: #e6f1ff;
}}
.stApp {{ background: linear-gradient(135deg, #0a192f 0%, #020c1b 100%); color: var(--text); }}
header[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
.block-container {{ padding-top: 1rem; padding-bottom: 2rem; max-width: 1600px; }}

@keyframes aliFloat {{
    0% {{ transform: translateY(0px) rotate(0deg); }}
    50% {{ transform: translateY(-8px) rotate(0.5deg); }}
    100% {{ transform: translateY(0px) rotate(0deg); }}
}}

@keyframes speechPop {{
    0% {{ transform: scale(0.8); opacity: 0; }}
    100% {{ transform: scale(1); opacity: 1; }}
}}

.pms-header {{ 
    background: linear-gradient(105deg, #112240, #1d3557); 
    color: white; 
    border-radius: 16px; 
    padding: 24px 30px; 
    margin-bottom: 20px; 
    border: 1px solid #233554;
    box-shadow: 0 8px 32px rgba(10, 25, 47, 0.5); 
}}
.pms-header h1 {{ margin: 0; font-size: 2.4rem; color: #ffffff; letter-spacing: .5px; }}
.pms-header p {{ margin: 6px 0 0; color: #8892b0; }}

/* Anime Ali Hero Banner */
.ali-hero {{ 
    background: linear-gradient(110deg,#112240,#1d3557 65%,#112240); 
    border: 1px solid #233554; 
    border-radius: 20px; 
    padding: 24px; 
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.ali-hero-text {{ max-width: 65%; }}
.ali-hero h3 {{ color: #12c7ed; margin: 0 0 8px; }}

.ali-anime-container {{
    text-align: center;
    position: relative;
    padding-right: 20px;
}}
.ali-anime-img {{
    width: 130px;
    height: auto;
    filter: drop-shadow(0px 8px 16px rgba(18, 199, 237, 0.3));
    animation: aliFloat 3.5s ease-in-out infinite;
}}
.ali-speech-bubble {{
    position: relative;
    background: #087cf0;
    border-radius: 14px;
    color: white;
    padding: 8px 14px;
    font-size: 0.88rem;
    font-weight: 600;
    margin-bottom: 10px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(8, 124, 240, 0.3);
    animation: speechPop 0.5s ease-out, aliFloat 3.5s ease-in-out infinite;
}}
.ali-speech-bubble:after {{
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    width: 0;
    height: 0;
    border: 8px solid transparent;
    border-top-color: #087cf0;
    border-bottom: 0;
    margin-left: -8px;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Database Setup --------------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS pms_ai_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            platform TEXT NOT NULL,
            health_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            report TEXT NOT NULL
        )""")
init_db()

def save_history(platform, health_score, status, report):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO pms_ai_history(created_at, platform, health_score, status, report) VALUES(?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), platform, health_score, status, report)
        )

def load_history(limit=100):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT id, created_at, platform, health_score, status, report FROM pms_ai_history ORDER BY id DESC LIMIT ?", conn, params=(limit,))

# ----------------------------- OpenAI API & Secrets Helpers ------------------
def get_api_key():
    # 1. Check Streamlit Secrets
    try:
        if "OPENAI_API_KEY" in st.secrets:
            key = st.secrets["OPENAI_API_KEY"]
            if key:
                return key
    except Exception:
        pass
    
    # 2. Check Environment Variables
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key:
        return env_key
        
    return ""

def get_model():
    return "gpt-6-luna"

def ask_avionics_ai(prompt, system_persona="You are ALI, an innocent and brilliant anime avionics engineering assistant for autonomous systems."):
    key = get_api_key()
    if not key or OpenAI is None:
        return f"*(Demo Mode)*: {prompt[:300]}...\n\n*(Please configure `OPENAI_API_KEY` in Streamlit Secrets to enable live GPT-6 Luna responses)*"
    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": system_persona},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"**API execution error:** {exc}\n\nRunning in Demo Mode fallback."

# ----------------------------- Document Exporters ----------------------------
def docx_bytes(title, content):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(f"Generated by PMS AI (ALI & Chotu Assistant) • {datetime.now().strftime('%d %b %Y, %H:%M')}")
    doc.add_paragraph("")
    for line in content.splitlines():
        if line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("- ") or line.startswith("* "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif re.match(r"^\d+\.\s", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s", "", line), style="List Number")
        elif line.strip():
            doc.add_paragraph(line.replace("**", "").replace("`", ""))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def pdf_bytes(title, content):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.65*inch, leftMargin=0.65*inch, topMargin=0.65*inch, bottomMargin=0.65*inch)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for line in content.splitlines():
        safe = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("**", "").replace("`", ""))
        if not safe.strip():
            story.append(Spacer(1, 6))
        elif line.startswith("#"):
            story.append(Paragraph(safe.lstrip("# ").strip(), styles["Heading2"]))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph("• " + safe[2:], styles["BodyText"]))
        else:
            story.append(Paragraph(safe, styles["BodyText"]))
            story.append(Spacer(1, 4))
    doc.build(story)
    return buf.getvalue()

# ----------------------------- Header ----------------------------------------
st.markdown("""
<div class="pms-header">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap">
    <div>
      <h1>🚁 PMS AI — Predictive Maintenance System</h1>
      <p><b>Autonomous Systems Reliability & Avionics Diagnostics</b></p>
    </div>
    <div style="text-align:right">
      <div style="font-size:0.95rem;color:#64ffda">Assistants: <b>ALI & Chotu 👦</b></div>
      <div style="border:1px solid #12c7ed;border-radius:10px;padding:6px 12px;display:inline-block;margin-top:6px;font-size:0.85rem">
        <span style="color:#28e08b">●</span> GPT-6 Luna Connected
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Sidebar Navigation ----------------------------
with st.sidebar:
    st.markdown("## 🧭 PMS AI Navigation")
    page = st.radio(
        "Navigation Menu",
        [
            "📊 Live Telemetry & Fleet Status",
            "🤖 AI Diagnostics & Work Orders",
            "💬 Chotu Chatbot",
            "📈 Flight Log Analyzer (CSV Upload)",
            "🕘 History & Maintenance Database",
            "⚙️ System Settings"
        ],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("### 👦 Meet ALI & Chotu")
    st.markdown(f"""
    <div style="text-align:center; padding: 5px 0;">
      <img src="{ALI_ANIME_AVATAR}" style="width: 90px; filter: drop-shadow(0px 4px 10px rgba(0,0,0,0.3)); animation: aliFloat 4s ease-in-out infinite;" />
    </div>
    """, unsafe_allow_html=True)
    st.caption('"Always here to keep your fleet flying safely!"')
    st.divider()
    st.caption("Platform: Multi-Rotor & UGV Fleet")
    st.caption("Designed by Engr. Bilal Mehmood")

# ============================= PAGE 1: LIVE TELEMETRY ========================
if page == "📊 Live Telemetry & Fleet Status":
    st.markdown(f"""
    <div class="ali-hero">
      <div class="ali-hero-text">
        <h3>👋 Hi! I'm ALI, your avionics assistant!</h3>
        <p style="margin:0; font-size: 0.95rem; color: #a0aec0;">
          I'm monitoring your drone and autonomous fleet telemetry in real time. Check the sensors below and let's make sure everything is ready for flight!
        </p>
      </div>
      <div class="ali-anime-container">
        <div class="ali-speech-bubble">All systems nominal! 🚀</div><br>
        <img src="{ALI_ANIME_AVATAR}" class="ali-anime-img" alt="Anime ALI" />
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Real-Time Fleet Telemetry & Physics Health Engine")
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        platform = st.selectbox(
            "Select Autonomous Platform",
            [
                "Heavy Lift Hexacopter (Drone #01)",
                "Long-Range Fixed-Wing UAV (Drone #04)",
                "Autonomous Rover / UGV (Rover #02)"
            ]
        )
    with col_sel2:
        st.markdown(f"**Selected Node ID:** `{platform.split('(')[-1].replace(')', '')}`")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🕹️ Telemetry Simulator")
    vibration = st.sidebar.slider("Motor Vibration (m/s²)", 0.0, 25.0, 3.2, 0.1)
    temperature = st.sidebar.slider("Motor/ESC Temperature (°C)", 20, 120, 48, 1)
    battery_delta = st.sidebar.slider("Battery Cell Delta (mV)", 5, 150, 15, 1)
    esc_current = st.sidebar.slider("Peak ESC Current (Amps)", 10, 120, 38, 1)
    rpm_variance = st.sidebar.slider("RPM Variance (% imbalance)", 0.0, 25.0, 1.2, 0.1)

    score_vib = max(0, 100 - (vibration / 25.0) * 100)
    score_temp = max(0, 100 - ((temperature - 20) / 100.0) * 100)
    score_batt = max(0, 100 - (battery_delta / 150.0) * 100)
    score_curr = max(0, 100 - ((esc_current - 10) / 110.0) * 100)
    score_rpm = max(0, 100 - (rpm_variance / 25.0) * 100)

    health_index = int(0.30 * score_vib + 0.25 * score_temp + 0.20 * score_batt + 0.15 * score_curr + 0.10 * score_rpm)

    if health_index > 80:
        status, status_color = "🟢 HEALTHY", "#28a745"
    elif health_index >= 50:
        status, status_color = "🟡 WARNING / DEGRADATION", "#ffb703"
    else:
        status, status_color = "🔴 CRITICAL ANOMALY", "#ff4b4b"

    st.session_state["pms_ai_telemetry"] = {
        "platform": platform,
        "health_index": health_index,
        "status": status,
        "vibration": vibration,
        "temperature": temperature,
        "battery_delta": battery_delta,
        "esc_current": esc_current,
        "rpm_variance": rpm_variance
    }

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Platform Health Index", f"{health_index}%", delta=f"{health_index - 100}%", delta_color="inverse")
    m2.metric("Motor Temperature", f"{temperature} °C", delta="Elevated" if temperature > 65 else "Normal", delta_color="inverse")
    m3.metric("Motor Vibration", f"{vibration} m/s²", delta="High" if vibration > 5.0 else "Nominal", delta_color="inverse")
    m4.metric("Battery Cell Delta", f"{battery_delta} mV", delta="Imbalanced" if battery_delta > 30 else "Stable", delta_color="inverse")

    st.markdown(f"### Overall System Status: <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
    st.divider()

    col_chart, col_table = st.columns([1.8, 1.2])
    with col_chart:
        st.subheader("📈 Telemetry Drift Simulator (Last 30 Cycles)")
        cycles = list(range(1, 31))
        sim_vib = np.clip(np.random.normal(vibration, 0.4, 30), 0, 25)
        sim_temp = np.clip(np.random.normal(temperature, 1.2, 30), 20, 120)
        
        df_sim = pd.DataFrame({"Cycle": cycles, "Vibration": sim_vib, "Temperature": sim_temp})
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_sim["Cycle"], y=df_sim["Vibration"], name="Vibration (m/s²)", line=dict(color="#12c7ed", width=2)))
        fig.add_trace(go.Scatter(x=df_sim["Cycle"], y=df_sim["Temperature"], name="Temperature (°C)", line=dict(color="#ff4b4b", width=2), yaxis="y2"))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e6f1ff"),
            xaxis=dict(title="Flight Cycle", gridcolor="#233554"),
            yaxis=dict(title="Vibration (m/s²)", titlefont=dict(color="#12c7ed"), gridcolor="#233554"),
            yaxis2=dict(title="Temperature (°C)", titlefont=dict(color="#ff4b4b"), overlaying="y", side="right"),
            legend=dict(x=0, y=1.1, orientation="h"), height=380, margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("⚙️ Avionics Sensor Parameters")
        st.dataframe(
            pd.DataFrame({
                "Sensor Metric": ["Vibration RMS", "ESC Temp", "Cell Delta", "ESC Current", "RPM Imbalance"],
                "Current": [f"{vibration} m/s²", f"{temperature} °C", f"{battery_delta} mV", f"{esc_current} A", f"{rpm_variance}%"],
                "Safe Threshold": ["< 5.0 m/s²", "< 65 °C", "< 30 mV", "< 50 A", "< 3.0%"]
            }),
            use_container_width=True, hide_index=True
        )

# ============================= PAGE 2: AI DIAGNOSTICS ========================
elif page == "🤖 AI Diagnostics & Work Orders":
    st.subheader("🤖 GPT-6 Luna & ALI AI Diagnostics & Maintenance Work Order Generator")
    
    if "pms_ai_telemetry" not in st.session_state:
        st.session_state["pms_ai_telemetry"] = {
            "platform": "Heavy Lift Hexacopter (Drone #01)",
            "health_index": 72,
            "status": "🟡 WARNING / DEGRADATION",
            "vibration": 6.2,
            "temperature": 74,
            "battery_delta": 45,
            "esc_current": 62,
            "rpm_variance": 4.1
        }

    t_data = st.session_state["pms_ai_telemetry"]
    
    st.markdown(f"""
    **Active Platform:** `{t_data['platform']}`  
    **Health Index:** `{t_data['health_index']}%` | **Status:** `{t_data['status']}`
    """)

    if st.button("✨ Run GPT-6 Luna Flight Diagnostic", type="primary", use_container_width=True):
        prompt = f"""
        Analyze the following telemetry data for autonomous platform {t_data['platform']}:
        - Health Index: {t_data['health_index']}%
        - Status: {t_data['status']}
        - Motor Vibration: {t_data['vibration']} m/s² (Normal: < 5.0)
        - Motor/ESC Temperature: {t_data['temperature']} °C (Normal: < 65)
        - Battery Cell Voltage Delta: {t_data['battery_delta']} mV (Normal: < 30)
        - Peak ESC Current Draw: {t_data['esc_current']} A (Normal: < 50)
        - RPM Variance / Prop Imbalance: {t_data['rpm_variance']}% (Normal: < 3.0)

        Provide a rigorous aviation/avionics engineering report containing:
        1. Root Cause Analysis (RCA): Explain mechanical/electrical failure mechanisms (e.g., motor bearing wear, ESC overheating, battery cell degradation, prop imbalance).
        2. Flight Risk & Pre-Flight Clearance: State explicitly whether the drone is CLEARED FOR FLIGHT or GROUNDED IMMEDIATELY.
        3. Corrective Maintenance Protocol: Step-by-step repair guide for field technicians.
        4. Formal Work Order Ticket: Summary including required replacement parts, tools, safety guidelines, and estimated service downtime.
        """
        
        with st.spinner("ALI is analyzing avionics telemetry via GPT-6 Luna..."):
            report_result = ask_avionics_ai(prompt)
            st.session_state["last_report"] = report_result
            save_history(t_data["platform"], t_data["health_index"], t_data["status"], report_result)

    if "last_report" in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Generated Avionics Diagnostic Report")
        st.markdown(st.session_state["last_report"])
        
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇️ Download Word Report (.docx)", docx_bytes("PMS AI Avionics Report", st.session_state["last_report"]), "PMS_AI_Avionics_Report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with dl2:
            st.download_button("⬇️ Download PDF Report (.pdf)", pdf_bytes("PMS AI Avionics Report", st.session_state["last_report"]), "PMS_AI_Avionics_Report.pdf", "application/pdf", use_container_width=True)

# ============================= PAGE 3: CHOTU CHATBOT ========================
elif page == "💬 Chotu Chatbot":
    st.subheader("💬 Chotu Chatbot — Avionics & Maintenance Assistant")
    st.caption("Chat live with Chotu & ALI for quick troubleshooting, wiring tips, and predictive maintenance guidance.")

    if "chotu_messages" not in st.session_state:
        st.session_state["chotu_messages"] = [
            {"role": "assistant", "content": "Hi! I'm Chotu 👦 zusammen with ALI! Ask me anything about drone maintenance, sensor troubleshooting, or engine diagnostics!"}
        ]

    for msg in st.session_state["chotu_messages"]:
        avatar = ALI_ANIME_AVATAR if msg["role"] == "assistant" else "🙂"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask Chotu a question...")
    if user_query:
        st.session_state["chotu_messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user", avatar="🙂"):
            st.markdown(user_query)

        with st.chat_message("assistant", avatar=ALI_ANIME_AVATAR):
            with st.spinner("Chotu is thinking..."):
                chotu_response = ask_avionics_ai(
                    user_query, 
                    system_persona="You are Chotu, a helpful, enthusiastic, and innocent anime assistant specializing in drones, robotics, and industrial predictive maintenance."
                )
            st.markdown(chotu_response)
        st.session_state["chotu_messages"].append({"role": "assistant", "content": chotu_response})

# ============================= PAGE 4: CSV LOG ANALYZER ======================
elif page == "📈 Flight Log Analyzer (CSV Upload)":
    st.subheader("📈 Black-Box Flight Log Analyzer (CSV Upload)")
    st.caption("Upload historical flight telemetry CSV logs to automatically scan for anomaly spikes and threshold breaches.")

    uploaded_file = st.file_uploader("Upload Flight Log CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df_log = pd.read_csv(uploaded_file)
            st.success("Flight log successfully loaded.")
            st.dataframe(df_log.head(10), use_container_width=True)
            
            if {"Timestamp", "Vibration", "Temperature", "Voltage", "Current"}.issubset(df_log.columns):
                st.subheader("📊 Telemetry Anomaly Scan")
                fig_log = px.line(df_log, x="Timestamp", y=["Vibration", "Temperature", "Voltage", "Current"], title="Flight Telemetry Timeseries Analysis")
                fig_log.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e6f1ff"))
                st.plotly_chart(fig_log, use_container_width=True)
            else:
                st.warning("CSV must contain columns: `Timestamp`, `Vibration`, `Temperature`, `Voltage`, `Current`.")
        except Exception as e:
            st.error(f"Error parsing CSV file: {e}")
    else:
        st.info("Tip: Upload a flight log CSV to inspect anomaly spikes across historical missions.")

# ============================= PAGE 5: HISTORY & DATABASE ====================
elif page == "🕘 History & Maintenance Database":
    st.subheader("🕘 Maintenance History & SQLite Database")
    st.caption("Review previous AI diagnostic reports and fleet health records.")

    history_df = load_history()
    if history_df.empty:
        st.info("No maintenance logs recorded yet. Run a diagnostic in **Page 2** to store records.")
    else:
        st.dataframe(history_df[["created_at", "platform", "health_score", "status"]], use_container_width=True, hide_index=True)
        
        selected_id = st.selectbox("Select Log ID to View Details", history_df["id"].tolist())
        selected_row = history_df[history_df["id"] == selected_id].iloc[0]
        
        st.markdown(f"### 📄 Report Details [ID #{selected_id}] — {selected_row['platform']}")
        st.caption(f"Generated at: {selected_row['created_at']} | Health: {selected_row['health_score']}% | Status: {selected_row['status']}")
        st.markdown(selected_row["report"])
        
        st.download_button("Download Report as TXT", selected_row["report"], f"PMS_AI_Log_{selected_id}.txt", "text/plain")

# ============================= PAGE 6: SETTINGS ==============================
elif page == "⚙️ System Settings":
    st.subheader("⚙️ System Settings & Configuration")
    
    key_status = bool(get_api_key()) and OpenAI is not None
    st.metric("OpenAI API Status", "Connected via Secrets/Env" if key_status else "Demo / Fallback Mode")
    st.write(f"**Locked AI Engine Model:** `{get_model()}`")
    
    st.markdown("#### Configure Streamlit Secrets (`.streamlit/secrets.toml`)")
    st.code('OPENAI_API_KEY = "your-actual-openai-api-key-here"', language="toml")
    st.markdown("For Streamlit Community Cloud, open your app dashboard → **Settings → Secrets** and add your OpenAI API key securely.")
    
    st.divider()
    st.markdown("#### About PMS AI & Chotu")
    st.write("Predictive Maintenance System AI (PMS AI) for Drones & Autonomous Platforms")
    st.write("Assistants: ALI & Chotu | Built with Python, Streamlit, and OpenAI API (`gpt-6-luna`)")

st.divider()
st.caption("PMS AI — Autonomous Systems Reliability & Avionics Diagnostics  |  Powered by GPT-6 Luna  |  Designed by Engr. Bilal Mehmood")
