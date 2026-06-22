from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QHeaderView, QWidget,
                               QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from qfluentwidgets import (ScrollArea, PushButton, TableWidget, SubtitleLabel,
                            CaptionLabel, HeaderCardWidget, ProgressRing,
                            FluentIcon as FIF, CardWidget, IconWidget,
                            InfoBar, InfoBarPosition, StrongBodyLabel,
                            BodyLabel)
import database
from config import HEALTH_LEVELS, CYCLE_THRESHOLD


class HealthCard(CardWidget):
    def __init__(self, title, value, color, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)

        self.titleLabel = CaptionLabel(title)
        self.titleLabel.setStyleSheet("color: gray;")
        layout.addWidget(self.titleLabel)

        self.valueLabel = StrongBodyLabel(str(value))
        self.valueLabel.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.valueLabel)


class HealthPage(ScrollArea):
    battery_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HealthPage")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self._container = QVBoxLayout()
        self._container.setSpacing(16)
        self._container.setContentsMargins(24, 20, 24, 20)

        stats_card = HeaderCardWidget(self)
        stats_card.setTitle("总体概览")
        stats_layout = QGridLayout()
        stats_layout.setSpacing(16)
        stats_layout.setContentsMargins(20, 16, 20, 16)

        self.totalCard = HealthCard("电池总数", 0, "#0078d4")
        self.excellentCard = HealthCard("优", 0, "#1e8ae6")
        self.goodCard = HealthCard("良", 0, "#3ca03c")
        self.mediumCard = HealthCard("中", 0, "#dca01e")
        self.poorCard = HealthCard("差", 0, "#dc3232")
        self.pendingCard = HealthCard("待检测", 0, "#e65050")

        stats_layout.addWidget(self.totalCard, 0, 0)
        stats_layout.addWidget(self.excellentCard, 0, 1)
        stats_layout.addWidget(self.goodCard, 0, 2)
        stats_layout.addWidget(self.mediumCard, 1, 0)
        stats_layout.addWidget(self.poorCard, 1, 1)
        stats_layout.addWidget(self.pendingCard, 1, 2)
        stats_card.viewLayout.addLayout(stats_layout)
        self._container.addWidget(stats_card)

        detail_card = HeaderCardWidget(self)
        detail_card.setTitle("电池健康详情")
        self.detailTable = TableWidget()
        self.detailTable.setBorderVisible(True)
        self.detailTable.setBorderRadius(8)
        self.detailTable.setColumnCount(8)
        self.detailTable.setHorizontalHeaderLabels([
            "电池编号", "适配机型", "循环次数", "健康等级",
            "阈值", "距阈值", "状态", "备注"
        ])
        self.detailTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detailTable.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.detailTable.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        detail_card.viewLayout.addWidget(self.detailTable)
        self._container.addWidget(detail_card)

        pending_card = HeaderCardWidget(self)
        pending_card.setTitle("待检测名单（连续两次异常耗电）")
        self.pendingTable = TableWidget()
        self.pendingTable.setBorderVisible(True)
        self.pendingTable.setBorderRadius(8)
        self.pendingTable.setColumnCount(6)
        self.pendingTable.setHorizontalHeaderLabels([
            "电池编号", "适配机型", "循环次数", "健康等级", "状态", "备注"
        ])
        self.pendingTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pendingTable.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.pendingTable.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        pending_card.viewLayout.addWidget(self.pendingTable)
        self._container.addWidget(pending_card)

        w = QWidget()
        w.setLayout(self._container)
        self.setWidget(w)

    def _load_data(self):
        stats = database.get_battery_stats()
        self.totalCard.valueLabel.setText(str(stats["total"]))
        self.excellentCard.valueLabel.setText(str(stats["health_counts"].get("优", 0)))
        self.goodCard.valueLabel.setText(str(stats["health_counts"].get("良", 0)))
        self.mediumCard.valueLabel.setText(str(stats["health_counts"].get("中", 0)))
        self.poorCard.valueLabel.setText(str(stats["health_counts"].get("差", 0)))
        self.pendingCard.valueLabel.setText(str(stats["pending_check"]))

        batteries = database.get_all_batteries()
        self.detailTable.setRowCount(len(batteries))
        for row, b in enumerate(batteries):
            self.detailTable.setItem(row, 0, self._make_item(b["id"]))
            self.detailTable.setItem(row, 1, self._make_item(b["model"] or ""))
            cycle_item = self._make_item(str(b["cycle_count"]))
            if b["cycle_count"] > CYCLE_THRESHOLD:
                cycle_item.setForeground(QColor(220, 50, 50))
            self.detailTable.setItem(row, 2, cycle_item)
            health_item = self._make_item(b["health_level"])
            color_map = {"优": "#1e8ae6", "良": "#3ca03c", "中": "#dca01e", "差": "#dc3232"}
            if b["health_level"] in color_map:
                health_item.setForeground(QColor(color_map[b["health_level"]]))
            self.detailTable.setItem(row, 3, health_item)
            self.detailTable.setItem(row, 4, self._make_item(str(CYCLE_THRESHOLD)))
            remaining = CYCLE_THRESHOLD - b["cycle_count"]
            remain_item = self._make_item(str(remaining) if remaining >= 0 else f"已超 {abs(remaining)}")
            if remaining < 0:
                remain_item.setForeground(QColor(220, 50, 50))
            elif remaining < 50:
                remain_item.setForeground(QColor(220, 160, 30))
            self.detailTable.setItem(row, 5, remain_item)
            self.detailTable.setItem(row, 6, self._make_item(b["status"]))
            self.detailTable.setItem(row, 7, self._make_item(b["remark"] or ""))

        pending = database.get_pending_check_batteries()
        self.pendingTable.setRowCount(len(pending))
        for row, b in enumerate(pending):
            self.pendingTable.setItem(row, 0, self._make_item(b["id"]))
            self.pendingTable.setItem(row, 1, self._make_item(b["model"] or ""))
            self.pendingTable.setItem(row, 2, self._make_item(str(b["cycle_count"])))
            self.pendingTable.setItem(row, 3, self._make_item(b["health_level"]))
            self.pendingTable.setItem(row, 4, self._make_item(b["status"]))
            self.pendingTable.setItem(row, 5, self._make_item(b["remark"] or ""))

    def _make_item(self, text):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
