import sanic
from sanic import response
import paypalrestsdk
import asyncio
import math
import textwrap
from sanic_jinja2 import SanicJinja2
from jinja2 import select_autoescape
from sanic_compress import Compress
import usaddress

from gsheet import GSheet

paypalrestsdk.configure({
  "mode": "live", # sandbox or live
  "client_id": "",
  "client_secret": "" })

app = sanic.Sanic(__name__)
Compress(app)
jinja = SanicJinja2(app, autoescape=select_autoescape(['html', 'xml']))

@app.listener('before_server_start')
async def setup(app, loop):
    app.sheet = GSheet('GSHEET_LINK', loop=loop)

@app.route('/')
@jinja.template('index.html')
async def render_form(req):
    return

@app.route('/api/new_request', methods=['POST'])
async def post_new_request(req):
    """
    Process the incoming data
    """
    data = req.json
    # put the data onto the sheet!
    print(data)
    try:
        #raise TypeError()

        payment = paypalrestsdk.Payment.find(data['payment']['paymentID'])
        
        if payment.execute({"payer_id": data['payment']['payerID']}):
            print("Payment execute successfully")
        else:
            print(payment.error) # Error Hash
            return response.json({'success': False, 'error': 'Payment did not execute correctly'})
    except:
        return response.json({'success': False, 'error': 'There was a problem during the transaction. Please make sure you have the right information typed in.'})

    user_address = usaddress.parse(data['user']['address'])
    parts = [x[0] for x in user_address]

    columns = [
        data['user']['full_name'],
        data['user']['email'],
        data['user']['address'],
        data['user']['description'],
        data['user']['relief'],
        data['payment']['paymentID'],
        payment['transactions'][0]['related_resources'][0]['sale']['id'],
        ' ',
        *parts
    ]
    ret = await app.sheet.insert(columns)

    return response.json({'success': True})




@app.route('/api/verify_input', methods=['POST'])
async def api_verify_input(req):
    data = req.json
    total_content = render_data(data['user'])
    return response.json({
        'amount': page_count_to_human(predict_page_count(total_content)),
        'actual_used': predict_page_count(total_content)
    })

def page_count_to_human(page_count):
    page_str = str(page_count[1])
    first_half = page_str.split('.')[0]
    return f'Using {aah}/4 pages.'

def predict_page_count(input):
    MAX_WIDTH = 78
    MAX_HEIGHT = 48
    PAGES = 4

    line_count = 0
    for line in input.splitlines():
        if len(line) >= MAX_WIDTH:
            new_lines = textwrap.wrap(line, width=MAX_WIDTH)
            line_count += len(new_lines)
        else:
            line_count += 1

    pages = line_count / MAX_HEIGHT
    return line_count, math.ceil(pages)

def render_data(user):
    return """Pre-Arbitration Claim Resolution Form

To:
ZeniMax Media Inc.
Attn: Legal Dep't
1370 Piccard Drive
Rockville, MD 20850
USA


"ZENIMAX MEDIA TERMS OF SERVICE"
"15....... Dispute Resolution, Arbitration and Class Action Waiver"
"For all Disputes, whether pursued in court or arbitration, You must first give ZeniMax an opportunity to resolve the Dispute. You must commence this process by mailing written notification to ZeniMax Media Inc., Attn: Legal Dep't, 1370 Piccard Drive, Rockville, MD 20850 USA. That written notification must include (1) Your name, (2) Your address, (3) a written description of Your Dispute, and (4) a description of the specific relief You seek. If ZeniMax does not resolve the Dispute to your satisfaction within forty-five (45) days after receipt of Your written notification, You may pursue Your Dispute in arbitration. You may pursue Your Dispute in a court only under the circumstances described below."


(1) Your name,
{full_name}

(2) Your address,
{address}

(3) a written description of Your Dispute, and
{description}

(4) a description of the specific relief You seek
{relief}
    """.format(**user)

if __name__ == '__main__':
    app.run('0.0.0.0', 8086)