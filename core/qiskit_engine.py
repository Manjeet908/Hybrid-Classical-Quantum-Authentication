"""
Qiskit Simulation Engine: Minimal Matrix Product State (MPS) simulator 
tailored for BB84, B92, and E91 QKD protocol execution.
"""
from typing import Dict, List, Optional, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class QiskitEngine:
    """AerSimulator wrapper pre-configured with Matrix Product State for linear scaling."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.simulator = AerSimulator(method="matrix_product_state", seed_simulator=seed)

    def run_circuit(self, circuit: QuantumCircuit, shots: int = 1) -> Dict[str, int]:
        """Executes a quantum circuit on AerSimulator and returns the measurement counts."""
        job = self.simulator.run(circuit, shots=shots)
        return job.result().get_counts(circuit)

    def sample_registers(self, circuit: QuantumCircuit) -> Tuple[List[int], Optional[List[int]]]:
        """
        Executes a 1-shot run and decodes classical bit registers in qubit index order.
        Returns:
            (bob_bits, eve_bits) if Eve's register is present, otherwise (bob_bits, None).
        """
        counts = self.run_circuit(circuit, shots=1)
        outcome_str = next(iter(counts))

        # In Qiskit, multiple registers are space-separated in reverse creation order: "eve bob"
        if " " in outcome_str:
            parts = outcome_str.split(" ")
            bob_bits = [int(b) for b in reversed(parts[-1])]
            eve_bits = [int(b) for b in reversed(parts[0])]
            return bob_bits, eve_bits

        bob_bits = [int(b) for b in reversed(outcome_str)]
        return bob_bits, None

    def sample_measurement(self, circuit: QuantumCircuit) -> List[int]:
        """Runs a 1-shot execution and returns the primary measured register bits (used by E91)."""
        bob_bits, _ = self.sample_registers(circuit)
        return bob_bits
