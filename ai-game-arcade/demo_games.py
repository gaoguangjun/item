"""Built-in demo games for first-time launch."""

DEMO_GAMES = [
    {
        'title': '接球游戏',
        'description': '控制篮子接住掉落的球，越接越多越快！',
        'prompt': '一个接球游戏',
        'category': '休闲',
        'plays': 256,
        'likes': 42,
        'code': '''<!DOCTYPE html>
<html><head><style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}canvas{border-radius:8px}</style></head>
<body><canvas id="c" width="800" height="600"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');
let basket={x:370,w:80,h:20},balls=[],score=0,missed=0,over=false,speed=2,spawnRate=60,frame=0;
document.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect();basket.x=Math.max(0,Math.min(c.width-basket.w,e.clientX-r.left-basket.w/2))});
document.addEventListener('touchmove',e=>{e.preventDefault();const r=c.getBoundingClientRect(),t=e.touches[0];basket.x=Math.max(0,Math.min(c.width-basket.w,t.clientX-r.left-basket.w/2))},{passive:false});
document.addEventListener('click',()=>{if(over){over=false;score=0;missed=0;balls=[];speed=2;frame=0}});
function spawn(){balls.push({x:Math.random()*(c.width-20)+10,y:-20,r:10,color:`hsl(${Math.random()*360},70%,60%)`)})}
function draw(){
if(over){x.fillStyle='#fff';x.font='48px sans-serif';x.textAlign='center';x.fillText('游戏结束',c.width/2,c.height/2-30);x.font='24px sans-serif';x.fillText(`得分: ${score}  点击重新开始`,c.width/2,c.height/2+30);return}
x.fillStyle='#0f0f1a';x.fillRect(0,0,c.width,c.height);
frame++;if(frame%spawnRate===0)spawn();
balls.forEach(b=>{b.y+=speed;x.beginPath();x.arc(b.x,b.y,b.r,0,Math.PI*2);x.fillStyle=b.color;x.fill()});
balls=balls.filter(b=>{
if(b.y+b.r>=c.height-basket.h&&b.x>=basket.x&&b.x<=basket.x+basket.w){score+=10;speed+=0.1;if(spawnRate>20)spawnRate--;return false}
if(b.y>c.height+20){missed++;if(missed>=5)over=true;return false}return true});
x.fillStyle='#6366f1';x.fillRect(basket.x,c.height-basket.h,basket.w,basket.h);
x.fillStyle='#fff';x.font='20px sans-serif';x.textAlign='left';x.fillText(`得分: ${score}`,20,35);x.fillText(`生命: ${5-missed}`,20,65);
requestAnimationFrame(draw)}draw()</script></body></html>'''
    },
    {
        'title': '打砖块',
        'description': '经典打砖块游戏，控制挡板反弹小球消除所有砖块。',
        'prompt': '打砖块游戏',
        'category': '益智',
        'plays': 512,
        'likes': 78,
        'code': '''<!DOCTYPE html>
<html><head><style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}canvas{border-radius:8px}</style></head>
<body><canvas id="c" width="800" height="600"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');
let pad={x:350,w:100,h:14},ball={x:400,y:500,dx:4,dy:-4,r:8},bricks=[],score=0,over=false,won=false;
const cols=10,rows=5,bw=72,bh=24,gap=4,ox=30,oy=50;
const colors=['#ef4444','#f59e0b','#22c55e','#3b82f6','#8b5cf6'];
for(let r=0;r<rows;r++)for(let cl=0;cl<cols;cl++)bricks.push({x:ox+cl*(bw+gap),y:oy+r*(bh+gap),w:bw,h:bh,alive:true,color:colors[r]});
document.addEventListener('mousemove',e=>{const rc=c.getBoundingClientRect();pad.x=Math.max(0,Math.min(c.width-pad.w,e.clientX-rc.left-pad.w/2))});
document.addEventListener('touchmove',e=>{e.preventDefault();const rc=c.getBoundingClientRect(),t=e.touches[0];pad.x=Math.max(0,Math.min(c.width-pad.w,t.clientX-rc.left-pad.w/2))},{passive:false});
document.addEventListener('click',()=>{if(over||won){over=false;won=false;score=0;ball={x:400,y:500,dx:4,dy:-4,r:8};bricks.forEach(b=>b.alive=true)}});
function draw(){
x.fillStyle='#0f0f1a';x.fillRect(0,0,c.width,c.height);
if(over){x.fillStyle='#fff';x.font='48px sans-serif';x.textAlign='center';x.fillText('游戏结束',c.width/2,c.height/2-20);x.font='20px sans-serif';x.fillText(`得分: ${score} 点击重新开始`,c.width/2,c.height/2+30);requestAnimationFrame(draw);return}
if(won){x.fillStyle='#22c55e';x.font='48px sans-serif';x.textAlign='center';x.fillText('恭喜通关!',c.width/2,c.height/2-20);x.font='20px sans-serif';x.fillText(`得分: ${score} 点击重新开始`,c.width/2,c.height/2+30);requestAnimationFrame(draw);return}
ball.x+=ball.dx;ball.y+=ball.dy;
if(ball.x-ball.r<0||ball.x+ball.r>c.width)ball.dx*=-1;
if(ball.y-ball.r<0)ball.dy*=-1;
if(ball.y+ball.r>=c.height-pad.h&&ball.x>=pad.x&&ball.x<=pad.x+pad.w){ball.dy=-Math.abs(ball.dy);ball.dx+=((ball.x-(pad.x+pad.w/2))/pad.w)*2}
if(ball.y>c.height+20){over=true}
bricks.forEach(b=>{if(!b.alive)return;if(ball.x+ball.r>b.x&&ball.x-ball.r<b.x+b.w&&ball.y+ball.r>b.y&&ball.y-ball.r<b.y+b.h){b.alive=false;ball.dy*=-1;score+=10}});
if(bricks.every(b=>!b.alive))won=true;
bricks.forEach(b=>{if(b.alive){x.fillStyle=b.color;x.fillRect(b.x,b.y,b.w,b.h)}});
x.fillStyle='#6366f1';x.fillRect(pad.x,c.height-pad.h,pad.w,pad.h);
x.beginPath();x.arc(ball.x,ball.y,ball.r,0,Math.PI*2);x.fillStyle='#fff';x.fill();
x.fillStyle='#fff';x.font='20px sans-serif';x.textAlign='left';x.fillText(`得分: ${score}`,20,30);
requestAnimationFrame(draw)}draw()</script></body></html>'''
    },
    {
        'title': '贪吃蛇',
        'description': '经典贪吃蛇游戏，吃掉食物让蛇越来越长！',
        'prompt': '贪吃蛇游戏',
        'category': '益智',
        'plays': 340,
        'likes': 56,
        'code': '''<!DOCTYPE html>
<html><head><style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}canvas{border-radius:8px}</style></head>
<body><canvas id="c" width="800" height="600"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d'),sz=20,cols=40,rows=30;
let snake=[{x:20,y:15}],dir={x:1,y:0},next={x:1,y:0},food={x:10,y:10},score=0,over=false,tick=0,speed=8;
function spawnFood(){food={x:Math.floor(Math.random()*cols),y:Math.floor(Math.random()*rows)}}
spawnFood();
document.addEventListener('keydown',e=>{
if(e.key==='ArrowUp'&&dir.y!==1)next={x:0,y:-1};
if(e.key==='ArrowDown'&&dir.y!==-1)next={x:0,y:1};
if(e.key==='ArrowLeft'&&dir.x!==1)next={x:-1,y:0};
if(e.key==='ArrowRight'&&dir.x!==-1)next={x:1,y:0};
if(e.key===' '&&over){over=false;snake=[{x:20,y:15}];dir={x:1,y:0};next={x:1,y:0};score=0;speed=8;spawnFood()}
});
function draw(){
x.fillStyle='#0f0f1a';x.fillRect(0,0,c.width,c.height);
if(over){x.fillStyle='#fff';x.font='40px sans-serif';x.textAlign='center';x.fillText('游戏结束',c.width/2,c.height/2-30);x.font='20px sans-serif';x.fillText(`得分: ${score}  按空格重新开始`,c.width/2,c.height/2+20);return}
tick++;if(tick%speed===0){
dir=next;const h={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
if(h.x<0||h.x>=cols||h.y<0||h.y>=rows||snake.some(s=>s.x===h.x&&s.y===h.y)){over=true;return}
snake.unshift(h);
if(h.x===food.x&&h.y===food.y){score+=10;spawnFood();if(speed>3)speed--}else snake.pop()
}
snake.forEach((s,i)=>{const g=Math.max(60,255-i*8);x.fillStyle=i===0?`#6366f1`:`hsl(240,60%,${g/255*60+30}%)`;x.fillRect(s.x*sz,s.y*sz,sz-1,sz-1)});
x.fillStyle='#ef4444';x.fillRect(food.x*sz,food.y*sz,sz-1,sz-1);
x.fillStyle='#fff';x.font='20px sans-serif';x.textAlign='left';x.fillText(`得分: ${score}`,20,30);
requestAnimationFrame(draw)}draw()</script></body></html>'''
    },
    {
        'title': '点击反应',
        'description': '点击屏幕上随机出现的圆圈，越快得分越高！',
        'prompt': '点击反应游戏',
        'category': '休闲',
        'plays': 180,
        'likes': 33,
        'code': '''<!DOCTYPE html>
<html><head><style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}canvas{border-radius:8px;cursor:pointer}</style></head>
<body><canvas id="c" width="800" height="600"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');
let circles=[],score=0,timeLeft=30,started=false,gameOver=false,lastSpawn=0;
c.addEventListener('click',e=>{
if(gameOver){gameOver=false;score=0;timeLeft=30;circles=[];started=false;return}
const rc=c.getBoundingClientRect(),mx=e.clientX-rc.left,my=e.clientY-rc.top;
for(let i=circles.length-1;i>=0;i--){
const ci=circles[i],d=Math.hypot(mx-ci.x,my-ci.y);
if(d<ci.r){const bonus=Math.max(10,Math.floor(50-ci.r));score+=bonus;circles.splice(i,1);break}
}
if(!started)started=true;
});
let timer=null;
function startTimer(){if(timer)clearInterval(timer);timer=setInterval(()=>{if(started&&!gameOver){timeLeft--;if(timeLeft<=0){gameOver=true;clearInterval(timer)}}},1000)}
function draw(){
x.fillStyle='#0f0f1a';x.fillRect(0,0,c.width,c.height);
if(gameOver){x.fillStyle='#fff';x.font='48px sans-serif';x.textAlign='center';x.fillText('时间到!',c.width/2,c.height/2-40);x.font='28px sans-serif';x.fillText(`最终得分: ${score}`,c.width/2,c.height/2+20);x.font='18px sans-serif';x.fillText('点击重新开始',c.width/2,c.height/2+60);return}
if(started){
const now=Date.now();
if(now-lastSpawn>800){circles.push({x:Math.random()*700+50,y:Math.random()*450+80,r:Math.random()*30+15,maxR:Math.random()*30+15,born:now,life:2000,color:`hsl(${Math.random()*360},70%,60%)`});lastSpawn=now}
circles=circles.filter(ci=>{const age=Date.now()-ci.born;ci.r=ci.maxR*(1-age/ci.life);return ci.r>2});
}
circles.forEach(ci=>{x.beginPath();x.arc(ci.x,ci.y,ci.r,0,Math.PI*2);x.fillStyle=ci.color;x.globalAlpha=0.8;x.fill();x.globalAlpha=1});
x.fillStyle='#fff';x.font='20px sans-serif';x.textAlign='left';x.fillText(`得分: ${score}`,20,35);x.textAlign='right';x.fillText(`时间: ${timeLeft}s`,c.width-20,35);
if(!started){x.fillStyle='rgba(0,0,0,0.6)';x.fillRect(0,0,c.width,c.height);x.fillStyle='#fff';x.font='32px sans-serif';x.textAlign='center';x.fillText('点击任意位置开始',c.width/2,c.height/2)}
requestAnimationFrame(draw)}
startTimer();draw()</script></body></html>'''
    },
]
