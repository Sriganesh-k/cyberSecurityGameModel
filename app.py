import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Cyber Stackelberg", page_icon="🛡️", layout="wide")

NODES = ["Entry", "Workstation", "Server", "Database", "Critical System"]
EDGES = [
    ("Entry", "Workstation"),
    ("Workstation", "Server"),
    ("Workstation", "Database"),
    ("Server", "Critical System"),
    ("Database", "Critical System"),
]


def initialise_game() -> None:
    if "round" not in st.session_state:
        st.session_state.round = 1
        st.session_state.turn = "Defender"
        st.session_state.status = {node: "Safe" for node in NODES}
        st.session_state.protected = set()
        st.session_state.log = ["Game started. Defender moves first."]


def reset_game() -> None:
    for key in ["round", "turn", "status", "protected", "log"]:
        st.session_state.pop(key, None)
    initialise_game()


def draw_network() -> None:
    graph = nx.Graph()
    graph.add_nodes_from(NODES)
    graph.add_edges_from(EDGES)

    positions = {
        "Entry": (0, 2),
        "Workstation": (0, 1),
        "Server": (-1, 0),
        "Database": (1, 0),
        "Critical System": (0, -1),
    }

    colours = []
    for node in NODES:
        if st.session_state.status[node] == "Compromised":
            colours.append("#ef4444")
        elif node in st.session_state.protected:
            colours.append("#f59e0b")
        else:
            colours.append("#22c55e")

    fig, ax = plt.subplots(figsize=(7, 5))
    nx.draw_networkx(
        graph,
        positions,
        node_color=colours,
        node_size=2600,
        font_size=9,
        font_weight="bold",
        edge_color="#64748b",
        width=2,
        ax=ax,
    )
    ax.set_axis_off()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def defender_action(node: str) -> None:
    st.session_state.protected.add(node)
    st.session_state.log.append(f"Defender protected {node}.")
    st.session_state.turn = "Attacker"


def attacker_action(node: str) -> None:
    if node in st.session_state.protected:
        st.session_state.log.append(f"Attack on {node} failed because it was protected.")
    else:
        st.session_state.status[node] = "Compromised"
        st.session_state.log.append(f"Attacker compromised {node}.")

    if node == "Critical System" and st.session_state.status[node] == "Compromised":
        st.session_state.turn = "Game Over"
    elif st.session_state.round >= 3:
        st.session_state.turn = "Game Over"
    else:
        st.session_state.round += 1
        st.session_state.turn = "Defender"
        st.session_state.protected.clear()


initialise_game()

st.title("🛡️ Cyber Stackelberg Learning Game")
st.caption("Minimal two-player prototype: the Defender acts first, then the Attacker responds.")

metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Round", f"{st.session_state.round} / 3")
metric_b.metric("Current turn", st.session_state.turn)
metric_c.metric(
    "Compromised nodes",
    sum(value == "Compromised" for value in st.session_state.status.values()),
)

board_col, control_col = st.columns([2, 1])

with board_col:
    st.subheader("Game board")
    draw_network()
    st.info("Green = safe · Amber = protected · Red = compromised")

with control_col:
    st.subheader("Player actions")

    if st.session_state.turn == "Defender":
        target = st.selectbox("Choose a node to protect", NODES)
        if st.button("Protect node", type="primary", use_container_width=True):
            defender_action(target)
            st.rerun()

    elif st.session_state.turn == "Attacker":
        target = st.selectbox("Choose a node to attack", NODES)
        if st.button("Attack node", type="primary", use_container_width=True):
            attacker_action(target)
            st.rerun()

    else:
        critical_lost = st.session_state.status["Critical System"] == "Compromised"
        if critical_lost:
            st.error("Attacker wins: the Critical System was compromised.")
        else:
            st.success("Defender wins: the Critical System remained safe.")

    if st.button("Reset game", use_container_width=True):
        reset_game()
        st.rerun()

st.subheader("Event log")
for event in reversed(st.session_state.log):
    st.write(f"• {event}")
