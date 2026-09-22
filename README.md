# 🛡️ Cyber Stackelberg Learning Game

A simple **cybersecurity research game** built with **Python + Streamlit** to study Defender–Attacker decision-making, budget usage, and attack-path progression.

## 🎯 Game Objective

* 🛡️ **Defender:** Stop the attacker from reaching the Critical System.
* ⚔️ **Attacker:** Move through the network and compromise the Critical System.

## 🌐 Network

```text
Entry
  ↓
Workstation
 ↙       ↘
Server   Database
 ↘       ↙
Critical System
```

## 🛡️ Defender Actions

* 🟠 **Protect** — reduce attack success
* ⛔ **Block** — strongly restrict attacks
* 🔍 **Detect** — detect attacker activity

## ⚔️ Attacker Actions

* 🔎 **Scan** — improve future attack success
* 💥 **Attack** — compromise a connected node
* 🕳️ **Bypass** — expensive but less affected by defence

## 💰 Budget System

Both players have limited money.

Resources can be spent on:

* actions
* defence tools
* attacker tools
* protecting important systems
* improving attack chances

## 🗺️ Visual Status

* 🟢 Safe
* 🟠 Protected
* ⚫ Blocked
* 🔴 Compromised
* 🔵 Detection Sensor
* 🟣 `A` = Attacker Position

## 📊 Research Dashboard

The application displays:

* current round
* attacker location
* Defender and Attacker budgets
* utility values
* estimated win probability
* compromised nodes
* detection events
* experiment history
* CSV export

## 🚀 Run the Project

Create and activate the virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the application:

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## 🧠 Game-Theory Idea

The game follows a simplified **Stackelberg leader–follower model**:

```text
Defender acts first
        ↓
Attacker observes
        ↓
Attacker responds
        ↓
Game state updates
```

🛡️ **Defender = Leader**
⚔️ **Attacker = Follower**

## 🔬 Research Purpose

The project explores how **limited cybersecurity budgets and strategic resource allocation** can influence attack and defence outcomes.

> ⚠️ The displayed win probability is currently a heuristic estimate and not a formal Strong Stackelberg Equilibrium calculation.

## 🛠️ Technologies

* 🐍 Python
* 🎈 Streamlit
* 🌐 NetworkX
* 📈 Matplotlib
* 📊 Pandas

## 📌 Project Status

**Research Prototype / Learning Project**
