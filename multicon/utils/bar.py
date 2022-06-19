
import math

home="\033[H"
clear="\033[J"
up="\033[F"
upline = "\033[F\033[K"
clearln = "\033[K"
end = '\033[0;0m'
green="\033[5;32m"
red="\033[5;31m"
white="\033[5;37m"
COLOR={
    "black":"30",
    "red": "31",
    "green": "32",
    "yellow":"33",
    "blue": "34",
    "magenta": "35",
    "cyan":"36",
    "white": "37",
}
BACKGROUND={
    "black":"40",
    "red": "41",
    "green": "42",
    "yellow":"43",
    "blue": "44",
    "magenta": "45",
    "cyan":"46",
    "white": "47",
}
STYLE={
    "bold":"1",
}

def bar(current, max, maxlen=20, color="green", text=None, textcolor=None):
    if max==0:
        c=0
    else:
        if current>max: current=max
        c=current*maxlen/max
        if c<1: c=math.ceil(c)
        else: c=round(c)
    if color==None or not color in BACKGROUND:
        color="blue"
    color=BACKGROUND[color]
    unitColor = '\033[5;'+color+'m'
    if text:
        l= len(text)
        f = round((maxlen-l)/2)
        z= l+f
        if textcolor==None or textcolor not in COLOR:
            ct=COLOR['black' if color=='47' else 'white']
            ct2=COLOR['white']
        else: 
            ct=COLOR[textcolor]
            ct2=ct
        if c==0:
            line=('|'+(' '*f+ '\033[5;' +ct2+'m'+text+ end+' '*(maxlen-z))+'|')
        elif c<=f:
            line=('|'+unitColor+ ' '*c+ end
            +' '*(f-c)+ '\033[5;' +ct2+'m'+text + end+' '*(maxlen-z)+'|')
        elif c>=z:
            line=('|'+'\033[5;' +ct+'m'+unitColor+' '*f+text
            +' '*(c-z)+end+ end+' '*(maxlen-c)+'|')
        else:
            s1= text[0: c-f]
            s2= text[c-f: ]
            line=('|' +unitColor+' '*f+ end
            +'\033[5;' +ct+'m'+unitColor+s1+ end+end
            +'\033[5;' +ct2+'m'+s2+ end
            +' '*(maxlen-z)+'|')
    else:
        if c==0:
            line=('|'+(' '*maxlen)+'|')
        else:
            line=('|%s%s|' % (unitColor+ ' '*c+ end, ' '*(maxlen-c)))
    return line
def center(text, maxlen=20, pos=1):
    if text==None or text=="": return ' '*maxlen
    strlen=len(text)
    f = round((maxlen-strlen)/2)
    n= maxlen-strlen-f
    return ' '*f+ text+ ' '*n
def gettext(text, color=None, arr=None, backcolor=None, backarr=None):
    prefix = []
    suffix = []
    if color and color in arr:
        prefix.append('\033[5;'+arr[color]+'m')
        suffix.append(end)
    if backcolor and backcolor in backarr:
        prefix.append('\033[5;'+backarr[backcolor]+'m') 
        suffix.append(end)
    if isinstance(text, str):
        prefix.append(text)
    else:
        prefix.extend(text)
    prefix.extend(suffix)
    return "".join(prefix)
def getarr(text, color=None, arr=None, backcolor=None, backarr=None, style=None):
    style="bold"
    prefix = []
    suffix = []
    if color and color in arr:
        prefix.append('\033[5;'+arr[color]+'m')
        suffix.append(end)
    if backcolor and backcolor in backarr:
        prefix.append('\033[5;'+backarr[backcolor]+'m') 
        suffix.append(end)
    # if style and style in STYLE:
    #     prefix.append('\e['+STYLE[style]+'m') 
    #     suffix.append('\e[22m')
    if isinstance(text, str):
        prefix.append(text)
    else:
        prefix.extend(text)
    prefix.extend(suffix)
    return prefix
def getchar(chararr, i, defChar= ' '):
    if i in chararr:
        return chararr[i]
    return defChar
LINE = {
    "space": " ",
    "bold": "■",
    "thin": "─",
    "thin_margin": "―"
}
def barn(input=[], maxlen=20, colorarr=[], text=None, textcolor=None, space=' ', style=0, line=None, chararr=[]):
    BACKARR = BACKGROUND
    COLORARR = COLOR
    prefix = suffix = "|"
    # style=1
    # line = "thin"
    if line and line in LINE:
        space = LINE[line]
        BACKARR = COLOR
        COLORARR = {}
    if style==1:
        prefix="├"
        suffix= "┤"
        BACKARR = COLOR
        COLORARR = BACKGROUND
    # chararr = [('-' if i=="white" else "|") for i in colorarr]
    arr=[]
    input.reverse()
    p=None
    pj =0 
    t=0
    for i in input:
        if p==None:
            j=maxlen
            t=i
            pj=j
        elif t==0:
            j=0
            pj=j
        else:
            if p==0:
                i=0
            elif i>p:
                i=p
            j = (i*maxlen/t)
            j=round(j)

            # s= (pj-j)
            # if s>0 and s<1: j=math.floor(j) #loop nguoc
            # else: j=round(j)
            pj=j
        p=i
        arr.append(j)
    arr.reverse()
    lines=[prefix]
    i=0
    p=0
    m=len(colorarr)
    f=n=-1
    if text:
        l= len(text)
        f = round((maxlen-l)/2)
        z= l+f
    for k in arr:
        n = k-p
        if n==0:
            p=k
            i+=1
            continue
        if i < m:
            if  colorarr[i] in BACKARR:
                c = colorarr[i]
            else:
                c= 'white'
            if f==-1 or f>k or z<p:
                # lines.append('\033[5;'+BACKARR[c]+'m' + space*n + end)
                lines.extend(getarr(getchar(chararr, i, space)*n, c, BACKARR))
            else:
                # if textcolor==None or textcolor not in COLORARR:
                #     ct=COLORARR['black' if c=='white' else 'white']
                # else: ct=COLORARR[textcolor]
                # a=[]
                # for j in range(p, k):
                #     if j>=f and j<z:
                #         a.append(text[j-f])
                #     else: a.append(space)
                # lines.append(
                # '\033[5;' +ct +'m'+
                # '\033[5;'+BACKARR[c]+'m' 
                # + (''.join(a) )
                # +'' + end
                # +end
                # )
                if textcolor==None or textcolor not in COLORARR:
                    ct='black' if c=='white' else 'white'
                else: ct=textcolor
                a=[]
                for j in range(p, k):
                    if j>=f and j<z:
                        a.append(text[j-f])
                    else: a.append(getchar(chararr, i, space))
                lines.extend(getarr(a, ct, COLORARR, c, BACKARR))
        else: 
            if f==-1:
                lines.append(getchar(chararr, i, space)*n)
            else:
                if textcolor==None or textcolor not in COLORARR:
                    ct='white'
                else: ct=textcolor
                a=[]
                for j in range(p, k):
                    if j>=f and j<z:
                        a.append(text[j-f])
                    else: a.append(getchar(chararr, i, space))
                # lines.append('\033[5;' +COLORARR[ct] +'m'+''.join(a)+end)
                lines.extend(getarr(a, ct, COLORARR))
        i+=1
        p =k
    lines.append(suffix)
    return ''.join(lines)
def bar3(current, max, total, maxlen=20, color="green", bg=None):
    if total==0:
        c=0
        m=0
    else:
        if max>total: max=total
        m=round(max*maxlen/total)
        if current>max: current=max
        c=round(current*maxlen/total)
    if color==None or not color in BACKGROUND:
        color="blue"
    unitColor = '\033[5;'+BACKGROUND[color]+'m'
    if bg==None or not bg in BACKGROUND:
        bg="white"
    bgColor = '\033[5;'+BACKGROUND[bg]+'m'
    if m==0:
        text=('|%s%s|' % ('' , ' '*(maxlen)))
    else:
        n = m-c
        text=('|%s%s%s|' % ('' if c==0 else (unitColor + ' '*c+ end), 
        '' if n==0 else (bgColor +' '*n+  end), ' '*(maxlen-m)))
    return text
def bar2(current, max, maxlen=20):
    if max==0:
        c=0
    else:
        if current>max: current=max
        c=round(current*maxlen/max)
    text="["
    for i in range(0, c):
        text+="|"
    for i in range(c, maxlen):
        text+=" "
    text+="]"
    return text