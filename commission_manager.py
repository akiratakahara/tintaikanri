"""
仲介手数料・広告宣伝費管理ウィジェット
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QTextEdit, QPushButton, QComboBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from utils import MessageHelper, FormatHelper

# マウスホイール無効化SpinBox
class NoWheelSpinBox(QSpinBox):
    """マウスホイールによる値変更を無効化したSpinBox"""
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """マウスホイールによる値変更を無効化したDoubleSpinBox"""
    def wheelEvent(self, event):
        event.ignore()

class CommissionCalculator(QWidget):
    """仲介手数料計算ウィジェット"""
    
    commission_updated = pyqtSignal(dict)  # 手数料が更新された時のシグナル
    
    def __init__(self, contract_data=None):
        super().__init__()
        self.contract_data = contract_data or {}
        self.init_ui()
        self.load_commission_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 基本情報表示
        info_group = QGroupBox("契約基本情報")
        info_layout = QFormLayout()
        
        self.rent_label = QLabel("0円")
        self.rent_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        self.contract_period_label = QLabel("-")
        
        info_layout.addRow("月額賃料:", self.rent_label)
        info_layout.addRow("契約期間:", self.contract_period_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 借主手数料設定
        tenant_group = QGroupBox("借主仲介手数料")
        tenant_layout = QFormLayout()
        
        # 月数指定（マウスホイール無効化版）
        self.tenant_months_spin = NoWheelDoubleSpinBox()
        self.tenant_months_spin.setRange(0, 10)
        self.tenant_months_spin.setSingleStep(0.1)
        self.tenant_months_spin.setDecimals(1)
        self.tenant_months_spin.setSuffix(" ヶ月")
        self.tenant_months_spin.valueChanged.connect(self.calculate_tenant_commission)

        # 金額指定（マウスホイール無効化版）
        self.tenant_amount_spin = NoWheelSpinBox()
        self.tenant_amount_spin.setRange(0, 9999999)
        self.tenant_amount_spin.setSuffix(" 円")
        self.tenant_amount_spin.valueChanged.connect(self.update_tenant_months_from_amount)
        
        # 計算タイプ選択
        self.tenant_calc_type_combo = QComboBox()
        self.tenant_calc_type_combo.addItems(["月数指定", "金額直接指定"])
        self.tenant_calc_type_combo.currentTextChanged.connect(self.on_tenant_calc_type_changed)
        
        tenant_layout.addRow("計算方法:", self.tenant_calc_type_combo)
        tenant_layout.addRow("手数料月数:", self.tenant_months_spin)
        tenant_layout.addRow("手数料金額:", self.tenant_amount_spin)
        
        tenant_group.setLayout(tenant_layout)
        layout.addWidget(tenant_group)
        
        # 貸主手数料設定
        landlord_group = QGroupBox("貸主仲介手数料")
        landlord_layout = QFormLayout()
        
        # 月数指定（マウスホイール無効化版）
        self.landlord_months_spin = NoWheelDoubleSpinBox()
        self.landlord_months_spin.setRange(0, 10)
        self.landlord_months_spin.setSingleStep(0.1)
        self.landlord_months_spin.setDecimals(1)
        self.landlord_months_spin.setSuffix(" ヶ月")
        self.landlord_months_spin.valueChanged.connect(self.calculate_landlord_commission)

        # 金額指定（マウスホイール無効化版）
        self.landlord_amount_spin = NoWheelSpinBox()
        self.landlord_amount_spin.setRange(0, 9999999)
        self.landlord_amount_spin.setSuffix(" 円")
        self.landlord_amount_spin.valueChanged.connect(self.update_landlord_months_from_amount)
        
        # 計算タイプ選択
        self.landlord_calc_type_combo = QComboBox()
        self.landlord_calc_type_combo.addItems(["月数指定", "金額直接指定"])
        self.landlord_calc_type_combo.currentTextChanged.connect(self.on_landlord_calc_type_changed)
        
        landlord_layout.addRow("計算方法:", self.landlord_calc_type_combo)
        landlord_layout.addRow("手数料月数:", self.landlord_months_spin)
        landlord_layout.addRow("手数料金額:", self.landlord_amount_spin)
        
        landlord_group.setLayout(landlord_layout)
        layout.addWidget(landlord_group)
        
        # 広告宣伝費設定
        ad_group = QGroupBox("広告宣伝費")
        ad_layout = QFormLayout()
        
        self.advertising_fee_spin = NoWheelSpinBox()
        self.advertising_fee_spin.setRange(0, 9999999)
        self.advertising_fee_spin.setSuffix(" 円")
        
        self.advertising_included_check = QCheckBox("仲介手数料に含む")
        
        # 広告費の種別
        self.ad_type_combo = QComboBox()
        self.ad_type_combo.addItems(["なし", "ポータルサイト掲載費", "看板・チラシ費用", "その他"])
        
        ad_layout.addRow("広告費種別:", self.ad_type_combo)
        ad_layout.addRow("広告宣伝費:", self.advertising_fee_spin)
        ad_layout.addRow("", self.advertising_included_check)
        
        ad_group.setLayout(ad_layout)
        layout.addWidget(ad_group)
        
        # 手数料備考
        notes_group = QGroupBox("手数料備考")
        notes_layout = QVBoxLayout()
        
        self.commission_notes_edit = QTextEdit()
        self.commission_notes_edit.setMaximumHeight(80)
        self.commission_notes_edit.setPlaceholderText("手数料に関する特記事項があれば記載...")
        
        notes_layout.addWidget(self.commission_notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # 計算結果表示
        summary_group = QGroupBox("手数料合計")
        summary_layout = QFormLayout()
        
        self.tenant_total_label = QLabel("0円")
        self.tenant_total_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
        
        self.landlord_total_label = QLabel("0円")
        self.landlord_total_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
        
        self.total_commission_label = QLabel("0円")
        self.total_commission_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 16px;")
        
        summary_layout.addRow("借主から受取:", self.tenant_total_label)
        summary_layout.addRow("貸主から受取:", self.landlord_total_label)
        summary_layout.addRow("手数料合計:", self.total_commission_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        self.setLayout(layout)
    
    def set_contract_data(self, contract_data):
        """契約データを設定"""
        self.contract_data = contract_data
        self.load_commission_data()
        
    def load_commission_data(self):
        """契約データから手数料情報を読み込み"""
        if not self.contract_data:
            return
        
        # 基本情報表示
        rent = self.contract_data.get('rent', 0)
        self.rent_label.setText(f"{rent:,}円")
        
        start_date = self.contract_data.get('start_date', '')
        end_date = self.contract_data.get('end_date', '')
        self.contract_period_label.setText(f"{start_date} ～ {end_date}")
        
        # 借主手数料
        tenant_months = self.contract_data.get('tenant_commission_months', 0)
        tenant_amount = self.contract_data.get('tenant_commission_amount', 0)
        
        self.tenant_months_spin.setValue(tenant_months)
        self.tenant_amount_spin.setValue(tenant_amount)
        
        # 貸主手数料
        landlord_months = self.contract_data.get('landlord_commission_months', 0)
        landlord_amount = self.contract_data.get('landlord_commission_amount', 0)
        
        self.landlord_months_spin.setValue(landlord_months)
        self.landlord_amount_spin.setValue(landlord_amount)
        
        # 広告宣伝費
        advertising_fee = self.contract_data.get('advertising_fee', 0)
        advertising_included = self.contract_data.get('advertising_fee_included', False)
        
        self.advertising_fee_spin.setValue(advertising_fee)
        self.advertising_included_check.setChecked(advertising_included)
        
        # 手数料備考
        commission_notes = self.contract_data.get('commission_notes', '')
        self.commission_notes_edit.setPlainText(commission_notes)
        
        self.update_summary()
    
    def calculate_tenant_commission(self):
        """借主手数料を計算（月数から金額）"""
        if self.tenant_calc_type_combo.currentText() == "月数指定":
            rent = self.contract_data.get('rent', 0)
            months = self.tenant_months_spin.value()
            amount = int(rent * months * 1.1)  # 消費税込み
            
            # 金額フィールドを更新（シグナルを一時的に無効化）
            self.tenant_amount_spin.blockSignals(True)
            self.tenant_amount_spin.setValue(amount)
            self.tenant_amount_spin.blockSignals(False)
            
            self.update_summary()
    
    def update_tenant_months_from_amount(self):
        """借主手数料を計算（金額から月数）"""
        if self.tenant_calc_type_combo.currentText() == "金額直接指定":
            rent = self.contract_data.get('rent', 0)
            if rent > 0:
                amount = self.tenant_amount_spin.value()
                months = amount / (rent * 1.1)  # 消費税を考慮
                
                # 月数フィールドを更新（シグナルを一時的に無効化）
                self.tenant_months_spin.blockSignals(True)
                self.tenant_months_spin.setValue(months)
                self.tenant_months_spin.blockSignals(False)
                
        self.update_summary()
    
    def calculate_landlord_commission(self):
        """貸主手数料を計算（月数から金額）"""
        if self.landlord_calc_type_combo.currentText() == "月数指定":
            rent = self.contract_data.get('rent', 0)
            months = self.landlord_months_spin.value()
            amount = int(rent * months * 1.1)  # 消費税込み
            
            # 金額フィールドを更新（シグナルを一時的に無効化）
            self.landlord_amount_spin.blockSignals(True)
            self.landlord_amount_spin.setValue(amount)
            self.landlord_amount_spin.blockSignals(False)
            
            self.update_summary()
    
    def update_landlord_months_from_amount(self):
        """貸主手数料を計算（金額から月数）"""
        if self.landlord_calc_type_combo.currentText() == "金額直接指定":
            rent = self.contract_data.get('rent', 0)
            if rent > 0:
                amount = self.landlord_amount_spin.value()
                months = amount / (rent * 1.1)  # 消費税を考慮
                
                # 月数フィールドを更新（シグナルを一時的に無効化）
                self.landlord_months_spin.blockSignals(True)
                self.landlord_months_spin.setValue(months)
                self.landlord_months_spin.blockSignals(False)
                
        self.update_summary()
    
    def on_tenant_calc_type_changed(self, calc_type):
        """借主計算タイプ変更時の処理"""
        if calc_type == "月数指定":
            self.tenant_months_spin.setEnabled(True)
            self.tenant_amount_spin.setEnabled(False)
            self.calculate_tenant_commission()
        else:
            self.tenant_months_spin.setEnabled(False)
            self.tenant_amount_spin.setEnabled(True)
            self.update_tenant_months_from_amount()
    
    def on_landlord_calc_type_changed(self, calc_type):
        """貸主計算タイプ変更時の処理"""
        if calc_type == "月数指定":
            self.landlord_months_spin.setEnabled(True)
            self.landlord_amount_spin.setEnabled(False)
            self.calculate_landlord_commission()
        else:
            self.landlord_months_spin.setEnabled(False)
            self.landlord_amount_spin.setEnabled(True)
            self.update_landlord_months_from_amount()
    
    def update_summary(self):
        """合計金額を更新"""
        tenant_total = self.tenant_amount_spin.value()
        landlord_total = self.landlord_amount_spin.value()
        advertising_fee = self.advertising_fee_spin.value()
        
        # 広告費が含まれていない場合は合計に加算
        if not self.advertising_included_check.isChecked():
            total = tenant_total + landlord_total + advertising_fee
        else:
            total = tenant_total + landlord_total
        
        self.tenant_total_label.setText(f"{tenant_total:,}円")
        self.landlord_total_label.setText(f"{landlord_total:,}円")
        self.total_commission_label.setText(f"{total:,}円")
        
        # シグナルを発生
        commission_data = self.get_commission_data()
        self.commission_updated.emit(commission_data)
    
    def get_commission_data(self):
        """手数料データを取得"""
        return {
            'tenant_commission_months': self.tenant_months_spin.value(),
            'landlord_commission_months': self.landlord_months_spin.value(),
            'tenant_commission_amount': self.tenant_amount_spin.value(),
            'landlord_commission_amount': self.landlord_amount_spin.value(),
            'advertising_fee': self.advertising_fee_spin.value(),
            'advertising_fee_included': self.advertising_included_check.isChecked(),
            'commission_notes': self.commission_notes_edit.toPlainText().strip()
        }
    
    def set_commission_data(self, data):
        """手数料データを設定"""
        self.tenant_months_spin.setValue(data.get('tenant_commission_months', 0))
        self.landlord_months_spin.setValue(data.get('landlord_commission_months', 0))
        self.tenant_amount_spin.setValue(data.get('tenant_commission_amount', 0))
        self.landlord_amount_spin.setValue(data.get('landlord_commission_amount', 0))
        self.advertising_fee_spin.setValue(data.get('advertising_fee', 0))
        self.advertising_included_check.setChecked(data.get('advertising_fee_included', False))
        self.commission_notes_edit.setPlainText(data.get('commission_notes', ''))
        
        self.update_summary()

class CommissionManager(QWidget):
    """手数料管理メインウィジェット"""
    
    def __init__(self, contract_id=None):
        super().__init__()
        self.contract_id = contract_id
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 手数料計算機
        self.calculator = CommissionCalculator()
        layout.addWidget(self.calculator)
        
        # 保存ボタン
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("手数料情報を保存")
        save_btn.clicked.connect(self.save_commission_data)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_contract_data(self, contract_data):
        """契約データを設定"""
        self.contract_data = contract_data
        self.contract_id = contract_data.get('id')
        self.calculator.set_contract_data(contract_data)
    
    def save_commission_data(self):
        """手数料データを保存"""
        if not self.contract_id:
            MessageHelper.show_warning(self, "契約IDが設定されていません")
            return
        
        try:
            commission_data = self.calculator.get_commission_data()
            
            # データベースに保存
            from models import TenantContract
            TenantContract.update_commission(self.contract_id, commission_data)
            
            MessageHelper.show_success(self, "手数料情報を保存しました")
            
        except Exception as e:
            MessageHelper.show_error(self, f"手数料情報の保存中にエラーが発生しました: {str(e)}")
    
    def get_commission_data(self):
        """手数料データを取得"""
        return self.calculator.get_commission_data()