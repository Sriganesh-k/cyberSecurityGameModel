import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

from game_engine import (
    NODES,
    EDGES,
    NODE_VALUES,
    MAX_ROUNDS,
    DEFENDER_ACTION_COSTS,
    ATTACKER_ACTION_COSTS,
    DEFENDER_ITEMS,
    ATTACKER_ITEMS,
    GameRuleError,
    new_game,
    active_defences,
    defender_targets,
    attacker_targets,
    defender_action,
    attacker_action,
    buy_item,
    pass_turn,
    success_probability,
    estimate_win_probability,
    current_utilities,
    state_table,
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Cyber Stackelberg Research Game",
    page_icon="🛡️",
    layout="wide",
)


# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    .hero-box {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a8a 55%,
            #2563eb 100%
        );
        color: white;
        border-radius: 22px;
        padding: 1.6rem 1.8rem;
        box-shadow: 0 12px 35px rgba(15, 23, 42, 0.18);
        margin-bottom: 1rem;
    }

    .research-label {
        font-size: 0.78rem;
        color: #bfdbfe;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 750;
        margin-bottom: 0.25rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: #dbeafe;
        margin-bottom: 0.9rem;
        max-width: 1000px;
    }

    .hero-pill {
        display: inline-block;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.18);
        color: white;
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        margin-right: 0.35rem;
        margin-top: 0.25rem;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 1rem;
        border: 1px solid rgba(15,23,42,0.08);
        box-shadow: 0 8px 25px rgba(15,23,42,0.06);
        min-height: 112px;
    }

    .metric-label {
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        color: #0f172a;
        font-size: 1.45rem;
        font-weight: 800;
    }

    .metric-caption {
        color: #94a3b8;
        font-size: 0.76rem;
        margin-top: 0.3rem;
    }

    .turn-defender {
        background: linear-gradient(90deg, #dbeafe, #eff6ff);
        color: #1e3a8a;
        border: 1px solid #93c5fd;
        padding: 1rem;
        border-radius: 15px;
        font-weight: 800;
        margin-bottom: 1rem;
    }

    .turn-attacker {
        background: linear-gradient(90deg, #fee2e2, #fff1f2);
        color: #991b1b;
        border: 1px solid #fca5a5;
        padding: 1rem;
        border-radius: 15px;
        font-weight: 800;
        margin-bottom: 1rem;
    }

    .turn-over {
        background: linear-gradient(90deg, #ede9fe, #f5f3ff);
        color: #5b21b6;
        border: 1px solid #c4b5fd;
        padding: 1rem;
        border-radius: 15px;
        font-weight: 800;
        margin-bottom: 1rem;
    }

    .legend-chip {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        margin: 0.15rem 0.2rem;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #334155;
        font-size: 0.78rem;
        font-weight: 650;
    }

    .network-info {
        background: #f8fafc;
        border-left: 4px solid #7c3aed;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        margin-top: 0.8rem;
        color: #334155;
        font-size: 0.9rem;
    }

    .small-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 0.25rem 0.55rem;
        margin-right: 0.25rem;
        font-size: 0.75rem;
        font-weight: 700;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #334155;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# SESSION STATE
# ==========================================================

if "game" not in st.session_state:
    st.session_state.game = new_game(seed=42)

game = st.session_state.game


# ==========================================================
# HELPERS
# ==========================================================

def reset_game():
    seed = int(
        st.session_state.get(
            "seed_value",
            42,
        )
    )

    st.session_state.game = new_game(seed=seed)
    st.rerun()


def metric_card(label, value, caption):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                {label}
            </div>

            <div class="metric-value">
                {value}
            </div>

            <div class="metric-caption">
                {caption}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_turn_banner():
    if game["turn"] == "Defender":
        st.markdown(
            """
            <div class="turn-defender">
                🛡️ DEFENDER TURN —
                Select a defensive strategy before the attacker responds.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif game["turn"] == "Attacker":
        st.markdown(
            """
            <div class="turn-attacker">
                ⚔️ ATTACKER TURN —
                Observe the current defence and select the next offensive action.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            f"""
            <div class="turn-over">
                🏁 GAME OVER
                &nbsp;&nbsp;
                Winner: <b>{game["winner"]}</b>
                &nbsp;&nbsp;
                {game["end_reason"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================
# NETWORK GRAPH
# ==========================================================

def draw_network():

    graph = nx.DiGraph()

    graph.add_nodes_from(NODES)
    graph.add_edges_from(EDGES)

    positions = {
        "Entry": (0, 3.3),
        "Workstation": (0, 2.15),
        "Server": (-1.25, 1.0),
        "Database": (1.25, 1.0),
        "Critical System": (0, -0.25),
    }

    current_position = game["attacker_position"]

    fig, ax = plt.subplots(
        figsize=(9, 6.4)
    )

    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    # ------------------------------------------------------
    # STANDARD NETWORK EDGES
    # ------------------------------------------------------

    nx.draw_networkx_edges(
        graph,
        positions,
        edge_color="#cbd5e1",
        width=2.3,
        arrows=True,
        arrowsize=20,
        arrowstyle="-|>",
        min_source_margin=30,
        min_target_margin=30,
        ax=ax,
    )

    # ------------------------------------------------------
    # REACHABLE ATTACK PATH
    # ------------------------------------------------------

    reachable_nodes = attacker_targets(game)

    reachable_edges = []

    for target in reachable_nodes:
        if (current_position, target) in EDGES:
            reachable_edges.append(
                (current_position, target)
            )

        elif (target, current_position) in EDGES:
            reachable_edges.append(
                (target, current_position)
            )

    if reachable_edges:
        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=reachable_edges,
            edge_color="#8b5cf6",
            width=4,
            arrows=True,
            arrowsize=22,
            arrowstyle="-|>",
            min_source_margin=30,
            min_target_margin=30,
            ax=ax,
        )

    # ------------------------------------------------------
    # NODE COLOURS
    # ------------------------------------------------------

    node_colours = []

    for node in NODES:

        defence = active_defences(
            game,
            node,
        )

        if game["status"][node] == "Compromised":
            node_colours.append("#ef4444")

        elif "Blocked" in defence:
            node_colours.append("#334155")

        elif "Protected" in defence:
            node_colours.append("#f59e0b")

        else:
            node_colours.append("#22c55e")

    # ------------------------------------------------------
    # NODE SHADOW
    # ------------------------------------------------------

    shadow_positions = {
        node: (
            position[0] + 0.035,
            position[1] - 0.035,
        )
        for node, position in positions.items()
    }

    nx.draw_networkx_nodes(
        graph,
        shadow_positions,
        node_color="#cbd5e1",
        node_size=3350,
        linewidths=0,
        ax=ax,
    )

    # ------------------------------------------------------
    # MAIN NODES
    # ------------------------------------------------------

    nx.draw_networkx_nodes(
        graph,
        positions,
        node_color=node_colours,
        node_size=3250,
        edgecolors="#ffffff",
        linewidths=3,
        ax=ax,
    )

    # ------------------------------------------------------
    # CRITICAL SYSTEM BORDER
    # ------------------------------------------------------

    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=["Critical System"],
        node_color="none",
        node_size=3750,
        edgecolors="#dc2626",
        linewidths=3,
        ax=ax,
    )

    # ------------------------------------------------------
    # DETECTION SENSOR RING
    # ------------------------------------------------------

    sensor_nodes = []

    for node in NODES:
        if "Sensor" in active_defences(
            game,
            node,
        ):
            sensor_nodes.append(node)

    if sensor_nodes:
        nx.draw_networkx_nodes(
            graph,
            positions,
            nodelist=sensor_nodes,
            node_color="none",
            node_size=3800,
            edgecolors="#2563eb",
            linewidths=4,
            ax=ax,
        )

    # ------------------------------------------------------
    # NODE LABELS
    # ------------------------------------------------------

    labels = {
        "Entry": "ENTRY\nGateway",
        "Workstation": "WORKSTATION\n€20",
        "Server": "SERVER\n€45",
        "Database": "DATABASE\n€55",
        "Critical System": "CRITICAL SYSTEM\n€100",
    }

    nx.draw_networkx_labels(
        graph,
        positions,
        labels=labels,
        font_size=9,
        font_weight="bold",
        font_color="white",
        ax=ax,
    )

    # ------------------------------------------------------
    # ATTACKER TOKEN
    # ------------------------------------------------------

    attacker_x = positions[current_position][0]
    attacker_y = positions[current_position][1]

    token_x = attacker_x + 0.48
    token_y = attacker_y + 0.38

    # Outer coin
    ax.scatter(
        token_x,
        token_y,
        s=1100,
        color="#6d28d9",
        edgecolors="#ffffff",
        linewidths=4,
        zorder=20,
    )

    # Inner coin
    ax.scatter(
        token_x,
        token_y,
        s=760,
        color="#7c3aed",
        edgecolors="#c4b5fd",
        linewidths=2,
        zorder=21,
    )

    # A symbol
    ax.text(
        token_x,
        token_y,
        "A",
        color="white",
        fontsize=17,
        fontweight="bold",
        horizontalalignment="center",
        verticalalignment="center",
        zorder=22,
    )

    # Pointer
    ax.annotate(
        "",
        xy=(
            attacker_x,
            attacker_y,
        ),
        xytext=(
            token_x,
            token_y,
        ),
        arrowprops={
            "arrowstyle": "->",
            "color": "#7c3aed",
            "linewidth": 2,
        },
        zorder=19,
    )

    # Attacker label
    ax.text(
        token_x + 0.20,
        token_y,
        "Attacker",
        fontsize=9,
        fontweight="bold",
        color="#6d28d9",
        verticalalignment="center",
        zorder=22,
    )

    # ------------------------------------------------------
    # GRAPH LABELS
    # ------------------------------------------------------

    ax.text(
        -1.9,
        3.75,
        "ATTACK PATH",
        fontsize=8,
        fontweight="bold",
        color="#64748b",
    )

    ax.text(
        1.05,
        -0.67,
        "PRIMARY TARGET",
        fontsize=8,
        fontweight="bold",
        color="#dc2626",
    )

    ax.set_xlim(
        -2.25,
        2.3,
    )

    ax.set_ylim(
        -1.0,
        4.05,
    )

    ax.set_axis_off()

    ax.set_title(
        "Cyber Attack Surface and Current Game State",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
        pad=18,
    )

    fig.tight_layout()

    return fig


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.markdown(
        "## 🔬 Experiment Controls"
    )

    st.caption(
        "Configure the game experiment and manage strategic resources."
    )

    st.number_input(
        "Random Seed",
        min_value=1,
        max_value=999999,
        value=int(game["seed"]),
        key="seed_value",
        help=(
            "Using the same seed reproduces "
            "the same stochastic sequence."
        ),
    )

    if st.button(
        "🔄 Reset Experiment",
        width="stretch",
    ):
        reset_game()

    st.divider()

    # ------------------------------------------------------
    # BUDGET
    # ------------------------------------------------------

    st.markdown(
        "### 💰 Current Resources"
    )

    st.metric(
        "Defender Budget",
        f"€{game['budgets']['Defender']}",
    )

    st.metric(
        "Attacker Budget",
        f"€{game['budgets']['Attacker']}",
    )

    st.divider()

    # ------------------------------------------------------
    # SHOP
    # ------------------------------------------------------

    st.markdown(
        "### 🛒 Strategic Tools"
    )

    if game["turn"] in [
        "Defender",
        "Attacker",
    ]:

        current_player = game["turn"]

        if current_player == "Defender":
            items = DEFENDER_ITEMS
        else:
            items = ATTACKER_ITEMS

        st.caption(
            f"Current buyer: {current_player}"
        )

        for item_name, item in items.items():

            with st.container(
                border=True
            ):

                st.write(
                    f"**{item_name}**"
                )

                st.caption(
                    item["description"]
                )

                st.write(
                    f"Cost: €{item['cost']}"
                )

                owned = (
                    game["inventory"]
                    [current_player]
                    .get(
                        item_name,
                        0,
                    )
                )

                st.write(
                    f"Owned: {owned}"
                )

                disabled = (
                    game["budgets"][current_player]
                    < item["cost"]
                )

                if st.button(
                    f"Buy {item_name}",
                    key=(
                        f"buy_"
                        f"{current_player}_"
                        f"{item_name}"
                    ),
                    disabled=disabled,
                    width="stretch",
                ):

                    try:
                        buy_item(
                            game,
                            current_player,
                            item_name,
                        )

                        st.rerun()

                    except GameRuleError as error:
                        st.error(
                            str(error)
                        )


# ==========================================================
# HERO HEADER
# ==========================================================

st.markdown("## CYBER SECURITY GAME THEORY LAB")

st.title("🛡️ Cyber Stackelberg Research Game")

st.caption(
     "Defender–attacker simulation for network security, "
     "budget allocation, and sequential game-theoretic decision making."
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.info("🛡️ Defender\n\nLeader")

with col2:
    st.error("⚔️ Attacker\n\nFollower")

with col3:
    st.success("💰 Budget\n\nConstrained")

with col4:
    st.info("🌐 Network\n\nSecurity")

with col5:
    st.success("📊 Experimental\n\nAnalytics")


# ==========================================================
# TURN INDICATOR
# ==========================================================

show_turn_banner()


# ==========================================================
# METRICS
# ==========================================================

attacker_probability, defender_probability = (
    estimate_win_probability(
        game
    )
)

utilities = current_utilities(
    game
)

m1, m2, m3, m4, m5 = st.columns(5)


def metric_card(label, value, caption):

    with st.container(border=True):

        st.caption(label)

        st.markdown(
            f"### {value}"
        )

        st.caption(
            caption
        )


# ==========================================================
# WIN OUTLOOK
# ==========================================================

st.subheader(
    "📈 Game-State Outlook"
)

prob_col1, prob_col2 = (
    st.columns(2)
)


with prob_col1:

    st.write(
        "**Defender Win Estimate**"
    )

    st.progress(
        int(
            defender_probability
            * 100
        )
    )

    st.caption(
        f"{defender_probability:.0%}"
    )


with prob_col2:

    st.write(
        "**Attacker Win Estimate**"
    )

    st.progress(
        int(
            attacker_probability
            * 100
        )
    )

    st.caption(
        f"{attacker_probability:.0%}"
    )


st.caption(
    "The percentages are heuristic game-state indicators "
    "and not a formally solved Strong Stackelberg Equilibrium."
)


# ==========================================================
# TABS
# ==========================================================

board_tab, analytics_tab, log_tab, research_tab = (
    st.tabs(
        [
            "🗺️ Game Board",
            "📊 Analytics",
            "🧾 Experiment Log",
            "🧠 Research Model",
        ]
    )
)


# ==========================================================
# GAME BOARD TAB
# ==========================================================

with board_tab:

    board_column, action_column = (
        st.columns(
            [
                1.9,
                1,
            ],
            gap="large",
        )
    )

    # ------------------------------------------------------
    # BOARD
    # ------------------------------------------------------

    with board_column:

        st.subheader(
            "Network Attack Graph"
        )

        figure = draw_network()

        st.pyplot(
            figure,
            width="stretch",
        )

        plt.close(
            figure
        )

        # --------------------------------------------------
        # LEGEND
        # --------------------------------------------------

        st.markdown(
            """
            <span class="legend-chip">
                🟢 Safe Asset
            </span>

            <span class="legend-chip">
                🟠 Protected
            </span>

            <span class="legend-chip">
                ⚫ Blocked
            </span>

            <span class="legend-chip">
                🔴 Compromised
            </span>

            <span class="legend-chip">
                🔵 Detection Sensor
            </span>

            <span class="legend-chip">
                🟣 A = Attacker Token
            </span>
            """,
            unsafe_allow_html=True,
        )

        # --------------------------------------------------
        # NETWORK STATUS
        # --------------------------------------------------

        with st.container(border=True):

            st.markdown(
                "#### 📡 Live Network State"
            )

            state_col1, state_col2 = st.columns(2)

            with state_col1:
                st.metric(
                    "Attacker Position",
                    game["attacker_position"],
                )

            with state_col2:
                st.metric(
                    "Current Actor",
                    game["turn"],
                )

            st.caption(
                "🟣 Purple connection = currently reachable attack path."
            )

            st.caption(
                "🔴 Red Critical System border = primary target."
            )

        # --------------------------------------------------
        # NODE TABLE
        # --------------------------------------------------

        st.subheader(
            "Node-Level State"
        )

        node_dataframe = pd.DataFrame(
            state_table(
                game
            )
        )

        st.dataframe(
            node_dataframe,
            width="stretch",
            hide_index=True,
        )

    # ======================================================
    # ACTION PANEL
    # ======================================================

    with action_column:

        st.subheader(
            "Decision Console"
        )

        # --------------------------------------------------
        # DEFENDER
        # --------------------------------------------------

        if game["turn"] == "Defender":

            st.markdown(
                "### 🛡️ Defender"
            )

            defender_choice = st.radio(
                "Select defensive action",
                [
                    "Protect",
                    "Block",
                    "Detect",
                ],
            )

            available_targets = (
                defender_targets(
                    game
                )
            )

            if available_targets:

                defender_target = (
                    st.selectbox(
                        "Target asset",
                        available_targets,
                        key="defender_target",
                    )
                )

                defender_cost = (
                    DEFENDER_ACTION_COSTS[
                        defender_choice
                    ]
                )

                st.markdown(
                    f"""
                    <span class="small-badge">
                        Cost €{defender_cost}
                    </span>

                    <span class="small-badge">
                        Defender Action
                    </span>
                    """,
                    unsafe_allow_html=True,
                )

                if defender_choice == "Protect":
                    st.info(
                        "Protect lowers the probability "
                        "of a successful normal attack."
                    )

                elif defender_choice == "Block":
                    st.info(
                        "Block creates stronger temporary "
                        "resistance to Attack and Bypass."
                    )

                else:
                    st.info(
                        "Detect deploys a sensor that may "
                        "identify attacker activity."
                    )

                if st.button(
                    f"Execute {defender_choice}",
                    type="primary",
                    width="stretch",
                    disabled=(
                        game["budgets"]["Defender"]
                        < defender_cost
                    ),
                ):

                    try:
                        defender_action(
                            game,
                            defender_choice,
                            defender_target,
                        )

                        st.rerun()

                    except GameRuleError as error:
                        st.error(
                            str(error)
                        )

            if st.button(
                "Pass Defender Turn",
                width="stretch",
            ):

                try:
                    pass_turn(
                        game
                    )

                    st.rerun()

                except GameRuleError as error:
                    st.error(
                        str(error)
                    )

        # --------------------------------------------------
        # ATTACKER
        # --------------------------------------------------

        elif game["turn"] == "Attacker":

            st.markdown(
                "### ⚔️ Attacker"
            )

            attacker_choice = (
                st.radio(
                    "Select offensive action",
                    [
                        "Scan",
                        "Attack",
                        "Bypass",
                    ],
                )
            )

            available_targets = (
                attacker_targets(
                    game
                )
            )

            if available_targets:

                attacker_target = (
                    st.selectbox(
                        "Reachable asset",
                        available_targets,
                        key="attacker_target",
                    )
                )

                attacker_cost = (
                    ATTACKER_ACTION_COSTS[
                        attacker_choice
                    ]
                )

                st.markdown(
                    f"""
                    <span class="small-badge">
                        Cost €{attacker_cost}
                    </span>

                    <span class="small-badge">
                        Attacker Action
                    </span>
                    """,
                    unsafe_allow_html=True,
                )

                if attacker_choice == "Scan":

                    st.info(
                        "Scan gathers temporary intelligence "
                        "and improves later offensive probability."
                    )

                else:

                    success_chance = (
                        success_probability(
                            game,
                            attacker_choice,
                            attacker_target,
                        )
                    )

                    st.metric(
                        "Calculated Success",
                        f"{success_chance:.0%}",
                    )

                    if attacker_choice == "Attack":
                        st.caption(
                            "Standard offensive attempt "
                            "to compromise the selected asset."
                        )

                    else:
                        st.caption(
                            "A more expensive action that is "
                            "less sensitive to some defences."
                        )

                if st.button(
                    f"Execute {attacker_choice}",
                    type="primary",
                    width="stretch",
                    disabled=(
                        game["budgets"]["Attacker"]
                        < attacker_cost
                    ),
                ):

                    try:
                        attacker_action(
                            game,
                            attacker_choice,
                            attacker_target,
                        )

                        st.rerun()

                    except GameRuleError as error:
                        st.error(
                            str(error)
                        )

            else:
                st.warning(
                    "There are no valid reachable safe nodes "
                    "from the current attacker position."
                )

            if st.button(
                "Pass Attacker Turn",
                width="stretch",
            ):

                try:
                    pass_turn(
                        game
                    )

                    st.rerun()

                except GameRuleError as error:
                    st.error(
                        str(error)
                    )

        # --------------------------------------------------
        # GAME OVER
        # --------------------------------------------------

        else:

            if game["winner"] == "Attacker":
                st.error(
                    "⚔️ Attacker Victory"
                )

            else:
                st.success(
                    "🛡️ Defender Victory"
                )

            st.write(
                game["end_reason"]
            )

        st.divider()

        st.subheader(
            "Current State"
        )

        st.write(
            f"**Round:** "
            f"{game['round']} / {MAX_ROUNDS}"
        )

        st.write(
            f"**Attacker Position:** "
            f"{game['attacker_position']}"
        )

        st.write(
            f"**Defender Utility:** "
            f"{utilities['Defender']:.1f}"
        )

        st.write(
            f"**Attacker Utility:** "
            f"{utilities['Attacker']:.1f}"
        )


# ==========================================================
# ANALYTICS TAB
# ==========================================================

with analytics_tab:

    st.subheader(
        "Experimental Measurements"
    )

    defender_spending = (
        game["initial_budgets"]["Defender"]
        -
        game["budgets"]["Defender"]
    )

    attacker_spending = (
        game["initial_budgets"]["Attacker"]
        -
        game["budgets"]["Attacker"]
    )

    compromised_count = sum(
        1
        for status
        in game["status"].values()
        if status == "Compromised"
    )

    a1, a2, a3, a4 = (
        st.columns(4)
    )

    with a1:
        metric_card(
            "DEFENDER SPEND",
            f"€{defender_spending}",
            "Accumulated resource usage",
        )

    with a2:
        metric_card(
            "ATTACKER SPEND",
            f"€{attacker_spending}",
            "Accumulated resource usage",
        )

    with a3:
        metric_card(
            "COMPROMISED NODES",
            compromised_count,
            "Current network impact",
        )

    with a4:
        metric_card(
            "DETECTIONS",
            game["detections"],
            "Successful detection events",
        )

    history_dataframe = pd.DataFrame(
        game["history"]
    )

    if not history_dataframe.empty:

        st.subheader(
            "Experiment Dataset"
        )

        st.dataframe(
            history_dataframe,
            width="stretch",
            hide_index=True,
        )

        st.download_button(
            "⬇ Download Experiment CSV",
            data=(
                history_dataframe
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8"
                )
            ),
            file_name=(
                f"cyber_stackelberg_"
                f"seed_{game['seed']}.csv"
            ),
            mime="text/csv",
            width="stretch",
        )

        # --------------------------------------------------
        # BUDGET CHART
        # --------------------------------------------------

        st.subheader(
            "Budget Trajectory"
        )

        budget_data = (
            history_dataframe[
                [
                    "defender_budget",
                    "attacker_budget",
                ]
            ]
        )

        st.line_chart(
            budget_data
        )

        # --------------------------------------------------
        # WIN ESTIMATE CHART
        # --------------------------------------------------

        st.subheader(
            "Win Estimate Trend"
        )

        probability_data = (
            history_dataframe[
                [
                    "defender_win_estimate",
                    "attacker_win_estimate",
                ]
            ]
        )

        st.line_chart(
            probability_data
        )

        # --------------------------------------------------
        # UTILITY CHART
        # --------------------------------------------------

        st.subheader(
            "Utility Trend"
        )

        utility_data = (
            history_dataframe[
                [
                    "defender_utility",
                    "attacker_utility",
                ]
            ]
        )

        st.line_chart(
            utility_data
        )

    else:
        st.info(
            "Play at least one action "
            "to generate experimental analytics."
        )


# ==========================================================
# EVENT LOG
# ==========================================================

with log_tab:

    st.subheader(
        "Sequential Event Log"
    )

    st.caption(
        "Latest event appears first."
    )

    for event in reversed(
        game["log"]
    ):

        st.write(
            f"• {event}"
        )


# ==========================================================
# RESEARCH MODEL
# ==========================================================

with research_tab:

    st.subheader(
        "Game-Theoretic Structure"
    )

    st.markdown(
        """
### Leader-Follower Model

The game follows a simplified Stackelberg-style sequence:

1. **Defender acts first**
2. The defensive state becomes observable
3. **Attacker responds**
4. The network state is updated
5. A new round begins


### Defender Actions

**Protect**

Reduces the success probability of a normal attack.

**Block**

Introduces stronger temporary resistance to offensive progression.

**Detect**

Deploys a monitoring sensor that may detect attacker activity.


### Attacker Actions

**Scan**

Collects temporary intelligence about the next target.

**Attack**

Attempts to compromise the next connected asset.

**Bypass**

Uses more resources but is less sensitive to some defensive controls.


### Network Progression

The offensive path is:

`Entry`

↓

`Workstation`

↙  ↘

`Server`  `Database`

↘  ↙

`Critical System`


### Resource Model

Both players operate with limited budgets.

Each action therefore creates an economic trade-off between:

- immediate tactical advantage
- future resource availability
- protection of high-value nodes
- offensive progression
- tool purchases


### Utility

The prototype calculates Defender and Attacker utilities based on:

- asset state
- resource expenditure
- compromised value
- detection events


### Model Limitation

The displayed win percentage is a heuristic game-state indicator.

The current prototype does not compute a formal
**Strong Stackelberg Equilibrium (SSE)**.

Future research extensions could include:

- explicit payoff matrices
- mixed defender strategies
- attacker best-response calculation
- Monte Carlo experiments
- policy comparison
- formal Stackelberg equilibrium optimisation
"""
    )