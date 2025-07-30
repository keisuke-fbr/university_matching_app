from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import csv
import os
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

PASS_CSV_PATH = './pass.csv'
MESSAGES_CSV_PATH = './message.csv'
CSV_PATH = './users2.csv'  

def load_passes():
    passes = []
    if not os.path.exists(PASS_CSV_PATH):
        return passes
    with open(PASS_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            passes.append(row)
    return passes

def load_messages():
    messages = []
    if not os.path.exists(MESSAGES_CSV_PATH):
        return messages
    with open(MESSAGES_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            messages.append(row)
    return messages

def load_users():
    users = []
    if not os.path.exists(CSV_PATH):
        return users
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in row:
                value = row[k]
                if isinstance(value, list):
                    value = "".join(map(str, value))
                if k not in ("id", "名前", "学年") and value != '':
                    try:
                        row[k] = int(value)
                    except Exception:
                        row[k] = 0
                else:
                    row[k] = value
            if "id" in row and row["id"]:
                try:
                    row["id"] = int(row["id"])
                except Exception:
                    pass
            if "学年" in row and row["学年"]:
                try:
                    row["学年"] = int(row["学年"])
                except Exception:
                    pass
            users.append(row)
    return users

def save_user(user):
    file_exists = os.path.exists(CSV_PATH)
    write_header = not file_exists or os.stat(CSV_PATH).st_size == 0
    with open(CSV_PATH, "a", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id","名前","学年","数学","物理","英語","プログラミング",
            "プレゼンレポート","実験レポート","授業レポート","論文作成",
            "ES添削","面接練習","業界研究","インターンシップ情報",
            "新歓情報","サークル情報"
        ])
        if write_header:
            writer.writeheader()
        writer.writerow(user)

def save_message(from_user, to_user, message):
    file_exists = os.path.exists(MESSAGES_CSV_PATH)
    write_header = not file_exists or os.stat(MESSAGES_CSV_PATH).st_size == 0
    with open(MESSAGES_CSV_PATH, "a", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["from_user", "to_user", "message", "timestamp"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "from_user": from_user,
            "to_user": to_user,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        })

def check_login(name, password):
    if not os.path.exists(PASS_CSV_PATH):
        return False
    with open(PASS_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['name'] == name and row['pass'] == password:
                return True
    return False

# --- ルーティング ---

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_name' not in session:
        return jsonify({"success": False, "error": "ログインしていません"})
    from_user = session['user_name']
    to_user = request.form['to_user']
    message = request.form['message']
    save_message(from_user, to_user, message)
    return jsonify({"success": True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        name = request.form['user_name']
        password = request.form['password']
        if check_login(name, password):
            session['user_name'] = name
            return redirect(url_for('search'))
        else:
            error = "名前またはパスワードが間違っています"
    return render_template('login.html', error=error)

@app.route('/register_pass', methods=['GET', 'POST'])
def register_pass():
    success = False
    error = ""
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        exists = False
        if os.path.exists(PASS_CSV_PATH):
            with open(PASS_CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['name'] == name:
                        exists = True
                        break
        if exists:
            error = "その名前は既に使われています"
        else:
            file_exists = os.path.exists(PASS_CSV_PATH)
            write_header = not file_exists or os.stat(PASS_CSV_PATH).st_size == 0
            with open(PASS_CSV_PATH, "a", encoding="utf-8", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "pass"])
                if write_header:
                    writer.writeheader()
                writer.writerow({"name": name, "pass": password})
            success = True
    return render_template('register_pass.html', success=success, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/search')
def search():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('search.html')

@app.route('/inbox')
def inbox():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    user_name = session['user_name']
    all_messages = load_messages()
    received = [m for m in all_messages if m['to_user'] == user_name]
    # 送信者一覧を重複なしで取得
    senders = list({m['from_user'] for m in received})
    # ユーザー名→ユーザーID辞書を用意（users2.csvのみ）
    users = load_users()
    name_to_id = {u["名前"]: u["id"] for u in users if u.get("id") is not None}
    # Jinja2で使えるよう、リスト形式で渡す
    senders_info = [{"name": s, "id": name_to_id.get(s)} for s in senders]
    return render_template('inbox.html', messages=received, user_name=user_name, senders=senders_info)

@app.route('/get_pass_users')
def get_pass_users():
    passes = load_passes()
    return jsonify(passes)

@app.route('/search_study')
def search_study():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('search_study.html')

@app.route('/search_report')
def search_report():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('search_report.html')

@app.route('/search_job')
def search_job():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('search_job.html')

@app.route('/search_circle')
def search_circle():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('search_circle.html')

@app.route('/list')
def list_page():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('list.html')

@app.route('/chat')
def chat():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    success = request.args.get('success', default=0, type=int)
    if request.method == 'POST':
        users = load_users()
        form = request.form
        new_id = max([u["id"] for u in users if u.get("id") is not None], default=0) + 1
        new_user = {
            "id": new_id,
            "名前": form['名前'],
            "学年": int(form['学年']),
            "数学": int('数学' in form),
            "物理": int('物理' in form),
            "英語": int('英語' in form),
            "プログラミング": int('プログラミング' in form),
            "プレゼンレポート": int('プレゼンレポート' in form),
            "実験レポート": int('実験レポート' in form),
            "授業レポート": int('授業レポート' in form),
            "論文作成": int('論文作成' in form),
            "ES添削": int('ES添削' in form),
            "面接練習": int('面接練習' in form),
            "業界研究": int('業界研究' in form),
            "インターンシップ情報": int('インターンシップ情報' in form),
            "新歓情報": int('新歓情報' in form),
            "サークル情報": int('サークル情報' in form)
        }
        save_user(new_user)
        return redirect(url_for('register', success=1))
    return render_template('register2.html', success=success)

@app.route('/get_users')
def get_users():
    users = load_users()  # users2.csv
    passes = load_passes()  # pass.csv
    known_names = {u['名前'] for u in users}
    # pass.csvは nameカラムなので '名前' キーでマージ
    for p in passes:
        if p['name'] not in known_names:
            users.append({'id': None, '名前': p['name']})
    return jsonify(users)

@app.route('/get_chat_history')
def get_chat_history():
    if 'user_name' not in session:
        return jsonify([])  # ログインしてなければ空
    my_name = session['user_name']
    partner_name = request.args.get('to_user', '')

    all_msgs = load_messages()
    history = [
        m for m in all_msgs
        if (m['from_user'] == my_name and m['to_user'] == partner_name)
        or (m['from_user'] == partner_name and m['to_user'] == my_name)
    ]
    history = sorted(history, key=lambda x: x.get('timestamp', ''))
    return jsonify(history)

@app.route('/get_me')
def get_me():
    if 'user_name' not in session:
        return jsonify({"user_name": ""})
    return jsonify({"user_name": session['user_name']})

if __name__ == '__main__':
    app.run(debug=True)
