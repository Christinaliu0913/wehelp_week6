from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import mysql.connector


app = FastAPI()

app.mount("/static_week7", StaticFiles(directory="static"), name="static_week7")
templates = Jinja2Templates(directory="templates")


#mysql database connection
db_config= {
    'host':'localhost',
    'user':'root',
    'password':'12345678',
    'database':'website'
}


#middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

###登出登入問題
# 定義用戶狀態的鍵
USER_STATE_KEY = "SIGNED-IN"
#登入時
def user_logged_in(req:Request,username:str):
    req.session[USER_STATE_KEY]=True
    req.session['username']=username

#登出時
def user_logger_out(req:Request):
    req.session.pop(USER_STATE_KEY,None)



#Homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#member page
@app.get("/member", response_class=HTMLResponse)
async def member(request: Request): 
    session = request.session
    if not session.get(USER_STATE_KEY, False): #檢查session 中是否存在鍵USER_STATE_KEY，並且其值是否為True，如果鍵不存在或其值為False，則條件成立。
        return RedirectResponse(url="/", status_code=303)
    username= session.get('username')
    con=mysql.connector.connect(**db_config)
    cursor = con.cursor()
    try:
        cursor.execute('''
            select member.name AS sender_name, message.content 
            from message 
            inner join member on message.member_id = member.id 
            order by message.time desc''')
        messages = cursor.fetchall()
        messages =[{'sender_name':msg[0], 'content':msg[1] } for msg in messages]
    finally:
        cursor.close()
        con.close()
    return templates.TemplateResponse("member.html", {"request": request,'username':username,'messages':messages})

#註冊帳號
@app.post("/signup")
async def signup_post(req: Request, name:str = Form(default=''), username: str = Form(default=''), password: str = Form(default='')):
    con=mysql.connector.connect(**db_config)
    cursor = con.cursor()
    try:
        if not name or not username or not password:
            return RedirectResponse(url="/", status_code=303)
        cursor.execute('select id from member where username=%s',(username,))
        member = cursor.fetchone() #check
        print(member)
        if member:
            return RedirectResponse(url="/error?message=使用者名稱已被註冊", status_code=303)
        cursor.execute('insert into member(name,username,password) value(%s,%s,%s)',(name,username,password))
        con.commit()
        return RedirectResponse(url='/',status_code=303)
    finally:    
        cursor.close()
        con.close()
        

#登入驗證
@app.post("/signin")
async def signin_post(req: Request, username: str = Form(default=""), password: str = Form(default="")):
    con=mysql.connector.connect(**db_config)
    cursor = con.cursor()
    try:
        if not username or not password:
            return RedirectResponse(url="/", status_code=303)
        cursor.execute("select username from member where username=%s and password=%s",(username, password))
        member = cursor.fetchone()
        if member is None:
            return RedirectResponse(url='/error?message=你的帳號或密碼不正確',status_code=303)
        user_logged_in(req,username)
        return RedirectResponse(url='/member',status_code=303)
    finally:    
        cursor.close()
        con.close()

#創建留言
@app.post("/createMessage")
async def createMessage_post(req: Request, content: str=Form(default='')):
    session = req.session
    if not content:
        return RedirectResponse(url='/member',status_code=303)
    username = session.get('username')
    try:
        con = mysql.connector.connect(**db_config)
        cursor = con.cursor()
        cursor.execute('select id from member where username=%s',(username,))
        member_id = cursor.fetchone()
        print(member_id)
        if member_id:
            member_id = member_id[0]
            cursor.fetchall()
            cursor.execute('insert into message(member_id, content) value(%s,%s)',(member_id, content))
            con.commit()
        return RedirectResponse(url='/member',status_code=303)
    finally:
        cursor.close()
        con.close()
    

#登出
@app.get('/signout',response_class=HTMLResponse)
async def signout( req: Request):
    user_logger_out(req)
    return RedirectResponse(url='/',status_code=303)

# 顯示不同錯誤的消息
@app.get("/error", response_class=HTMLResponse)
async def error(req: Request, message: str = None):
    return templates.TemplateResponse("error.html", {"request": req, "message": message})





# 讓termial run python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)