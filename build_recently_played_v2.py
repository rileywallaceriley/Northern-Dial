from PIL import Image, ImageDraw, ImageFont
import os, random
ROOT='/root/.openclaw/workspace'; ART=ROOT+'/Northern-Dial/instagram-posts/preview-last-five'
OUT=ROOT+'/Northern-Dial/instagram-posts/northern-dial-recently-played-20260904-v2.png'; W=H=1080
random.seed(44)
def F(n,b=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf'
 if not os.path.exists(p): p='/usr/share/fonts/opentype/liberation/LiberationSans-Bold.ttf' if b else '/usr/share/fonts/opentype/liberation/LiberationSans-Regular.ttf'
 return ImageFont.truetype(p,n) if os.path.exists(p) else ImageFont.load_default()
def crop(p,w,h):
 im=Image.open(p).convert('RGB'); r=max(w/im.width,h/im.height); im=im.resize((int(im.width*r),int(im.height*r)),Image.Resampling.LANCZOS); x=(im.width-w)//2; y=(im.height-h)//2; return im.crop((x,y,x+w,y+h))
im=Image.new('RGB',(W,H),'#e6dac1'); d=ImageDraw.Draw(im)
d.polygon([(0,0),(420,0),(460,150),(0,215)],fill='#d83421'); d.polygon([(660,0),(1080,0),(1080,210),(930,235),(790,150)],fill='#161616')
d.polygon([(0,900),(190,800),(420,900),(350,1080),(0,1080)],fill='#123b58'); d.polygon([(730,850),(1080,730),(1080,1080),(650,1080)],fill='#d83421')
for i in range(55):
 x=random.randrange(W); y=random.randrange(H); d.line((x,y,x+random.randrange(-170,170),y+random.randrange(-40,40)),fill=random.choice(['#b7a789','#8c806f','#f5ead5']),width=random.choice([1,2,3]))
for i in range(4500): d.point((random.randrange(W),random.randrange(H)),fill=random.choice(['#d6c8ad','#f4ead7','#8c7f6d']))
d.text((44,30),'NORTHERN',font=F(52,True),fill='#171717'); d.text((44,78),'DIAL',font=F(102,True),fill='#f3e7d0')
d.text((48,193),'RECENTLY PLAYED',font=F(48,True),fill='#171717'); d.text((52,248),'FIVE TRACKS / ONE FREQUENCY',font=F(22,True),fill='#c83321'); d.line((48,285,1032,285),fill='#171717',width=6)
items=[('01','JUSTO THE MC + DK','THIS IS ME'),('02','TRE CAPITAL × WONDAGURL','BIG CAPITAL'),('03','6LACK','UNFAIR'),('04','VT + LIL BERETE','CLUB'),('05','BELLY','HOLLYWOOD INTERLUDE')]
xs=[38,244,450,656,862]; y=330; cw,ch=174,454
for i,((num,artist,title),x) in enumerate(zip(items,xs)):
 d.polygon([(x-7,y-6),(x+cw+5,y+4),(x+cw-5,y+ch+7),(x-11,y+ch-2)],fill='#f7ecd8')
 panel=crop(f'{ART}/{i+1}.jpg',cw,ch); pd=ImageDraw.Draw(panel); pd.rectangle((0,ch-73,cw,ch),fill='#171717'); im.paste(panel,(x,y))
 d=ImageDraw.Draw(im); d.rectangle((x+10,y+12,x+64,y+57),fill='#d83421'); d.text((x+20,y+17),num,font=F(22,True),fill='#f6ead6'); d.text((x+9,y+ch-66),artist,font=F(13,True),fill='#f6ead6'); d.text((x+9,y+ch-41),title,font=F(15,True),fill='#dd3822')
d.rectangle((48,1012,1032,1046),fill='#171717')
d.text((52,1052),'NORTHERN DIAL  /  CANADIAN MUSIC DISCOVERY',font=F(16,True),fill='#171717')
d.text((856,1052),'northerndial.ca',font=F(16,True),fill='#c83321')
im.save(OUT,quality=96,subsampling=0); print(OUT)
