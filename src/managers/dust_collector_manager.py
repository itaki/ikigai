from loguru import logger
from devices.dust_collector import DustCollector
import threading
import time

class DustCollectorManager:
    def __init__(self, device_config):
        self.device_config = device_config
        self.collectors = {}
        self.collector_users = {}
        self._stop_thread = threading.Event()
        self.thread = threading.Thread(target=self._manage_collectors)
        self.initialize_collectors()
        self.thread.start()

    def initialize_collectors(self):
        for device in self.device_config:
            if device['type'] == 'collector':
                collector_label = device['label']
                if device['connection']['board'] == 'pi_gpio':
                    self.collectors[collector_label] = DustCollector(device)
                    self.collector_users[collector_label] = set()
                    logger.debug(f"✅ 💨 {collector_label} initialized on Raspberry Pi GPIO")
                else:
                    logger.error(f"❌ Unsupported board type for {collector_label}")

    def update_collector_state(self, voltage_states, button_states):
        for collector_id, collector in self.collectors.items():
            new_users = set()
            for device_id, state in voltage_states.items():
                if state.get('state') == 'on':
                    new_users.add(device_id)
            for button_id, state in button_states.items():
                if state == 'on':
                    new_users.add(button_id)
            
            current_users = self.collector_users[collector_id]
            if new_users != current_users:
                added_users = new_users - current_users
                removed_users = current_users - new_users
                self.collector_users[collector_id] = new_users
                
                if added_users:
                    logger.info(f"Dust collector {collector_id} added users: {added_users}")
                if removed_users:
                    logger.info(f"Dust collector {collector_id} removed users: {removed_users}")

    def _manage_collectors(self):
        while not self._stop_thread.is_set():
            for collector_id, collector in self.collectors.items():
                if collector.relay_status == "on":
                    if time.time() - collector.last_on_time >= collector.minimum_up_time:
                        if not self.collector_users[collector_id]:
                            collector.turn_off()
                            logger.info(f"💨 🛑 Dust Collector {collector_id} 🛑")
                elif collector.relay_status == "off":
                    if time.time() - collector.last_off_time >= collector.cool_down_time:
                        if self.collector_users[collector_id]:
                            collector.turn_on()
                            logger.info(f"💨 🌀 Dust Collector {collector_id} 🌀")
            time.sleep(1)

    def cleanup(self):
        logger.info("🧹 Cleaning up DustCollectorManager")
        self._stop_thread.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            logger.warning("DustCollectorManager thread did not stop within the timeout period.")
        for collector in self.collectors.values():
            collector.turn_off()
            collector.cleanup()
        logger.info("✅ DustCollectorManager cleanup completed")

    def get_all_collector_states(self):
        return {collector_id: collector.relay_status for collector_id, collector in self.collectors.items()}