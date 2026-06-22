from PySide6.QtWidgets import QVBoxLayout, QFormLayout, QDateEdit, QLineEdit, QSpinBox
from PySide6.QtCore import QDate, Qt
from qfluentwidgets import (MessageBoxBase, SubtitleLabel, LineEdit, ComboBox,
                            TextEdit, DatePicker, SpinBox, InfoBar, InfoBarPosition)
import database
from config import HEALTH_LEVELS, STATUS_OPTIONS, CYCLE_THRESHOLD, validate_battery


class BatteryFormDialog(MessageBoxBase):
    def __init__(self, parent=None, battery=None):
        super().__init__(parent)
        self.battery = battery
        self.is_edit = battery is not None
        self._setup_ui()
        if battery:
            self._fill_data(battery)

    def _setup_ui(self):
        self.titleLabel = SubtitleLabel("编辑电池" if self.is_edit else "新增电池")
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(12)

        self.idEdit = LineEdit()
        self.idEdit.setPlaceholderText("请输入电池编号")
        if self.is_edit:
            self.idEdit.setEnabled(False)
        form.addRow("电池编号 *", self.idEdit)

        self.modelEdit = LineEdit()
        self.modelEdit.setPlaceholderText("请输入适配机型")
        form.addRow("适配机型", self.modelEdit)

        self.purchaseDateEdit = DatePicker()
        self.purchaseDateEdit.setDate(QDate.currentDate())
        form.addRow("购入日期", self.purchaseDateEdit)

        self.cycleSpin = SpinBox()
        self.cycleSpin.setRange(0, 99999)
        self.cycleSpin.setValue(0)
        form.addRow("当前循环次数", self.cycleSpin)

        self.healthCombo = ComboBox()
        self.healthCombo.addItems(HEALTH_LEVELS)
        form.addRow("健康等级", self.healthCombo)

        self.lastCheckDateEdit = DatePicker()
        self.lastCheckDateEdit.setDate(QDate.currentDate())
        form.addRow("最近检测日期", self.lastCheckDateEdit)

        self.statusCombo = ComboBox()
        self.statusCombo.addItems(STATUS_OPTIONS)
        form.addRow("在库状态", self.statusCombo)

        self.remarkEdit = TextEdit()
        self.remarkEdit.setPlaceholderText("备注信息")
        self.remarkEdit.setFixedHeight(80)
        form.addRow("备注", self.remarkEdit)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(420)

    def _fill_data(self, battery):
        self.idEdit.setText(battery["id"])
        self.modelEdit.setText(battery["model"] or "")
        if battery["purchase_date"]:
            parts = battery["purchase_date"].split("-")
            if len(parts) == 3:
                self.purchaseDateEdit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        self.cycleSpin.setValue(battery["cycle_count"] or 0)
        idx = HEALTH_LEVELS.index(battery["health_level"]) if battery["health_level"] in HEALTH_LEVELS else 0
        self.healthCombo.setCurrentIndex(idx)
        if battery["last_check_date"]:
            parts = battery["last_check_date"].split("-")
            if len(parts) == 3:
                self.lastCheckDateEdit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        sidx = STATUS_OPTIONS.index(battery["status"]) if battery["status"] in STATUS_OPTIONS else 0
        self.statusCombo.setCurrentIndex(sidx)
        self.remarkEdit.setPlainText(battery["remark"] or "")

    def get_data(self):
        return {
            "id": self.idEdit.text().strip(),
            "model": self.modelEdit.text().strip(),
            "purchase_date": self.purchaseDateEdit.date.toString("yyyy-MM-dd"),
            "cycle_count": self.cycleSpin.value(),
            "health_level": self.healthCombo.currentText(),
            "last_check_date": self.lastCheckDateEdit.date.toString("yyyy-MM-dd"),
            "status": self.statusCombo.currentText(),
            "remark": self.remarkEdit.toPlainText().strip()
        }

    def validate(self):
        data = self.get_data()
        original_id = self.battery["id"] if self.is_edit else ""
        errors = validate_battery(data, is_edit=self.is_edit, original_id=original_id)
        if errors:
            for err in errors:
                InfoBar.error(
                    title="验证错误",
                    content=err,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.parent()
                )
            return False
        return True
