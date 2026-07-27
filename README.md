# Cyber Stackelberg Learning Game — Minimal Prototype

A small two-player learning prototype built with Python and Streamlit.

## 1. Install Python

Install Python 3.11 or newer from the official Python website.
During Windows installation, select **Add Python to PATH**.

Check the installation:

```bash
python --version
```

On some systems use:

```bash
python3 --version
```

## 2. Open the project folder

```bash
cd cyber_stackelberg_minimal
```

## 3. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Start the game

```bash
streamlit run app.py
```

The browser should open automatically. Otherwise open the local address shown in the terminal, normally `http://localhost:8501`.

## Current prototype features

- Two-player local turn flow
- Defender moves first
- Attacker responds
- Five-node network map
- Protected, safe and compromised states
- Three rounds
- Basic winner screen
- Event log

## Next development steps

1. Validate whether an attack target is connected to a compromised node.
2. Add Block, Detect, Scan and Bypass actions.
3. Move game rules into a separate backend module.
4. Add scoring and learning feedback.
5. Improve the interface and add a start screen.
