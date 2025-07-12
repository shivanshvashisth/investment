import random
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Message:
    """Represents a message in the Dolev-Strong protocol"""
    value: str
    signatures: List[int]  # List of node IDs that have signed this message

    def __str__(self):
        return f"⟨{self.value}, {{{', '.join(map(str, self.signatures))}}}⟩"

    def add_signature(self, node_id: int) -> 'Message':
        """Add a signature to the message"""
        new_signatures = self.signatures + [node_id]
        return Message(self.value, new_signatures)

    def is_valid(self, f: int) -> bool:
        """Check if message has valid signature count and no duplicates"""
        return len(set(self.signatures)) == len(self.signatures) and len(self.signatures) <= f + 2


class Node:
    def __init__(self, node_id, f, is_byzantine=False):
        self.node_id = node_id
        self.extracted = set()  # Changed to set for proper protocol
        self.f = f
        self.is_byzantine = is_byzantine

    def sign(self, message):
        return f"{message}|{self.node_id}"

    def verify(self, signed_message):
        parts = signed_message.split('|')
        if len(parts) < 2:
            return False
        signers = parts[1:]
        # Check no duplicate signers and within bounds
        return len(set(signers)) == len(signers) and len(signers) <= self.f + 2

    def receive(self, round_msgs):
        new_msgs = []
        for msg in round_msgs:
            parts = msg.split('|')
            if len(parts) < 2:
                continue

            payload = parts[0]
            signers = [int(s) for s in parts[1:]]

            # Dolev-Strong protocol: check if message is valid for this round
            if not self.verify(msg):
                continue

            # Check if sender (first signer) is node 0
            if len(signers) > 0 and signers[0] != 0:
                continue

            # Add to extracted set if not already present
            if payload not in self.extracted:
                self.extracted.add(payload)

                # Relay message with our signature if we haven't signed it
                if self.node_id not in signers:
                    new_msg = f"{payload}|" + '|'.join(map(str, signers + [self.node_id]))
                    new_msgs.append(new_msg)

        return new_msgs

    def decide(self):
        # Dolev-Strong decision rule: if |extracted| = 1, output that bit; else output 0
        if len(self.extracted) == 1:
            return list(self.extracted)[0]
        return "0"  # Default value as per protocol


class DolevStrongConsensus:
    def __init__(self, total_nodes: int, f: int, byzantine_nodes: List[int], sender_id: int = 0):
        self.total_nodes = total_nodes
        self.f = f
        self.sender_id = sender_id

        # Create nodes
        self.nodes = []
        for i in range(total_nodes):
            is_byzantine = i in byzantine_nodes
            node = Node(i, f, is_byzantine)
            self.nodes.append(node)

        print(f"  Created {total_nodes} nodes with f={f}")
        print(f"  Byzantine nodes: {byzantine_nodes}")
        print(f" Sender: Node {sender_id}")

    def run_consensus(self, initial_value: str) -> Dict[int, str]:
        """Run the complete Dolev-Strong consensus protocol"""
        print(f"\n Starting Dolev-Strong consensus with initial value: '{initial_value}'")
        print("=" * 60)

        # Reset all nodes
        for node in self.nodes:
            node.extracted.clear()

        # Round 0: Sender broadcasts initial value
        print(f"\n ROUND 0: Sender (Node {self.sender_id}) broadcasting")
        sender = self.nodes[self.sender_id]
        round_messages = [sender.sign(initial_value)] * (self.total_nodes - 1)

        # Distribute round 0 messages to all non-sender nodes
        message_queues = [[] for _ in range(self.total_nodes)]
        for i, node in enumerate(self.nodes):
            if i != self.sender_id:
                message_queues[i] = [round_messages[i - (1 if i > self.sender_id else 0)]]

        # Rounds 1 to f+1
        for round_num in range(1, self.f + 2):
            print(f"\n ROUND {round_num}:")
            next_round_messages = [[] for _ in range(self.total_nodes)]

            # Each node processes its messages
            for node_id, node in enumerate(self.nodes):
                if message_queues[node_id]:
                    outgoing = node.receive(message_queues[node_id])

                    # Distribute outgoing messages to all other nodes
                    for other_id in range(self.total_nodes):
                        if other_id != node_id:
                            next_round_messages[other_id].extend(outgoing)

            message_queues = next_round_messages

        # Final decision phase
        print(f"\n DECISION PHASE:")
        decisions = {}
        for node in self.nodes:
            decisions[node.node_id] = node.decide()

        return decisions

    def analyze_results(self, decisions: Dict[int, str], byzantine_nodes: List[int]):
        """Analyze consensus results"""
        print(f"\n CONSENSUS RESULTS:")
        print("=" * 60)

        honest_decisions = []
        byzantine_decisions = []

        for node_id, decision in decisions.items():
            node_type = " Byzantine" if node_id in byzantine_nodes else "✅ Honest"
            print(f"Node {node_id:2d} ({node_type:12s}): {decision:15s} | Extracted: {self.nodes[node_id].extracted}")

            if node_id in byzantine_nodes:
                byzantine_decisions.append(decision)
            else:
                honest_decisions.append(decision)

        # Check agreement among honest nodes
        unique_honest = set(honest_decisions)
        if len(unique_honest) == 1:
            print(f"\n SUCCESS: All honest nodes agreed on '{list(unique_honest)[0]}'")
        else:
            print(f"\n FAILURE: Honest nodes disagreed: {unique_honest}")

        print(f" Honest nodes: {len(honest_decisions)} decisions: {set(honest_decisions)}")
        print(f"️  Byzantine nodes: {len(byzantine_decisions)} decisions: {set(byzantine_decisions)}")


def main():
    """Run multiple consensus scenarios"""
    print("  DOLEV-STRONG BYZANTINE CONSENSUS SIMULATION")
    print("=" * 60)

    # Scenario 1: Basic case with f=1
    print("\n SCENARIO 1: f=1, 4 nodes, 1 Byzantine")
    consensus1 = DolevStrongConsensus(
        total_nodes=4,
        f=1,
        byzantine_nodes=[2],
        sender_id=0
    )
    decisions1 = consensus1.run_consensus("buy")
    consensus1.analyze_results(decisions1, [2])

    # Scenario 2: Higher fault tolerance with f=2
    print("\n" + "=" * 80)
    print("\n SCENARIO 2: f=2, 7 nodes, 2 Byzantine")
    consensus2 = DolevStrongConsensus(
        total_nodes=7,
        f=2,
        byzantine_nodes=[1, 4],
        sender_id=0
    )
    decisions2 = consensus2.run_consensus("sell")
    consensus2.analyze_results(decisions2, [1, 4])

    # Scenario 3: Byzantine sender
    print("\n" + "=" * 80)
    print("\n🔬 SCENARIO 3: f=1, 4 nodes, Byzantine sender")
    consensus3 = DolevStrongConsensus(
        total_nodes=4,
        f=1,
        byzantine_nodes=[0],  # Sender is Byzantine
        sender_id=0
    )
    decisions3 = consensus3.run_consensus("hold")
    consensus3.analyze_results(decisions3, [0])


if __name__ == "__main__":
    main()
