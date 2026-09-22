import math
import random
from collections import deque


# ----------------------------------------------------
# NETWORK
# ----------------------------------------------------

NODES = [
    "Entry",
    "Workstation",
    "Server",
    "Database",
    "Critical System",
]


EDGES = [
    (
        "Entry",
        "Workstation",
    ),
    (
        "Workstation",
        "Server",
    ),
    (
        "Workstation",
        "Database",
    ),
    (
        "Server",
        "Critical System",
    ),
    (
        "Database",
        "Critical System",
    ),
]


# ----------------------------------------------------
# ASSET VALUES
# ----------------------------------------------------

NODE_VALUES = {
    "Entry": 5,
    "Workstation": 20,
    "Server": 45,
    "Database": 55,
    "Critical System": 100,
}


# Higher number = harder target
NODE_DIFFICULTY = {
    "Entry": 0.05,
    "Workstation": 0.12,
    "Server": 0.22,
    "Database": 0.27,
    "Critical System": 0.34,
}


# ----------------------------------------------------
# ACTION COSTS
# ----------------------------------------------------

DEFENDER_ACTION_COSTS = {
    "Protect": 12,
    "Block": 16,
    "Detect": 9,
}


ATTACKER_ACTION_COSTS = {
    "Scan": 6,
    "Attack": 14,
    "Bypass": 20,
}


# ----------------------------------------------------
# SHOP ITEMS
# ----------------------------------------------------

DEFENDER_ITEMS = {

    "Hardening Tool": {
        "cost": 24,
        "description": (
            "Makes the next Protect "
            "action stronger."
        ),
    },

    "Detection Coupon": {
        "cost": 18,
        "description": (
            "Improves the next "
            "Detect action."
        ),
    },

    "Emergency Block Token": {
        "cost": 22,
        "description": (
            "Makes the next Block "
            "action stronger."
        ),
    },
}


ATTACKER_ITEMS = {

    "Recon Tool": {
        "cost": 18,
        "description": (
            "Makes the next Scan "
            "action stronger."
        ),
    },

    "Exploit Token": {
        "cost": 25,
        "description": (
            "Improves the next "
            "Attack probability."
        ),
    },

    "Bypass Coupon": {
        "cost": 24,
        "description": (
            "Improves the next "
            "Bypass probability."
        ),
    },
}


# ----------------------------------------------------
# BASIC GAME SETTINGS
# ----------------------------------------------------

MAX_ROUNDS = 8


INITIAL_BUDGETS = {
    "Defender": 125,
    "Attacker": 110,
}


class GameRuleError(
    ValueError
):
    pass


# ----------------------------------------------------
# NETWORK ADJACENCY
# ----------------------------------------------------

def create_adjacency():

    adjacency = {
        node: []
        for node in NODES
    }

    for (
        node_a,
        node_b,
    ) in EDGES:

        adjacency[
            node_a
        ].append(
            node_b
        )

        adjacency[
            node_b
        ].append(
            node_a
        )

    return adjacency


ADJACENCY = (
    create_adjacency()
)


# ----------------------------------------------------
# NEW GAME
# ----------------------------------------------------

def new_game(
    seed=42,
):

    state = {

        "seed":
            int(seed),

        "rng_counter":
            0,

        "round":
            1,

        "turn":
            "Defender",

        "winner":
            None,

        "end_reason":
            "",

        "status": {
            node: "Safe"
            for node in NODES
        },

        "attacker_position":
            "Entry",

        "protected_until":
            {},

        "protection_strength":
            {},

        "blocked_until":
            {},

        "block_strength":
            {},

        "sensors_until":
            {},

        "sensor_strength":
            {},

        "intel_until":
            {},

        "intel_bonus":
            {},

        "detected_penalty_until":
            0,

        "detections":
            0,

        "budgets":
            dict(
                INITIAL_BUDGETS
            ),

        "initial_budgets":
            dict(
                INITIAL_BUDGETS
            ),

        "inventory": {

            "Defender": {
                name: 0
                for name
                in DEFENDER_ITEMS
            },

            "Attacker": {
                name: 0
                for name
                in ATTACKER_ITEMS
            },
        },

        "log": [
            (
                "Game started. "
                "Attacker begins at Entry. "
                "Defender acts first."
            )
        ],

        "history":
            [],
    }

    # Attacker already has an initial foothold
    state["status"][
        "Entry"
    ] = "Compromised"

    return state


# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def is_active(
    mapping,
    node,
    round_number,
):

    return (
        int(
            mapping.get(
                node,
                0,
            )
        )
        >= round_number
    )


def ensure_turn(
    state,
    player,
):

    if (
        state["turn"]
        != player
    ):

        raise GameRuleError(
            f"It is currently "
            f"{state['turn']}'s turn."
        )


def spend(
    state,
    player,
    cost,
):

    if (
        state["budgets"][
            player
        ]
        < cost
    ):

        raise GameRuleError(
            f"{player} does not "
            f"have enough money."
        )

    state["budgets"][
        player
    ] -= cost


def random_roll(
    state,
):

    generator = (
        random.Random(
            state["seed"]
            +
            state["rng_counter"]
            * 1009
        )
    )

    state[
        "rng_counter"
    ] += 1

    return (
        generator.random()
    )


# ----------------------------------------------------
# ACTIVE DEFENCES
# ----------------------------------------------------

def active_defences(
    state,
    node,
):

    result = []

    if is_active(
        state[
            "protected_until"
        ],
        node,
        state["round"],
    ):

        result.append(
            "Protected"
        )

    if is_active(
        state[
            "blocked_until"
        ],
        node,
        state["round"],
    ):

        result.append(
            "Blocked"
        )

    if is_active(
        state[
            "sensors_until"
        ],
        node,
        state["round"],
    ):

        result.append(
            "Sensor"
        )

    return result


# ----------------------------------------------------
# VALID TARGETS
# ----------------------------------------------------

def defender_targets(
    state,
):

    return [

        node

        for node
        in NODES

        if (
            state["status"][node]
            != "Compromised"
        )
    ]


def attacker_targets(
    state,
):

    current_position = (
        state[
            "attacker_position"
        ]
    )

    return [

        node

        for node
        in ADJACENCY[
            current_position
        ]

        if (
            state["status"][node]
            != "Compromised"
        )
    ]


# ----------------------------------------------------
# BUY SHOP ITEM
# ----------------------------------------------------

def buy_item(
    state,
    player,
    item_name,
):

    if (
        state["turn"]
        != player
    ):

        raise GameRuleError(
            "Only the player whose "
            "turn is active may buy."
        )

    if (
        player
        == "Defender"
    ):

        catalogue = (
            DEFENDER_ITEMS
        )

    else:

        catalogue = (
            ATTACKER_ITEMS
        )

    if (
        item_name
        not in catalogue
    ):

        raise GameRuleError(
            "Unknown item."
        )

    item = catalogue[
        item_name
    ]

    spend(
        state,
        player,
        item["cost"],
    )

    state["inventory"][
        player
    ][
        item_name
    ] += 1

    state["log"].append(
        f"{player} bought "
        f"{item_name} "
        f"for €{item['cost']}."
    )

    record_history(
        state,
        player,
        f"Buy {item_name}",
        "-",
        item["cost"],
        "Purchased",
    )


# ----------------------------------------------------
# DEFENDER ACTION
# ----------------------------------------------------

def defender_action(
    state,
    action,
    target,
):

    ensure_turn(
        state,
        "Defender",
    )

    if (
        action
        not in
        DEFENDER_ACTION_COSTS
    ):

        raise GameRuleError(
            "Unknown Defender action."
        )

    if (
        target
        not in
        defender_targets(
            state
        )
    ):

        raise GameRuleError(
            "Invalid Defender target."
        )

    cost = (
        DEFENDER_ACTION_COSTS[
            action
        ]
    )

    spend(
        state,
        "Defender",
        cost,
    )


    # --------------------------------
    # PROTECT
    # --------------------------------

    if action == "Protect":

        strength = 0.25

        duration = (
            state["round"]
        )

        if (
            state["inventory"]
            ["Defender"]
            ["Hardening Tool"]
            > 0
        ):

            state["inventory"][
                "Defender"
            ][
                "Hardening Tool"
            ] -= 1

            strength = 0.38

            duration = (
                state["round"]
                + 1
            )

        state[
            "protected_until"
        ][
            target
        ] = duration

        state[
            "protection_strength"
        ][
            target
        ] = strength

        result = (
            f"Protection "
            f"{strength:.0%}"
        )


    # --------------------------------
    # BLOCK
    # --------------------------------

    elif action == "Block":

        strength = 0.42

        if (
            state["inventory"]
            ["Defender"]
            ["Emergency Block Token"]
            > 0
        ):

            state["inventory"][
                "Defender"
            ][
                "Emergency Block Token"
            ] -= 1

            strength = 0.58

        state[
            "blocked_until"
        ][
            target
        ] = (
            state["round"]
        )

        state[
            "block_strength"
        ][
            target
        ] = strength

        result = (
            f"Block "
            f"{strength:.0%}"
        )


    # --------------------------------
    # DETECT
    # --------------------------------

    elif action == "Detect":

        strength = 0.40

        if (
            state["inventory"]
            ["Defender"]
            ["Detection Coupon"]
            > 0
        ):

            state["inventory"][
                "Defender"
            ][
                "Detection Coupon"
            ] -= 1

            strength = 0.67

        state[
            "sensors_until"
        ][
            target
        ] = (
            state["round"]
            + 1
        )

        state[
            "sensor_strength"
        ][
            target
        ] = strength

        result = (
            f"Detection "
            f"{strength:.0%}"
        )


    state["log"].append(
        f"Defender used "
        f"{action} on "
        f"{target}. "
        f"Cost €{cost}."
    )

    record_history(
        state,
        "Defender",
        action,
        target,
        cost,
        result,
    )

    state[
        "turn"
    ] = "Attacker"


# ----------------------------------------------------
# DETECTION
# ----------------------------------------------------

def resolve_detection(
    state,
    target,
):

    if not is_active(
        state[
            "sensors_until"
        ],
        target,
        state["round"],
    ):

        return False

    chance = float(
        state[
            "sensor_strength"
        ].get(
            target,
            0.40,
        )
    )

    detected = (
        random_roll(
            state
        )
        < chance
    )

    if detected:

        state[
            "detections"
        ] += 1

        state[
            "detected_penalty_until"
        ] = (
            state["round"]
            + 1
        )

        state["log"].append(
            f"Defender detected "
            f"attacker activity "
            f"at {target}."
        )

    else:

        state["log"].append(
            f"Sensor at "
            f"{target} did not "
            f"detect the attacker."
        )

    return detected


# ----------------------------------------------------
# ATTACK SUCCESS PROBABILITY
# ----------------------------------------------------

def success_probability(
    state,
    action,
    target,
):

    if (
        action
        not in [
            "Attack",
            "Bypass",
        ]
    ):

        return 1.0


    if (
        target
        not in
        ADJACENCY[
            state[
                "attacker_position"
            ]
        ]
    ):

        return 0.0


    # --------------------------------
    # NORMAL ATTACK
    # --------------------------------

    if action == "Attack":

        chance = (
            0.80
            -
            NODE_DIFFICULTY[
                target
            ]
        )

        if is_active(
            state[
                "protected_until"
            ],
            target,
            state["round"],
        ):

            chance -= (
                state[
                    "protection_strength"
                ].get(
                    target,
                    0.25,
                )
            )

        if is_active(
            state[
                "blocked_until"
            ],
            target,
            state["round"],
        ):

            chance -= (
                state[
                    "block_strength"
                ].get(
                    target,
                    0.42,
                )
            )


    # --------------------------------
    # BYPASS
    # --------------------------------

    else:

        chance = (
            0.66
            -
            (
                NODE_DIFFICULTY[
                    target
                ]
                * 0.75
            )
        )

        if is_active(
            state[
                "protected_until"
            ],
            target,
            state["round"],
        ):

            chance -= (
                state[
                    "protection_strength"
                ].get(
                    target,
                    0.25,
                )
                * 0.35
            )

        if is_active(
            state[
                "blocked_until"
            ],
            target,
            state["round"],
        ):

            chance -= (
                state[
                    "block_strength"
                ].get(
                    target,
                    0.42,
                )
                * 0.50
            )


    # --------------------------------
    # SCAN BONUS
    # --------------------------------

    if is_active(
        state[
            "intel_until"
        ],
        target,
        state["round"],
    ):

        chance += (
            state[
                "intel_bonus"
            ].get(
                target,
                0.16,
            )
        )


    # --------------------------------
    # DETECTION PENALTY
    # --------------------------------

    if (
        state[
            "detected_penalty_until"
        ]
        >= state["round"]
    ):

        chance -= 0.12


    # --------------------------------
    # SHOP ITEMS
    # --------------------------------

    if (
        action == "Attack"
        and
        state["inventory"]
        ["Attacker"]
        ["Exploit Token"]
        > 0
    ):

        chance += 0.15


    if (
        action == "Bypass"
        and
        state["inventory"]
        ["Attacker"]
        ["Bypass Coupon"]
        > 0
    ):

        chance += 0.20


    return max(
        0.05,
        min(
            0.95,
            chance,
        ),
    )


# ----------------------------------------------------
# ATTACKER ACTION
# ----------------------------------------------------

def attacker_action(
    state,
    action,
    target,
):

    ensure_turn(
        state,
        "Attacker",
    )

    if (
        action
        not in
        ATTACKER_ACTION_COSTS
    ):

        raise GameRuleError(
            "Unknown Attacker action."
        )

    if (
        target
        not in
        attacker_targets(
            state
        )
    ):

        raise GameRuleError(
            "The attacker can only "
            "target a connected safe node."
        )


    cost = (
        ATTACKER_ACTION_COSTS[
            action
        ]
    )

    spend(
        state,
        "Attacker",
        cost,
    )


    # --------------------------------
    # SCAN
    # --------------------------------

    if action == "Scan":

        bonus = 0.16

        duration = (
            state["round"]
            + 1
        )

        if (
            state["inventory"]
            ["Attacker"]
            ["Recon Tool"]
            > 0
        ):

            state["inventory"][
                "Attacker"
            ][
                "Recon Tool"
            ] -= 1

            bonus = 0.25

            duration = (
                state["round"]
                + 3
            )

        state[
            "intel_until"
        ][
            target
        ] = duration

        state[
            "intel_bonus"
        ][
            target
        ] = bonus

        resolve_detection(
            state,
            target,
        )

        state["log"].append(
            f"Attacker scanned "
            f"{target}. "
            f"Cost €{cost}."
        )

        record_history(
            state,
            "Attacker",
            "Scan",
            target,
            cost,
            f"Intel +{bonus:.0%}",
        )

        finish_attacker_turn(
            state
        )

        return


    # --------------------------------
    # ATTACK / BYPASS
    # --------------------------------

    probability = (
        success_probability(
            state,
            action,
            target,
        )
    )


    # Consume attacker items
    if (
        action == "Attack"
        and
        state["inventory"]
        ["Attacker"]
        ["Exploit Token"]
        > 0
    ):

        state["inventory"][
            "Attacker"
        ][
            "Exploit Token"
        ] -= 1


    if (
        action == "Bypass"
        and
        state["inventory"]
        ["Attacker"]
        ["Bypass Coupon"]
        > 0
    ):

        state["inventory"][
            "Attacker"
        ][
            "Bypass Coupon"
        ] -= 1


    success = (
        random_roll(
            state
        )
        < probability
    )


    resolve_detection(
        state,
        target,
    )


    if success:

        state["status"][
            target
        ] = "Compromised"

        state[
            "attacker_position"
        ] = target

        result = (
            f"Success "
            f"({probability:.0%})"
        )

        state["log"].append(
            f"Attacker used "
            f"{action} on "
            f"{target} and "
            f"succeeded."
        )

    else:

        result = (
            f"Failed "
            f"({probability:.0%})"
        )

        state["log"].append(
            f"Attacker used "
            f"{action} on "
            f"{target} and failed."
        )


    record_history(
        state,
        "Attacker",
        action,
        target,
        cost,
        result,
    )


    # Critical system compromised
    if (
        success
        and
        target
        == "Critical System"
    ):

        state[
            "winner"
        ] = "Attacker"

        state[
            "end_reason"
        ] = (
            "The Critical System "
            "was compromised."
        )

        state[
            "turn"
        ] = "Game Over"

        return


    finish_attacker_turn(
        state
    )


# ----------------------------------------------------
# PASS
# ----------------------------------------------------

def pass_turn(
    state,
):

    if (
        state["turn"]
        == "Defender"
    ):

        state["log"].append(
            "Defender passed."
        )

        record_history(
            state,
            "Defender",
            "Pass",
            "-",
            0,
            "No spending",
        )

        state[
            "turn"
        ] = "Attacker"


    elif (
        state["turn"]
        == "Attacker"
    ):

        state["log"].append(
            "Attacker passed."
        )

        record_history(
            state,
            "Attacker",
            "Pass",
            "-",
            0,
            "No spending",
        )

        finish_attacker_turn(
            state
        )


    else:

        raise GameRuleError(
            "Game is already over."
        )


# ----------------------------------------------------
# END ATTACKER TURN
# ----------------------------------------------------

def finish_attacker_turn(
    state,
):

    # Round limit
    if (
        state["round"]
        >= MAX_ROUNDS
    ):

        state[
            "winner"
        ] = "Defender"

        state[
            "end_reason"
        ] = (
            "The Critical System "
            "remained safe until "
            "the round limit."
        )

        state[
            "turn"
        ] = "Game Over"

        return


    # Attacker ran out of usable budget
    cheapest_action = min(
        ATTACKER_ACTION_COSTS.values()
    )

    if (
        state["budgets"]
        ["Attacker"]
        < cheapest_action
    ):

        state[
            "winner"
        ] = "Defender"

        state[
            "end_reason"
        ] = (
            "The Attacker no longer "
            "has enough money for "
            "another action."
        )

        state[
            "turn"
        ] = "Game Over"

        return


    state[
        "round"
    ] += 1

    state[
        "turn"
    ] = "Defender"


# ----------------------------------------------------
# DISTANCE TO CRITICAL SYSTEM
# ----------------------------------------------------

def shortest_distance(
    start,
    goal,
):

    queue = deque(
        [
            (
                start,
                0,
            )
        ]
    )

    visited = {
        start
    }

    while queue:

        (
            node,
            distance,
        ) = queue.popleft()

        if (
            node
            == goal
        ):

            return distance


        for neighbour in (
            ADJACENCY[
                node
            ]
        ):

            if (
                neighbour
                not in visited
            ):

                visited.add(
                    neighbour
                )

                queue.append(
                    (
                        neighbour,
                        distance + 1,
                    )
                )

    return 99


# ----------------------------------------------------
# WIN PROBABILITY ESTIMATE
# ----------------------------------------------------

def estimate_win_probability(
    state,
):

    if (
        state["winner"]
        == "Attacker"
    ):

        return (
            1.0,
            0.0,
        )


    if (
        state["winner"]
        == "Defender"
    ):

        return (
            0.0,
            1.0,
        )


    initial_distance = (
        shortest_distance(
            "Entry",
            "Critical System",
        )
    )

    current_distance = (
        shortest_distance(
            state[
                "attacker_position"
            ],
            "Critical System",
        )
    )


    progress = (
        1.0
        -
        (
            current_distance
            /
            initial_distance
        )
    )


    scored_nodes = [

        node

        for node
        in NODES

        if (
            node
            != "Entry"
        )
    ]


    total_value = sum(
        NODE_VALUES[node]
        for node
        in scored_nodes
    )


    compromised_value = sum(

        NODE_VALUES[node]

        for node
        in scored_nodes

        if (
            state["status"][node]
            == "Compromised"
        )
    )


    compromise_ratio = (
        compromised_value
        /
        total_value
    )


    total_remaining_money = (
        state["budgets"][
            "Attacker"
        ]
        +
        state["budgets"][
            "Defender"
        ]
    )


    attacker_money_share = (
        state["budgets"][
            "Attacker"
        ]
        /
        max(
            1,
            total_remaining_money,
        )
    )


    critical_defence = 0.0


    if (
        "Protected"
        in active_defences(
            state,
            "Critical System",
        )
    ):

        critical_defence += 0.7


    if (
        "Blocked"
        in active_defences(
            state,
            "Critical System",
        )
    ):

        critical_defence += 0.9


    if (
        "Sensor"
        in active_defences(
            state,
            "Critical System",
        )
    ):

        critical_defence += 0.3


    round_pressure = (
        state["round"]
        - 1
    ) / max(
        1,
        MAX_ROUNDS - 1,
    )


    score = (

        -0.8

        + 2.2
        * progress

        + 1.2
        * compromise_ratio

        + 0.8
        * (
            attacker_money_share
            - 0.5
        )

        - 0.8
        * critical_defence

        - 1.1
        * round_pressure
    )


    attacker_probability = (
        1.0
        /
        (
            1.0
            +
            math.exp(
                -score
            )
        )
    )


    attacker_probability = max(
        0.03,
        min(
            0.97,
            attacker_probability,
        ),
    )


    defender_probability = (
        1.0
        -
        attacker_probability
    )


    return (
        attacker_probability,
        defender_probability,
    )


# ----------------------------------------------------
# UTILITY CALCULATION
# ----------------------------------------------------

def current_utilities(
    state,
):

    scored_nodes = [

        node

        for node
        in NODES

        if (
            node
            != "Entry"
        )
    ]


    compromised_value = sum(

        NODE_VALUES[node]

        for node
        in scored_nodes

        if (
            state["status"][node]
            == "Compromised"
        )
    )


    safe_value = sum(

        NODE_VALUES[node]

        for node
        in scored_nodes

        if (
            state["status"][node]
            != "Compromised"
        )
    )


    defender_spending = (
        state[
            "initial_budgets"
        ][
            "Defender"
        ]
        -
        state[
            "budgets"
        ][
            "Defender"
        ]
    )


    attacker_spending = (
        state[
            "initial_budgets"
        ][
            "Attacker"
        ]
        -
        state[
            "budgets"
        ][
            "Attacker"
        ]
    )


    defender_utility = (

        safe_value

        -
        0.55
        * defender_spending

        +
        4
        * state[
            "detections"
        ]
    )


    attacker_utility = (

        compromised_value

        -
        0.55
        * attacker_spending

        -
        3
        * state[
            "detections"
        ]
    )


    return {

        "Defender":
            defender_utility,

        "Attacker":
            attacker_utility,
    }


# ----------------------------------------------------
# NODE TABLE
# ----------------------------------------------------

def state_table(
    state,
):

    rows = []


    for node in NODES:

        defences = (
            active_defences(
                state,
                node,
            )
        )


        scanned = is_active(
            state[
                "intel_until"
            ],
            node,
            state["round"],
        )


        attacker_here = (
            state[
                "attacker_position"
            ]
            == node
        )


        rows.append(
            {

                "Node":
                    node,

                "Asset Value":
                    f"€{NODE_VALUES[node]}",

                "Status":
                    state[
                        "status"
                    ][
                        node
                    ],

                "Defence":
                    (
                        ", ".join(
                            defences
                        )
                        if defences
                        else "None"
                    ),

                "Scanned":
                    (
                        "Yes"
                        if scanned
                        else "No"
                    ),

                "Attacker Here":
                    (
                        "●"
                        if attacker_here
                        else ""
                    ),
            }
        )


    return rows


# ----------------------------------------------------
# RESEARCH HISTORY
# ----------------------------------------------------

def record_history(
    state,
    actor,
    action,
    target,
    cost,
    result,
):

    attacker_probability, defender_probability = (
        estimate_win_probability(
            state
        )
    )


    utilities = (
        current_utilities(
            state
        )
    )


    state[
        "history"
    ].append(
        {

            "round":
                state["round"],

            "actor":
                actor,

            "action":
                action,

            "target":
                target,

            "cost":
                cost,

            "result":
                result,

            "attacker_position":
                state[
                    "attacker_position"
                ],

            "defender_budget":
                state[
                    "budgets"
                ][
                    "Defender"
                ],

            "attacker_budget":
                state[
                    "budgets"
                ][
                    "Attacker"
                ],

            "attacker_win_estimate":
                round(
                    attacker_probability,
                    4,
                ),

            "defender_win_estimate":
                round(
                    defender_probability,
                    4,
                ),

            "defender_utility":
                round(
                    utilities[
                        "Defender"
                    ],
                    2,
                ),

            "attacker_utility":
                round(
                    utilities[
                        "Attacker"
                    ],
                    2,
                ),
        }
    )