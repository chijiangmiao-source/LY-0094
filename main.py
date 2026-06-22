import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import database
import db_operations
import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WeddingScriptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("婚礼主持词版本校对记录器")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)
        
        database.init_database()
        
        self.current_script_id = None
        self.setup_ui()
        self.load_script_list()
    
    def setup_ui(self):
        style = ttkb.Style(theme='cosmo')
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame, width=350)
        left_frame.pack(side=LEFT, fill=BOTH, padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
    
    def setup_left_panel(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="主持词列表", font=('Microsoft YaHei', 16, 'bold'))
        title_label.pack(side=LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(header_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=RIGHT, padx=(10, 0))
        
        search_btn = ttk.Button(header_frame, text="搜索", command=self.search_scripts)
        search_btn.pack(side=RIGHT)
        
        filter_frame = ttk.LabelFrame(parent, text="筛选条件")
        filter_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="主持人:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.host_combobox = ttk.Combobox(filter_frame, width=15)
        self.host_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_host_names()
        
        ttk.Label(filter_frame, text="定稿状态:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.status_combobox = ttk.Combobox(filter_frame, width=10, values=['', '未定稿', '已定稿'])
        self.status_combobox.grid(row=0, column=3, padx=5, pady=5)
        
        filter_btn = ttk.Button(filter_frame, text="筛选", command=self.filter_scripts)
        filter_btn.grid(row=0, column=4, padx=5, pady=5)
        
        clear_btn = ttk.Button(filter_frame, text="清空", command=self.clear_filter)
        clear_btn.grid(row=0, column=5, padx=5, pady=5)
        
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('id', 'record_no', 'bride', 'groom', 'date', 'host', 'version', 'round', 'status')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        self.tree.heading('record_no', text='记录编号')
        self.tree.heading('bride', text='新娘姓名')
        self.tree.heading('groom', text='新郎姓名')
        self.tree.heading('date', text='婚礼日期')
        self.tree.heading('host', text='主持人')
        self.tree.heading('version', text='版本号')
        self.tree.heading('round', text='反馈轮次')
        self.tree.heading('status', text='定稿状态')
        
        self.tree.column('id', width=0, stretch=NO)
        self.tree.column('record_no', width=100)
        self.tree.column('bride', width=70)
        self.tree.column('groom', width=70)
        self.tree.column('date', width=80)
        self.tree.column('host', width=70)
        self.tree.column('version', width=60)
        self.tree.column('round', width=60)
        self.tree.column('status', width=60)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_script_select)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        self.add_btn = ttk.Button(btn_frame, text="新增记录", command=self.open_add_dialog)
        self.add_btn.pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
        
        self.edit_btn = ttk.Button(btn_frame, text="编辑记录", command=self.open_edit_dialog, state=DISABLED)
        self.edit_btn.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.delete_btn = ttk.Button(btn_frame, text="删除记录", command=self.delete_script, state=DISABLED)
        self.delete_btn.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.export_btn = ttk.Button(btn_frame, text="导出报表", command=self.export_report)
        self.export_btn.pack(side=LEFT, padx=(5, 0), fill=X, expand=True)
    
    def setup_right_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=BOTH, expand=True)
        
        detail_frame = ttk.Frame(notebook)
        notebook.add(detail_frame, text="详情")
        
        change_frame = ttk.Frame(notebook)
        notebook.add(change_frame, text="变更记录")
        
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="统计分析")
        
        self.setup_detail_panel(detail_frame)
        self.setup_change_panel(change_frame)
        self.setup_stats_panel(stats_frame)
    
    def setup_detail_panel(self, parent):
        detail_frame = ttk.LabelFrame(parent, text="主持词详情")
        detail_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        fields = [
            ('记录编号', 'record_no'),
            ('新娘姓名', 'bride_name'),
            ('新郎姓名', 'groom_name'),
            ('婚礼日期', 'wedding_date'),
            ('主持人', 'host_name'),
            ('当前版本', 'current_version'),
            ('反馈轮次', 'feedback_round'),
            ('定稿状态', 'finalized_status'),
            ('备注', 'remarks')
        ]
        
        self.detail_vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(detail_frame, text=f"{label}:").grid(row=i, column=0, padx=10, pady=8, sticky=W)
            var = tk.StringVar()
            self.detail_vars[key] = var
            if key == 'remarks':
                text = ttk.Label(detail_frame, textvariable=var, wraplength=500, justify=LEFT)
                text.grid(row=i, column=1, padx=10, pady=8, sticky=W)
            else:
                ttk.Label(detail_frame, textvariable=var).grid(row=i, column=1, padx=10, pady=8, sticky=W)
        
        no_data_label = ttk.Label(detail_frame, text="请选择一条主持词记录查看详情", font=('Microsoft YaHei', 14))
        no_data_label.grid(row=0, column=0, columnspan=2, padx=20, pady=100)
        self.no_data_label = no_data_label
    
    def setup_change_panel(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, padx=10, pady=10)
        
        self.add_change_btn = ttk.Button(btn_frame, text="新增变更记录", command=self.open_add_change_dialog, state=DISABLED)
        self.add_change_btn.pack(side=LEFT)
        
        self.delete_change_btn = ttk.Button(btn_frame, text="删除变更记录", command=self.delete_selected_change, state=DISABLED)
        self.delete_change_btn.pack(side=LEFT, padx=10)
        
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True, padx=10)
        
        columns = ('id', 'modify_date', 'paragraph', 'reason', 'source', 'adopted')
        self.change_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        self.change_tree.heading('modify_date', text='修改日期')
        self.change_tree.heading('paragraph', text='修改段落')
        self.change_tree.heading('reason', text='修改原因')
        self.change_tree.heading('source', text='反馈来源')
        self.change_tree.heading('adopted', text='是否采纳')
        
        self.change_tree.column('id', width=0, stretch=NO)
        self.change_tree.column('modify_date', width=150)
        self.change_tree.column('paragraph', width=120)
        self.change_tree.column('reason', width=150)
        self.change_tree.column('source', width=100)
        self.change_tree.column('adopted', width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.change_tree.yview)
        self.change_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.change_tree.pack(fill=BOTH, expand=True)
        
        self.change_tree.bind('<<TreeviewSelect>>', self.on_change_select)
    
    def setup_stats_panel(self, parent):
        overview_frame = ttk.LabelFrame(parent, text="概览统计")
        overview_frame.pack(fill=X, padx=10, pady=10)
        
        stats = db_operations.get_stats_overview()
        stat_items = [
            ('主持总数', stats['total']),
            ('已定稿', stats['finalized']),
            ('平均反馈轮次', stats['avg_round']),
            ('变更记录总数', stats['total_changes'])
        ]
        
        for i, (label, value) in enumerate(stat_items):
            frame = ttk.Frame(overview_frame)
            frame.pack(side=LEFT, padx=20, pady=10)
            ttk.Label(frame, text=label, font=('Microsoft YaHei', 10)).pack()
            ttk.Label(frame, text=str(value), font=('Microsoft YaHei', 20, 'bold')).pack()
        
        chart_frame = ttk.LabelFrame(parent, text="统计图表")
        chart_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        version_stats = db_operations.get_version_stats()
        if version_stats:
            versions = [str(v[0]) for v in version_stats]
            counts = [v[1] for v in version_stats]
            sns.barplot(x=versions, y=counts, ax=ax1)
            ax1.set_title('版本分布')
            ax1.set_xlabel('版本号')
            ax1.set_ylabel('数量')
        
        reason_stats = db_operations.get_change_reason_stats()
        if reason_stats:
            reasons = [r[0][:8] if len(r[0]) > 8 else r[0] for r in reason_stats]
            counts = [r[1] for r in reason_stats]
            sns.barplot(x=counts, y=reasons, ax=ax2, orient='h')
            ax2.set_title('修改原因TOP10')
            ax2.set_xlabel('数量')
            ax2.set_ylabel('原因')
        
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        high_freq_frame = ttk.LabelFrame(parent, text="高频问题（出现≥3次）")
        high_freq_frame.pack(fill=X, padx=10, pady=10)
        
        high_freq_issues = db_operations.get_high_freq_issues()
        high_freq_issues = [i for i in high_freq_issues if i[1] >= 3]
        
        if high_freq_issues:
            columns = ('issue', 'count', 'first', 'last')
            tree = ttk.Treeview(high_freq_frame, columns=columns, show='headings', height=5)
            tree.heading('issue', text='问题描述')
            tree.heading('count', text='出现次数')
            tree.heading('first', text='首次出现')
            tree.heading('last', text='最近出现')
            
            tree.column('issue', width=250)
            tree.column('count', width=80)
            tree.column('first', width=120)
            tree.column('last', width=120)
            
            for issue in high_freq_issues:
                tree.insert('', END, values=(issue[0], issue[1], issue[2], issue[3]))
            
            tree.pack(fill=X)
        else:
            ttk.Label(high_freq_frame, text="暂无高频问题").pack(pady=10)
    
    def load_script_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        scripts = db_operations.get_all_host_scripts()
        for script in scripts:
            self.tree.insert('', END, values=(script[0], script[1], script[2], script[3], script[4], 
                                              script[5], script[6], script[7], script[8]))
    
    def load_host_names(self):
        hosts = db_operations.get_host_names()
        host_list = [''] + [h[0] for h in hosts]
        self.host_combobox['values'] = host_list
    
    def on_script_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            script_id = item['values'][0]
            self.current_script_id = script_id
            self.load_script_detail(script_id)
            self.load_change_records(script_id)
            
            self.edit_btn.config(state=NORMAL)
            self.delete_btn.config(state=NORMAL)
            self.add_change_btn.config(state=NORMAL)
            
            script = db_operations.get_host_script_by_id(script_id)
            if script and script[8] == '已定稿':
                self.add_change_btn.config(state=DISABLED)
        else:
            self.current_script_id = None
            self.edit_btn.config(state=DISABLED)
            self.delete_btn.config(state=DISABLED)
            self.add_change_btn.config(state=DISABLED)
    
    def on_change_select(self, event):
        selection = self.change_tree.selection()
        if selection:
            self.delete_change_btn.config(state=NORMAL)
        else:
            self.delete_change_btn.config(state=DISABLED)
    
    def load_script_detail(self, script_id):
        script = db_operations.get_host_script_by_id(script_id)
        if script:
            self.no_data_label.grid_remove()
            keys = ['record_no', 'bride_name', 'groom_name', 'wedding_date', 'host_name', 
                    'current_version', 'feedback_round', 'finalized_status', 'remarks']
            for i, key in enumerate(keys):
                self.detail_vars[key].set(str(script[i + 1]))
    
    def load_change_records(self, script_id):
        for item in self.change_tree.get_children():
            self.change_tree.delete(item)
        
        records = db_operations.get_change_records_by_script_id(script_id)
        for record in records:
            adopted = '是' if record[6] == 1 else '否'
            self.change_tree.insert('', END, values=(record[0], record[2], record[3], 
                                                      record[4], record[5], adopted))
    
    def search_scripts(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            self.load_script_list()
            return
        
        scripts = db_operations.search_host_scripts(keyword)
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for script in scripts:
            self.tree.insert('', END, values=(script[0], script[1], script[2], script[3], script[4], 
                                              script[5], script[6], script[7], script[8]))
    
    def filter_scripts(self):
        host_name = self.host_combobox.get() if self.host_combobox.get() else None
        status = self.status_combobox.get() if self.status_combobox.get() else None
        
        scripts = db_operations.filter_host_scripts(host_name, status)
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for script in scripts:
            self.tree.insert('', END, values=(script[0], script[1], script[2], script[3], script[4], 
                                              script[5], script[6], script[7], script[8]))
    
    def clear_filter(self):
        self.host_combobox.set('')
        self.status_combobox.set('')
        self.search_var.set('')
        self.load_script_list()
    
    def open_add_dialog(self):
        dialog = ScriptDialog(self.root, self)
        self.root.wait_window(dialog.top)
    
    def open_edit_dialog(self):
        if self.current_script_id:
            dialog = ScriptDialog(self.root, self, self.current_script_id)
            self.root.wait_window(dialog.top)
    
    def delete_script(self):
        if self.current_script_id:
            if messagebox.askyesno("确认删除", "确定要删除这条主持词记录吗？"):
                success, error = db_operations.delete_host_script(self.current_script_id)
                if success:
                    messagebox.showinfo("成功", "删除成功")
                    self.load_script_list()
                    self.current_script_id = None
                    self.edit_btn.config(state=DISABLED)
                    self.delete_btn.config(state=DISABLED)
                    self.add_change_btn.config(state=DISABLED)
                    self.no_data_label.grid()
                else:
                    messagebox.showerror("错误", f"删除失败: {error}")
    
    def open_add_change_dialog(self):
        if self.current_script_id:
            script = db_operations.get_host_script_by_id(self.current_script_id)
            if script and script[8] == '已定稿':
                messagebox.showwarning("警告", "该主持词已定稿，无法新增变更记录")
                return
            
            dialog = ChangeRecordDialog(self.root, self, self.current_script_id)
            self.root.wait_window(dialog.top)
    
    def delete_selected_change(self):
        selection = self.change_tree.selection()
        if selection:
            item = self.change_tree.item(selection[0])
            record_id = item['values'][0]
            
            if messagebox.askyesno("确认删除", "确定要删除这条变更记录吗？"):
                success, error = db_operations.delete_change_record(record_id)
                if success:
                    messagebox.showinfo("成功", "删除成功")
                    self.load_change_records(self.current_script_id)
                else:
                    messagebox.showerror("错误", f"删除失败: {error}")
    
    def export_report(self):
        wb = openpyxl.Workbook()
        
        ws1 = wb.active
        ws1.title = "主持词列表"
        headers1 = ['记录编号', '新娘姓名', '新郎姓名', '婚礼日期', '主持人', 
                    '当前版本', '反馈轮次', '定稿状态', '备注', '更新时间']
        for i, header in enumerate(headers1):
            cell = ws1.cell(row=1, column=i + 1, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.font.color = openpyxl.styles.colors.WHITE
        
        scripts = db_operations.get_all_host_scripts()
        for row_idx, script in enumerate(scripts, start=2):
            for col_idx, value in enumerate(script[1:], start=1):
                ws1.cell(row=row_idx, column=col_idx, value=value)
        
        ws2 = wb.create_sheet(title="变更记录")
        headers2 = ['主持词编号', '修改日期', '修改段落', '修改原因', '反馈来源', '是否采纳']
        for i, header in enumerate(headers2):
            cell = ws2.cell(row=1, column=i + 1, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.font.color = openpyxl.styles.colors.WHITE
        
        all_changes = []
        for script in scripts:
            changes = db_operations.get_change_records_by_script_id(script[0])
            for change in changes:
                all_changes.append((script[1], change[2], change[3], change[4], change[5], '是' if change[6] == 1 else '否'))
        
        for row_idx, change in enumerate(all_changes, start=2):
            for col_idx, value in enumerate(change, start=1):
                ws2.cell(row=row_idx, column=col_idx, value=value)
        
        ws3 = wb.create_sheet(title="高频问题")
        headers3 = ['问题描述', '出现次数', '首次出现', '最近出现']
        for i, header in enumerate(headers3):
            cell = ws3.cell(row=1, column=i + 1, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.font.color = openpyxl.styles.colors.WHITE
        
        high_freq = db_operations.get_high_freq_issues()
        high_freq = [i for i in high_freq if i[1] >= 3]
        for row_idx, issue in enumerate(high_freq, start=2):
            for col_idx, value in enumerate(issue, start=1):
                ws3.cell(row=row_idx, column=col_idx, value=value)
        
        today = datetime.datetime.now().strftime('%Y%m%d')
        filename = f'主持词报表_{today}.xlsx'
        wb.save(filename)
        messagebox.showinfo("成功", f"报表已导出为: {filename}")

class ScriptDialog:
    def __init__(self, parent, app, script_id=None):
        self.app = app
        self.script_id = script_id
        
        self.top = ttk.Toplevel(parent)
        self.top.title("编辑主持词" if script_id else "新增主持词")
        self.top.geometry("500x450")
        self.top.resizable(False, False)
        self.top.grab_set()
        
        frame = ttk.LabelFrame(self.top, text="主持词信息")
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        fields = [
            ('新娘姓名', 'bride_name', True),
            ('新郎姓名', 'groom_name', True),
            ('婚礼日期', 'wedding_date', True),
            ('主持人', 'host_name', True),
            ('当前版本', 'current_version', False),
            ('反馈轮次', 'feedback_round', False),
            ('定稿状态', 'finalized_status', False),
            ('备注', 'remarks', False)
        ]
        
        self.entries = {}
        self.vars = {}
        
        for i, (label, key, required) in enumerate(fields):
            ttk.Label(frame, text=f"{label}{'*' if required else ''}:").grid(row=i, column=0, padx=10, pady=10, sticky=W)
            
            if key == 'current_version':
                var = tk.StringVar(value='1.0')
                entry = ttk.Entry(frame, textvariable=var, width=30)
            elif key == 'feedback_round':
                var = tk.StringVar(value='0')
                entry = ttk.Entry(frame, textvariable=var, width=30)
            elif key == 'finalized_status':
                var = tk.StringVar(value='未定稿')
                entry = ttk.Combobox(frame, textvariable=var, values=['未定稿', '已定稿'], width=27)
            elif key == 'remarks':
                var = tk.StringVar()
                entry = ttk.Text(frame, width=30, height=3)
                entry.grid(row=i, column=1, padx=10, pady=10)
                self.entries[key] = entry
                self.vars[key] = var
                continue
            else:
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var, width=30)
            
            entry.grid(row=i, column=1, padx=10, pady=10)
            self.entries[key] = entry
            self.vars[key] = var
        
        if script_id:
            script = db_operations.get_host_script_by_id(script_id)
            if script:
                keys = ['bride_name', 'groom_name', 'wedding_date', 'host_name', 
                        'current_version', 'feedback_round', 'finalized_status']
                for i, key in enumerate(keys):
                    self.vars[key].set(str(script[i + 2]))
                self.entries['remarks'].insert('1.0', script[10] if script[10] else '')
        
        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=LEFT, padx=20)
        ttk.Button(btn_frame, text="取消", command=self.top.destroy).pack(side=RIGHT, padx=20)
    
    def save(self):
        bride_name = self.vars['bride_name'].get().strip()
        groom_name = self.vars['groom_name'].get().strip()
        wedding_date = self.vars['wedding_date'].get().strip()
        host_name = self.vars['host_name'].get().strip()
        
        try:
            current_version = float(self.vars['current_version'].get().strip())
        except ValueError:
            messagebox.showerror("错误", "版本号必须为数字")
            return
        
        try:
            feedback_round = int(self.vars['feedback_round'].get().strip())
        except ValueError:
            messagebox.showerror("错误", "反馈轮次必须为整数")
            return
        
        finalized_status = self.vars['finalized_status'].get()
        remarks = self.entries['remarks'].get('1.0', tk.END).strip()
        
        if not bride_name or not groom_name or not wedding_date or not host_name:
            messagebox.showerror("错误", "请填写必填字段")
            return
        
        if self.script_id:
            original_script = db_operations.get_host_script_by_id(self.script_id)
            if original_script and original_script[8] == '已定稿' and finalized_status != '已定稿':
                messagebox.showerror("错误", "已定稿的主持词不能修改为未定稿")
                return
            
            if current_version < original_script[6]:
                messagebox.showerror("错误", "版本号必须大于等于当前版本")
                return
            
            if feedback_round > 0:
                change_count = db_operations.get_change_record_count(self.script_id)
                if change_count == 0:
                    messagebox.showerror("错误", "反馈轮次大于0时，必须至少有一条变更记录")
                    return
            
            if db_operations.check_duplicate(bride_name, groom_name, wedding_date, self.script_id):
                messagebox.showerror("错误", "同一新人姓名与婚礼日期组合只能创建一份主持词")
                return
            
            success, error = db_operations.update_host_script(
                self.script_id, bride_name, groom_name, wedding_date, host_name,
                current_version, feedback_round, finalized_status, remarks
            )
        else:
            if db_operations.check_duplicate(bride_name, groom_name, wedding_date):
                messagebox.showerror("错误", "同一新人姓名与婚礼日期组合只能创建一份主持词")
                return
            
            success, error = db_operations.add_host_script(
                bride_name, groom_name, wedding_date, host_name,
                current_version, feedback_round, finalized_status, remarks
            )
        
        if success:
            messagebox.showinfo("成功", "保存成功")
            self.app.load_script_list()
            self.app.load_host_names()
            self.top.destroy()
        else:
            messagebox.showerror("错误", f"保存失败: {error}")

class ChangeRecordDialog:
    def __init__(self, parent, app, script_id):
        self.app = app
        self.script_id = script_id
        
        self.top = ttk.Toplevel(parent)
        self.top.title("新增变更记录")
        self.top.geometry("500x400")
        self.top.resizable(False, False)
        self.top.grab_set()
        
        frame = ttk.LabelFrame(self.top, text="变更记录信息")
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="修改段落*:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.paragraph_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.paragraph_var, width=40).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(frame, text="修改原因*:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.reason_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.reason_var, width=40).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(frame, text="反馈来源:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        self.source_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self.source_var, values=['客户', '策划师', '主持人', '其他'], width=37).grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(frame, text="是否采纳:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        self.adopted_var = tk.IntVar(value=1)
        ttk.Radiobutton(frame, text="是", variable=self.adopted_var, value=1).grid(row=3, column=1, padx=10, pady=10, sticky=W)
        ttk.Radiobutton(frame, text="否", variable=self.adopted_var, value=0).grid(row=3, column=1, padx=60, pady=10, sticky=W)
        
        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=LEFT, padx=20)
        ttk.Button(btn_frame, text="取消", command=self.top.destroy).pack(side=RIGHT, padx=20)
    
    def save(self):
        modify_paragraph = self.paragraph_var.get().strip()
        modify_reason = self.reason_var.get().strip()
        feedback_source = self.source_var.get().strip()
        is_adopted = self.adopted_var.get()
        
        if not modify_paragraph or not modify_reason:
            messagebox.showerror("错误", "请填写必填字段")
            return
        
        success, error = db_operations.add_change_record(
            self.script_id, modify_paragraph, modify_reason, feedback_source, is_adopted
        )
        
        if success:
            script = db_operations.get_host_script_by_id(self.script_id)
            if script:
                new_version = round(script[6] + 0.1, 1)
                new_round = script[7] + 1
                db_operations.update_host_script(
                    self.script_id, script[2], script[3], script[4], script[5],
                    new_version, new_round, script[8], script[10]
                )
            
            messagebox.showinfo("成功", "保存成功")
            self.app.load_script_list()
            self.app.load_change_records(self.script_id)
            self.top.destroy()
        else:
            messagebox.showerror("错误", f"保存失败: {error}")

if __name__ == "__main__":
    root = ttkb.Window(themename='cosmo')
    app = WeddingScriptApp(root)
    root.mainloop()