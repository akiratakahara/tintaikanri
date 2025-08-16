"""
Tkinterベース賃貸管理システム - PyQt6の代替版
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv
import os

class TkinterRentalSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("賃貸管理システム v2.0 - Tkinter Edition")
        self.root.geometry("1200x800")
        
        # データベース初期化
        self.init_database()
        
        # UI作成
        self.create_ui()
        
        # データ読み込み
        self.load_customers()
    
    def init_database(self):
        """データベース初期化"""
        try:
            from models import create_tables
            create_tables()
            print("データベースが初期化されました")
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
    
    def create_ui(self):
        """UI作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = tk.Label(main_frame, text="賃貸管理システム", 
                              font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=(0, 10))
        
        # タブ作成
        self.notebook = ttk.Notebook(main_frame)
        
        # ダッシュボードタブ
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📊 ダッシュボード")
        self.create_dashboard()
        
        # 顧客管理タブ
        self.customer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.customer_frame, text="👥 顧客管理")
        self.create_customer_tab()
        
        # 物件管理タブ
        self.property_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.property_frame, text="🏢 物件管理")
        self.create_property_tab()
        
        # 契約管理タブ
        self.contract_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.contract_frame, text="📝 契約管理")
        self.create_contract_tab()
        
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self.status_bar = tk.Label(self.root, text="準備完了", 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 現在時刻表示
        self.update_time()
    
    def create_dashboard(self):
        """ダッシュボード作成"""
        # スクロールフレーム
        canvas = tk.Canvas(self.dashboard_frame)
        scrollbar = ttk.Scrollbar(self.dashboard_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 統計情報
        stats_frame = ttk.LabelFrame(scrollable_frame, text="システム統計")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 統計データを取得して表示
        try:
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            # 顧客数
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]
            
            # 物件数
            cursor.execute("SELECT COUNT(*) FROM properties")
            property_count = cursor.fetchone()[0]
            
            # 契約数
            cursor.execute("SELECT COUNT(*) FROM tenant_contracts")
            contract_count = cursor.fetchone()[0]
            
            conn.close()
            
            stats_text = f"""
顧客数: {customer_count}
物件数: {property_count}
契約数: {contract_count}
最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            tk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(padx=10, pady=10)
            
        except Exception as e:
            tk.Label(stats_frame, text=f"統計データ取得エラー: {e}").pack(padx=10, pady=10)
        
        # アラート情報
        alert_frame = ttk.LabelFrame(scrollable_frame, text="重要なお知らせ")
        alert_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(alert_frame, text="現在、重要なアラートはありません。", 
                fg="green").pack(padx=10, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_customer_tab(self):
        """顧客管理タブ作成"""
        # 検索フレーム
        search_frame = ttk.Frame(self.customer_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="検索:").pack(side=tk.LEFT)
        self.customer_search_var = tk.StringVar()
        self.customer_search_var.trace('w', self.filter_customers)
        search_entry = tk.Entry(search_frame, textvariable=self.customer_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.customer_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="新規登録", 
                  command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="編集", 
                  command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="削除", 
                  command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新", 
                  command=self.load_customers).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="CSV出力", 
                  command=self.export_customers_csv).pack(side=tk.LEFT, padx=5)
        
        # 顧客一覧テーブル
        columns = ('ID', '顧客名', '種別', '電話番号', 'メール', '住所')
        self.customer_tree = ttk.Treeview(self.customer_frame, columns=columns, show='headings')
        
        for col in columns:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=100)
        
        # スクロールバー
        customer_scrollbar = ttk.Scrollbar(self.customer_frame, orient="vertical", 
                                          command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=customer_scrollbar.set)
        
        self.customer_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        customer_scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # ダブルクリックで編集
        self.customer_tree.bind('<Double-1>', lambda e: self.edit_customer())
    
    def create_property_tab(self):
        """物件管理タブ作成"""
        tk.Label(self.property_frame, text="物件管理機能は開発中です", 
                font=("Arial", 12)).pack(expand=True)
    
    def create_contract_tab(self):
        """契約管理タブ作成"""
        tk.Label(self.contract_frame, text="契約管理機能は開発中です", 
                font=("Arial", 12)).pack(expand=True)
    
    def load_customers(self):
        """顧客データを読み込み"""
        try:
            # 既存のアイテムをクリア
            for item in self.customer_tree.get_children():
                self.customer_tree.delete(item)
            
            # データベースから読み込み
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
            customers = cursor.fetchall()
            conn.close()
            
            # テーブルに追加
            for customer in customers:
                customer_type = "オーナー" if customer[2] == 'owner' else "テナント"
                values = (customer[0], customer[1], customer_type, 
                         customer[3] or '', customer[4] or '', customer[5] or '')
                self.customer_tree.insert('', 'end', values=values)
            
            self.status_bar.config(text=f"顧客データを読み込みました ({len(customers)}件)")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データ読み込みエラー: {e}")
    
    def filter_customers(self, *args):
        """顧客フィルタリング"""
        search_text = self.customer_search_var.get().lower()
        
        for item in self.customer_tree.get_children():
            values = self.customer_tree.item(item, 'values')
            if any(search_text in str(value).lower() for value in values):
                self.customer_tree.set(item, '#0', '')  # 表示
            else:
                self.customer_tree.detach(item)  # 非表示
        
        if search_text == '':
            self.load_customers()  # 検索テキストが空の場合は全て表示
    
    def add_customer(self):
        """顧客新規登録"""
        self.open_customer_dialog()
    
    def edit_customer(self):
        """顧客編集"""
        selection = self.customer_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集する顧客を選択してください")
            return
        
        item = selection[0]
        values = self.customer_tree.item(item, 'values')
        customer_id = values[0]
        
        self.open_customer_dialog(customer_id)
    
    def delete_customer(self):
        """顧客削除"""
        selection = self.customer_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除する顧客を選択してください")
            return
        
        item = selection[0]
        values = self.customer_tree.item(item, 'values')
        customer_name = values[1]
        customer_id = values[0]
        
        if messagebox.askyesno("確認", f"顧客「{customer_name}」を削除してもよろしいですか？"):
            try:
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "顧客を削除しました")
                self.load_customers()
                
            except Exception as e:
                messagebox.showerror("エラー", f"削除エラー: {e}")
    
    def open_customer_dialog(self, customer_id=None):
        """顧客登録・編集ダイアログ"""
        dialog = tk.Toplevel(self.root)
        dialog.title("顧客編集" if customer_id else "顧客新規登録")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 既存データの読み込み
        customer_data = None
        if customer_id:
            try:
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
                customer_data = cursor.fetchone()
                conn.close()
            except Exception as e:
                messagebox.showerror("エラー", f"データ読み込みエラー: {e}")
                dialog.destroy()
                return
        
        # フォームフィールド
        fields = {}
        
        # 顧客名
        tk.Label(dialog, text="顧客名 *:").pack(anchor='w', padx=10, pady=(10, 0))
        fields['name'] = tk.Entry(dialog, width=40)
        fields['name'].pack(padx=10, pady=(0, 10))
        
        # 顧客種別
        tk.Label(dialog, text="顧客種別:").pack(anchor='w', padx=10)
        fields['type'] = ttk.Combobox(dialog, values=["テナント", "オーナー"], width=37)
        fields['type'].pack(padx=10, pady=(0, 10))
        
        # 電話番号
        tk.Label(dialog, text="電話番号:").pack(anchor='w', padx=10)
        fields['phone'] = tk.Entry(dialog, width=40)
        fields['phone'].pack(padx=10, pady=(0, 10))
        
        # メールアドレス
        tk.Label(dialog, text="メールアドレス:").pack(anchor='w', padx=10)
        fields['email'] = tk.Entry(dialog, width=40)
        fields['email'].pack(padx=10, pady=(0, 10))
        
        # 住所
        tk.Label(dialog, text="住所:").pack(anchor='w', padx=10)
        fields['address'] = tk.Text(dialog, width=40, height=3)
        fields['address'].pack(padx=10, pady=(0, 10))
        
        # メモ
        tk.Label(dialog, text="メモ:").pack(anchor='w', padx=10)
        fields['memo'] = tk.Text(dialog, width=40, height=3)
        fields['memo'].pack(padx=10, pady=(0, 10))
        
        # 既存データをフィールドに設定
        if customer_data:
            fields['name'].insert(0, customer_data[1] or '')
            fields['type'].set("オーナー" if customer_data[2] == 'owner' else "テナント")
            fields['phone'].insert(0, customer_data[3] or '')
            fields['email'].insert(0, customer_data[4] or '')
            fields['address'].insert('1.0', customer_data[5] or '')
            fields['memo'].insert('1.0', customer_data[6] or '')
        else:
            fields['type'].set("テナント")
        
        # ボタンフレーム
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def save_customer():
            # バリデーション
            name = fields['name'].get().strip()
            if not name:
                messagebox.showwarning("警告", "顧客名を入力してください")
                return
            
            # データ保存
            try:
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()
                
                customer_type = 'owner' if fields['type'].get() == 'オーナー' else 'tenant'
                phone = fields['phone'].get().strip()
                email = fields['email'].get().strip()
                address = fields['address'].get('1.0', tk.END).strip()
                memo = fields['memo'].get('1.0', tk.END).strip()
                
                if customer_id:
                    # 更新
                    cursor.execute('''
                        UPDATE customers 
                        SET name=?, type=?, phone=?, email=?, address=?, memo=?, updated_at=CURRENT_TIMESTAMP 
                        WHERE id=?
                    ''', (name, customer_type, phone, email, address, memo, customer_id))
                else:
                    # 新規登録
                    cursor.execute('''
                        INSERT INTO customers (name, type, phone, email, address, memo) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, customer_type, phone, email, address, memo))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "顧客情報を保存しました")
                dialog.destroy()
                self.load_customers()
                
            except Exception as e:
                messagebox.showerror("エラー", f"保存エラー: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def export_customers_csv(self):
        """顧客データをCSVエクスポート"""
        try:
            file_path = filedialog.asksavefilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="CSVファイルの保存"
            )
            
            if file_path:
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
                customers = cursor.fetchall()
                conn.close()
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', '顧客名', '種別', '電話番号', 'メール', '住所', 'メモ', '作成日'])
                    
                    for customer in customers:
                        customer_type = "オーナー" if customer[2] == 'owner' else "テナント"
                        row = [customer[0], customer[1], customer_type, 
                              customer[3] or '', customer[4] or '', customer[5] or '',
                              customer[6] or '', customer[7] or '']
                        writer.writerow(row)
                
                messagebox.showinfo("成功", f"CSVファイルを出力しました:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("エラー", f"CSV出力エラー: {e}")
    
    def update_time(self):
        """時刻更新"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        self.root.title(f"賃貸管理システム v2.0 - {current_time}")
        self.root.after(1000, self.update_time)
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

def main():
    """メイン関数"""
    try:
        app = TkinterRentalSystem()
        app.run()
    except Exception as e:
        print(f"アプリケーション起動エラー: {e}")
        input("エラーが発生しました。Enterキーを押して終了してください。")

if __name__ == "__main__":
    main()