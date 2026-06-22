from datetime import date

CYCLE_THRESHOLD = 300

HEALTH_LEVELS = ["优", "良", "中", "差"]

STATUS_OPTIONS = ["在库", "借出", "待检测", "已报废"]

ANOMALY_OPTIONS = ["否", "是"]


def validate_battery(data: dict, is_edit: bool = False, original_id: str = ""):
    errors = []
    if not data.get("id", "").strip():
        errors.append("电池编号不能为空")
    if not is_edit and data.get("id", "").strip():
        from database import get_battery
        if get_battery(data["id"].strip()):
            errors.append("电池编号已存在，不能重复")
    if is_edit and data.get("id", "").strip() != original_id.strip():
        from database import get_battery
        if get_battery(data["id"].strip()):
            errors.append("电池编号已存在，不能重复")
    today = date.today().isoformat()
    if data.get("purchase_date") and data["purchase_date"] > today:
        errors.append("购入日期不能晚于当前日期")
    if data.get("last_check_date") and data["last_check_date"] > today:
        errors.append("最近检测日期不能晚于当前日期")
    cycle = data.get("cycle_count", 0)
    health = data.get("health_level", "优")
    if isinstance(cycle, int) and cycle > CYCLE_THRESHOLD and health == "优":
        errors.append(f"当前循环次数({cycle})超过阈值({CYCLE_THRESHOLD})，健康等级不能为'优'")
    return errors


def validate_charge_record(data: dict):
    errors = []
    if not data.get("battery_id"):
        errors.append("请选择电池")
    if not data.get("record_date"):
        errors.append("记录日期不能为空")
    else:
        today = date.today().isoformat()
        if data["record_date"] > today:
            errors.append("记录日期不能晚于当前日期")
    charge_before = data.get("charge_before", 0)
    charge_after = data.get("charge_after", 0)
    if isinstance(charge_before, int) and isinstance(charge_after, int):
        if charge_after < charge_before:
            errors.append("充电后电量必须大于等于充电前电量")
    if charge_before < 0 or charge_before > 100:
        errors.append("充电前电量范围应为 0-100")
    if charge_after < 0 or charge_after > 100:
        errors.append("充电后电量范围应为 0-100")
    if data.get("is_anomaly") == 1 and not data.get("remark", "").strip():
        errors.append("异常标记为'是'时，备注不能为空")
    return errors
