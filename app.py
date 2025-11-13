from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import webbrowser

from database import Database
from security import Security
from payment_handler import payment_system
from admin import AdminScreen

# Set mobile-friendly window size
Window.size = (360, 640)

# Global database instance to be initialized in the App class
db = None

class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Check if user is already logged in
        if hasattr(App.get_running_app(), 'user_id'):
            App.get_running_app().root.current = 'home'
        else:
            self.show_login()
    def show_login(self):
        self.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # Header
        header = Label(
            text='💰 Investment App',
            font_size='24sp',
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)
        
        # Phone Input
        self.phone_input = TextInput(
            hint_text='Phone Number (10 digits)',
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.phone_input)
        
        # Security Code Input
        self.security_input = TextInput(
            hint_text='Security Code (6 digits)',
            password=True,
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.security_input)
        
        # Login Button
        login_btn = Button(
            text='Login',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.86, 1)
        )
        login_btn.bind(on_press=self.login)
        layout.add_widget(login_btn)
        
        # Register Button
        register_btn = Button(
            text='New User? Register',
            size_hint_y=None,
            height=40,
            background_color=(0.4, 0.4, 0.4, 1)
        )
        register_btn.bind(on_press=lambda x: self.show_register())
        layout.add_widget(register_btn)
        
        # Customer Care
        care_label = Label(
            text='Customer Care: +91-9876543210',
            font_size='12sp',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(care_label)
        
        # Add admin access button at the bottom
        admin_btn = Button(
            text='Admin Access',
            size_hint_y=None,
            height=40,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        admin_btn.bind(on_press=lambda x: self.go_to_admin())
        layout.add_widget(admin_btn)
        
        self.add_widget(layout)
    
    def show_register(self):
        # ... existing register code ...
        # This method is large, so I'm omitting the body for brevity.
        self.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # Header
        header = Label(
            text='📝 Register',
            font_size='24sp',
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)
        
        # Phone Input
        self.reg_phone = TextInput(
            hint_text='Phone Number (10 digits)',
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.reg_phone)
        
        # Send OTP Button
        self.send_otp_btn = Button(
            text='Send OTP & Security Code',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.send_otp_btn.bind(on_press=self.send_otp)
        layout.add_widget(self.send_otp_btn)
        
        # OTP Section (initially hidden)
        self.otp_section = BoxLayout(orientation='vertical', spacing=10)
        
        otp_info = Label(
            text='OTP & Security Code sent via SMS',
            font_size='12sp',
            size_hint_y=None,
            height=30
        )
        self.otp_section.add_widget(otp_info)
        
        self.otp_input = TextInput(
            hint_text='Enter OTP (6 digits)',
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.otp_section.add_widget(self.otp_input)
        
        self.reg_security = TextInput(
            hint_text='Enter Security Code from SMS',
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.otp_section.add_widget(self.reg_security)
        
        self.referral_input = TextInput(
            hint_text='Referral Code (Optional)',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.otp_section.add_widget(self.referral_input)
        
        layout.add_widget(self.otp_section)
        self.otp_section.disabled = True
        self.otp_section.opacity = 0
        
        # Register Button
        register_btn = Button(
            text='Complete Registration',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.86, 1)
        )
        register_btn.bind(on_press=self.register)
        layout.add_widget(register_btn)
        
        # Back to Login
        back_btn = Button(
            text='← Back to Login',
            size_hint_y=None,
            height=40
        )
        back_btn.bind(on_press=lambda x: self.show_login())
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def send_otp(self, instance):
        phone = self.reg_phone.text.strip()
        
        if not Security.validate_phone(phone):
            self.show_popup('Error', 'Please enter valid 10-digit phone number')
            return
        
        # Generate OTP and security code
        otp = Security.generate_otp()
        security_code = Security.generate_security_code()
        
        # Store in database
        db.store_otp(phone, otp, security_code)
        
        # Show OTP section
        self.otp_section.disabled = False
        self.otp_section.opacity = 1
        
        self.show_popup('Demo OTP', f'OTP: {otp}\nSecurity Code: {security_code}')
    def register(self, instance):
        phone = self.reg_phone.text.strip()
        otp = self.otp_input.text.strip()
        security_code = self.reg_security.text.strip()
        referral_code = self.referral_input.text.strip().upper()
        
        if not Security.validate_phone(phone):
            self.show_popup('Error', 'Invalid phone number')
            return
        
        if not db.verify_otp(phone, otp):
            self.show_popup('Error', 'Invalid OTP')
            return
        
        if len(security_code) != 6:
            self.show_popup('Error', 'Security code must be 6 digits')
            return
        
        success, message = db.register_user(phone, security_code, referral_code)
        
        if success:
            # ✅ AUTO-LOGIN AFTER REGISTRATION
            login_success, user_id = db.login_user(phone, security_code)
            if login_success:
                app = App.get_running_app()
                app.user_id = user_id
                app.root.current = 'home'
                self.show_popup('Success', 'Registration successful! Welcome!')
            else:
                self.show_popup('Error', 'Registration failed - please login manually')
                self.show_login()
        else:
            self.show_popup('Error', message)
    def login(self, instance):
        phone = self.phone_input.text.strip()
        security_code = self.security_input.text.strip()
        
        if not Security.validate_phone(phone):
            self.show_popup('Error', 'Please enter valid 10-digit phone number')
            return
        
        if len(security_code) != 6:
            self.show_popup('Error', 'Security code must be 6 digits')
            return
        
        success, result = db.login_user(phone, security_code)
        
        if success:
            app = App.get_running_app()
            # Check for admin user
            if phone == '0000000000' and security_code == '000000':
                app.root.current = 'admin'
                return

            app.user_id = result
            app.root.current = 'home'
            self.show_popup('Success', 'Login successful!')
        else:
            self.show_popup('Error', result)
    def show_popup(self, title, message):
        popup = ModalView(size_hint=(0.8, 0.4))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text=title, font_size='18sp', bold=True))
        layout.add_widget(Label(text=message, font_size='14sp'))
        
        close_btn = Button(text='OK', size_hint_y=None, height=50)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(close_btn)
        
        popup.add_widget(layout)
        popup.open()

    def go_to_admin(self):
        """Navigate to admin screen"""
        app = App.get_running_app()
        app.root.current = 'admin'

class HomeScreen(Screen):
    def on_enter(self):
        self.refresh_plans()
    
    def refresh_plans(self):
        self.clear_widgets()
        
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # Welcome
        welcome = Label(
            text='💰 Investment Plans',
            font_size='20sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        layout.add_widget(welcome)
        
        # Plan 1
        plan1 = self.create_plan_card(1, 'Starter Plan', [599, 1099], 4, 80, '#3b82f6')
        layout.add_widget(plan1)
        
        # Plan 2
        plan2 = self.create_plan_card(2, 'Growth Plan', [1799, 3050], 4, 110, '#8b5cf6')
        layout.add_widget(plan2)
        
        # Plan 3 - CHANGED FROM 180 TO 150 DAYS
        plan3 = self.create_plan_card(3, 'Premium Plan', [10000, 20000], 5, 150, '#ef4444')
        layout.add_widget(plan3)
        
        # Customer Care
        care_card = Button(
            text='📞 Customer Care: +91-9876543210\n24/7 Support Available',
            size_hint_y=None,
            height=80,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        care_card.bind(on_press=self.show_customer_care)
        layout.add_widget(care_card)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)
    
    def create_plan_card(self, plan_id, name, amounts, return_rate, days, color):
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=300, spacing=10)
        
        # Header
        header = Button(
            text=f'{name}\n{return_rate}% Daily Return • {days} Days',
            size_hint_y=None,
            height=80,
            background_color=self.hex_to_rgb(color),
            color=(1, 1, 1, 1)
        )
        header.disabled = True
        card.add_widget(header)
        
        # Amount options
        for amount in amounts:
            daily_return = amount * return_rate / 100
            total_return = amount + (daily_return * days)
            
            amount_btn = Button(
                text=f'₹{amount}\nDaily: ₹{daily_return:.2f} • Total: ₹{total_return:.0f}',
                size_hint_y=None,
                height=70,
                background_color=(0.9, 0.9, 0.9, 1)
            )
            amount_btn.bind(on_press=lambda x, p=plan_id, a=amount: self.invest(p, a))
            card.add_widget(amount_btn)
        
        return card
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
    
    def invest(self, plan_id, amount):
        app = App.get_running_app()
        if not hasattr(app, 'user_id'):
            return
        
        self.show_payment_options(plan_id, amount)
    
    def show_payment_options(self, plan_id, amount):
        popup = ModalView(size_hint=(0.9, 0.5))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(
            text=f'Invest ₹{amount}',
            font_size='20sp',
            bold=True
        ))
        
        phonepe_btn = Button(
            text='Pay with PhonePe',
            size_hint_y=None,
            height=50,
            background_color=(0.5, 0.2, 0.8, 1)
        )
        phonepe_btn.bind(on_press=lambda x: self.process_payment(plan_id, amount, 'phonepe', popup))
        layout.add_widget(phonepe_btn)
        
        cancel_btn = Button(
            text='Cancel',
            size_hint_y=None,
            height=50
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(cancel_btn)
        popup.add_widget(layout)
        popup.open()
    
    def process_investment_payment(self, plan_id, amount, method, popup):
        app = App.get_running_app()
        user = db.get_user(app.user_id)
        
        payment_result = payment_system.generate_investment_payment(amount, user[1], method)
        
        if payment_result['success']:
            webbrowser.open(payment_result['payment_url'])
            popup.dismiss()
            
            # Show verification popup
            self.show_verification_popup(
                'investment', plan_id, amount, method, 
                payment_result['transaction_id'], user[1]
            )
    
    def process_withdrawal_payment(self, amount, bank_details, method, popup):
        app = App.get_running_app()
        user = db.get_user(app.user_id)
        
        # First create withdrawal request
        success, message = db.create_withdrawal_request(app.user_id, amount, bank_details)
        
        if not success:
            self.show_popup('Error', message)
            return
        
        # Generate payment for withdrawal
        payment_result = payment_system.generate_withdrawal_payment(amount, user[1], method)
        
        if payment_result['success']:
            webbrowser.open(payment_result['payment_url'])
            popup.dismiss()
            
            # Show verification popup
            self.show_verification_popup(
                'withdrawal', None, amount, method,
                payment_result['transaction_id'], user[1]
            )
    
    def check_verification_status(self, dt, transaction_id, plan_id, amount, method):
        """Periodically checks if the payment has been verified."""
        if payment_system.auto_verify_payment(transaction_id):
            payment_type = payment_system.get_payment_type(transaction_id)
            if payment_type == 'investment':
                self.verify_and_activate(plan_id, amount, method, transaction_id)
                return False  # Stop the scheduled check
            # Add logic for other payment types like 'withdrawal' here if needed
        return True # Continue checking

    def verify_and_activate(self, plan_id, amount, method, txn_id):
        """Activates the investment once payment is confirmed."""
        app = App.get_running_app()
        db.add_investment(app.user_id, plan_id, amount, method)
        # Use a separate popup to notify user of success
        self.show_popup('Success', 'Payment verified and investment activated! Daily returns will be credited.')

    
    def show_customer_care(self, instance):
        self.show_popup('Customer Care', '📞 +91-9876543210\n✉️ support@investmentapp.com\n\n24/7 Support Available')
    
    def show_popup(self, title, message):
        popup = ModalView(size_hint=(0.8, 0.4))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text=title, font_size='18sp', bold=True))
        layout.add_widget(Label(text=message, font_size='14sp'))
        
        close_btn = Button(text='OK', size_hint_y=None, height=50)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(close_btn)
        
        popup.add_widget(layout)
        popup.open()

class InvestScreen(Screen):
    def on_enter(self):
        self.refresh_investments()
    
    def refresh_investments(self):
        self.clear_widgets()
        
        app = App.get_running_app()
        investments = db.get_active_investments(app.user_id)
        
        if not investments:
            # No investments
            layout = BoxLayout(orientation='vertical', padding=50)
            layout.add_widget(Label(
                text='No Active Investments',
                font_size='20sp',
                bold=True
            ))
            layout.add_widget(Label(
                text='Start investing to see your active plans',
                font_size='14sp'
            ))
            self.add_widget(layout)
            return
        
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        for inv in investments:
            inv_id, user_id, plan_id, amount, daily_return, total_days, days_remaining, total_profit, status, method, created_at = inv
            
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=200, padding=15, spacing=10)
            
            # Header
            header = BoxLayout(size_hint_y=None, height=30)
            header.add_widget(Label(
                text=f'Plan {plan_id} • ₹{amount}',
                font_size='16sp',
                bold=True
            ))
            header.add_widget(Label(
                text=f'{days_remaining}/{total_days} Days',
                font_size='14sp'
            ))
            card.add_widget(header)
            
            # Details
            card.add_widget(Label(
                text=f'Daily Return: ₹{daily_return:.2f}',
                font_size='14sp'
            ))
            card.add_widget(Label(
                text=f'Total Profit: ₹{total_profit:.2f}',
                font_size='14sp'
            ))
            card.add_widget(Label(
                text=f'Payment: {method}',
                font_size='12sp'
            ))
            
            # Progress
            progress = ProgressBar(max=total_days, value=total_days-days_remaining, size_hint_y=None, height=20)
            card.add_widget(progress)
            
            layout.add_widget(card)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

class ProfileScreen(Screen):
    def on_enter(self):
        self.refresh_profile()
    
    def refresh_profile(self):
        self.clear_widgets()
        
        app = App.get_running_app()
        user = db.get_user(app.user_id)
        balance = db.get_wallet_balance(app.user_id)
        
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # Profile info
        profile_card = BoxLayout(orientation='vertical', size_hint_y=None, height=100, padding=15)
        profile_card.add_widget(Label(
            text=f'📱 +91 {user[1]}',
            font_size='18sp',
            bold=True
        ))
        profile_card.add_widget(Label(
            text=f'Referral Code: {user[4]}',
            font_size='14sp'
        ))
        layout.add_widget(profile_card)
        
        # Wallet
        wallet_card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=15)
        wallet_card.add_widget(Label(
            text='💰 Wallet Balance',
            font_size='16sp',
            bold=True
        ))
        wallet_card.add_widget(Label(
            text=f'₹{balance:.2f}',
            font_size='24sp',
            bold=True
        ))
        
        withdraw_btn = Button(
            text='Withdraw Money',
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        withdraw_btn.bind(on_press=self.show_withdrawal)
        wallet_card.add_widget(withdraw_btn)
        
        layout.add_widget(wallet_card)
        
        # Transactions
        transactions = db.get_transactions(app.user_id, 10)
        if transactions:
            layout.add_widget(Label(
                text='Recent Transactions',
                font_size='16sp',
                bold=True,
                size_hint_y=None,
                height=30
            ))
            
            for txn in transactions:
                txn_id, user_id, type, amount, desc, status, created_at = txn
                
                txn_card = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, padding=10)
                txn_card.add_widget(Label(
                    text=desc,
                    font_size='12sp'
                ))
                txn_card.add_widget(Label(
                    text=f'₹{amount}',
                    font_size='14sp',
                    bold=True
                ))
                layout.add_widget(txn_card)
        
        # Logout
        logout_btn = Button(
            text='Logout',
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        logout_btn.bind(on_press=self.logout)
        layout.add_widget(logout_btn)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)
    
    def show_withdrawal(self, instance):
        popup = ModalView(size_hint=(0.9, 0.8), auto_dismiss=False)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(
            text='Withdraw Funds',
            font_size='20sp',
            bold=True
        ))
        
        app = App.get_running_app()
        balance = db.get_wallet_balance(app.user_id)
        
        layout.add_widget(Label(
            text=f'Available: ₹{balance:.2f}',
            font_size='16sp'
        ))
        
        self.withdraw_amount = TextInput(
            hint_text='Amount (Min: ₹100)',
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.withdraw_amount)
        
        self.account_holder = TextInput(
            hint_text='Account Holder Name',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.account_holder)
        
        self.account_number = TextInput(
            hint_text='Bank Account Number',
            input_filter='int',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.account_number)
        
        self.ifsc_code = TextInput(
            hint_text='IFSC Code',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.ifsc_code)
        
        # Payment method selection
        payment_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        phonepe_btn = Button(text='Pay with PhonePe', size_hint_x=0.5)
        phonepe_btn.bind(on_press=lambda x: self.process_withdrawal(
            popup, 'phonepe'
        ))
        
        gpay_btn = Button(text='Pay with Google Pay', size_hint_x=0.5)
        gpay_btn.bind(on_press=lambda x: self.process_withdrawal(
            popup, 'googlepay'
        ))
        
        payment_layout.add_widget(phonepe_btn)
        payment_layout.add_widget(gpay_btn)
        layout.add_widget(payment_layout)
        
        # Add a label for the payment buttons
        info_label = Label(text='Select a method to pay the withdrawal fee', size_hint_y=None, height=30, font_size='12sp')
        layout.add_widget(info_label)
        
        cancel_btn = Button(
            text='Cancel',
            size_hint_y=None,
            height=50
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(cancel_btn)
        
        popup.add_widget(layout)
        popup.open()
    
    def process_withdrawal(self, popup, method):
        amount = float(self.withdraw_amount.text or 0)
        
        bank_details = {
            'account_holder': Security.sanitize_input(self.account_holder.text),
            'account_number': Security.sanitize_input(self.account_number.text),
            'ifsc_code': Security.sanitize_input(self.ifsc_code.text)
        }
        
        app = App.get_running_app()
        app.process_withdrawal_payment(amount, bank_details, method, popup)
    
    def logout(self, instance):
        app = App.get_running_app()
        if hasattr(app, 'user_id'):
            delattr(app, 'user_id')
        app.root.current = 'auth'
        self.show_popup('Info', 'Logged out successfully')
    
    def show_popup(self, title, message):
        popup = ModalView(size_hint=(0.8, 0.4))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text=title, font_size='18sp', bold=True))
        layout.add_widget(Label(text=message, font_size='14sp'))
        
        close_btn = Button(text='OK', size_hint_y=None, height=50)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(close_btn)
        
        popup.add_widget(layout)
        popup.open()

class InvestmentApp(App):
    def build(self):
        self.user_id = None

        # Initialize the database in the correct user data directory
        global db
        db_path = self.user_data_dir + '/investment_data.db'
        db = Database(db_path)
        
        # Calculate daily returns on app start
        db.calculate_daily_returns()
        
        self.sm = ScreenManager()
        
        # Add screens
        self.auth_screen = AuthScreen(name='auth')
        self.home_screen = HomeScreen(name='home')
        self.invest_screen = InvestScreen(name='invest')
        self.profile_screen = ProfileScreen(name='profile')
        self.admin_screen = AdminScreen(name='admin')
        
        self.sm.add_widget(self.auth_screen)
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.invest_screen)
        self.sm.add_widget(self.profile_screen)
        self.sm.add_widget(self.admin_screen)

        return self.sm
    
    def show_verification_popup(self, payment_type, plan_id, amount, method, transaction_id, user_phone):
        popup = ModalView(size_hint=(0.8, 0.6), auto_dismiss=False)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        if payment_type == 'investment':
            title = '🔄 Verifying Investment'
            success_msg = 'Investment activated!'
        else:
            title = '🔄 Verifying Withdrawal'
            success_msg = 'Withdrawal completed!'
        
        layout.add_widget(Label(text=title, font_size='18sp', bold=True))
        
        status_label = Label(text='Waiting for payment confirmation...', font_size='14sp')
        layout.add_widget(status_label)
        
        progress = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        layout.add_widget(progress)
        
        popup.add_widget(layout)
        popup.open()
        
        # Start auto-verification
        self.start_payment_verification(
            payment_type, plan_id, amount, method, transaction_id, 
            popup, status_label, progress, success_msg
        )

    def start_payment_verification(self, payment_type, plan_id, amount, method, 
                                 transaction_id, popup, status_label, progress, success_msg):
        
        def update_verification(dt):
            if payment_system.auto_verify_payment(transaction_id):
                # Payment verified - complete the action
                if payment_type == 'investment':
                    db.add_investment(self.user_id, plan_id, amount, method)
                    self.home_screen.refresh_plans() # Or navigate away
                else:  # withdrawal
                    db.complete_withdrawal_after_payment(self.user_id, amount, transaction_id)
                    self.profile_screen.refresh_profile()
                
                popup.dismiss()
                self.profile_screen.show_popup('Success', success_msg) # Use a screen's popup
                return False  # Stop checking
            
            else:
                # Still verifying
                progress.value = min(progress.value + 5, 95)
                if progress.value >= 90:
                    status_label.text = 'Almost there...'
                
            return True  # Continue checking
        
        Clock.schedule_interval(update_verification, 3)  # Check every 3 seconds

    def process_withdrawal_payment(self, amount, bank_details, method, popup):
        # This method is now part of the App class
        user = db.get_user(self.user_id)
        success, message = db.create_withdrawal_request(self.user_id, amount, bank_details)
        if not success:
            self.profile_screen.show_popup('Error', message)
            return
        
        payment_result = payment_system.generate_withdrawal_payment(amount, user[1], method)
        if payment_result['success']:
            webbrowser.open(payment_result['payment_url'])
            popup.dismiss()
            self.show_verification_popup(
                'withdrawal', None, amount, method,
                payment_result['transaction_id'], user[1]
            )

if __name__ == '__main__':
    InvestmentApp().run()