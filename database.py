import sqlite3
from datetime import datetime, date
import os
import shutil
from pathlib import Path
import hashlib

class Database:
    def __init__(self, db_path="cow_management.db"):
        self.db_path = db_path
        self.init_database()
        self.create_users_table()
        self.create_backup()
    
    def create_backup(self):
        """Create automatic backup of database"""
        try:
            if os.path.exists(self.db_path):
                backup_dir = "backups"
                Path(backup_dir).mkdir(parents=True, exist_ok=True)
                backup_name = f"{backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.db_path, backup_name)
                print(f"✅ Backup created: {backup_name}")
                
                # Keep only last 10 backups
                backups = sorted(Path(backup_dir).glob("backup_*.db"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
        except Exception as e:
            print(f"⚠️ Backup warning: {e}")
    
    def init_database(self):
        """Initialize all tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ear_tag TEXT UNIQUE NOT NULL,
                date_of_birth DATE,
                breed TEXT,
                photo_url TEXT,
                is_deleted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')
        
        # Inseminations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inseminations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id INTEGER,
                insemination_date DATE,
                inseminer_name TEXT,
                semen_type TEXT,
                semen_breed TEXT,
                times_inseminated INTEGER DEFAULT 1,
                success BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cow_id) REFERENCES cows(id)
            )
        ''')
        
        # Pregnancies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pregnancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id INTEGER,
                confirmation_date DATE,
                gestation_period INTEGER DEFAULT 283,
                expected_birth_date DATE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cow_id) REFERENCES cows(id)
            )
        ''')
        
        # Births table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS births (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id INTEGER,
                birth_date DATE,
                offspring_gender TEXT,
                offspring_health TEXT,
                offspring_ear_tag TEXT,
                notes TEXT,
                pregnancy_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cow_id) REFERENCES cows(id)
            )
        ''')
        
        # Milkings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS milkings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id INTEGER,
                milking_date DATE,
                morning_amount REAL DEFAULT 0,
                evening_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cow_id) REFERENCES cows(id)
            )
        ''')
        
        # Feedings table (with Kannada support)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id INTEGER,
                feeding_date DATE,
                busa_amount REAL DEFAULT 0,
                hindi_amount REAL DEFAULT 0,
                peni_amount REAL DEFAULT 0,
                water_amount REAL DEFAULT 0,
                total_feed REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cow_id) REFERENCES cows(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_users_table(self):
        """Create users table for authentication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    # ==================== USER METHODS ====================
    def add_user(self, username, password):
        """Add a new user"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                          (username, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                      (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        return user is not None
    
    def get_user_id(self, username):
        """Get user ID by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user[0] if user else None
    
    # ==================== COW METHODS ====================
    def add_cow(self, name, ear_tag, date_of_birth, breed, photo_url):
        """Add a new cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cows (name, ear_tag, date_of_birth, breed, photo_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, ear_tag, date_of_birth, breed, photo_url))
        cow_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return cow_id
    
    def get_all_cows(self):
        """Get all active cows (not deleted)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cows WHERE is_deleted = 0 ORDER BY name')
        cows = cursor.fetchall()
        conn.close()
        
        return [{'id': c[0], 'name': c[1], 'ear_tag': c[2], 'date_of_birth': c[3], 
                 'breed': c[4], 'photo_url': c[5]} for c in cows]
    
    def get_cow(self, cow_id):
        """Get a single cow by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cows WHERE id = ?', (cow_id,))
        cow = cursor.fetchone()
        conn.close()
        if cow:
            return {'id': cow[0], 'name': cow[1], 'ear_tag': cow[2], 
                   'date_of_birth': cow[3], 'breed': cow[4], 'photo_url': cow[5]}
        return None
    
    def update_cow(self, cow_id, name, ear_tag, date_of_birth, breed, photo_url):
        """Update cow information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cows 
            SET name=?, ear_tag=?, date_of_birth=?, breed=?, photo_url=?
            WHERE id=?
        ''', (name, ear_tag, date_of_birth, breed, photo_url, cow_id))
        conn.commit()
        conn.close()
    
    def soft_delete_cow(self, cow_id):
        """Soft delete - move to archive"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cows SET is_deleted=1, deleted_at=CURRENT_TIMESTAMP WHERE id=?
        ''', (cow_id,))
        conn.commit()
        conn.close()
    
    def restore_cow(self, cow_id):
        """Restore from archive"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE cows SET is_deleted=0, deleted_at=NULL WHERE id=?', (cow_id,))
        conn.commit()
        conn.close()
    
    def permanent_delete_cow(self, cow_id):
        """Permanently delete a cow and all related records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete related records first (foreign key constraints)
        cursor.execute('DELETE FROM inseminations WHERE cow_id = ?', (cow_id,))
        cursor.execute('DELETE FROM pregnancies WHERE cow_id = ?', (cow_id,))
        cursor.execute('DELETE FROM births WHERE cow_id = ?', (cow_id,))
        cursor.execute('DELETE FROM milkings WHERE cow_id = ?', (cow_id,))
        cursor.execute('DELETE FROM feedings WHERE cow_id = ?', (cow_id,))
        
        # Finally delete the cow
        cursor.execute('DELETE FROM cows WHERE id = ?', (cow_id,))
        
        conn.commit()
        conn.close()
    
    def get_archived_cows(self):
        """Get all archived cows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cows WHERE is_deleted = 1 ORDER BY deleted_at DESC')
        cows = cursor.fetchall()
        conn.close()
        return [{'id': c[0], 'name': c[1], 'ear_tag': c[2], 'date_of_birth': c[3], 
                 'breed': c[4], 'photo_url': c[5]} for c in cows]
    
    def get_summary_stats(self):
        """Get summary statistics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM cows WHERE is_deleted=0')
        total_cows = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM births')
        total_births = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(total_amount) FROM milkings')
        avg_milk = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM feedings')
        total_feeds = cursor.fetchone()[0]
        
        conn.close()
        return {'total_cows': total_cows, 'total_births': total_births, 
                'avg_milk': round(avg_milk, 1), 'total_feeds': total_feeds}
    
    # ==================== INSEMINATION METHODS ====================
    def add_insemination(self, cow_id, insemination_date, inseminer_name, 
                        semen_type, semen_breed, times_inseminated, success):
        """Add insemination record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO inseminations (cow_id, insemination_date, inseminer_name, 
                                     semen_type, semen_breed, times_inseminated, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cow_id, insemination_date, inseminer_name, semen_type, 
              semen_breed, times_inseminated, success))
        conn.commit()
        conn.close()
    
    def get_inseminations(self, cow_id):
        """Get all inseminations for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inseminations WHERE cow_id=? ORDER BY insemination_date DESC', (cow_id,))
        insems = cursor.fetchall()
        conn.close()
        return [{'id': i[0], 'cow_id': i[1], 'insemination_date': i[2], 
                'inseminer_name': i[3], 'semen_type': i[4], 'semen_breed': i[5],
                'times_inseminated': i[6], 'success': i[7]} for i in insems]
    
    def get_insemination(self, insem_id):
        """Get a single insemination record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inseminations WHERE id=?', (insem_id,))
        insem = cursor.fetchone()
        conn.close()
        if insem:
            return {'id': insem[0], 'cow_id': insem[1], 'insemination_date': insem[2],
                   'inseminer_name': insem[3], 'semen_type': insem[4], 
                   'semen_breed': insem[5], 'times_inseminated': insem[6], 'success': insem[7]}
        return None
    
    def update_insemination(self, insem_id, insemination_date, inseminer_name,
                           semen_type, semen_breed, times_inseminated, success):
        """Update insemination record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE inseminations 
            SET insemination_date=?, inseminer_name=?, semen_type=?, 
                semen_breed=?, times_inseminated=?, success=?
            WHERE id=?
        ''', (insemination_date, inseminer_name, semen_type, semen_breed, 
              times_inseminated, success, insem_id))
        conn.commit()
        conn.close()
    
    # ==================== PREGNANCY METHODS ====================
    def add_pregnancy(self, cow_id, confirmation_date, gestation_period, expected_birth_date):
        """Add pregnancy record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pregnancies (cow_id, confirmation_date, gestation_period, expected_birth_date)
            VALUES (?, ?, ?, ?)
        ''', (cow_id, confirmation_date, gestation_period, expected_birth_date))
        conn.commit()
        conn.close()
    
    def get_pregnancies(self, cow_id):
        """Get all pregnancies for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pregnancies WHERE cow_id=? ORDER BY confirmation_date DESC', (cow_id,))
        preg = cursor.fetchall()
        conn.close()
        return [{'id': p[0], 'cow_id': p[1], 'confirmation_date': p[2], 
                'gestation_period': p[3], 'expected_birth_date': p[4], 'status': p[5]} for p in preg]
    
    def get_active_pregnancies(self, cow_id):
        """Get active pregnancies for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pregnancies WHERE cow_id=? AND status="active"', (cow_id,))
        preg = cursor.fetchall()
        conn.close()
        return [{'id': p[0], 'expected_birth_date': p[4]} for p in preg]
    
    def get_pregnancy(self, preg_id):
        """Get a single pregnancy record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pregnancies WHERE id=?', (preg_id,))
        preg = cursor.fetchone()
        conn.close()
        if preg:
            return {'id': preg[0], 'cow_id': preg[1], 'confirmation_date': preg[2],
                   'gestation_period': preg[3], 'expected_birth_date': preg[4], 'status': preg[5]}
        return None
    
    def update_pregnancy(self, preg_id, confirmation_date, gestation_period, expected_birth_date, status):
        """Update pregnancy record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pregnancies 
            SET confirmation_date=?, gestation_period=?, expected_birth_date=?, status=?
            WHERE id=?
        ''', (confirmation_date, gestation_period, expected_birth_date, status, preg_id))
        conn.commit()
        conn.close()
    
    def complete_pregnancy(self, preg_id):
        """Mark pregnancy as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE pregnancies SET status="completed" WHERE id=?', (preg_id,))
        conn.commit()
        conn.close()
    
    # ==================== BIRTH METHODS ====================
    def add_birth(self, cow_id, birth_date, offspring_gender, offspring_health, offspring_ear_tag, notes):
        """Add birth record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO births (cow_id, birth_date, offspring_gender, offspring_health, offspring_ear_tag, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cow_id, birth_date, offspring_gender, offspring_health, offspring_ear_tag, notes))
        birth_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return birth_id
    
    def get_births(self, cow_id):
        """Get all births for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM births WHERE cow_id=? ORDER BY birth_date DESC', (cow_id,))
        births = cursor.fetchall()
        conn.close()
        return [{'id': b[0], 'cow_id': b[1], 'birth_date': b[2], 'offspring_gender': b[3],
                'offspring_health': b[4], 'offspring_ear_tag': b[5], 'notes': b[6]} for b in births]
    
    def get_birth(self, birth_id):
        """Get a single birth record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM births WHERE id=?', (birth_id,))
        birth = cursor.fetchone()
        conn.close()
        if birth:
            return {'id': birth[0], 'cow_id': birth[1], 'birth_date': birth[2],
                   'offspring_gender': birth[3], 'offspring_health': birth[4],
                   'offspring_ear_tag': birth[5], 'notes': birth[6]}
        return None
    
    def update_birth(self, birth_id, birth_date, offspring_gender, offspring_health, offspring_ear_tag, notes):
        """Update birth record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE births 
            SET birth_date=?, offspring_gender=?, offspring_health=?, 
                offspring_ear_tag=?, notes=?
            WHERE id=?
        ''', (birth_date, offspring_gender, offspring_health, offspring_ear_tag, notes, birth_id))
        conn.commit()
        conn.close()
    
    # ==================== MILKING METHODS ====================
    def add_milking(self, cow_id, milking_date, morning_amount, evening_amount, total_amount):
        """Add milking record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO milkings (cow_id, milking_date, morning_amount, evening_amount, total_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (cow_id, milking_date, morning_amount, evening_amount, total_amount))
        conn.commit()
        conn.close()
    
    def get_milkings(self, cow_id):
        """Get all milkings for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM milkings WHERE cow_id=? ORDER BY milking_date DESC', (cow_id,))
        milkings = cursor.fetchall()
        conn.close()
        return [{'id': m[0], 'cow_id': m[1], 'milking_date': m[2], 
                'morning_amount': m[3], 'evening_amount': m[4], 'total_amount': m[5]} for m in milkings]
    
    def get_milking(self, milking_id):
        """Get a single milking record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM milkings WHERE id=?', (milking_id,))
        milking = cursor.fetchone()
        conn.close()
        if milking:
            return {'id': milking[0], 'cow_id': milking[1], 'milking_date': milking[2],
                   'morning_amount': milking[3], 'evening_amount': milking[4], 'total_amount': milking[5]}
        return None
    
    def update_milking(self, milking_id, milking_date, morning_amount, evening_amount, total_amount):
        """Update milking record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE milkings 
            SET milking_date=?, morning_amount=?, evening_amount=?, total_amount=?
            WHERE id=?
        ''', (milking_date, morning_amount, evening_amount, total_amount, milking_id))
        conn.commit()
        conn.close()
    
    # ==================== FEEDING METHODS (Kannada Support) ====================
    def add_feeding(self, cow_id, feeding_date, busa_amount, hindi_amount, peni_amount, water_amount, notes):
        """Add feeding record with Kannada support"""
        total_feed = busa_amount + hindi_amount + peni_amount
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedings (cow_id, feeding_date, busa_amount, hindi_amount, peni_amount, water_amount, total_feed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cow_id, feeding_date, busa_amount, hindi_amount, peni_amount, water_amount, total_feed, notes))
        conn.commit()
        conn.close()
    
    def get_feedings(self, cow_id):
        """Get all feedings for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM feedings WHERE cow_id=? ORDER BY feeding_date DESC', (cow_id,))
        feedings = cursor.fetchall()
        conn.close()
        return [{'id': f[0], 'cow_id': f[1], 'feeding_date': f[2], 
                'busa_amount': f[3], 'hindi_amount': f[4], 'peni_amount': f[5],
                'water_amount': f[6], 'total_feed': f[7], 'notes': f[8]} for f in feedings]
    
    def get_feeding(self, feeding_id):
        """Get a single feeding record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM feedings WHERE id=?', (feeding_id,))
        feeding = cursor.fetchone()
        conn.close()
        if feeding:
            return {'id': feeding[0], 'cow_id': feeding[1], 'feeding_date': feeding[2],
                   'busa_amount': feeding[3], 'hindi_amount': feeding[4], 'peni_amount': feeding[5],
                   'water_amount': feeding[6], 'total_feed': feeding[7], 'notes': feeding[8]}
        return None
    
    def update_feeding(self, feeding_id, feeding_date, busa_amount, hindi_amount, peni_amount, water_amount, notes):
        """Update feeding record"""
        total_feed = busa_amount + hindi_amount + peni_amount
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE feedings 
            SET feeding_date=?, busa_amount=?, hindi_amount=?, peni_amount=?, 
                water_amount=?, total_feed=?, notes=?
            WHERE id=?
        ''', (feeding_date, busa_amount, hindi_amount, peni_amount, water_amount, total_feed, notes, feeding_id))
        conn.commit()
        conn.close()
    
    def get_feeding_summary(self, cow_id):
        """Get feeding summary statistics for a cow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                SUM(busa_amount) as total_busa,
                SUM(hindi_amount) as total_hindi,
                SUM(peni_amount) as total_peni,
                SUM(water_amount) as total_water,
                SUM(total_feed) as total_feed,
                AVG(busa_amount) as avg_busa,
                AVG(hindi_amount) as avg_hindi,
                AVG(peni_amount) as avg_peni,
                AVG(water_amount) as avg_water,
                COUNT(*) as days
            FROM feedings WHERE cow_id=?
        ''', (cow_id,))
        summary = cursor.fetchone()
        conn.close()
        return {
            'total_busa': summary[0] or 0,
            'total_hindi': summary[1] or 0,
            'total_peni': summary[2] or 0,
            'total_water': summary[3] or 0,
            'total_feed': summary[4] or 0,
            'avg_busa': round(summary[5] or 0, 1),
            'avg_hindi': round(summary[6] or 0, 1),
            'avg_peni': round(summary[7] or 0, 1),
            'avg_water': round(summary[8] or 0, 1),
            'days': summary[9] or 0
        }