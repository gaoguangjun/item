"""AI game code generator using LLM API."""

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = """你是一个专业的HTML5游戏开发者。用户会描述一个游戏，你需要生成一个完整的、可直接运行的HTML5游戏代码。

要求：
1. 输出一个完整的HTML文档（包含<!DOCTYPE html>）
2. 使用HTML5 Canvas进行游戏渲染
3. 所有CSS和JavaScript必须内联在HTML中
4. 游戏必须包含：开始画面、游戏逻辑、得分系统、结束画面
5. 添加触控和键盘控制支持
6. 画面风格要色彩丰富、有趣
7. 游戏区域大小固定为800x600像素
8. 代码中不要使用外部资源（图片、音频等）
9. 不要使用alert/prompt/confirm
10. body背景色使用 #1a1a2e，Canvas居中显示
11. 支持鼠标和触摸控制

请直接输出HTML代码，不要添加markdown代码块标记。"""


def generate_game(prompt, category=''):
    """Generate HTML5 game code from text prompt."""
    if not LLM_API_KEY:
        return _fallback_game(prompt)

    try:
        import urllib.request
        import json

        # Use raw HTTP to avoid openai package dependency
        url = LLM_BASE_URL.rstrip('/') + '/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LLM_API_KEY}'
        }
        payload = json.dumps({
            'model': LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f'请创建一个游戏：{prompt}' + (f'\n游戏类型：{category}' if category else '')}
            ],
            'max_tokens': 4096,
            'temperature': 0.8,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx) as resp:
            result = json.loads(resp.read().decode())
            code = result['choices'][0]['message']['content'].strip()
            return _clean_game_code(code)

        user_msg = f'请创建一个游戏：{prompt}'
        if category:
            user_msg += f'\n游戏类型：{category}'

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_msg}
            ],
            max_tokens=4096,
            temperature=0.8,
        )

        code = response.choices[0].message.content.strip()
        return _clean_game_code(code)

    except Exception as e:
        print(f'AI generation error: {e}')
        return _fallback_game(prompt)


def _clean_game_code(raw):
    """Strip markdown code fences if present."""
    code = raw.strip()
    if code.startswith('```html'):
        code = code[len('```html'):]
    elif code.startswith('```'):
        code = code[3:]
    if code.endswith('```'):
        code = code[:-3]
    return code.strip()


def _fallback_game(prompt):
    """Return a simple demo game when no API key is configured."""
    template = '''<!DOCTYPE html>
<html><head><style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}canvas{border-radius:8px}</style></head>
<body><canvas id="c" width="800" height="600"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');
let circles=[],score=0,timeLeft=30,started=false,over=false;
c.addEventListener('click',e=>{
if(over){over=false;score=0;timeLeft=30;circles=[];started=false;return}
const rc=c.getBoundingClientRect(),mx=e.clientX-rc.left,my=e.clientY-rc.top;
for(let i=circles.length-1;i>=0;i--){
const ci=circles[i],d=Math.hypot(mx-ci.x,my-ci.y);
if(d<ci.r){score+=Math.max(10,50-Math.floor(ci.r));circles.splice(i,1);break}
}
if(!started)started=true;
});
let timer=null;
function startTimer(){if(timer)clearInterval(timer);timer=setInterval(()=>{if(started&&!over){timeLeft--;if(timeLeft<=0){over=true;clearInterval(timer)}}},1000)}
let lastSpawn=0;
function draw(){
x.fillStyle='#0f0f1a';x.fillRect(0,0,c.width,c.height);
if(over){x.fillStyle='#fff';x.font='48px sans-serif';x.textAlign='center';x.fillText('Time Up!',c.width/2,c.height/2-40);x.font='28px sans-serif';x.fillText('Score: '+score,c.width/2,c.height/2+20);x.font='18px sans-serif';x.fillText('Click to restart',c.width/2,c.height/2+60);return}
if(started){const now=Date.now();if(now-lastSpawn>700){circles.push({x:Math.random()*700+50,y:Math.random()*450+80,r:Math.random()*30+15,maxR:Math.random()*30+15,born:now,life:2000,color:'hsl('+Math.random()*360+',70%,60%)'});lastSpawn=now}
circles=circles.filter(ci=>{const age=Date.now()-ci.born;ci.r=ci.maxR*(1-age/ci.life);return ci.r>2})}
circles.forEach(ci=>{x.beginPath();x.arc(ci.x,ci.y,ci.r,0,Math.PI*2);x.fillStyle=ci.color;x.globalAlpha=0.8;x.fill();x.globalAlpha=1});
x.fillStyle='#fff';x.font='20px sans-serif';x.textAlign='left';x.fillText('Score: '+score,20,35);x.textAlign='right';x.fillText('Time: '+timeLeft+'s',c.width-20,35);
if(!started){x.fillStyle='rgba(0,0,0,0.6)';x.fillRect(0,0,c.width,c.height);x.fillStyle='#fff';x.font='32px sans-serif';x.textAlign='center';x.fillText('Click to Start',c.width/2,c.height/2-20);x.font='18px sans-serif';x.fillText('PROMPT_PLACEHOLDER',c.width/2,c.height/2+20)}
requestAnimationFrame(draw)}startTimer();draw()
</script></body></html>'''
    return template.replace('PROMPT_PLACEHOLDER', prompt.replace("'", "\\'"))
