import time
from loguru import logger
from devices.gate import Gate

class GateManager:
    def __init__(self, boards, gates_config):
        self.boards = boards
        self.gates_config = gates_config
        self.gates = {}
        self.previous_gate_states = {}  # Add this line to track previous states
        self.last_active_device = None  # Add this line to track the last active device
        logger.info("🔧 Initializing GateManager")
        self.initialize_gates()

    def initialize_gates(self):
        try:
            for gate_id, gate_config in self.gates_config.items():
                board_id = gate_config['io_location']['board']
                if board_id not in self.boards:
                    logger.warning(f"⚠️ Board ID {board_id} not found for gate {gate_id}")
                    continue
                try:
                    self.gates[gate_id] = Gate(gate_id, gate_config, self.boards)
                    self.previous_gate_states[gate_id] = gate_config['status']  # Initialize previous state
                    logger.info(f"✅ Gate {gate_id} initialized on board {board_id}")
                except Exception as e:
                    logger.error(f"💢 Error initializing gate {gate_id}: {str(e)}")
        except Exception as e:
            logger.error(f"💢 Error initializing gates: {str(e)}")
            raise e

    def set_gates(self, gates_to_open):
        try:
            if not gates_to_open:
                logger.info("⛩️ No gates to open. Maintaining current gate states.")
                return  # Exit the method early if gates_to_open is empty

            changed_gates = []
            for gate_id, gate in self.gates.items():
                new_state = 'open' if gate_id in gates_to_open else 'closed'
                if new_state != self.previous_gate_states[gate_id]:
                    if new_state == 'open':
                        gate.open()
                    else:
                        gate.close()
                    self.previous_gate_states[gate_id] = new_state
                    changed_gates.append(f"{gate_id} ({new_state})")

            time.sleep(0.1)
            for gate in self.gates.values():
                gate.stop_servo()

            if changed_gates:
                logger.info(f"⛩️ Gates updated: {', '.join(changed_gates)}")
        except Exception as e:
            logger.error(f"💢 Error setting gates: {str(e)}")

    def test_gates(self):
        for gate in self.gates.values():
            logger.info(f'Testing gate {gate.name}')
            gate.close()
            time.sleep(1)
            gate.open()
            time.sleep(1)

    def open_all_gates(self):
        for gate in self.gates.values():
            gate.open()

    def close_all_gates(self):
        for gate in self.gates.values():
            self.close_gate(gate.name)

    def open_gate(self, name):
        if name in self.gates:
            self.gates[name].open()
        else:
            logger.debug(f'Gate {name} not found.')

    def close_gate(self, name):
        if name in self.gates:
            self.gates[name].close()
        else:
            logger.debug(f'Gate {name} not found.')

    def view_gates(self):
        for gate_name, gate in self.gates.items():
            logger.debug(f'Gate: {gate_name}, Status: {gate.status}, '
                         f'Board: {gate.board}, Pin: {gate.pin}, '
                         f'Min: {gate.min_angle}, Max: {gate.max_angle}')

    def get_gate_settings(self, tools):
        open_gates = []
        active_tool = None
        for current_tool in tools:
            if current_tool.status != 'off':
                active_tool = current_tool
                for gate_pref in current_tool.gate_prefs:
                    if gate_pref in self.gates and gate_pref not in open_gates:
                        open_gates.append(gate_pref)

        if active_tool:
            self.last_active_device = active_tool
        elif self.last_active_device and not open_gates:
            # If no active tools and we have a last active device, maintain current gate states
            logger.info(f"⛩️ Maintaining current gate states for last active device: {self.last_active_device.id}")
            return []

        return open_gates
    
    def update(self):
        # This method can be used for any continuous updates needed for gates
        pass

    def cleanup(self):
        logger.info("🧹 Cleaning up GateManager")
        for gate in self.gates.values():
            gate.stop_servo()
        logger.info("✅ All gates closed during cleanup")


