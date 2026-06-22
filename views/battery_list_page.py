from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from qfluentwidgets import (ScrollArea, PushButton, ToolButton, LineEdit, ComboBox,
                            TableWidget, MessageBox, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, SearchLineEdit, CardWidget,
                            SubtitleLabel, CaptionLabel, IconWidget, HeaderCardWidget)
import database
from config import HEALTH_LEVELS, STATUS_OPTIONS
from views.battery_form import BatteryFormDialog


class BatteryListPage(ScrollArea):
    battery_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatteryListPage")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        container = QVBoxLayout()
        container.setSpacing(12)
        container.setContentsMargins(24, 20, 24, 20)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.searchEdit = SearchLineEdit()
        self.searchEdit.setPlaceholderText("搜索电池编号、适配机型...")
        self.searchEdit.setFixedWidth(300)
        self.searchEdit.searchSignal.connect(self._on_search)
        self.searchEdit.textChanged.connect(self._on_search)
        toolbar.addWidget(self.searchEdit)

        self.healthFilter = ComboBox()
        self.healthFilter.addItem("全部健康等级", "")
        for h in HEALTH_LEVELS:
            self.healthFilter.addItem(h, h)
        self.healthFilter.setFixedWidth(140)
        self.healthFilter.currentIndexChanged.connect(self._on_filter)
        toolbar.addWidget(self.healthFilter)

        self.statusFilter = ComboBox()
        self.statusFilter.addItem("全部状态", "")
        for s in STATUS_OPTIONS:
            self.statusFilter.addItem(s, s)
        self.statusFilter.setFixedWidth(140)
        self.statusFilter.currentIndexChanged.connect(self._on_filter)
        toolbar.addWidget(self.statusFilter)

        toolbar.addStretch()

        self.addButton = PushButton(FIF.ADD, "新增电池")
        self.addButton.clicked.connect(self._on_add)
        toolbar.addWidget(self.addButton)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新")
        self.refreshBtn.clicked.connect(self._load_data)
        toolbar.addWidget(self.refreshBtn)

        container.addLayout(toolbar)

        self.tableView = TableWidget()
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setWordWrap(False)
        self.tableView.setColumnCount(9)
        self.tableView.setHorizontalHeaderLabels([
            "电池编号", "适配机型", "购入日期", "循环次数",
            "健康等级", "最近检测日期", "在库状态", "待检测", "备注"
        ])
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableView.setSortingEnabled(True)
        self.tableView.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
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

        self.setWidget(QWidget()) if False else None
        from PySide6.QtWidgets import QWidget
        w = QWidget()
        w.setLayout(container)
        self.setWidget(w)

    def _load_data(self):
        batteries = database.get_all_batteries()
        self._batteries = batteries
        self._apply_filters()

    def _apply_filters(self):
        keyword = self.searchEdit.text().strip().lower()
        health = self.healthFilter.currentData()
        status = self.statusFilter.currentData()

        filtered = []
        for b in self._batteries:
            if keyword and keyword not in b["id"].lower() and keyword not in (b["model"] or "").lower():
                continue
            if health and b["health_level"] != health:
                continue
            if status and b["status"] != status:
                continue
            filtered.append(b)

        self.tableView.setRowCount(len(filtered))
        for row, b in enumerate(filtered):
            self.tableView.setItem(row, 0, self._make_item(b["id"]))
            self.tableView.setItem(row, 1, self._make_item(b["model"] or ""))
            self.tableView.setItem(row, 2, self._make_item(b["purchase_date"] or ""))
            self.tableView.setItem(row, 3, self._make_item(str(b["cycle_count"])))
            health_item = self._make_item(b["health_level"])
            if b["health_level"] == "差":
                health_item.setForeground(QColor(220, 50, 50))
            elif b["health_level"] == "中":
                health_item.setForeground(QColor(220, 160, 30))
            elif b["health_level"] == "良":
                health_item.setForeground(QColor(60, 160, 60))
            else:
                health_item.setForeground(QColor(30, 130, 220))
            self.tableView.setItem(row, 4, health_item)
            self.tableView.setItem(row, 5, self._make_item(b["last_check_date"] or ""))
            status_item = self._make_item(b["status"])
            if b["pending_check"] == 1:
                status_item.setBackground(QColor(255, 230, 230))
            self.tableView.setItem(row, 6, status_item)
            pending_item = self._make_item("⚠ 是" if b["pending_check"] == 1 else "否")
            if b["pending_check"] == 1:
                pending_item.setForeground(QColor(220, 50, 50))
            self.tableView.setItem(row, 7, pending_item)
            self.tableView.setItem(row, 8, self._make_item(b["remark"] or ""))

        self._filtered = filtered

    def _make_item(self, text):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def _on_search(self):
        self._apply_filters()

    def _on_filter(self):
        self._apply_filters()

    def _get_selected_battery(self):
        rows = self.tableView.selectionModel().selectedRows()
        if not rows:
            InfoBar.warning(
                title="提示",
                content="请先选择一行电池记录",
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return None
        row = rows[0].row()
        if row < len(self._filtered):
            return self._filtered[row]
        return None

    def _on_add(self):
        dialog = BatteryFormDialog(self.window())
        if dialog.exec():
            data = dialog.get_data()
            errors = dialog.validate() if hasattr(dialog, 'validate') else []
            from config import validate_battery
            errs = validate_battery(data, is_edit=False)
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
                database.insert_battery(data)
                InfoBar.success(
                    title="成功",
                    content=f"电池 {data['id']} 已添加",
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
        battery = self._get_selected_battery()
        if not battery:
            return
        dialog = BatteryFormDialog(self.window(), battery=dict(battery))
        if dialog.exec():
            data = dialog.get_data()
            from config import validate_battery
            errs = validate_battery(data, is_edit=True, original_id=battery["id"])
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
                database.update_battery(battery["id"], data)
                InfoBar.success(
                    title="成功",
                    content=f"电池 {battery['id']} 已更新",
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
        battery = self._get_selected_battery()
        if not battery:
            return
        msg = MessageBox(
            "确认删除",
            f"确定要删除电池 {battery['id']} 吗？\n删除后相关充放记录也将一并删除。",
            self.window()
        )
        if msg.exec():
            try:
                database.delete_battery(battery["id"])
                InfoBar.success(
                    title="成功",
                    content=f"电池 {battery['id']} 已删除",
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
