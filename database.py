import sqlite3
import hashlib
import secrets
from datetime import datetime
import json

class Database:
    def __init__(self, db_path):
        # Use the provided path to connect to the database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                security_code_hash TEXT NOT NULL,
                wallet_balance REAL DEFAULT 0,
                referral_code TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Investments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_id INTEGER,
                amount REAL,
                daily_return REAL,
                total_days INTEGER,
                days_remaining INTEGER,
                total_profit REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                payment_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,  -- investment, withdrawal, return, referral, withdrawal_payment
                amount REAL,
                description TEXT,
                status TEXT DEFAULT 'completed',
                bank_details JSON,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # OTP storage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_store (
                phone TEXT PRIMARY KEY,
                otp TEXT,
                security_code TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Withdrawal requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                bank_details JSON,
                status TEXT DEFAULT 'pending',  -- pending, paid, completed, cancelled
                payment_transaction_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def hash_security_code(self, code):
        return hashlib.sha256(code.encode()).hexdigest()
    
    def store_otp(self, phone, otp, security_code):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO otp_store (phone, otp, security_code, created_at)
            VALUES (?, ?, ?, ?)
        ''', (phone, otp, security_code, datetime.now().isoformat()))
        self.conn.commit()
    
    def verify_otp(self, phone, otp):
        cursor = self.conn.cursor()
        cursor.execute('SELECT otp, created_at FROM otp_store WHERE phone = ?', (phone,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        stored_otp, created_at = result
        # OTP expires after 10 minutes
        if (datetime.now() - datetime.fromisoformat(created_at)).seconds > 600:
            return False
        
        return stored_otp == otp
    
    def get_security_code(self, phone):
        cursor = self.conn.cursor()
        cursor.execute('SELECT security_code FROM otp_store WHERE phone = ?', (phone,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def register_user(self, phone, security_code, referral_code=None):
        cursor = self.conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
        if cursor.fetchone():
            return False, "Phone already registered"
        
        security_hash = self.hash_security_code(security_code)
        ref_code = phone[-6:]  # Use last 6 digits as referral code
        
        try:
            cursor.execute('''
                INSERT INTO users (phone, security_code_hash, referral_code)
                VALUES (?, ?, ?)
            ''', (phone, security_hash, ref_code))
            
            # Handle referral
            if referral_code:
                referrer = self.get_user_by_referral(referral_code)
                if referrer:
                    # Give ₹50 referral bonus
                    self.update_wallet(referrer[0], 50)
                    self.add_transaction(referrer[0], 'referral', 50, f'Referral bonus from {phone}')
            
            self.conn.commit()
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
    
    def login_user(self, phone, security_code):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, security_code_hash FROM users WHERE phone = ?', (phone,))
        result = cursor.fetchone()
        
        if not result:
            return False, "User not found"
        
        user_id, stored_hash = result
        if self.hash_security_code(security_code) == stored_hash:
            return True, user_id
        else:
            return False, "Invalid security code"
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
    
    def get_user_by_referral(self, referral_code):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
        return cursor.fetchone()
    
    def update_wallet(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?', (amount, user_id))
        self.conn.commit()
    
    def get_wallet_balance(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT wallet_balance FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def add_investment(self, user_id, plan_id, amount, payment_method):
        plans = {
            1: {'return': 0.04, 'days': 80},
            2: {'return': 0.04, 'days': 110},
            3: {'return': 0.05, 'days': 150}  # CHANGED FROM 180 TO 150 DAYS
        }
        
        plan = plans.get(plan_id)
        if not plan:
            return False
        
        daily_return = amount * plan['return']
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO investments (user_id, plan_id, amount, daily_return, total_days, days_remaining, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, plan_id, amount, daily_return, plan['days'], plan['days'], payment_method))
        
        self.add_transaction(user_id, 'investment', amount, f'Invested in Plan {plan_id}')
        
        # Add first day return immediately
        self.update_wallet(user_id, daily_return)
        self.add_transaction(user_id, 'return', daily_return, f'First day return from Plan {plan_id}')
        
        self.conn.commit()
        return True
    
    def get_active_investments(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM investments 
            WHERE user_id = ? AND status = 'active' 
            ORDER BY created_at DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    def add_transaction(self, user_id, type, amount, description, bank_details=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, description, bank_details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, type, amount, description, json.dumps(bank_details) if bank_details else None))
        self.conn.commit()
    
    def get_transactions(self, user_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    def create_withdrawal_request(self, user_id, amount, bank_details):
        """Create withdrawal request - user will pay for withdrawal"""
        cursor = self.conn.cursor()
        
        current_balance = self.get_wallet_balance(user_id)
        
        if amount < 100:
            return False, "Minimum withdrawal is ₹100"
        
        if amount > current_balance:
            return False, "Insufficient balance"
        
        # Create withdrawal request
        cursor.execute('''
            INSERT INTO withdrawal_requests (user_id, amount, bank_details, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, amount, json.dumps(bank_details)))
        
        self.conn.commit()
        return True, "Withdrawal request created"
    
    def complete_withdrawal_after_payment(self, user_id, amount, transaction_id):
        """Complete withdrawal after user makes payment"""
        cursor = self.conn.cursor()
        
        # Find pending withdrawal
        cursor.execute('''
            SELECT id FROM withdrawal_requests 
            WHERE user_id = ? AND amount = ? AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id, amount))
        
        result = cursor.fetchone()
        if not result:
            return False, "No pending withdrawal found"
        
        withdrawal_id = result[0]
        
        # Deduct from wallet
        self.update_wallet(user_id, -amount)
        
        # Update withdrawal status
        cursor.execute('''
            UPDATE withdrawal_requests 
            SET status = 'completed', payment_transaction_id = ?
            WHERE id = ?
        ''', (transaction_id, withdrawal_id))
        
        # Add transaction record
        self.add_transaction(user_id, 'withdrawal', amount, 'Withdrawal completed', {})
        
        self.conn.commit()
        return True, "Withdrawal completed successfully"
    
    def get_pending_withdrawals(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM withdrawal_requests 
            WHERE user_id = ? AND status = 'pending'
            ORDER BY created_at DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    def calculate_daily_returns(self):
        """Calculate and credit daily returns for all active investments"""
        cursor = self.conn.cursor()
        
        # Get all active investments
        cursor.execute('SELECT * FROM investments WHERE status = "active"')
        investments = cursor.fetchall()
        
        for inv in investments:
            inv_id, user_id, plan_id, amount, daily_return, total_days, days_remaining, total_profit, status, payment_method, created_at = inv
            
            if days_remaining > 0:
                # Credit daily return
                self.update_wallet(user_id, daily_return)
                
                # Update investment
                cursor.execute('''
                    UPDATE investments 
                    SET days_remaining = days_remaining - 1, 
                        total_profit = total_profit + ?
                    WHERE id = ?
                ''', (daily_return, inv_id))
                
                # Add transaction
                self.add_transaction(user_id, 'return', daily_return, f'Daily return from Plan {plan_id}')
                
                # Mark as completed if no days remaining
                if days_remaining - 1 == 0:
                    cursor.execute('UPDATE investments SET status = "completed" WHERE id = ?', (inv_id,))
        
        self.conn.commit()
    
    def get_all_users(self):
        """Get all users for admin view"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, phone, wallet_balance, referral_code, created_at 
            FROM users ORDER BY created_at DESC
        ''')
        return cursor.fetchall()
    
    def get_all_investments(self):
        """Get all investments for admin view"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT i.*, u.phone 
            FROM investments i 
            JOIN users u ON i.user_id = u.id 
            ORDER BY i.created_at DESC
        ''')
        return cursor.fetchall()
    
    def get_all_transactions(self, limit=100):
        """Get all transactions for admin view"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, u.phone 
            FROM transactions t 
            JOIN users u ON t.user_id = u.id 
            ORDER BY t.created_at DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_platform_stats(self):
        """Get platform statistics for admin dashboard"""
        cursor = self.conn.cursor()
        
        stats = {
            'total_users': cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'total_investments': cursor.execute('SELECT COUNT(*) FROM investments').fetchone()[0],
            'active_investments': cursor.execute('SELECT COUNT(*) FROM investments WHERE status = "active"').fetchone()[0],
            'total_investment_amount': cursor.execute('SELECT SUM(amount) FROM investments').fetchone()[0] or 0,
            'total_returns_paid': cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "return"').fetchone()[0] or 0,
            'total_withdrawals': cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "withdrawal"').fetchone()[0] or 0,
            'total_wallet_balance': cursor.execute('SELECT SUM(wallet_balance) FROM users').fetchone()[0] or 0,
        }
        
        return stats
    
    def update_user_wallet(self, user_id, amount, reason=""):
        """Admin: Update user wallet balance"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?', (amount, user_id))
        
        # Add transaction record
        self.add_transaction(user_id, 'admin_adjustment', amount, f'Admin adjustment: {reason}')
        
        self.conn.commit()
        return True
    
    def delete_user(self, user_id):
        """Admin: Delete user and all their data"""
        cursor = self.conn.cursor()
        
        try:
            # Delete user's data from all tables
            cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM investments WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM withdrawal_requests WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            self.conn.commit()
            return True, "User deleted successfully"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
    
    def get_user_detailed_info(self, user_id):
        """Get detailed user information"""
        cursor = self.conn.cursor()
        
        # User basic info
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return None
        
        # User investments
        investments = cursor.execute('SELECT * FROM investments WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
        
        # User transactions (last 20)
        transactions = cursor.execute('''
            SELECT * FROM transactions WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 20
        ''', (user_id,)).fetchall()
        
        return {
            'user_info': user,
            'investments': investments,
            'transactions': transactions
        }

# Global database instance
db = None