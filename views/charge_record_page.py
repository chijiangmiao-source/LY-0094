from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QHeaderView, QWidget,
                               QFormLayout)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor
from qfluentwidgets import (ScrollArea, PushButton, ComboBox, LineEdit,
                            TableWidget, MessageBox, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, SpinBox, DatePicker, TextEdit,
                            SwitchButton, SubtitleLabel, MessageBoxBase)
import database
from config import validate_charge_record


class ChargeRecordFormDialog(MessageBoxBase):
    def __init__(self, parent=None, battery_id="", record=None):
        super().__init__(parent)
        self.record = record
        self.is_edit = record is not None
        self._setup_ui(battery_id)
        if record:
            self._fill_data(record)

    def _setup_ui(self, battery_id):
        self.titleLabel = SubtitleLabel("编辑充放记录" if self.is_edit else "新增充放记录")
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(12)

        self.batteryCombo = ComboBox()
        batteries = database.get_all_batteries()
        self._battery_ids = []
        for b in batteries:
            self.batteryCombo.addItem(f"{b['id']} ({b['model'] or '未指定'})", b["id"])
            self._battery_ids.append(b["id"])
        if battery_id:
            idx = self._battery_ids.index(battery_id) if battery_id in self._battery_ids else 0
            self.batteryCombo.setCurrentIndex(idx)
        if self.is_edit:
            self.batteryCombo.setEnabled(False)
        form.addRow("电池 *", self.batteryCombo)

        self.dateEdit = DatePicker()
        self.dateEdit.setDate(QDate.currentDate())
        form.addRow("记录日期 *", self.dateEdit)

        self.chargeBeforeSpin = SpinBox()
        self.chargeBeforeSpin.setRange(0, 100)
        self.chargeBeforeSpin.setValue(0)
        self.chargeBeforeSpin.setSuffix(" %")
        form.addRow("充电前电量 *", self.chargeBeforeSpin)

        self.chargeAfterSpin = SpinBox()
        self.chargeAfterSpin.setRange(0, 100)
        self.chargeAfterSpin.setValue(100)
        self.chargeAfterSpin.setSuffix(" %")
        form.addRow("充电后电量 *", self.chargeAfterSpin)

        self.durationSpin = SpinBox()
        self.durationSpin.setRange(0, 9999)
        self.durationSpin.setValue(0)
        self.durationSpin.setSuffix(" 分钟")
        form.addRow("使用时长", self.durationSpin)

        self.anomalySwitch = SwitchButton("异常标记")
        form.addRow("异常标记", self.anomalySwitch)

        self.operatorEdit = LineEdit()
        self.operatorEdit.setPlaceholderText("操作人")
        form.addRow("操作人", self.operatorEdit)

        self.remarkEdit = TextEdit()
        self.remarkEdit.setPlaceholderText("备注信息（异常时必填）")
        self.remarkEdit.setFixedHeight(60)
        form.addRow("备注", self.remarkEdit)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(420)

    def _fill_data(self, record):
        if record["record_date"]:
            parts = record["record_date"].split("-")
            if len(parts) == 3:
                self.dateEdit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        self.chargeBeforeSpin.setValue(record["charge_before"] or 0)
        self.chargeAfterSpin.setValue(record["charge_after"] or 0)
        self.durationSpin.setValue(int(record["usage_duration"] or 0))
        self.anomalySwitch.setChecked(record["is_anomaly"] == 1)
        self.operatorEdit.setText(record["operator"] or "")
        self.remarkEdit.setPlainText(record["remark"] or "")

    def get_data(self):
        return {
            "battery_id": self.batteryCombo.currentData() or "",
            "record_date": self.dateEdit.date.toString("yyyy-MM-dd"),
            "charge_before": self.chargeBeforeSpin.value(),
            "charge_after": self.chargeAfterSpin.value(),
            "usage_duration": self.durationSpin.value(),
            "is_anomaly": 1 if self.anomalySwitch.isChecked() else 0,
            "operator": self.operatorEdit.text().strip(),
            "remark": self.remarkEdit.toPlainText().strip()
        }


class ChargeRecordPage(ScrollArea):
    battery_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChargeRecordPage")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._current_battery_id = None
        self._setup_ui()
        self._refresh_battery_combo()

    def _setup_ui(self):
        container = QVBoxLayout()
        container.setSpacing(12)
        container.setContentsMargins(24, 20, 24, 20)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.batteryCombo = ComboBox()
        self.batteryCombo.addItem("全部电池", "")
        self.batteryCombo.setFixedWidth(260)
        self.batteryCombo.currentIndexChanged.connect(self._on_battery_changed)
        toolbar.addWidget(self.batteryCombo)

        toolbar.addStretch()

        self.addButton = PushButton(FIF.ADD, "新增记录")
        self.addButton.clicked.connect(self._on_add)
        toolbar.addWidget(self.addButton)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新")
        self.refreshBtn.clicked.connect(self._load_data)
        toolbar.addWidget(self.refreshBtn)

        container.addLayout(toolbar)

        self.tableView = TableWidget()
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setColumnCount(9)
        self.tableView.setHorizontalHeaderLabels([
            "电池编号", "记录日期", "充电前电量", "充电后电量",
            "使用时长(分)", "异常标记", "操作人", "备注", "ID"
        ])
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableView.setSortingEnabled(True)
        self.tableView.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.tableView.hideColumn(8)
        container.addWidget(self.tableView)

        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)

        self.editBtn = PushButton(FIF.EDIT, "编辑")
        self.editBtn.clicked.connect(self._on_edit)
        btn_bar.addWidget(self.editBtn)

        self.deleteBtn = PushButton(FIF.DELETE, "删除")
        self.deleteBtn.clicked.connect(self._on_delete)
        btn_bar.addWidget(self.deleteBtn)

        btn_bar.addStretch()
        container.addLayout(btn_bar)

        w = QWidget()
        w.setLayout(container)
        self.setWidget(w)

    def _refresh_battery_combo(self):
        self.batteryCombo.blockSignals(True)
        current_data = self.batteryCombo.currentData()
        self.batteryCombo.clear()
        self.batteryCombo.addItem("全部电池", "")
        batteries = database.get_all_batteries()
        for b in batteries:
            self.batteryCombo.addItem(f"{b['id']} ({b['model'] or '未指定'})", b["id"])
        if current_data:
            idx = self.batteryCombo.findData(current_data)
            if idx >= 0:
                self.batteryCombo.setCurrentIndex(idx)
        self.batteryCombo.blockSignals(False)
        self._load_data()

    def _on_battery_changed(self):
        self._current_battery_id = self.batteryCombo.currentData() or None
        self._load_data()

    def _load_data(self):
        battery_id = self.batteryCombo.currentData() or None
        if battery_id:
            records = database.get_charge_records(battery_id)
        else:
            records = database.get_all_charge_records()

        self._records = records
        self.tableView.setRowCount(len(records))
        for row, r in enumerate(records):
            self.tableView.setItem(row, 0, self._make_item(r["battery_id"]))
            self.tableView.setItem(row, 1, self._make_item(r["record_date"] or ""))
            self.tableView.setItem(row, 2, self._make_item(f"{r['charge_before']}%"))
            self.tableView.setItem(row, 3, self._make_item(f"{r['charge_after']}%"))
            self.tableView.setItem(row, 4, self._make_item(str(r["usage_duration"] or 0)))
            anomaly_item = self._make_item("⚠ 是" if r["is_anomaly"] == 1 else "否")
            if r["is_anomaly"] == 1:
                anomaly_item.setForeground(QColor(220, 50, 50))
            self.tableView.setItem(row, 5, anomaly_item)
            self.tableView.setItem(row, 6, self._make_item(r["operator"] or ""))
            self.tableView.setItem(row, 7, self._make_item(r["remark"] or ""))
            self.tableView.setItem(row, 8, self._make_item(str(r["id"])))

    def _make_item(self, text):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def _get_selected_record(self):
        rows = self.tableView.selectionModel().selectedRows()
        if not rows:
            InfoBar.warning(
                title="提示",
                content="请先选择一行记录",
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return None
        row = rows[0].row()
        if row < len(self._records):
            return self._records[row]
        return None

    def _on_add(self):
        battery_id = self.batteryCombo.currentData() or ""
        dialog = ChargeRecordFormDialog(self.window(), battery_id=battery_id)
        if dialog.exec():
            data = dialog.get_data()
            errs = validate_charge_record(data)
            if errs:
                for e in errs:
                    InfoBar.error(
                        title="验证错误",
                        content=e,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                return
            try:
                database.insert_charge_record(data)
                InfoBar.success(
                    title="成功",
                    content="充放记录已添加",
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self._load_data()
                self.battery_changed.emit()
            except Exception as ex:
                InfoBar.error(
                    title="错误",
                    content=str(ex),
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_edit(self):
        record = self._get_selected_record()
        if not record:
            return
        dialog = ChargeRecordFormDialog(
            self.window(),
            battery_id=record["battery_id"],
            record=dict(record)
        )
        if dialog.exec():
            data = dialog.get_data()
            errs = validate_charge_record(data)
            if errs:
                for e in errs:
                    InfoBar.error(
                        title="验证错误",
                        content=e,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                return
            try:
                database.update_charge_record(record["id"], data)
                InfoBar.success(
                    title="成功",
                    content="充放记录已更新",
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self._load_data()
                self.battery_changed.emit()
            except Exception as ex:
                InfoBar.error(
                    title="错误",
                    content=str(ex),
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_delete(self):
        record = self._get_selected_record()
        if not record:
            return
        msg = MessageBox(
            "确认删除",
            f"确定要删除该充放记录吗？",
            self.window()
        )
        if msg.exec():
            try:
                database.delete_charge_record(record["id"])
                InfoBar.success(
                    title="成功",
                    content="充放记录已删除",
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self._load_data()
                self.battery_changed.emit()
            except Exception as ex:
                InfoBar.error(
                    title="错误",
                    content=str(ex),
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def refresh_combo(self):
        self._refresh_battery_combo()
