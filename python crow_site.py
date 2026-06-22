import json
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_BOT_TOKEN = "тут_не_потрібен_для_сайту"
OPENMODEL_API_KEY = "om-2fLAUbzjVVqRZvkqmv8vWKEdma2THm5JnRMHMWbybi6"

OPENMODEL_BASE_URL = "https://api.openmodel.ai"
OPENMODEL_MODEL = "deepseek-v4-flash"
MAX_OUTPUT_TOKENS = 8200

SYSTEM_PROMPT = """
You are Crow AI, a smart and friendly AI assistant.
Always answer in the same language the user used.
You are running on deepseek-v4-flash through OpenModel API.
Do not say you are GPT, ChatGPT, OpenAI, Claude, Gemini, or another model.
If user asks for prompt, code, letter, message, text, essay, post, script, template, plan or ready-to-copy content:
write a short intro, then put ready content between [QUOTE] and [/QUOTE].
Do not use markdown code fences.
Be clear, useful and direct.
"""

HTML = r"""
<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crow AI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#0b1220;color:#e5e7eb;height:100vh;overflow:hidden}
.app{height:100vh;display:flex;justify-content:center;background:#0b1220}
.chat{width:100%;max-width:900px;height:100vh;display:flex;flex-direction:column;background:#0f172a;border-left:1px solid #1e293b;border-right:1px solid #1e293b}
.header{height:64px;padding:14px 18px;border-bottom:1px solid #1e293b;display:flex;align-items:center;gap:12px}
.avatar{width:38px;height:38px;border-radius:50%;background:#22c55e;color:#052e16;display:flex;align-items:center;justify-content:center;font-weight:900}
.title strong{display:block;font-size:16px}.title span{font-size:12px;color:#93c5fd}
.messages{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:78%;padding:12px 14px;border-radius:14px;line-height:1.45;font-size:15px;white-space:pre-wrap;word-break:break-word}
.user{align-self:flex-end;background:#2563eb;color:white;border-bottom-right-radius:5px}
.bot{align-self:flex-start;background:#1e293b;color:white;border-bottom-left-radius:5px}
.error{align-self:flex-start;background:#3f1d1d;color:#fecaca;border:1px solid #7f1d1d}
.quote{margin-top:8px;padding:10px 12px;border-left:4px solid #22c55e;background:#052e16;color:#dcfce7;border-radius:8px;white-space:pre-wrap}
.form{padding:12px;border-top:1px solid #1e293b;display:flex;gap:10px;background:#0f172a}
textarea{flex:1;min-height:44px;max-height:140px;resize:none;border:1px solid #334155;outline:none;border-radius:10px;background:#020617;color:white;padding:12px;font-size:15px}
button{width:48px;height:44px;border:0;border-radius:10px;background:#22c55e;color:#052e16;font-weight:900;cursor:pointer}
button:disabled{opacity:.5}
@media(max-width:600px){.chat{max-width:none;border:0}.messages{padding:12px}.msg{max-width:88%;font-size:14px}.header{height:58px;padding:10px 12px}.form{padding:8px}}
</style>
</head>
<body>
<div class="app">
<div class="chat">
<header class="header">
<div class="avatar">C</div>
<div class="title"><strong>Crow AI</strong><span>deepseek-v4-flash через OpenModel</span></div>
</header>
<main class="messages" id="messages">
<div class="msg bot">Привіт! Я Crow AI. Напиши питання або тему, і я допоможу.</div>
</main>
<form class="form" id="form">
<textarea id="input" placeholder="Напиши повідомлення..." rows="1"></textarea>
<button id="btn">➤</button>
</form>
</div>
</div>

<script>
const messagesEl=document.getElementById("messages");
const form=document.getElementById("form");
const input=document.getElementById("input");
const btn=document.getElementById("btn");
const history=[];

function scroll(){messagesEl.scrollTop=messagesEl.scrollHeight}
function esc(t){return t.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}
function add(cls,text,html=false){
  const d=document.createElement("div");
  d.className="msg "+cls;
  html?d.innerHTML=text:d.textContent=text;
  messagesEl.appendChild(d);scroll();return d;
}
function format(text){
  text=text.replace(/```(?:\w+)?\s*([\s\S]*?)```/g,"[QUOTE]$1[/QUOTE]");
  let out="",last=0,re=/\[QUOTE\]([\s\S]*?)\[\/QUOTE\]/g,m;
  while((m=re.exec(text))){
    const before=text.slice(last,m.index).trim();
    const quote=m[1].trim();
    if(before) out+=`<div>${esc(before)}</div>`;
    if(quote) out+=`<div class="quote">${esc(quote)}</div>`;
    last=re.lastIndex;
  }
  const after=text.slice(last).trim();
  if(after) out+=`<div>${esc(after)}</div>`;
  return out || esc(text);
}
function detectLang(t){
  const s=t.toLowerCase();
  if(/[іїєґ]/i.test(s))return"uk";
  if(/[ыэъё]/i.test(s))return"ru";
  if(/\b(what|which|language|model|you|work|use|are)\b/i.test(s))return"en";
  return"uk";
}
function localAnswer(t){
  const s=t.toLowerCase(), lang=detectLang(t);
  const model=["модель","моделі","модели","model","gpt","chatgpt"].some(w=>s.includes(w));
  const language=["мова","мові","мовою","язык","языке","language"].some(w=>s.includes(w));
  if(model){
    if(lang==="ru")return"Я Crow AI. Сейчас я работаю на модели deepseek-v4-flash через OpenModel API.";
    if(lang==="en")return"I am Crow AI. I am powered by deepseek-v4-flash through the OpenModel API.";
    return"Я Crow AI. Зараз я працюю на моделі deepseek-v4-flash через OpenModel API.";
  }
  if(language){
    if(lang==="ru")return"Я могу работать на разных языках. Обычно отвечаю на том языке, на котором ты пишешь.";
    if(lang==="en")return"I can work in many languages. I usually reply in the same language you use.";
    return"Я можу працювати різними мовами. Зазвичай відповідаю тією мовою, якою ти пишеш.";
  }
  return null;
}
form.addEventListener("submit",async e=>{
  e.preventDefault();
  const text=input.value.trim();
  if(!text)return;
  add("user",text);
  input.value="";
  btn.disabled=true;
  const typing=add("bot","Crow AI пише...");
  try{
    let answer=localAnswer(text);
    if(!answer){
      const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:[...history,{role:"user",content:text}]})});
      const data=await r.json();
      if(!r.ok)throw new Error(data.error||"Unknown error");
      answer=data.answer;
    }
    typing.remove();
    add("bot",format(answer),true);
    history.push({role:"user",content:text});
    history.push({role:"assistant",content:answer});
  }catch(err){
    typing.remove();
    add("error","Помилка запиту до AI:\\n\\n"+err.message);
  }finally{
    btn.disabled=false;
    input.focus();
  }
});
input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();form.requestSubmit()}});
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        messages = body.get("messages", [])

        payload = {
            "model": OPENMODEL_MODEL,
            "system": SYSTEM_PROMPT,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0.5,
            "messages": messages,
        }

        req = urllib.request.Request(
            f"{OPENMODEL_BASE_URL}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENMODEL_API_KEY}",
                "x-api-key": OPENMODEL_API_KEY,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                data = json.loads(res.read().decode("utf-8"))

            answer = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    answer += block.get("text", "")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"answer": answer.strip()}).encode("utf-8"))

        except Exception as error:
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(error)}).encode("utf-8"))


print("Crow AI site started: http://localhost:8000")
HTTPServer(("localhost", 8000), Handler).serve_forever()