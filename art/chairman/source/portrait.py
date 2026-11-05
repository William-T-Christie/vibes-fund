import math,sys,os
I='#161513'; P='#F4F3EE'; A='{{accent}}'
out=[]; defs=[]
def add(s): out.append(s)
def path(d,fill='none',stroke=I,sw=1,extra=''):
    add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}></path>')
def hatch(cid, region, angle, spacing, bbox, sw=0.7, color=I):
    defs.append(f'<clipPath id="{cid}"><path d="{region}"></path></clipPath>')
    x0,y0,x1,y1=bbox; cx,cy=(x0+x1)/2,(y0+y1)/2
    R=math.hypot(x1-x0,y1-y0)/2+2
    a=math.radians(angle); dx,dy=math.cos(a),math.sin(a); nx,ny=-dy,dx
    n=int(R/spacing)+1; d=[]
    for k in range(-n,n+1):
        ox,oy=cx+nx*k*spacing,cy+ny*k*spacing
        d.append(f'M{ox-dx*R:.1f} {oy-dy*R:.1f}L{ox+dx*R:.1f} {oy+dy*R:.1f}')
    add(f'<path clip-path="url(#{cid})" d="{"".join(d)}" fill="none" stroke="{color}" stroke-width="{sw}"></path>')

def taper(p0,c,p1,w0,w1,sw=1.1,n=18):
    L=[];R=[]
    for i in range(n+1):
        t=i/n
        x=(1-t)**2*p0[0]+2*(1-t)*t*c[0]+t*t*p1[0]
        y=(1-t)**2*p0[1]+2*(1-t)*t*c[1]+t*t*p1[1]
        dx=2*(1-t)*(c[0]-p0[0])+2*t*(p1[0]-c[0]); dy=2*(1-t)*(c[1]-p0[1])+2*t*(p1[1]-c[1])
        m=math.hypot(dx,dy) or 1; nx,ny=-dy/m,dx/m
        w=(w0+(w1-w0)*t)/2
        L.append((x+nx*w,y+ny*w)); R.append((x-nx*w,y-ny*w))
    r=w1/2
    d='M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in L)
    d+=f' A{r:.2f} {r:.2f} 0 0 1 {R[-1][0]:.2f} {R[-1][1]:.2f} L'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in reversed(R))+' Z'
    path(d,fill=P,sw=sw)

CHAIR="M48 500 L48 250 C48 205 62 190 78 196 L78 150 C78 78 134 44 200 44 C266 44 322 78 322 150 L322 196 C338 190 352 205 352 250 L352 500 Z"
BACK="M104 500 L104 164 C104 104 148 74 200 74 C252 74 296 104 296 164 L296 500 Z"
ARML="M22 430 C22 404 56 396 84 408 L120 428 L120 500 L22 500 Z"
ARMR="M378 430 C378 404 344 396 316 408 L280 428 L280 500 L378 500 Z"
HEAD=("M200 212 C182 212 170 221 166 236 C163 245 163 252 161 257 C160 260 161 263 163 266 "
      "C161 273 157 280 151 286 C146 291 141 294 137 298 C135 300 136 304 140 305 "
      "C145 306 151 305 155 305 C156 308 156 311 155 313 C156 315 158 316 159 316 "
      "C157 318 157 320 158 322 C159 324 158 327 157 330 C159 335 166 338 176 338 "
      "C196 337 216 327 230 309 C240 301 244 286 242 268 C242 236 228 212 200 212 Z")
BODY=("M132 500 L134 442 C134 410 140 386 152 370 C163 357 175 348 188 343 L212 343 "
      "C225 348 237 357 248 370 C260 386 266 410 266 442 L268 500 Z")
OPEN="M182 345 L200 351 L218 345 L216 432 L200 472 L184 432 Z"
VEST="M185 378 L200 397 L215 378 L215 432 L200 470 L185 432 Z"

add('<g clip-path="url(#a3p-frame)" stroke-linejoin="round" stroke-linecap="round">')
# chair
for d in (CHAIR,ARML,ARMR):
    add(f'<path d="{d}" fill="{A}"></path><path d="{d}" fill="url(#a3-screen)"></path>')
hatch('a3p-tuft',BACK,45,34,(104,74,296,500),0.6)
hatch('a3p-tuft2',BACK,-45,34,(104,74,296,500),0.6)
hatch('a3p-sh1',"M270 92 C290 110 296 130 296 164 L296 404 L283 404 C284 340 282 200 270 92 Z",60,3.4,(260,90,300,406),0.6)
SH="M246 330 C254 340 260 352 264 364 C272 384 278 410 280 440 L282 448 L270 448 C268 420 264 400 258 380 C254 366 248 352 240 342 Z"

path(CHAIR,sw=2.6); path(BACK.replace(' Z',''),sw=1.2)
path("M78 196 L78 500 M322 196 L322 500 M84 200 C90 190 96 186 104 186 M316 200 C310 190 304 186 296 186",sw=1.2)
for d in (ARML,ARMR): path(d,sw=2.6)
path("M30 432 C34 416 56 412 70 420 M370 432 C366 416 344 412 330 420 M36 446 C44 440 60 438 72 444 M364 446 C356 440 340 438 328 444",sw=1)
btn=[(x,y) for y in [91,125,159,193,227,261,295,329] for x in [132,166,200,234,268]]+[(x,y) for y in [108,142,176,210,244,278,312] for x in [115,149,183,217,251,285]]
add('<g fill="'+I+'">'+''.join(f'<circle cx="{x}" cy="{y}" r="1.8"></circle>' for x,y in btn)+'</g>')

# ---- seat cushion: top behind his hips, front edge below his knees
CUSH="M120 436 C160 432 240 432 280 436 L280 492 L120 492 Z"
path(CUSH,fill=A,stroke='none'); path(CUSH,fill='url(#a3-screen)',stroke='none')
path("M120 436 C160 432 240 432 280 436",sw=2.0)
path("M120 464 C160 461 240 461 280 464",sw=2.0)
path("M121 468 C160 465 240 465 279 468",sw=0.8)
# ---- legs: thighs run forward to the seat edge, knees sit on the edge, shins hang over the front
LAP="M160 462 L160 442 C176 438 190 434 200 427 C210 434 224 438 240 442 L240 462 Z"
path(LAP,fill=I,stroke='none')
path("M160 462 L160 442 M240 442 L240 462",sw=1.6)
SHL="M166 465 L169.4 481 L187 481 L190.6 465 Z"; SHR="M209.4 465 L213 481 L230.6 481 L234 465 Z"
for d in (SHL,SHR): path(d,fill=I,sw=1.6)
for d in ("M160 462 C160 456 168 453 179 453 C190 453 198.8 456 198.8 462 C198.8 467 191 470 179 470 C167 470 160 467 160 462 Z",
          "M201.2 462 C201.2 456 210 453 221 453 C232 453 240 456 240 462 C240 467 233 470 221 470 C209 470 201.2 467 201.2 462 Z"):
    path(d,fill=I,sw=1.6)
path("M200 443 L200 455",stroke=P,sw=0.9)
path("M167 457.4 C172 455.4 185 455.4 191 457.4 M209 457.4 C215 455.4 228 455.4 233 457.4",stroke=P,sw=0.8)
for d in ("M163 483.4 C163 478.4 170 476.8 178 476.8 C186 476.8 193.4 478.4 193.4 483.4 C193.4 488.4 186 490.4 178 490.4 C170 490.4 163 488.4 163 483.4 Z",
          "M206.6 483.4 C206.6 478.4 214 476.8 222 476.8 C230 476.8 237 478.4 237 483.4 C237 488.4 230 490.4 222 490.4 C214 490.4 206.6 488.4 206.6 483.4 Z"):
    path(d,fill=I,sw=1.4)
path("M168 480.8 C172 479.2 182 479.2 187 480.6 M212 480.6 C217 479.2 227 479.2 231.4 480.8",stroke=P,sw=0.8)

# ---- the figure, drawn at full size and set down 20% smaller so the chair dwarfs him
add('<g transform="translate(200 440) scale(0.8) translate(-200 -440)">')
# ---- jacket: small torso, skirt resting on the lap
BODY=("M150 444 C151 434 152 426 152 416 C150 398 148 380 156 366 C164 356 176 348 188 343 L212 343 "
      "C224 348 236 356 244 366 C252 380 250 398 248 416 C248 426 249 434 250 444 "
      "C240 447 226 447 214 442 L200 426 L186 442 C174 447 160 447 150 444 Z")
path(BODY,fill=I,sw=2.2)
OPEN="M182 345 L200 351 L218 345 L216 420 L200 426 L184 420 Z"
path(OPEN,fill=P,sw=1.3)
VEST="M185 376 L200 396 L215 376 L215.6 420 L200 425 L184.4 420 Z"
hatch('a3p-vest',VEST,35,2.2,(184,376,216,442),0.6)
hatch('a3p-vest2',VEST,-55,2.8,(184,376,216,442),0.5)
path(VEST,sw=1.2)
path("M182 345 L172 380 L184 390 L186 432 M218 345 L228 380 L216 390 L214 432",stroke=P,sw=1.3)
path("M158 362 C166 356 174 351 182 348 M242 362 C234 356 226 351 218 348",stroke=P,sw=0.8)
path("M152 444 C164 447 176 446 186 442 M248 444 C236 447 224 446 214 442",stroke=P,sw=0.8)
# carnation: round ruffled head, small calyx, printed in mood ink
import math as _m
cx,cy=238,373.6
pts=[]
for k in range(73):
    t=k/72*2*_m.pi
    r=6.4+0.9*_m.cos(14*t)
    pts.append((cx+r*_m.cos(t),cy+r*0.86*_m.sin(t)))
CARN='M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in pts)+' Z'
path(CARN,fill=A,stroke='none'); path(CARN,fill='url(#a3-screen-sm)',stroke='none'); path(CARN,stroke=P,sw=0.9)
path("M235.6 379.6 L238 383 L240.4 379.6 Z",fill=I,stroke=P,sw=0.8)
path("M238 383 L236.6 392",stroke=P,sw=1)

# ---- neck, collar, tie
NECK="M186 316 L186 345 L215 345 L215 318 Z"
path(NECK,fill=P,sw=1.8); hatch('a3p-neck',NECK,35,2.6,(184,314,217,347),0.6)
path("M184.6 345.6 L184.6 333 C193 336.2 207 336.2 215.4 333 L215.4 345.6 Z",fill=P,sw=1.3)
path("M196 335.4 L188.4 340.8 L197.2 342 Z M204 335.4 L211.6 340.8 L202.8 342 Z",fill=P,sw=1.1)
path("M187.6 342 L200 348 L212.4 342 L213.4 356 L200 351 L186.6 356 Z",fill=I,sw=1)
path("M196.8 345.6 L203.2 345.6 L203.2 352.6 L196.8 352.6 Z",fill=I,stroke=I,sw=0.8)

# ---- head
path(HEAD,fill=P,stroke='none')
hatch('a3p-face',"M216 222 C236 232 246 262 242 284 C240 302 230 318 212 331 C222 312 228 292 227 270 C226 250 222 234 216 222 Z",62,2.6,(210,220,246,334),0.6)
hatch('a3p-face2',"M168 330 C184 340 206 334 226 318 C214 333 196 340 180 339 C174 338 170 335 168 330 Z",-28,2.4,(164,316,228,341),0.55)
path(HEAD,sw=2.4)
# ear, fringe, wisps (unchanged near side)
path("M232 270 C244 265 251 278 246 290 C243 298 236 301 231 296",fill=P,sw=1.8)
path("M236 276 C241 280 241 287 237 291 M238 282 C236 284 236 286 238 288",sw=0.9)
fr=[]
for i in range(9):
    x=228+i*2.0; y=248+i*1.5
    fr.append(f'M{x:.1f} {y:.1f} C{x+5:.1f} {y+8:.1f} {x+6:.1f} {y+16:.1f} {x+4:.1f} {y+24:.1f}')
for i in range(4):
    x=238+i*1.2; y=292+i*1.6
    fr.append(f'M{x:.1f} {y:.1f} C{x+3:.1f} {y+5:.1f} {x+1:.1f} {y+10:.1f} {x-3:.1f} {y+14:.1f}')
fr.append('M222 262 C225 270 225 280 223 290 M219 264 C221 272 221 280 220 287 M216 266 C218 272 218 278 217 283')
path(" ".join(fr),sw=0.75)
path("M184 221 C198 214 214 216 226 225 M190 218 C204 212 219 215 230 228 M196 216 C206 213 214 214 220 217",sw=0.8)
path("M174 240 C182 236 191 236 199 239 M176 246 C183 243 190 243 196 245",sw=0.7)
# near brow, eye, lens (unchanged)
path("M172.6 256.6 C176 251.6 182 248.6 188.6 248.6 C193 248.6 196.6 250.4 198.4 254.6 C193.6 252.6 188 252.4 182.6 253.6 C179 254.4 175.6 255.4 172.6 256.6 Z",fill=I,sw=0.8)
path("M178 269 C182 266 188 266 191 269",sw=1.8)
path("M179 271 C183 273 187 273 190 271 M180 275 C183 276 186 276 189 275",sw=0.7)
add(f'<circle cx="184.5" cy="269.5" r="1.5" fill="{I}"></circle>')
path("M196 267 C196 279 190 280 184 280 C176 280 173 274 173 268 C173 261 178 258 185 258 C192 258 196 261 196 267 Z",sw=1.3)
path("M188 261 C191 263 192 266 192 268",sw=0.6)
path("M196 265 L233 273",sw=1.2)
# far side: the far lens is hidden behind the nose; only the bridge shows

path("M173 265 C170.6 262 166.4 261.8 163.4 264.2",sw=1.2)
# nose: wing, bridge shading, fold
path("M149 300 C151 296.5 155 296.5 157 300 C157.6 302 156.6 303.6 155 304",sw=1.3)
path("M167 271 C165 280 159 288 152 294",sw=0.8)
path("M158 296 C165 302 168 308 169.5 313",sw=0.8)
# mouth, lips, chin
path("M159 316 C164 315.6 170 316.4 175 318.4 C176.4 319.2 177.2 320.4 177.5 322",sw=1.6)
path("M160 322.5 L163 320.5 M162.5 323.5 L165.5 321.2 M165 323.8 L168 321.6",sw=0.6)
path("M153.5 307.5 L156.3 305.6 M154.6 310 L157 308.3",sw=0.6)
path("M162 330 C166 332 170 332 173 330",sw=0.8)

# ---- arms as separate sleeves so you can follow each one, then the cup set
UA_R="M157 364 C150 378 144 398 140 416 C138 426 135 434 133 442 L144 446 C146 432 150 416 156 398 Z"
FA_R="M133 442 C134 432 137 424 140.6 418.6 L148.6 426.6 C147 434 145.6 440 144 446 Z"
UA_L="M243 364 C250 378 256 398 260 416 C262 426 265 434 267 442 L256 446 C254 432 250 416 244 398 Z"
FA_L="M267 442 C262 432 252 426 243.4 422.6 L244.8 436.2 C248 440 252 443 256 446 Z"
for d in (UA_R,UA_L,FA_R,FA_L):
    path(d,fill=I,stroke='none')
path("M156 398 C150 416 146 432 144 446 M148.6 426.6 C147 434 145.6 440 144 446",stroke=P,sw=1.1)
path("M244 398 C250 416 254 432 256 446 M243.4 422.6 C252 426 262 432 267 442 M244.8 436.2 C248 440 252 443 256 446",stroke=P,sw=1.1)
path("M157 364 C150 378 144 398 140 416 C138 426 135 434 133 442 L144 446",sw=1.8)
path("M243 364 C250 378 256 398 260 416 C262 426 265 434 267 442 L256 446",sw=1.8)
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import importlib, cupset; importlib.reload(cupset)
cupset.build(path,hatch,add)
add('</g>')
add('</g>')
add(f'<rect x="1" y="1" width="398" height="498" fill="none" stroke="{I}" stroke-width="2"></rect>')
add(f'<rect x="7.5" y="7.5" width="385" height="485" fill="none" stroke="{I}" stroke-width="0.75"></rect>')
defs.insert(0,'<clipPath id="a3p-frame"><rect x="8" y="8" width="384" height="484"></rect></clipPath>')
svg=('<svg viewBox="0 0 400 500" width="100%" role="img" aria-label="Pen and ink portrait of Sir Peregrine Ashby, a small balding man with a long nose, bushy raised eyebrows and thin round spectacles, in a wing collar, bow tie and waistcoat, lifting a cup of tea from its saucer with his little finger raised, almost swallowed by an enormous tufted wingback chair upholstered in today\'s mood ink" style="display: block; background: #F4F3EE">\n<defs>'+''.join(defs)+'</defs>\n'+'\n'.join(out)+'\n</svg>')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'portrait.svgfrag'),'w').write(svg)
