#!/usr/bin/env python3
"""Phase 5 Blockchain: Consensus & Smart Contracts"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_blockchain_consensus() -> str:
    return '''
class BlockchainNode:
    """Simplified blockchain node with PBFT consensus."""

    def __init__(self, node_id: str):
        self._node_id = node_id
        self._blocks = []
        self._pending_transactions = []
        self._consensus_state = {}

    def propose_block(self, transactions: List[Dict]) -> Dict:
        """Propose new block"""
        block = {
            "height": len(self._blocks),
            "timestamp": datetime.utcnow().isoformat(),
            "transactions": transactions,
            "proposer": self._node_id
        }
        return block

    def vote_on_block(self, block: Dict, vote: bool) -> None:
        """Vote on block (PBFT consensus)"""
        block_id = f"{block['height']}"
        if block_id not in self._consensus_state:
            self._consensus_state[block_id] = {"votes": 0, "total": 0}

        if vote:
            self._consensus_state[block_id]["votes"] += 1
        self._consensus_state[block_id]["total"] += 1

    def commit_block(self, block: Dict) -> bool:
        """Commit block if consensus reached (2/3 majority)"""
        block_id = f"{block['height']}"
        votes = self._consensus_state.get(block_id, {})
        majority = votes.get("votes", 0) > (votes.get("total", 0) * 2 / 3)

        if majority:
            self._blocks.append(block)
            return True
        return False

    def execute_smart_contract(self, contract: Dict, input_data: Dict) -> Dict:
        """Execute smart contract"""
        return {
            "contract_id": contract.get("id"),
            "status": "executed",
            "result": input_data,
            "timestamp": datetime.utcnow().isoformat()
        }
'''
    return generate_blockchain_consensus()


if __name__ == "__main__":
    print(generate_blockchain_consensus())
