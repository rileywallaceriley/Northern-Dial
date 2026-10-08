"""Northern Dial mix email service. Run behind an HTTPS reverse proxy."""
import os, json, sqlite3, hashlib, hmac, secrets, time, smtplib, ssl
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

DB = os.getenv('MIX_DB', './mix-email.sqlite3')
CONSENT = 'Email me music recommendations and stories based on my mix.'
ORIGINS = {'https://www.northerndial.ca', 'https://northerndial.ca'}

def connect():
    db = sqlite3.connect(DB, timeout=20)
    db.executescript('''
      CREATE TABLE IF NOT EXISTS deliveries (id TEXT PRIMARY KEY, digest TEXT, state TEXT, created INTEGER);
      CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, count INTEGER, expires INTEGER);
      CREATE TABLE IF NOT EXISTS subscribers (email TEXT PRIMARY KEY, preferences TEXT, token TEXT UNIQUE, confirmed INTEGER DEFAULT 0, consent TEXT, created INTEGER, confirmed_at INTEGER);
    ''')
    return db

def validate(data):
    email = data.get('email', '')
    if not isinstance(email,str) or len(email)>254 or '\n' in email or '\r' in email or ' ' in email or email.count('@')!=1 or '.' not in email.split('@')[-1]:
        raise ValueError('Enter a valid email address.')
    tracks = data.get('tracks')
    if not isinstance(tracks,list) or not 1<=len(tracks)<=5:
        raise ValueError('Choose between one and five songs.')
    clean = []
    for t in tracks:
        if not isinstance(t,dict) or any(not isinstance(t.get(k),str) or not t[k].strip() or len(t[k])>300 or '\n' in t[k] or '\r' in t[k] for k in ('title','artist')):
            raise ValueError('Invalid song details.')
        clean.append({k:t[k].strip() for k in ('title','artist')})
    rid = data.get('requestId','')
    if not isinstance(rid,str) or len(rid)!=36 or any(c not in '0123456789abcdef-' for c in rid.lower()):
        raise ValueError('Invalid request ID.')
    if type(data.get('recommendations',False)) is not bool:
        raise ValueError('Invalid recommendation choice.')
    return email.strip().lower(),clean,rid,data.get('recommendations',False)

def email_text(tracks, token=None):
    text = 'Your Northern Dial mix\n\n'
    for i,t in enumerate(tracks,1):
        q = quote(t['artist']+' '+t['title'],safe='')
        text += f"{i}. {t['artist']} - {t['title']}\nFind on YouTube: https://www.youtube.com/results?search_query={q}\nFind on Spotify: https://open.spotify.com/search/{q}\n\n"
    text += 'These links search for your songs on the listening services.\nhttps://www.northerndial.ca\n'
    if token:
        base = os.environ['MIX_PUBLIC_URL'].rstrip('/')
        text += f'\nYou asked for future music recommendations and stories based on this mix. Confirm your subscription:\n{base}/confirm?token={token}\n\nCancel this request or unsubscribe:\n{base}/unsubscribe?token={token}\n'
        text += os.environ['SENDER_CONTACT']+'\n'
    else:
        text += '\nThis is the song list you requested. You have not been added to a mailing list.\n'
    return text

def deliver(email, text):
    msg=EmailMessage()
    msg['From']=os.environ['SMTP_FROM']
    msg['To']=email
    msg['Subject']='Your Northern Dial mix'
    msg.set_content(text)
    host=os.environ['SMTP_HOST']; port=int(os.getenv('SMTP_PORT','587'))
    context=ssl.create_default_context()
    if port==465:
        server=smtplib.SMTP_SSL(host,port,timeout=20,context=context)
    else:
        server=smtplib.SMTP(host,port,timeout=20)
        server.starttls(context=context)
    with server:
        server.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
        refused=server.send_message(msg)
        if refused: raise RuntimeError('Recipient rejected')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass # Do not log addresses or subscription tokens.
    def reply(self,status,value):
        body=json.dumps(value).encode()
        self.send_response(status)
        origin=self.headers.get('Origin','')
        if origin in ORIGINS:self.send_header('Access-Control-Allow-Origin',origin)
        self.send_header('Vary','Origin'); self.send_header('Cache-Control','no-store')
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_OPTIONS(self):
        if self.headers.get('Origin') not in ORIGINS:return self.reply(403,{'error':'Origin not allowed.'})
        self.send_response(204);self.send_header('Access-Control-Allow-Origin',self.headers['Origin'])
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type');self.send_header('Vary','Origin');self.end_headers()
    def do_GET(self):
        path=urlparse(self.path)
        if path.path not in ('/confirm','/unsubscribe'):return self.reply(404,{'error':'Not found.'})
        token=parse_qs(path.query).get('token',[''])[0]
        if len(token)!=64:return self.reply(400,{'error':'Invalid link.'})
        with connect() as db:
            if path.path=='/confirm':
                result=db.execute('UPDATE subscribers SET confirmed=1, confirmed_at=? WHERE token=?',(int(time.time()),token))
                message='Subscription confirmed. You can unsubscribe using the link in your mix email.'
            else:
                result=db.execute('DELETE FROM subscribers WHERE token=?',(token,))
                message='You are unsubscribed.'
            if not result.rowcount:return self.reply(404,{'error':'This link is no longer active.'})
        self.reply(200,{'message':message})
    def do_POST(self):
        if self.path!='/send-mix':return self.reply(404,{'error':'Not found.'})
        if self.headers.get('Origin') not in ORIGINS:return self.reply(403,{'error':'Origin not allowed.'})
        needed=['SMTP_HOST','SMTP_USER','SMTP_PASSWORD','SMTP_FROM','MIX_PUBLIC_URL','SENDER_CONTACT','RATE_SECRET']
        if any(not os.getenv(k) for k in needed):return self.reply(503,{'error':'Direct email is not connected yet.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>8192:return self.reply(413,{'error':'Invalid request size.'})
            data=json.loads(self.rfile.read(size)); email,tracks,rid,optin=validate(data)
        except (ValueError,TypeError,AttributeError):return self.reply(400,{'error':'Check your email and song list.'})
        digest=hashlib.sha256(json.dumps([email,tracks,optin],sort_keys=True).encode()).hexdigest()
        now=int(time.time());ip=self.client_address[0]
        if os.getenv('TRUST_PROXY')=='1':ip=self.headers.get('X-Real-IP',ip)
        iphash=hmac.new(os.environ['RATE_SECRET'].encode(),ip.encode(),hashlib.sha256).hexdigest()
        emailhash=hmac.new(os.environ['RATE_SECRET'].encode(),email.encode(),hashlib.sha256).hexdigest()
        db=connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT digest,state FROM deliveries WHERE id=?',(rid,)).fetchone()
            if old:
                db.rollback()
                if old[0]!=digest:return self.reply(409,{'error':'This request ID belongs to a different mix.'})
                if old[1]=='sent':return self.reply(200,{'accepted':True})
                return self.reply(409,{'error':'This send is still being checked. Keep your mix and try again shortly.'})
            db.execute('DELETE FROM rate_limits WHERE expires < ?',(now,))
            db.execute('DELETE FROM deliveries WHERE created < ?',(now-86400*7,))
            db.execute('DELETE FROM subscribers WHERE confirmed=0 AND created < ?',(now-86400*7,))
            keys=[(f'ip:{iphash}:{now//3600}',5,now+3600),(f'email:{emailhash}:{now//600}',1,now+600),(f'day:{now//86400}',100,now+86400)]
            for key,limit,expiry in keys:
                row=db.execute('SELECT count FROM rate_limits WHERE key=?',(key,)).fetchone()
                if row and row[0]>=limit:db.rollback();return self.reply(429,{'error':'Please try again later. Your mix is still saved.'})
                db.execute('INSERT INTO rate_limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',(key,expiry))
            db.execute('INSERT INTO deliveries VALUES (?,?,?,?)',(rid,digest,'pending',now))
            token=None
            if optin:
                existing=db.execute('SELECT token FROM subscribers WHERE email=?',(email,)).fetchone()
                token=existing[0] if existing else secrets.token_hex(32)
                db.execute('INSERT INTO subscribers(email,preferences,token,consent,created) VALUES (?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET preferences=excluded.preferences, consent=excluded.consent',(email,json.dumps(tracks),token,CONSENT,now))
            db.commit()
            try:deliver(email,email_text(tracks,token))
            except Exception:
                # SMTP may have accepted an email before a network timeout. Keep
                # the request pending rather than automatically sending duplicates.
                return self.reply(502,{'error':'We could not confirm the send. Your mix is still saved; please keep it and try again later.'})
            db.execute('UPDATE deliveries SET state=? WHERE id=?',('sent',rid));db.commit()
            return self.reply(200,{'accepted':True,'recommendations':optin})
        finally:db.close()

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',int(os.getenv('PORT','8787'))),Handler)
    server.serve_forever()
