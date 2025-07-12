from market_sim.agents import ConsensusAgent


def simulate_consensus():
    num_agents = 6  # Smaller for clearer output
    f = 2
    byzantine_nodes = [0, 2]  # Make sender Byzantine to see the effect

    print(f"  Setting up {num_agents} agents with f={f}")
    print(f"️  Byzantine nodes: {byzantine_nodes}")

    agents = [
        ConsensusAgent(i, num_agents, f=f, is_byzantine=(i in byzantine_nodes))
        for i in range(num_agents)
    ]

    proposed_value = "buy"
    print(f"\n Dolev-Strong consensus simulation starting...")
    print(f" Proposed value: '{proposed_value}'")
    print("=" * 60)

    # Run consensus for each agent (they all participate in the same consensus)
    # We only need to run it once since they're all in the same protocol instance
    agents[0].run_consensus(agents, proposed_value)

    print(f"\n FINAL RESULTS:")
    print("=" * 50)

    honest_decisions = []
    byzantine_decisions = []

    for i, agent in enumerate(agents):
        decision = agent.node.decide()
        extracted = agent.node.extracted
        label = " Byzantine" if i in byzantine_nodes else "✅ Honest"
        print(f"Agent {i:2d} ({label:12s}) decided: {decision:<8} | Extracted: {extracted}")

        if i in byzantine_nodes:
            byzantine_decisions.append(decision)
        else:
            honest_decisions.append(decision)

    # Analysis
    unique_honest = set(honest_decisions)
    unique_byzantine = set(byzantine_decisions)

    print(f"\n Analysis:")
    print(f"   Honest decisions: {honest_decisions} → {unique_honest}")
    print(f"   Byzantine decisions: {byzantine_decisions} → {unique_byzantine}")

    if len(unique_honest) == 1:
        print(" SUCCESS: All honest nodes agreed!")
        print(f" Consensus value: {list(unique_honest)[0]}")
    else:
        print(" FAILURE: Honest nodes disagreed!")
        print(" This might indicate Byzantine nodes successfully disrupted consensus")


def test_different_scenarios():
    """Test multiple scenarios to see different outcomes"""

    scenarios = [
        {
            "name": "Honest Sender",
            "num_agents": 5,
            "f": 1,
            "byzantine_nodes": [2],
            "proposed_value": "buy"
        },
        {
            "name": "Byzantine Sender",
            "num_agents": 5,
            "f": 1,
            "byzantine_nodes": [0],  # Sender is Byzantine
            "proposed_value": "buy"
        },
        {
            "name": "Multiple Byzantine",
            "num_agents": 7,
            "f": 2,
            "byzantine_nodes": [1, 3],
            "proposed_value": "sell"
        }
    ]

    for i, scenario in enumerate(scenarios):
        print(f"\n{'=' * 80}")
        print(f" SCENARIO {i + 1}: {scenario['name']}")
        print(f"   Agents: {scenario['num_agents']}, f: {scenario['f']}")
        print(f"   Byzantine: {scenario['byzantine_nodes']}")
        print(f"   Proposed: {scenario['proposed_value']}")
        print('=' * 80)

        agents = [
            ConsensusAgent(j, scenario['num_agents'], f=scenario['f'],
                           is_byzantine=(j in scenario['byzantine_nodes']))
            for j in range(scenario['num_agents'])
        ]

        # Run consensus
        agents[0].run_consensus(agents, scenario['proposed_value'])

        # Show results
        print(f"\n Results for {scenario['name']}:")
        honest_decisions = []
        for j, agent in enumerate(agents):
            decision = agent.node.decide()
            extracted = agent.node.extracted
            label = " Byzantine" if j in scenario['byzantine_nodes'] else "✅ Honest"
            print(f"  Agent {j} ({label:12s}): {decision:<8} | Extracted: {extracted}")

            if j not in scenario['byzantine_nodes']:
                honest_decisions.append(decision)

        unique_honest = set(honest_decisions)
        if len(unique_honest) == 1:
            print(f"   Honest consensus: {list(unique_honest)[0]}")
        else:
            print(f"   No consensus: {unique_honest}")


if __name__ == "__main__":
    print("Choose simulation:")
    print("1. Single scenario")
    print("2. Multiple scenarios")

    choice = input("Enter choice (1-2): ").strip()

    if choice == "2":
        test_different_scenarios()
    else:
        simulate_consensus()
