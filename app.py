from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import Database
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date
import hashlib

app = Flask(__name__)
app.secret_key = 'kamadhenu-secret-key-2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = Database()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_age(birth_date):
    if not birth_date:
        return "Unknown"
    today = date.today()
    born = datetime.strptime(birth_date, '%Y-%m-%d').date()
    age_years = today.year - born.year
    age_months = today.month - born.month
    if age_months < 0:
        age_years -= 1
        age_months += 12
    if age_years > 0:
        return f"{age_years}y {age_months}m"
    return f"{age_months} months"

@app.context_processor
def utility_processor():
    return {'calculate_age': calculate_age}

# ==================== LOGIN/REGISTER ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.verify_user(username, password):
            session['username'] = username
            session['user_id'] = db.get_user_id(username)
            flash(f'🙏 Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if db.add_user(username, password):
            flash('✅ Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('❌ Username already exists. Please choose another.', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

# ==================== HOME ====================
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    cows = db.get_all_cows()
    summary = db.get_summary_stats()
    return render_template('index.html', cows=cows, summary=summary)

# ==================== MANUAL BACKUP ====================
@app.route('/manual_backup')
def manual_backup():
    if 'username' not in session:
        return redirect(url_for('login'))
    db.create_backup()
    flash('✅ Manual backup created successfully in backups folder!', 'success')
    return redirect(url_for('index'))

# ==================== COW ROUTES ====================
@app.route('/cow/<int:cow_id>')
def cow_detail(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    cow = db.get_cow(cow_id)
    if not cow:
        flash('Cow not found', 'danger')
        return redirect(url_for('index'))
    
    inseminations = db.get_inseminations(cow_id)
    pregnancies = db.get_pregnancies(cow_id)
    births = db.get_births(cow_id)
    milkings = db.get_milkings(cow_id)
    feedings = db.get_feedings(cow_id)
    feeding_summary = db.get_feeding_summary(cow_id)
    
    return render_template('cow_detail.html', 
                         cow=cow, 
                         inseminations=inseminations,
                         pregnancies=pregnancies,
                         births=births,
                         milkings=milkings,
                         feedings=feedings,
                         feeding_summary=feeding_summary)

@app.route('/add_cow', methods=['GET', 'POST'])
def add_cow():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        ear_tag = request.form['ear_tag']
        date_of_birth = request.form['date_of_birth']
        breed = request.form['breed']
        
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{ear_tag}_{int(datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_url = f"/static/uploads/{filename}"
        
        cow_id = db.add_cow(name, ear_tag, date_of_birth, breed, photo_url)
        flash(f'🐄 Cow {name} added successfully!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    return render_template('add_cow.html')

@app.route('/edit_cow/<int:cow_id>', methods=['GET', 'POST'])
def edit_cow(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    cow = db.get_cow(cow_id)
    if not cow:
        flash('Cow not found', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        ear_tag = request.form['ear_tag']
        date_of_birth = request.form['date_of_birth']
        breed = request.form['breed']
        
        photo_url = cow['photo_url']
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{ear_tag}_{int(datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_url = f"/static/uploads/{filename}"
        
        db.update_cow(cow_id, name, ear_tag, date_of_birth, breed, photo_url)
        flash('Cow updated successfully!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    return render_template('edit_cow.html', cow=cow)

# PERMANENT DELETE (New Feature)
@app.route('/permanent_delete_cow/<int:cow_id>')
def permanent_delete_cow(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    cow = db.get_cow(cow_id)
    if cow:
        db.permanent_delete_cow(cow_id)
        flash(f'⚠️ Cow "{cow["name"]}" has been PERMANENTLY DELETED! This action cannot be undone.', 'danger')
    else:
        flash('Cow not found', 'danger')
    return redirect(url_for('index'))

# Soft Delete (Archive)
@app.route('/delete_cow/<int:cow_id>')
def delete_cow(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    db.soft_delete_cow(cow_id)
    flash('Cow moved to archive', 'warning')
    return redirect(url_for('index'))

@app.route('/restore_cow/<int:cow_id>')
def restore_cow(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    db.restore_cow(cow_id)
    flash('Cow restored successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/archived')
def archived_cows():
    if 'username' not in session:
        return redirect(url_for('login'))
    cows = db.get_archived_cows()
    return render_template('archived.html', cows=cows)

# ==================== INSEMINATION ROUTES ====================
@app.route('/add_insemination/<int:cow_id>', methods=['GET', 'POST'])
def add_insemination(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        db.add_insemination(
            cow_id=cow_id,
            insemination_date=request.form['insemination_date'],
            inseminer_name=request.form['inseminer_name'],
            semen_type=request.form['semen_type'],
            semen_breed=request.form['semen_breed'],
            times_inseminated=request.form['times_inseminated'],
            success=request.form.get('success') == 'on'
        )
        flash('Insemination record added!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    cow = db.get_cow(cow_id)
    return render_template('add_insemination.html', cow=cow)

@app.route('/edit_insemination/<int:insem_id>', methods=['GET', 'POST'])
def edit_insemination(insem_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    insem = db.get_insemination(insem_id)
    if request.method == 'POST':
        db.update_insemination(
            insem_id=insem_id,
            insemination_date=request.form['insemination_date'],
            inseminer_name=request.form['inseminer_name'],
            semen_type=request.form['semen_type'],
            semen_breed=request.form['semen_breed'],
            times_inseminated=request.form['times_inseminated'],
            success=request.form.get('success') == 'on'
        )
        flash('Insemination record updated!', 'success')
        return redirect(url_for('cow_detail', cow_id=insem['cow_id']))
    
    return render_template('edit_insemination.html', insem=insem)

# ==================== PREGNANCY ROUTES ====================
@app.route('/add_pregnancy/<int:cow_id>', methods=['GET', 'POST'])
def add_pregnancy(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        db.add_pregnancy(
            cow_id=cow_id,
            confirmation_date=request.form['confirmation_date'],
            gestation_period=request.form['gestation_period'],
            expected_birth_date=request.form['expected_birth_date']
        )
        flash('Pregnancy record added!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    cow = db.get_cow(cow_id)
    return render_template('add_pregnancy.html', cow=cow)

@app.route('/edit_pregnancy/<int:preg_id>', methods=['GET', 'POST'])
def edit_pregnancy(preg_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    pregnancy = db.get_pregnancy(preg_id)
    if request.method == 'POST':
        db.update_pregnancy(
            preg_id=preg_id,
            confirmation_date=request.form['confirmation_date'],
            gestation_period=request.form['gestation_period'],
            expected_birth_date=request.form['expected_birth_date'],
            status=request.form['status']
        )
        flash('Pregnancy record updated!', 'success')
        return redirect(url_for('cow_detail', cow_id=pregnancy['cow_id']))
    
    return render_template('edit_pregnancy.html', pregnancy=pregnancy)

# ==================== BIRTH ROUTES ====================
@app.route('/add_birth/<int:cow_id>', methods=['GET', 'POST'])
def add_birth(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        birth_id = db.add_birth(
            cow_id=cow_id,
            birth_date=request.form['birth_date'],
            offspring_gender=request.form['offspring_gender'],
            offspring_health=request.form['offspring_health'],
            offspring_ear_tag=request.form.get('offspring_ear_tag', ''),
            notes=request.form.get('notes', '')
        )
        
        if request.form.get('pregnancy_id'):
            db.complete_pregnancy(request.form['pregnancy_id'])
        
        flash('Birth record added!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    cow = db.get_cow(cow_id)
    active_pregnancies = db.get_active_pregnancies(cow_id)
    return render_template('add_birth.html', cow=cow, pregnancies=active_pregnancies)

@app.route('/edit_birth/<int:birth_id>', methods=['GET', 'POST'])
def edit_birth(birth_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    birth = db.get_birth(birth_id)
    if request.method == 'POST':
        db.update_birth(
            birth_id=birth_id,
            birth_date=request.form['birth_date'],
            offspring_gender=request.form['offspring_gender'],
            offspring_health=request.form['offspring_health'],
            offspring_ear_tag=request.form.get('offspring_ear_tag', ''),
            notes=request.form.get('notes', '')
        )
        flash('Birth record updated!', 'success')
        return redirect(url_for('cow_detail', cow_id=birth['cow_id']))
    
    return render_template('edit_birth.html', birth=birth)

# ==================== MILKING ROUTES ====================
@app.route('/add_milking/<int:cow_id>', methods=['GET', 'POST'])
def add_milking(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        db.add_milking(
            cow_id=cow_id,
            milking_date=request.form['milking_date'],
            morning_amount=float(request.form.get('morning_amount', 0)),
            evening_amount=float(request.form.get('evening_amount', 0)),
            total_amount=float(request.form.get('morning_amount', 0)) + float(request.form.get('evening_amount', 0))
        )
        flash('Milking record added!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    cow = db.get_cow(cow_id)
    return render_template('add_milking.html', cow=cow)

@app.route('/edit_milking/<int:milking_id>', methods=['GET', 'POST'])
def edit_milking(milking_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    milking = db.get_milking(milking_id)
    if request.method == 'POST':
        db.update_milking(
            milking_id=milking_id,
            milking_date=request.form['milking_date'],
            morning_amount=float(request.form.get('morning_amount', 0)),
            evening_amount=float(request.form.get('evening_amount', 0)),
            total_amount=float(request.form.get('morning_amount', 0)) + float(request.form.get('evening_amount', 0))
        )
        flash('Milking record updated!', 'success')
        return redirect(url_for('cow_detail', cow_id=milking['cow_id']))
    
    return render_template('edit_milking.html', milking=milking)

# ==================== FEEDING ROUTES ====================
@app.route('/add_feeding/<int:cow_id>', methods=['GET', 'POST'])
def add_feeding(cow_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        db.add_feeding(
            cow_id=cow_id,
            feeding_date=request.form['feeding_date'],
            busa_amount=float(request.form.get('busa_amount', 0)),
            hindi_amount=float(request.form.get('hindi_amount', 0)),
            peni_amount=float(request.form.get('peni_amount', 0)),
            water_amount=float(request.form.get('water_amount', 0)),
            notes=request.form.get('notes', '')
        )
        flash('ಆಹಾರ ದಾಖಲೆ ಸೇರಿಸಲಾಗಿದೆ!', 'success')
        return redirect(url_for('cow_detail', cow_id=cow_id))
    
    cow = db.get_cow(cow_id)
    return render_template('add_feeding.html', cow=cow)

@app.route('/edit_feeding/<int:feeding_id>', methods=['GET', 'POST'])
def edit_feeding(feeding_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    feeding = db.get_feeding(feeding_id)
    if request.method == 'POST':
        db.update_feeding(
            feeding_id=feeding_id,
            feeding_date=request.form['feeding_date'],
            busa_amount=float(request.form.get('busa_amount', 0)),
            hindi_amount=float(request.form.get('hindi_amount', 0)),
            peni_amount=float(request.form.get('peni_amount', 0)),
            water_amount=float(request.form.get('water_amount', 0)),
            notes=request.form.get('notes', '')
        )
        flash('ಆಹಾರ ದಾಖಲೆ ನವೀಕರಿಸಲಾಗಿದೆ!', 'success')
        return redirect(url_for('cow_detail', cow_id=feeding['cow_id']))
    
    return render_template('edit_feeding.html', feeding=feeding)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)