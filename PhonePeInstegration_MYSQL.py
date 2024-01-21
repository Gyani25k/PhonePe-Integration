from flask import Flask, render_template, redirect, request
import uuid
import json
import mysql.connector
from mysql.connector import Error
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
from datetime import datetime
import os
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='template')
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key_here'

# INITIALIZE DATABASE CONNECTIVITY

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Initialize MySQL connection
try:
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    if connection.is_connected():
        print("Connected to MySQL database")

except Error as e:
    print(f"Error: {e}")

# Initialize PhonePePaymentClient
merchant_id = os.getenv('merchant_id')
salt_key = os.getenv('salt_key')
salt_index = 1
env = Env.UAT
should_publish_events = True
phonepe_client = PhonePePaymentClient(merchant_id, salt_key, salt_index, env, should_publish_events)

# Function to generate unique transaction ID
def generate_unique_transaction_id():
    unique_id = "silvertalkies-" + str(uuid.uuid4().int)[:6]
    return unique_id

# Function to initiate payment with PhonePe
def initiate_payment(name, email, amount):
    unique_transaction_id = generate_unique_transaction_id()

    # Define URLs
    ui_redirect_url = "http://127.0.0.1:8080/payment_success?unique_transaction_id=" + unique_transaction_id
    s2s_callback_url = "http://127.0.0.1:8080/payment_success?unique_transaction_id=" + unique_transaction_id
    id_assigned_to_user_by_merchant = '1'
    cancel_redirect_url = "https://creativelo.1gen.cloud/page/paymentcallback/false"

    # Build Pay Page Request
    pay_page_request = PgPayRequest.pay_page_pay_request_builder(
        merchant_transaction_id=unique_transaction_id,
        amount=amount,
        merchant_user_id=id_assigned_to_user_by_merchant,
        callback_url=s2s_callback_url,
        redirect_url=ui_redirect_url,
        cancel_redirect_url=cancel_redirect_url
    )

    # Make payment and get Pay Page URL
    pay_page_response = phonepe_client.pay(pay_page_request)
    pay_page_url = pay_page_response.data.instrument_response.redirect_info.url

    # Save payment details in MySQL
    payment_details = {
        "payment_started_at": datetime.now(),
        "name": name,
        "unique_transaction_id": unique_transaction_id,
        "amount": amount,
        "callback_url": s2s_callback_url,
        "redirect_url": ui_redirect_url,
        "pay_page_url": pay_page_url,
        "status": None,
        "status_msg": None
    }

    save_payment_details_to_mysql(payment_details)

    return payment_details

# Function to check payment status
def check_payment_status(unique_transaction_id):
    response = phonepe_client.check_status(unique_transaction_id)
    return response.message, response.data.state, response.data.response_code, response.data.payment_instrument.type.split('.')[-1], response.data.payment_instrument.pg_transaction_id

# Function to save payment details to MySQL database
def save_payment_details_to_mysql(payment_details):
    try:
        cursor = connection.cursor()

        # Define your MySQL table schema
        create_table_query = """
            CREATE TABLE IF NOT EXISTS payment_transactions_track (
                id INT AUTO_INCREMENT PRIMARY KEY,
                payment_started_at DATETIME,
                name VARCHAR(255),
                unique_transaction_id VARCHAR(255),
                amount DECIMAL(10, 2),
                callback_url VARCHAR(255),
                redirect_url VARCHAR(255),
                pay_page_url VARCHAR(255),
                status VARCHAR(255),
                status_msg VARCHAR(255),
                payment_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """
        cursor.execute(create_table_query)

        # Insert payment details into the table
        insert_query = """
            INSERT INTO payment_transactions_track
            (payment_started_at, name, unique_transaction_id, amount, callback_url,
            redirect_url, pay_page_url, status, status_msg, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            payment_details["payment_started_at"],
            payment_details["name"],
            payment_details["unique_transaction_id"],
            payment_details["amount"],
            payment_details["callback_url"],
            payment_details["redirect_url"],
            payment_details["pay_page_url"],
            payment_details["status"],
            payment_details["status_msg"],
            datetime.now().date()
        ))

        connection.commit()
        print("Payment details saved to MySQL database")

    except Error as e:
        print(f"Error: {e}")

    finally:
        cursor.close()


user_data = {
	'product_info':'',
    'firstname': '',
    'email': '',
    'phone': '',
    'amount':'',
	'surl':'',
	'furl':'',
	'key':'',
	'hash':'',
	'txnid':'',
    'paymentId':'',
	'service_provider':'Silver Talkies'
}

@app.route('/paymentform', methods=['GET', 'POST'])
def payment_form():

    global user_data

    user_data['name'] = request.form['firstname']
    user_data['email'] = request.form['email']
    user_data['amount'] = request.form['amount']
    user_data['product_info'] = request.form['productinfo']
    user_data['phone'] = request.form['phone']
    user_data['surl'] = request.form['surl']
    user_data['furl'] = request.form['furl']
    user_data['key'] = request.form['key']
    user_data['hash'] = request.form['hash']
    user_data['txnid'] = request.form['txnid']
    user_data['paymentId'] = request.form['paymentId']
    user_data['service_provider'] = 'Silver Talkies'

    name = user_data.get('name', '')
    email = user_data.get('email', '')
    amount = user_data.get('amount', '')
    product_info = user_data.get('product_info', '')
    phone = user_data.get('phone', '')
    surl = user_data.get('surl', '')
    furl = user_data.get('furl', '')
    key = user_data.get('key', '')
    hash_value = user_data.get('hash', '')
    txnid = user_data.get('txnid', '')
    paymentId = user_data.get('paymentId', '')
    service_provider = 'Silver Talkies'

    return render_template('index.html', name=name, email=email, amount=amount,
                           product_info=product_info, phone=phone, surl=surl,
                           furl=furl, key=key, hash=hash_value, txnid=txnid,paymentId=paymentId,
                           service_provider=service_provider)

@app.route('/make_payment', methods=['GET','POST'])
def make_payment():

    name = request.form['name']
    email = request.form['email']
    amount = request.form['amount']

    amount  = int(amount)*100


    payment_details = initiate_payment(name, email, amount)


    payment_details_to_save = {
        "payment_started_at": payment_details["payment_started_at"].isoformat(),
        "name": payment_details["name"],
        "unique_transaction_id": payment_details["unique_transaction_id"],
        "amount": payment_details["amount"],
        "callback_url": payment_details["callback_url"],
        "redirect_url": payment_details["redirect_url"],
        "pay_page_url": payment_details["pay_page_url"],
        "Message": None,
        "status": "PENDING",
        "phonepe_transactionid": None,
        "payment_mode": None,
    }

    with open('payment_details.json', 'w') as json_file:
        json.dump(payment_details_to_save, json_file, indent=2)

    return redirect(payment_details['pay_page_url'])


# Flask route to display payment success message
@app.route('/payment_success')
def payment_success():
    unique_transaction_id = request.args.get('unique_transaction_id')
    message, update, status, payment_mode, phonepe_transactionid = check_payment_status(unique_transaction_id)

    # Update payment_details with status information
    try:
        cursor = connection.cursor()
        update_query = """
            UPDATE payment_transactions_track
            SET status = %s, status_msg = %s, updated_at = CURRENT_TIMESTAMP
            WHERE unique_transaction_id = %s
        """
        cursor.execute(update_query, (status, message, unique_transaction_id))
        connection.commit()
    except Error as e:
        print(f"Error updating payment details: {e}")
    finally:
        cursor.close()

    return redirect('https://www.google.com/')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
