from flask import Flask, render_template, redirect,url_for,request,jsonify,render_template_string
import uuid
import json
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
from datetime import datetime
import os 
from flask_cors import CORS
import mysql.connector



from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__, template_folder='template')
CORS(app)

app.config['SECRET_KEY'] = 'PhonePay@!(*)2024'

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Initialize PhonePePaymentClient
merchant_id = os.getenv('merchant_id')
salt_key = os.getenv('salt_key')
salt_index = 1
env = Env.UAT
should_publish_events = True
phonepe_client = PhonePePaymentClient(merchant_id, salt_key, salt_index, env, should_publish_events)

# Establish a database connection



try:
    db_connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
    
    # Create a database cursor
    db_cursor = db_connection.cursor()
    
except mysql.connector.Error as e:
    print(f"Error accessing the database: {e}")





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


def initiate_payment(name, email, amount):

    global user_data

    unique_transaction_id = user_data.get('txnid')

    # Define URLs
    ui_redirect_url = "http://127.0.0.1:8080/CheckStatusV1?unique_transaction_id="+unique_transaction_id

    s2s_callback_url = "http://127.0.0.1:8080/CheckStatusV1?unique_transaction_id="+unique_transaction_id

    id_assigned_to_user_by_merchant = '1'
    cancel_redirect_url="https://creativelo.1gen.cloud/page/paymentcallback/false"

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

    # Save payment details in JSON
    payment_details = {
        "payment_started_at":datetime.now(),
        "name": name,
        "unique_transaction_id": unique_transaction_id,
        "amount": amount,
        "callback_url": s2s_callback_url,
        "redirect_url": ui_redirect_url,
        "pay_page_url": pay_page_url,
        "status": None,
        "status_msg": None
    }

    return payment_details


def check_payment_status(unique_transaction_id):
    response = phonepe_client.check_status(unique_transaction_id)
    print("response",response)
    print(response.data.payment_instrument.type.split('.')[-1])
    return response.message,response.data.state ,response.data.response_code , response.data.payment_instrument.type.split('.')[-1] , response.data.payment_instrument.pg_transaction_id

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
@app.route('/CheckStatusV1')
def payment_success():
    global user_data

    surl = user_data.get('surl')
    txnid = user_data.get('txnid')
    hash = user_data.get('hash')
    paymentId = user_data.get('paymentId')
    unique_transaction_id = request.args.get('unique_transaction_id')
    message, Update, status, payment_mode, phonepe_transactionid = check_payment_status(unique_transaction_id)

    
    status = status.lower()
    
    try:
        with open('payment_details.json', 'r') as json_file:
            # Check if the file is empty or not
            data = json_file.read().strip()
            if not data:
                raise ValueError("Empty JSON file")
            
            payment_details = json.loads(data)
            
            payment_details["payment_date"] = datetime.now().date().isoformat()
            payment_details["Message"] = message
            payment_details["payment_id"] = paymentId
            payment_details["payment_mode"] = payment_mode
            payment_details["status"] = status
            payment_details["phonepe_transactionid"] = phonepe_transactionid
            payment_details["payment_ended_at"] = datetime.now().isoformat()

    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")

    with open('payment_details.json', 'a') as json_file:
        json.dump(payment_details, json_file, indent=2, default=str)

    form_template = """
    <html>
    <body onload="document.forms['redirectForm'].submit()">
        <form name="redirectForm" action="{{surl}}" method="post">
            <input type="hidden" name="mihpayid" value="{{ phonepe_transactionid }}" required>
            <input type="hidden" name="status" value="{{ status }}" required>
            <input type="hidden" name="mode" value="{{ payment_mode }}" required>
            <input type="hidden" name="txnid" value="{{ txnid }}" required>
            <input type="hidden" name="hash" value="{{ hash }}" required>
            <input type="hidden" name="paymentId" value="{{ paymentId }}" required>
        </form>
    </body>
    </html>
    """

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


    return render_template_string(form_template,surl=surl, phonepe_transactionid=phonepe_transactionid,status=status,mode=payment_mode,txnid=txnid,paymentId=paymentId,hash=hash)


@app.route('/Verify',methods=['GET','POST'])
def verify():
    mihpayid = request.form['mihpayid']
    status = request.form['status']
    mode = request.form['mode']
    txnid = request.form['txnid']
    hash = request.form['hash']
    paymentId = request.form['paymentId']
    

    temp = {"paymentId":paymentId,"mihpayid":mihpayid,"status":status,"mode":mode,"txnid":txnid}

    return json.dumps(temp)

if __name__ == "__main__":
    app.run(debug=True,port=8080)