import os
import database

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "battery_data.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Removed old database")

database.init_db()
print("Database initialized")

database.insert_battery({'id':'BAT001','model':'Canon LP-E6','purchase_date':'2024-01-15','cycle_count':0,'health_level':'优','last_check_date':'2026-06-01','status':'在库','remark':''})
print('Insert battery OK')

b = database.get_battery('BAT001')
print(f'Battery: id={b["id"]}, cycle={b["cycle_count"]}, pending={b["pending_check"]}')

database.insert_charge_record({'battery_id':'BAT001','record_date':'2026-06-10','charge_before':20,'charge_after':100,'usage_duration':120,'is_anomaly':0,'operator':'张三','remark':''})
print('Insert record 1 OK')

b = database.get_battery('BAT001')
print(f'After record 1: cycle={b["cycle_count"]}, pending={b["pending_check"]}')

database.insert_charge_record({'battery_id':'BAT001','record_date':'2026-06-15','charge_before':15,'charge_after':100,'usage_duration':90,'is_anomaly':1,'operator':'李四','remark':'耗电过快'})
print('Insert record 2 (anomaly) OK')

b = database.get_battery('BAT001')
print(f'After record 2: cycle={b["cycle_count"]}, pending={b["pending_check"]}')

database.insert_charge_record({'battery_id':'BAT001','record_date':'2026-06-18','charge_before':10,'charge_after':100,'usage_duration':60,'is_anomaly':1,'operator':'张三','remark':'同样异常'})
print('Insert record 3 (consecutive anomaly) OK')

b = database.get_battery('BAT001')
print(f'After record 3: cycle={b["cycle_count"]}, pending={b["pending_check"]}')

pending = database.get_pending_check_batteries()
print(f'Pending check batteries: {len(pending)}')

from config import validate_battery, validate_charge_record
errs = validate_battery({'id':'BAT001','model':'Test','purchase_date':'2025-01-01','cycle_count':500,'health_level':'优','last_check_date':'2026-06-22','status':'在库','remark':''})
print(f'Cycle threshold validation: {errs}')

errs2 = validate_charge_record({'battery_id':'BAT001','record_date':'2026-06-22','charge_before':80,'charge_after':60,'usage_duration':30,'is_anomaly':0,'operator':'张三','remark':''})
print(f'Charge before>after validation: {errs2}')

errs3 = validate_charge_record({'battery_id':'BAT001','record_date':'2026-06-22','charge_before':20,'charge_after':100,'usage_duration':30,'is_anomaly':1,'operator':'张三','remark':''})
print(f'Anomaly without remark validation: {errs3}')

print('All tests passed!')
