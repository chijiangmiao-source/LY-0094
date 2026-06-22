from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QHeaderView, QWidget,
                               QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import (ScrollArea, PushButton, TableWidget, SubtitleLabel,
                            HeaderCardWidget, FluentIcon as FIF, StrongBodyLabel,
                            BodyLabel, CaptionLabel, CardWidget)
import database
from config import CYCLE_THRESHOLD

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class AnomalyStatsPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AnomalyStatsPage")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        container = QVBoxLayout()
        container.setSpacing(16)
        container.setContentsMargins(24, 20, 24, 20)

        toolbar = QHBoxLayout()
        self.refreshBtn = PushButton(FIF.SYNC, "刷新数据")
        self.refreshBtn.clicked.connect(self._load_data)
        toolbar.addWidget(self.refreshBtn)
        toolbar.addStretch()
        container.addLayout(toolbar)

        charts_layout = QGridLayout()
        charts_layout.setSpacing(16)

        health_card = HeaderCardWidget(self)
        health_card.setTitle("健康等级分布")
        self.healthFigure, self.healthAxes = plt.subplots(figsize=(4, 3), tight_layout=True)
        self.healthCanvas = FigureCanvas(self.healthFigure)
        health_card.viewLayout.addWidget(self.healthCanvas)
        charts_layout.addWidget(health_card, 0, 0)

        status_card = HeaderCardWidget(self)
        status_card.setTitle("在库状态分布")
        self.statusFigure, self.statusAxes = plt.subplots(figsize=(4, 3), tight_layout=True)
        self.statusCanvas = FigureCanvas(self.statusFigure)
        status_card.viewLayout.addWidget(self.statusCanvas)
        charts_layout.addWidget(status_card, 0, 1)

        cycle_card = HeaderCardWidget(self)
        cycle_card.setTitle("循环次数分布")
        self.cycleFigure, self.cycleAxes = plt.subplots(figsize=(4, 3), tight_layout=True)
        self.cycleCanvas = FigureCanvas(self.cycleFigure)
        cycle_card.viewLayout.addWidget(self.cycleCanvas)
        charts_layout.addWidget(cycle_card, 1, 0)

        anomaly_card = HeaderCardWidget(self)
        anomaly_card.setTitle("异常耗电统计（按电池）")
        self.anomalyFigure, self.anomalyAxes = plt.subplots(figsize=(4, 3), tight_layout=True)
        self.anomalyCanvas = FigureCanvas(self.anomalyFigure)
        anomaly_card.viewLayout.addWidget(self.anomalyCanvas)
        charts_layout.addWidget(anomaly_card, 1, 1)

        container.addLayout(charts_layout)

        detail_card = HeaderCardWidget(self)
        detail_card.setTitle("异常耗电记录明细")
        self.anomalyTable = TableWidget()
        self.anomalyTable.setBorderVisible(True)
        self.anomalyTable.setBorderRadius(8)
        self.anomalyTable.setColumnCount(8)
        self.anomalyTable.setHorizontalHeaderLabels([
            "电池编号", "记录日期", "充电前电量", "充电后电量",
            "使用时长(分)", "操作人", "备注", "ID"
        ])
        self.anomalyTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.anomalyTable.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.anomalyTable.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.anomalyTable.hideColumn(7)
        detail_card.viewLayout.addWidget(self.anomalyTable)
        container.addWidget(detail_card)

        trend_card = HeaderCardWidget(self)
        trend_card.setTitle("异常趋势（按月）")
        self.trendFigure, self.trendAxes = plt.subplots(figsize=(9, 2.8), tight_layout=True)
        self.trendCanvas = FigureCanvas(self.trendFigure)
        trend_card.viewLayout.addWidget(self.trendCanvas)
        container.addWidget(trend_card)

        w = QWidget()
        w.setLayout(container)
        self.setWidget(w)

    def _load_data(self):
        self._draw_health_chart()
        self._draw_status_chart()
        self._draw_cycle_chart()
        self._draw_anomaly_chart()
        self._load_anomaly_table()
        self._draw_trend_chart()

    def _draw_health_chart(self):
        self.healthAxes.clear()
        stats = database.get_battery_stats()
        labels = []
        sizes = []
        colors_map = {"优": "#1e8ae6", "良": "#3ca03c", "中": "#dca01e", "差": "#dc3232"}
        colors = []
        for h in ["优", "良", "中", "差"]:
            count = stats["health_counts"].get(h, 0)
            if count > 0:
                labels.append(h)
                sizes.append(count)
                colors.append(colors_map[h])
        if sizes:
            wedges, texts, autotexts = self.healthAxes.pie(
                sizes, labels=labels, colors=colors, autopct='%1.0f%%',
                startangle=90, textprops={'fontsize': 10}
            )
        else:
            self.healthAxes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
        self.healthAxes.set_aspect('equal')
        self.healthCanvas.draw()

    def _draw_status_chart(self):
        self.statusAxes.clear()
        stats = database.get_battery_stats()
        labels = []
        sizes = []
        colors_list = ["#1e8ae6", "#3ca03c", "#dca01e", "#dc3232", "#8e44ad"]
        colors = []
        for i, (k, v) in enumerate(stats["status_counts"].items()):
            if v > 0:
                labels.append(k)
                sizes.append(v)
                colors.append(colors_list[i % len(colors_list)])
        if sizes:
            wedges, texts, autotexts = self.statusAxes.pie(
                sizes, labels=labels, colors=colors, autopct='%1.0f%%',
                startangle=90, textprops={'fontsize': 10}
            )
        else:
            self.statusAxes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
        self.statusAxes.set_aspect('equal')
        self.statusCanvas.draw()

    def _draw_cycle_chart(self):
        self.cycleAxes.clear()
        batteries = database.get_all_batteries()
        if batteries:
            df = pd.DataFrame([dict(b) for b in batteries])
            bins = [0, 100, 200, 300, 500, 1000]
            labels = ['0-100', '101-200', '201-300', '301-500', '500+']
            df['cycle_bin'] = pd.cut(df['cycle_count'], bins=bins, labels=labels, right=True, include_lowest=True)
            counts = df['cycle_bin'].value_counts().sort_index()
            bar_colors = ['#3ca03c', '#1e8ae6', '#dca01e', '#dc3232', '#8e44ad']
            counts.plot(kind='bar', ax=self.cycleAxes, color=bar_colors[:len(counts)], edgecolor='white')
            self.cycleAxes.set_xlabel('循环次数区间')
            self.cycleAxes.set_ylabel('电池数量')
            self.cycleAxes.tick_params(axis='x', rotation=0)
            for p in self.cycleAxes.patches:
                self.cycleAxes.annotate(
                    str(int(p.get_height())),
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=9
                )
        else:
            self.cycleAxes.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                               transform=self.cycleAxes.transAxes, fontsize=12)
        self.cycleCanvas.draw()

    def _draw_anomaly_chart(self):
        self.anomalyAxes.clear()
        records = database.get_all_charge_records()
        if records:
            df = pd.DataFrame([dict(r) for r in records])
            anomaly_df = df[df['is_anomaly'] == 1]
            if not anomaly_df.empty:
                counts = anomaly_df.groupby('battery_id').size().sort_values(ascending=False)
                bar_colors = ['#dc3232'] * len(counts)
                counts.plot(kind='barh', ax=self.anomalyAxes, color=bar_colors, edgecolor='white')
                self.anomalyAxes.set_xlabel('异常次数')
                self.anomalyAxes.set_ylabel('电池编号')
                for p in self.anomalyAxes.patches:
                    self.anomalyAxes.annotate(
                        str(int(p.get_width())),
                        (p.get_width(), p.get_y() + p.get_height() / 2.),
                        ha='left', va='center', fontsize=9
                    )
            else:
                self.anomalyAxes.text(0.5, 0.5, '暂无异常记录', ha='center', va='center',
                                     transform=self.anomalyAxes.transAxes, fontsize=12)
        else:
            self.anomalyAxes.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                                 transform=self.anomalyAxes.transAxes, fontsize=12)
        self.anomalyCanvas.draw()

    def _load_anomaly_table(self):
        records = database.get_anomaly_records()
        self.anomalyTable.setRowCount(len(records))
        for row, r in enumerate(records):
            self.anomalyTable.setItem(row, 0, self._make_item(r["battery_id"]))
            self.anomalyTable.setItem(row, 1, self._make_item(r["record_date"] or ""))
            self.anomalyTable.setItem(row, 2, self._make_item(f"{r['charge_before']}%"))
            self.anomalyTable.setItem(row, 3, self._make_item(f"{r['charge_after']}%"))
            self.anomalyTable.setItem(row, 4, self._make_item(str(r["usage_duration"] or 0)))
            self.anomalyTable.setItem(row, 5, self._make_item(r["operator"] or ""))
            self.anomalyTable.setItem(row, 6, self._make_item(r["remark"] or ""))
            self.anomalyTable.setItem(row, 7, self._make_item(str(r["id"])))

    def _draw_trend_chart(self):
        self.trendAxes.clear()
        records = database.get_all_charge_records()
        if records:
            df = pd.DataFrame([dict(r) for r in records])
            anomaly_df = df[df['is_anomaly'] == 1].copy()
            if not anomaly_df.empty:
                anomaly_df['month'] = anomaly_df['record_date'].str[:7]
                monthly = anomaly_df.groupby('month').size()
                monthly.plot(kind='line', ax=self.trendAxes, marker='o', color='#dc3232', linewidth=2)
                self.trendAxes.fill_between(monthly.index, monthly.values, alpha=0.2, color='#dc3232')
                self.trendAxes.set_xlabel('月份')
                self.trendAxes.set_ylabel('异常次数')
                self.trendAxes.tick_params(axis='x', rotation=45)
                for x, y in zip(monthly.index, monthly.values):
                    self.trendAxes.annotate(str(int(y)), (x, y), textcoords="offset points",
                                           xytext=(0, 5), ha='center', fontsize=9)
            else:
                self.trendAxes.text(0.5, 0.5, '暂无异常记录', ha='center', va='center',
                                   transform=self.trendAxes.transAxes, fontsize=12)
        else:
            self.trendAxes.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                               transform=self.trendAxes.transAxes, fontsize=12)
        self.trendCanvas.draw()

    def _make_item(self, text):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
