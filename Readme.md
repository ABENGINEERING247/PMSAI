# 🚁 PMS AI — Predictive Maintenance System for Drones & Autonomous Platforms

**PMS AI** is an advanced, AI-powered Predictive Maintenance and Avionics Diagnostics platform designed for unmanned aerial vehicles (UAVs), multirotors (hexacopters/quadcopters), autonomous rovers (UGVs), and industrial controllers. 

It bridges raw hardware sensor telemetry (vibration, thermal drift, voltage variance) with **Agentic AI** (`gpt-6-luna`) to deliver real-time health index scoring, autonomous root-cause analysis, corrective maintenance protocols, and automated work orders.

---

## 🌟 Key Features

1. **📊 Real-Time Telemetry & Physics Health Engine**: Live tracking and simulation of motor vibration, ESC temperature, battery cell delta voltage, peak current draw, and RPM variance with a dynamic Health Index calculation ($0-100\%$).
2. **🤖 GPT-6 Luna Avionics Diagnostics**: Automated generation of comprehensive engineering reports including Root Cause Analysis (RCA), pre-flight clearance (`CLEARED` vs `GROUNDED`), step-by-step repair guides, and formal work order tickets.
3. **💬 Chotu Chatbot**: An interactive, dedicated chat assistant powered by **ALI & Chotu** to help field technicians troubleshoot wiring, sensor anomalies, and maintenance procedures in real time.
4. **📈 Black-Box Flight Log Analyzer**: Upload historical telemetry CSV files to scan for anomaly spikes and multi-parameter time-series drift.
5. **🕘 Maintenance History Database**: Local SQLite persistence (`pms_ai_history.db`) to store, search, and export past diagnostic logs.
6. **📄 Multi-Format Exports**: Instantly download professional engineering reports as Word (`.docx`), PDF (`.pdf`), or Text (`.txt`) files.

---

## 🔌 Connecting Industrial Hardware & Controllers to Agentic AI

PMS AI is architected to interface physical machines and embedded controllers with **Agentic AI workflows**:
* **Hardware Ingestion**: Microcontrollers (Arduino/ESP32), ESCs, and PLCs transmit telemetry via CAN bus, MQTT, or Modbus to edge gateways.
* **Deterministic Physics Layer**: Low-latency anomaly detection flags threshold breaches instantly.
* **Agentic Reasoning (ALI & Chotu)**: When anomalies occur, the AI agent reasons through cross-sensor telemetry patterns, diagnoses underlying failure mechanisms, and can trigger automated safety protocols or draft ERP work orders.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Install Dependencies
Clone or download the project repository and run:
```bash
pip install -r requirements.txt
