from market_sim.consensus import Node
import random


class ConsensusAgent:
    def __init__(self, node_id, total_agents, f=1, is_byzantine=False):
        self.node = Node(node_id, f, is_byzantine)
        self.total_agents = total_agents
        self.id = node_id
        self.final_decision = None
        self.final_extracted = set()

    def propose(self, value):
        if self.node.is_byzantine:
            # Byzantine sender sends DIFFERENT values to different nodes
            fake_values = ["sell", "hold", "attack", "corrupt"]
            fake_value = random.choice(fake_values)
            print(f"  Byzantine sender {self.id} proposing: {fake_value} instead of {value}")
            return self.node.sign(fake_value)
        return self.node.sign(value)

    def run_consensus(self, all_agents, proposed_value):
        # Reset extracted sets for new consensus
        for agent in all_agents:
            agent.node.extracted = set()

        print(f" Starting consensus with proposed value: {proposed_value}")
        print(f"️  Byzantine agents: {[a.id for a in all_agents if a.node.is_byzantine]}")

        # Round 0: Sender (node 0) sends initial value
        round_0_messages = []
        sender = all_agents[0]  # Node 0 is sender

        if sender.node.is_byzantine:
            # Byzantine sender sends different values to different nodes
            print(f" ROUND 0: Byzantine sender {sender.id} sending different values")
            for i, agent in enumerate(all_agents):
                if agent.id != 0:  # Don't send to self
                    fake_values = ["sell", "hold", "attack", f"fake_{i}"]
                    fake_value = random.choice(fake_values)
                    fake_msg = sender.node.sign(fake_value)
                    round_0_messages.append((agent.id, fake_msg))
                    print(f"  → Sending '{fake_value}' to node {agent.id}")
        else:
            # Honest sender sends same value to all
            print(f" ROUND 0: Honest sender {sender.id} broadcasting '{proposed_value}'")
            honest_msg = sender.propose(proposed_value)
            for agent in all_agents:
                if agent.id != 0:  # Don't send to self
                    round_0_messages.append((agent.id, honest_msg))

        # Deliver round 0 messages
        current_messages = {}
        for agent_id, msg in round_0_messages:
            if agent_id not in current_messages:
                current_messages[agent_id] = []
            current_messages[agent_id].append(msg)

        # Process round 0 messages
        for agent in all_agents:
            if agent.id != 0 and agent.id in current_messages:
                agent.node.receive(current_messages[agent.id])
                print(f"  Node {agent.id} extracted: {agent.node.extracted}")

        # Rounds 1 to f+1
        for round_num in range(1, self.node.f + 2):
            print(f"\n ROUND {round_num}:")
            next_round_messages = {}

            # Each agent processes messages and generates new ones
            for agent in all_agents:
                if agent.id in current_messages:
                    new_msgs = agent.node.receive(current_messages[agent.id])

                    # Byzantine agents might corrupt messages they relay
                    if agent.node.is_byzantine and new_msgs:
                        print(f"  Byzantine node {agent.id} corrupting {len(new_msgs)} messages")
                        corrupted_msgs = []
                        for msg in new_msgs:
                            if random.random() < 0.5:  # 50% chance to corrupt
                                parts = msg.split('|')
                                if len(parts) >= 2:
                                    corrupt_values = ["fake", "noise", "byzantine", "evil"]
                                    corrupted_msg = f"{random.choice(corrupt_values)}|" + '|'.join(parts[1:])
                                    corrupted_msgs.append(corrupted_msg)
                                    print(f"    Corrupted: {msg} → {corrupted_msg}")
                                else:
                                    corrupted_msgs.append(msg)
                            else:
                                corrupted_msgs.append(msg)
                        new_msgs = corrupted_msgs

                    # Distribute to all other agents
                    for other_agent in all_agents:
                        if other_agent.id != agent.id:
                            if other_agent.id not in next_round_messages:
                                next_round_messages[other_agent.id] = []
                            next_round_messages[other_agent.id].extend(new_msgs)

            # Byzantine agents might inject additional malicious messages
            for agent in all_agents:
                if agent.node.is_byzantine and random.random() < 0.5:  # Increased probability
                    malicious_values = ["sell", "panic", "crash", "exploit"]
                    malicious_value = random.choice(malicious_values)
                    # Create fake message with fake signature chain
                    fake_signatures = [0, agent.id]  # Pretend sender signed it
                    malicious_msg = f"{malicious_value}|" + '|'.join(map(str, fake_signatures))

                    print(f"  Byzantine node {agent.id} injecting malicious message: {malicious_msg}")

                    # Send to all other agents
                    for other_agent in all_agents:
                        if other_agent.id != agent.id:
                            if other_agent.id not in next_round_messages:
                                next_round_messages[other_agent.id] = []
                            next_round_messages[other_agent.id].append(malicious_msg)

            current_messages = next_round_messages

            # Show what each node extracted this round
            for agent in all_agents:
                if agent.id in current_messages:
                    old_extracted = agent.node.extracted.copy()
                    agent.node.receive(current_messages[agent.id])
                    new_extracted = agent.node.extracted - old_extracted
                    if new_extracted:
                        print(f"  Node {agent.id} newly extracted: {new_extracted} (total: {agent.node.extracted})")

        # Final decision
        print(f"\n DECISION PHASE:")
        self.final_decision = self.node.decide()
        self.final_extracted = self.node.extracted.copy()

        decision_reason = "single value" if len(self.final_extracted) == 1 else "multiple/no values"
        print(f"  Node {self.id} decides '{self.final_decision}' (reason: {decision_reason})")

        return self.final_decision
