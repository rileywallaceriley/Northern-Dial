from PIL import Image, ImageDraw, ImageFont
import random, os

ROOT='/root/.openclaw/workspace'
OUT=os.path.join(ROOT,'Northern-Dial/instagram-posts/northern-dial-recently-played-20260904.png')
ART=os.path.join(ROOT,'Northern-Dial/instagram-posts/preview-last-five')
W=H=1080
random.seed(19)

def font(size,bold=False):
    p='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf'
    return ImageFont.truetype(p,size) if os.path.exists(p) else ImageFont.load_default()

def fit_cover(path,size):
    im=Image.open(path).convert('RGB')
    r=max(size[0]/im.width,size[1]/im.height)
    im=im.resize((int(im.width*r),int(im.height*r)),Image.Resampling.LANCZOS)
    l,t=(im.width-size[0])//2,(im.height-size[1])//2
    return im.crop((l,t,l+size[0],t+size[1]))

img=Image.new('RGB',(W,H),'#eee1c8'); d=ImageDraw.Draw(img)
d.polygon([(0,0),(460,0),(405,70),(520,155),(0,205)],fill='#e34022')
d.polygon([(685,0),(1080,0),(1080,345),(990,300),(900,360),(790,260)],fill='#171717')
d.polygon([(0,870),(150,805),(300,885),(255,1080),(0,1080)],fill='#173b56')
d.polygon([(820,740),(1080,670),(1080,1080),(755,1080)],fill='#e34022')
d.polygon([(700,900),(830,835),(920,905),(800,1010)],fill='#173b56')
for i in range(30):
    x=random.randint(0,W); y=random.randint(0,H)
    d.line((x,y,x+random.randint(-180,180),y+random.randint(-60,60)),fill='#b7a78c',width=random.choice([1,2,3]))
for i in range(2600):
    x,y=random.randrange(W),random.randrange(H)
    d.point((x,y),fill=random.choice(['#c8b99f','#ffffff','#5e5345']))

d.text((62,48),'NORTHERN',font=font(62,True),fill='#171717')
d.text((62,108),'DIAL',font=font(112,True),fill='#f7edd8')
d.text((68,224),'RECENTLY PLAYED',font=font(34,True),fill='#171717')
d.line((68,276,1012,276),fill='#171717',width=5)
d.text((68,291),'5 TRACKS IN ROTATION',font=font(23,True),fill='#d34022')

items=[('01','JUSTO THE MC + DK','THIS IS ME'),('02','TRE CAPITAL × WONDAGURL','BIG CAPITAL'),('03','6LACK','UNFAIR'),('04','VT + LIL BERETE','CLUB'),('05','BELLY','HOLLYWOOD INTERLUDE')]
positions=[(68,350),(400,350),(732,350),(234,690),(566,690)]
for idx,((num,artist,title),(x,y)) in enumerate(zip(items,positions),1):
    d.rectangle((x+9,y+11,x+289,y+291),fill='#171717')
    img.paste(fit_cover(os.path.join(ART,f'{idx}.jpg'),(280,280)),(x,y))
    d=ImageDraw.Draw(img)
    d.rectangle((x,y,x+280,y+280),outline='#f7edd8',width=5)
    d.rectangle((x+12,y+12,x+70,y+60),fill='#e34022')
    d.text((x+25,y+18),num,font=font(27,True),fill='#f7edd8')
    d.rectangle((x,y+214,x+280,y+280),fill='#171717')
    d.text((x+10,y+219),artist,font=font(17,True),fill='#f7edd8')
    d.text((x+10,y+244),title,font=font(18,True),fill='#e34022')

d.rectangle((68,1010,1012,1040),fill='#171717')
d.text((68,1048),'NORTHERN DIAL  /  CANADIAN MUSIC DISCOVERY',font=font(17,True),fill='#171717')
d.text((785,1048),'northerndial.ca',font=font(17,True),fill='#d93622')
img.save(OUT,quality=96,subsampling=0)
print(OUT)
