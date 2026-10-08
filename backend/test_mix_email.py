import importlib.util, tempfile, os, json, threading, unittest, urllib.request, urllib.error
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('mix_server',Path(__file__).with_name('mix-email-server.py'))
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)

class MixEmailTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();service.DB=self.temp.name+'/test.sqlite'
        self.env=patch.dict(os.environ,{'SMTP_HOST':'test','SMTP_USER':'test','SMTP_PASSWORD':'test','SMTP_FROM':'Northern Dial <mix@example.test>','MIX_PUBLIC_URL':'https://mix.example.test','SENDER_CONTACT':'Northern Dial test contact','RATE_SECRET':'test-only'})
        self.env.start();self.send=patch.object(service,'deliver');self.delivery=self.send.start()
        self.server=service.ThreadingHTTPServer(('127.0.0.1',0),service.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.send.stop();self.env.stop();self.temp.cleanup()
    def payload(self, optin=False):return {'email':'listener@example.test','tracks':[{'artist':'Artist & Co','title':'Song'}],'requestId':'11111111-1111-4111-8111-111111111111','recommendations':optin}
    def request(self,path='/send-mix',data=None,origin='https://www.northerndial.ca'):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Origin':origin,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_one_off_and_retry(self):
        self.assertEqual(self.request(data=self.payload())[0],200)
        self.assertEqual(self.request(data=self.payload())[0],200)
        self.assertEqual(self.delivery.call_count,1)
        with service.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM subscribers').fetchone()[0],0)
        self.assertIn('Find on Spotify',self.delivery.call_args.args[1])
    def test_opt_in_requires_confirmation_and_unsubscribe(self):
        self.assertEqual(self.request(data=self.payload(True))[0],200)
        with service.connect() as db:
            row=db.execute('SELECT confirmed,token,preferences FROM subscribers').fetchone()
        self.assertEqual(row[0],0);self.assertIn('Artist & Co',row[2])
        self.assertEqual(self.request('/confirm?token='+row[1])[0],200)
        with service.connect() as db:self.assertEqual(db.execute('SELECT confirmed FROM subscribers').fetchone()[0],1)
        self.assertEqual(self.request('/unsubscribe?token='+row[1])[0],200)
        with service.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM subscribers').fetchone()[0],0)
    def test_failure_is_not_reported_as_success(self):
        self.delivery.side_effect=TimeoutError()
        code,result=self.request(data=self.payload());self.assertEqual(code,502);self.assertNotIn('accepted',result)
        self.assertEqual(self.request(data=self.payload())[0],409)
        self.assertEqual(self.delivery.call_count,1)
    def test_recipient_rate_limit(self):
        self.assertEqual(self.request(data=self.payload())[0],200)
        p=self.payload();p['requestId']='22222222-2222-4222-8222-222222222222'
        self.assertEqual(self.request(data=p)[0],429)
    def test_invalid_and_disallowed_requests(self):
        self.assertEqual(self.request(data=self.payload(),origin='https://other.test')[0],403)
        p=self.payload();p['tracks']=p['tracks']*6
        self.assertEqual(self.request(data=p)[0],400)
        p=self.payload();p['email']='test@example.test\r\nBcc: victim@example.test'
        self.assertEqual(self.request(data=p)[0],400)
        self.delivery.assert_not_called()
    def test_missing_setup(self):
        with patch.dict(os.environ,{'SMTP_PASSWORD':''}):self.assertEqual(self.request(data=self.payload())[0],503)

if __name__=='__main__':unittest.main()
