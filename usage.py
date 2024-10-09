from flask import Flask, request, jsonify, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/nandh/OneDrive/Desktop/my flask project/bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    current_balance = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False) # 'deposit' or 'withdraw'
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    users = User.query.all()
    transactions = Transaction.query.all()
    return render_template('index.html', users=users, transactions=transactions)

@app.route('/deposit', methods=['POST'])
def deposit():
    if request.headers['Content-Type'] == 'application/json':
        data = request.json
    else:
        data = request.form

    account_number = data.get('account_number')
    amount = float(data.get('amount', 0))  # Default to 0 if 'amount' is missing or not a number

    if not account_number or amount <= 0:
        return jsonify({'message': 'Invalid account number or amount'}), 400

    user = User.query.filter_by(account_number=account_number).first()
    if user:
        user.current_balance += amount
        db.session.add(user)
        transaction = Transaction(user_id=user.id, amount=amount, transaction_type='deposit')
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'message': 'Deposit successful'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if request.headers['Content-Type'] == 'application/json':
        data = request.json
    else:
        data = request.form

    account_number = data.get('account_number')
    amount = float(data.get('amount', 0))  # Default to 0 if 'amount' is missing or not a number

    if not account_number or amount <= 0:
        return jsonify({'message': 'Invalid account number or amount'}), 400

    user = User.query.filter_by(account_number=account_number).first()
    if user:
        if user.current_balance >= amount:
            user.current_balance -= amount
            db.session.add(user)
            transaction = Transaction(user_id=user.id, amount=amount, transaction_type='withdraw')
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'message': 'Withdrawal successful'}), 200
        else:
            return jsonify({'message': 'Insufficient funds'}), 400
    else:
        return jsonify({'message': 'User not found'}), 404



@app.route('/mini_statement/<account_number>', methods=['GET'])
def mini_statement(account_number):
    user = User.query.filter_by(account_number=account_number).first()
    if user:
        transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
        statement = [{'amount': t.amount, 'transaction_type': t.transaction_type, 'timestamp': t.timestamp} for t in transactions]
        return jsonify(statement), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/download_statement/<account_number>', methods=['GET'])
def download_statement(account_number):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    statement_type = request.args.get('type')

    user = User.query.filter_by(account_number=account_number).first()
    if user:
        transactions = Transaction.query.filter_by(user_id=user.id)

        if start_date:
            transactions = transactions.filter(Transaction.timestamp >= start_date)
        if end_date:
            transactions = transactions.filter(Transaction.timestamp <= end_date)

        transactions = transactions.all()

        if statement_type == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['amount', 'transaction_type', 'timestamp'])
            writer.writeheader()
            for t in transactions:
                writer.writerow({'amount': t.amount, 'transaction_type': t.transaction_type, 'timestamp': t.timestamp})
            output.seek(0)
            return send_file(output, as_attachment=True, attachment_filename='statement.csv', mimetype='text/csv')
        elif statement_type == 'pdf':
            # Logic for generating PDF statement
            pass
        else:
            return jsonify({'message': 'Invalid statement type'}), 400
    else:
        return jsonify({'message': 'User not found'}), 404

# @app.route('/')
# def home():
#     return render_template('index.html')
    
# @app.route('/')
# def home():
#     users = User.query.all()
#     transactions = Transaction.query.all()
#     return render_template('index.html', users=users, transactions=transactions)
    
if __name__ == '__main__':
    app.run(debug=True)


