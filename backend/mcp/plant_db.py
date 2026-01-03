from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

class PlantDatabase:
    """
    Simulated plant database following Model Context Protocol (MCP)
    In production, this would connect to actual SCADA/DCS systems
    """
    
    def __init__(self):
        # Simulated equipment registry
        self.equipment = {
            'RM001': {
                'name': 'Rolling Mill #1',
                'type': 'rolling_mill',
                'status': 'operational',
                'location': 'Hot Strip Mill',
                'last_maintenance': '2024-12-15'
            },
            'BF002': {
                'name': 'Blast Furnace #2',
                'type': 'blast_furnace',
                'status': 'operational',
                'location': 'Iron Making',
                'last_maintenance': '2024-12-10'
            },
            'CR003': {
                'name': 'Crane #3',
                'type': 'crane',
                'status': 'maintenance',
                'location': 'Steel Melting Shop',
                'last_maintenance': '2024-12-28'
            }
        }
        
        # Simulated sensor data
        self.sensors = {}
        self._initialize_sensors()
    
    def _initialize_sensors(self):
        """Initialize sensor readings for equipment"""
        for eq_id in self.equipment.keys():
            self.sensors[eq_id] = {
                'temperature': random.uniform(60, 90),
                'vibration': random.uniform(0.5, 2.5),
                'pressure': random.uniform(100, 150),
                'power_consumption': random.uniform(500, 1500),
                'runtime_hours': random.randint(1000, 5000),
                'last_updated': datetime.now().isoformat()
            }
    
    def get_equipment_info(self, equipment_id: str) -> Optional[Dict]:
        """Get equipment details"""
        return self.equipment.get(equipment_id)
    
    def get_all_equipment(self) -> List[Dict]:
        """Get all equipment with their IDs"""
        return [
            {'id': eq_id, **details}
            for eq_id, details in self.equipment.items()
        ]
    
    def get_sensor_data(self, equipment_id: str) -> Optional[Dict]:
        """Get current sensor readings for equipment"""
        if equipment_id in self.sensors:
            # Simulate live data with small variations
            data = self.sensors[equipment_id].copy()
            data['temperature'] += random.uniform(-2, 2)
            data['vibration'] += random.uniform(-0.1, 0.1)
            data['last_updated'] = datetime.now().isoformat()
            return data
        return None
    
    def get_maintenance_history(self, equipment_id: str, days: int = 30) -> List[Dict]:
        """Get maintenance history for equipment"""
        if equipment_id not in self.equipment:
            return []
        
        # Simulate maintenance records
        history = []
        base_date = datetime.now()
        
        for i in range(5):
            record_date = base_date - timedelta(days=random.randint(1, days))
            history.append({
                'date': record_date.strftime('%Y-%m-%d'),
                'type': random.choice(['preventive', 'corrective', 'inspection']),
                'description': random.choice([
                    'Lubrication check',
                    'Belt replacement',
                    'Sensor calibration',
                    'Motor inspection',
                    'Hydraulic system check'
                ]),
                'technician': f"Tech-{random.randint(1, 10)}",
                'duration_hours': random.randint(1, 8)
            })
        
        return sorted(history, key=lambda x: x['date'], reverse=True)
    
    def get_fault_history(self, equipment_id: str, days: int = 90) -> List[Dict]:
        """Get fault/alarm history"""
        if equipment_id not in self.equipment:
            return []
        
        faults = []
        fault_types = [
            'High Temperature Alert',
            'Abnormal Vibration',
            'Pressure Drop',
            'Emergency Stop',
            'Sensor Communication Lost'
        ]
        
        for i in range(random.randint(2, 8)):
            fault_date = datetime.now() - timedelta(days=random.randint(1, days))
            faults.append({
                'date': fault_date.strftime('%Y-%m-%d %H:%M'),
                'fault_type': random.choice(fault_types),
                'severity': random.choice(['low', 'medium', 'high']),
                'resolved': random.choice([True, False]),
                'resolution_time_hours': random.randint(1, 24) if random.choice([True, False]) else None
            })
        
        return sorted(faults, key=lambda x: x['date'], reverse=True)
    
    def check_equipment_status(self, equipment_id: str) -> Dict:
        """Check if equipment needs attention"""
        sensor_data = self.get_sensor_data(equipment_id)
        equipment_info = self.get_equipment_info(equipment_id)
        
        if not sensor_data or not equipment_info:
            return {'error': 'Equipment not found'}
        
        alerts = []
        
        # Check thresholds
        if sensor_data['temperature'] > 85:
            alerts.append({
                'type': 'temperature',
                'severity': 'high',
                'message': 'Temperature exceeds safe limit'
            })
        
        if sensor_data['vibration'] > 2.0:
            alerts.append({
                'type': 'vibration',
                'severity': 'medium',
                'message': 'Abnormal vibration detected'
            })
        
        if sensor_data['pressure'] < 110:
            alerts.append({
                'type': 'pressure',
                'severity': 'medium',
                'message': 'Pressure below optimal range'
            })
        
        return {
            'equipment_id': equipment_id,
            'name': equipment_info['name'],
            'status': equipment_info['status'],
            'alerts': alerts,
            'requires_attention': len(alerts) > 0,
            'sensor_data': sensor_data
        }
    
    def search_equipment(self, query: str) -> List[Dict]:
        """Search equipment by name, type, or location"""
        query = query.lower()
        results = []
        
        for eq_id, details in self.equipment.items():
            if (query in details['name'].lower() or 
                query in details['type'].lower() or 
                query in details['location'].lower()):
                results.append({'id': eq_id, **details})
        
        return results
    
    def update_equipment_status(self, equipment_id: str, new_status: str) -> bool:
        """Update equipment status"""
        if equipment_id in self.equipment:
            self.equipment[equipment_id]['status'] = new_status
            return True
        return False