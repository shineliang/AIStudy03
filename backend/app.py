from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import sqlite3
import json
import os
import requests
from datetime import datetime
import time
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI as CommunityChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import Dict, List, Optional, Any
import threading
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('assistant.db')
    cursor = conn.cursor()
    
    # 创建历史对话表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        ai_message TEXT,
        timestamp TEXT
    )
    ''')
    
    # 创建工具使用记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tool_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT,
        parameters TEXT,
        result TEXT,
        timestamp TEXT
    )
    ''')
    
    # 创建记忆记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        content TEXT,
        created_at TEXT
    )
    ''')
    
    # 创建考勤记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        date TEXT, 
        time TEXT, 
        type TEXT
    )
    ''')
    
    # 创建排班信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shift (
        name TEXT, 
        date TEXT, 
        detail TEXT
    )
    ''')
    
    # 创建请假记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leave (
        date TEXT, 
        type TEXT, 
        duration TEXT, 
        reason TEXT
    )
    ''')
    
    # 插入模拟数据
    cursor.execute("SELECT count(*) FROM attendance")
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
        INSERT INTO attendance VALUES
            ("2025-03-01", "09:00", "签到"),
            ("2025-03-01", "18:00", "签退"),
            ("2025-03-02", "09:15", "签到"),
            ("2025-03-02", "17:45", "签退"),
            ("2025-03-04", "08:50", "签到"),
            ("2025-03-04", "18:30", "签退"),
            ("2025-03-05", "08:50", "签到"),
            ("2025-03-05", "18:30", "签退"),
            ("2025-03-06", "08:50", "签到"),
            ("2025-03-06", "18:30", "签退"),
            ("2025-03-07", "08:50", "签到"),
            ("2025-03-07", "18:30", "签退");
        ''')
    
    cursor.execute("SELECT count(*) FROM shift")
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
        INSERT INTO shift VALUES
            ("钟晓樑", "2025-02-17", "周一:上午09:00-下午05:00(保洁)"),
            ("钟晓樑", "2025-02-18", "周二:上午10:00-下午12:00(保洁) 下午13:00 -下午06:00(值班)"),
            ("钟晓樑", "2025-02-19", "周三:上午10:00-下午12:00(保洁) 下午13:00 -下午06:00(值班)"),
            ("钟晓樑", "2025-02-20", "周四:上午9:00-下午5:00(保洁)"),
            ("钟晓樑", "2025-02-21", "周五:上午8:00-下午4:00(值班)"),
            ("钟晓樑", "2025-02-22", "周六:休息"),
            ("钟晓樑", "2025-02-23", "周日:休息"),
            ("钟晓樑", "2025-03-01", "周六:休息"),
            ("钟晓樑", "2025-03-02", "周日:休息"),
            ("钟晓樑", "2025-03-03", "周一:上午09:00-下午05:00(保洁)"),
            ("钟晓樑", "2025-03-04", "周二:上午10:00-下午12:00(保洁) 下午13:00 -下午06:00(值班)"),
            ("钟晓樑", "2025-03-05", "周三:上午10:00-下午12:00(保洁) 下午13:00 -下午06:00(值班)"),
            ("钟晓樑", "2025-03-06", "周四:上午9:00-下午5:00(保洁)"),
            ("钟晓樑", "2025-03-07", "周五:上午8:00-下午4:00(值班)"),
            ("钟晓樑", "2025-03-08", "周六:休息"),
            ("钟晓樑", "2025-03-09", "周日:休息"),
            ("钟晓樑", "2025-03-10", "周一:上午09:00-下午05:00(保洁)"),
            ("钟晓樑", "2025-03-11", "周二:上午10:00-下午12:00(保洁) 下午13:00 -下午06:00(值班)"),
            ("钟晓樑", "2025-03-12", "周三:休息"),
            ("钟晓樑", "2025-03-13", "周四:上午9:00-下午5:00(保洁)"),
            ("钟晓樑", "2025-03-14", "周五:上午8:00-下午4:00(值班)"),
            ("钟晓樑", "2025-03-15", "周六:上午9:00 下午2:00(值班)"),
            ("钟晓樑", "2025-03-16", "周日:休息");
        ''')
    
    cursor.execute("SELECT count(*) FROM leave")
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
        INSERT INTO leave VALUES
            ("2025-03-01", "事假", "1小时", "家里有事"),
            ("2025-03-02", "病假", "2小时", "感冒发烧"),
            ("2025-03-03", "事假", "1小时", "家里有事"),
            ("2025-03-04", "病假", "2小时", "感冒发烧");
        ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 工具函数：记录工具使用
def record_tool_usage(tool_name, parameters, result):
    conn = sqlite3.connect('assistant.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO tool_usage (tool_name, parameters, result, timestamp) VALUES (?, ?, ?, ?)",
        (tool_name, json.dumps(parameters), result, timestamp)
    )
    
    conn.commit()
    conn.close()

# 工具函数：记录记忆
def record_memory(memory_type, content):
    conn = sqlite3.connect('assistant.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO memory (type, content, created_at) VALUES (?, ?, ?)",
        (memory_type, content, timestamp)
    )
    
    conn.commit()
    conn.close()

# 工具函数：记录对话历史
def record_chat_history(user_message, ai_message):
    conn = sqlite3.connect('assistant.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO chat_history (user_message, ai_message, timestamp) VALUES (?, ?, ?)",
        (user_message, ai_message, timestamp)
    )
    
    conn.commit()
    conn.close()

# 工具1：高德地图天气API
def get_weather(city: str) -> str:
    """查询指定城市的天气信息"""
    try:
        api_key = os.environ.get("AMAP_API_KEY")
        if not api_key:
            return "错误：未设置高德地图API密钥，请在.env文件中设置AMAP_API_KEY"
            
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "1" and data["lives"]:
            weather_info = data["lives"][0]
            result = f"{city}天气：{weather_info['weather']}，温度{weather_info['temperature']}℃，湿度{weather_info['humidity']}%，风向{weather_info['winddirection']}，风力{weather_info['windpower']}级"
            record_tool_usage("天气查询", {"city": city}, result)
            return result
        else:
            error_msg = f"无法获取{city}的天气信息"
            record_tool_usage("天气查询", {"city": city}, error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"天气查询出错: {str(e)}"
        record_tool_usage("天气查询", {"city": city}, error_msg)
        return error_msg

# 工具2：抖音热搜API
def get_douyin_hot() -> str:
    """查询当前抖音热搜榜单"""
    try:
        api_key = os.environ.get("TIANAPI_KEY")
        if not api_key:
            return "错误：未设置天行API密钥，请在.env文件中设置TIANAPI_KEY"
            
        url = "https://apis.tianapi.com/douyinhot/index"
        payload = {"key": api_key}
        response = requests.post(url, data=payload)
        data = response.json()
        
        if data["code"] == 200:
            hot_list = data["result"]["list"]
            result = "抖音热搜榜单：\n"
            for i, item in enumerate(hot_list[:10], 1):
                result += f"{i}. {item['word']} - 热度: {item['hotindex']}\n"
            
            record_tool_usage("抖音热搜", {}, result)
            return result
        else:
            error_msg = f"获取抖音热搜失败: {data['msg']}"
            record_tool_usage("抖音热搜", {}, error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"抖音热搜查询出错: {str(e)}"
        record_tool_usage("抖音热搜", {}, error_msg)
        return error_msg

# 工具3：考勤记录查询
def query_attendance(start_date: str, end_date: Optional[str] = None) -> str:
    """查询指定日期范围内的考勤记录"""
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        
        if end_date:
            cursor.execute(
                "SELECT date, time, type FROM attendance WHERE date BETWEEN ? AND ? ORDER BY date, time",
                (start_date, end_date)
            )
        else:
            cursor.execute(
                "SELECT date, time, type FROM attendance WHERE date = ? ORDER BY time",
                (start_date,)
            )
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            result = f"未找到{start_date}到{end_date or start_date}的考勤记录"
            record_tool_usage("考勤记录查询", {"start_date": start_date, "end_date": end_date}, result)
            return result
        
        result = f"考勤记录（{start_date}到{end_date or start_date}）：\n"
        for date, time, record_type in records:
            result += f"{date} {time} {record_type}\n"
        
        record_tool_usage("考勤记录查询", {"start_date": start_date, "end_date": end_date}, result)
        return result
    except Exception as e:
        error_msg = f"考勤记录查询出错: {str(e)}"
        record_tool_usage("考勤记录查询", {"start_date": start_date, "end_date": end_date}, error_msg)
        return error_msg

# 工具4：排班信息查询
def query_shift(start_date: str, end_date: Optional[str] = None) -> str:
    """查询指定日期范围内的排班信息"""
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        
        if end_date:
            cursor.execute(
                "SELECT date, detail FROM shift WHERE date BETWEEN ? AND ? ORDER BY date",
                (start_date, end_date)
            )
        else:
            cursor.execute(
                "SELECT date, detail FROM shift WHERE date = ?",
                (start_date,)
            )
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            result = f"未找到{start_date}到{end_date or start_date}的排班信息"
            record_tool_usage("排班信息查询", {"start_date": start_date, "end_date": end_date}, result)
            return result
        
        result = f"排班信息（{start_date}到{end_date or start_date}）：\n"
        for date, detail in records:
            result += f"{date}: {detail}\n"
        
        record_tool_usage("排班信息查询", {"start_date": start_date, "end_date": end_date}, result)
        return result
    except Exception as e:
        error_msg = f"排班信息查询出错: {str(e)}"
        record_tool_usage("排班信息查询", {"start_date": start_date, "end_date": end_date}, error_msg)
        return error_msg

# 工具5：请假申请
def create_leave(date: str, leave_type: str, duration: str, reason: str) -> str:
    """创建请假申请记录"""
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        
        # 检查是否已存在该日期的请假记录
        cursor.execute("SELECT * FROM leave WHERE date = ?", (date,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE leave SET type = ?, duration = ?, reason = ? WHERE date = ?",
                (leave_type, duration, reason, date)
            )
            result = f"已更新{date}的请假申请：类型-{leave_type}，时长-{duration}，原因-{reason}"
        else:
            cursor.execute(
                "INSERT INTO leave (date, type, duration, reason) VALUES (?, ?, ?, ?)",
                (date, leave_type, duration, reason)
            )
            result = f"已创建{date}的请假申请：类型-{leave_type}，时长-{duration}，原因-{reason}"
        
        conn.commit()
        conn.close()
        
        record_tool_usage("请假申请", {
            "date": date,
            "type": leave_type,
            "duration": duration,
            "reason": reason
        }, result)
        
        # 记录用户偏好
        record_memory("用户偏好", f"用户申请了{leave_type}，原因是{reason}")
        
        return result
    except Exception as e:
        error_msg = f"请假申请出错: {str(e)}"
        record_tool_usage("请假申请", {
            "date": date,
            "type": leave_type,
            "duration": duration,
            "reason": reason
        }, error_msg)
        return error_msg

# 工具6：休假信息查询
def query_leave(start_date: str, end_date: Optional[str] = None) -> str:
    """查询指定日期范围内的休假信息"""
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        
        if end_date:
            cursor.execute(
                "SELECT date, type, duration, reason FROM leave WHERE date BETWEEN ? AND ? ORDER BY date",
                (start_date, end_date)
            )
        else:
            cursor.execute(
                "SELECT date, type, duration, reason FROM leave WHERE date = ?",
                (start_date,)
            )
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            result = f"未找到{start_date}到{end_date or start_date}的休假记录"
            record_tool_usage("休假信息查询", {"start_date": start_date, "end_date": end_date}, result)
            return result
        
        result = f"休假记录（{start_date}到{end_date or start_date}）：\n"
        for date, leave_type, duration, reason in records:
            result += f"{date}: {leave_type}，时长-{duration}，原因-{reason}\n"
        
        record_tool_usage("休假信息查询", {"start_date": start_date, "end_date": end_date}, result)
        return result
    except Exception as e:
        error_msg = f"休假信息查询出错: {str(e)}"
        record_tool_usage("休假信息查询", {"start_date": start_date, "end_date": end_date}, error_msg)
        return error_msg

# 创建工具列表
tools = [
    StructuredTool.from_function(get_weather),
    StructuredTool.from_function(get_douyin_hot),
    StructuredTool.from_function(query_attendance),
    StructuredTool.from_function(query_shift),
    StructuredTool.from_function(create_leave),
    StructuredTool.from_function(query_leave)
]

# 创建记忆
memory = ChatMessageHistory()

# 创建系统提示
system_prompt = """你是一个智能助手，可以帮助用户查询天气、抖音热搜、考勤记录、排班信息、休假信息，以及提交请假申请。
请使用中文回复用户，并尽可能提供详细和有用的信息。
今天日期是 {{current_date}}

如果用户询问的内容需要使用工具，请使用相应的工具来获取信息。
如果用户的请求不明确，请礼貌地询问更多细节。"""

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 创建LLM
try:
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("警告：未设置OpenAI API密钥，请在.env文件中设置OPENAI_API_KEY")
    
    llm = ChatOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        streaming=True,
        temperature=0
    )
except Exception as e:
    print(f"初始化LLM出错: {str(e)}")
    llm = None

# 创建Agent
try:
    if llm:
        agent = create_openai_functions_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # 限制最大迭代次数
            early_stopping_method="force"  # 强制在达到最大迭代次数时停止
        )
        
        # 添加消息历史处理
        agent_with_chat_history = RunnableWithMessageHistory(
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: x.get("agent_scratchpad", [])
            ) | agent_executor,
            lambda session_id: memory,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    else:
        print("警告：LLM初始化失败，Agent将无法正常工作")
        agent_executor = None
        agent_with_chat_history = None
except Exception as e:
    print(f"初始化Agent出错: {str(e)}")
    agent_executor = None
    agent_with_chat_history = None

# 流式响应生成器
def generate_stream_response(user_message):
    if not agent_with_chat_history:
        yield "系统错误：AI助手未正确初始化，请检查API密钥设置。"
        return
    
    response_chunks = []
    
    try:
        # 获取当前日期和时间
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 在用户消息中添加当前日期信息
        user_message_with_date = f"{user_message}\n\n当前日期: {current_date}"
        
        for chunk in agent_with_chat_history.stream(
            {"input": user_message_with_date},
            {"configurable": {"session_id": "default"}}
        ):
            if "output" in chunk:
                content = chunk["output"]
                response_chunks.append(content)
                yield content
    except Exception as e:
        error_msg = f"处理请求时出错: {str(e)}"
        yield error_msg
        response_chunks.append(error_msg)
    
    # 完成后记录对话历史
    full_response = "".join(response_chunks)
    
    # 在单独的线程中记录，避免阻塞响应
    threading.Thread(
        target=record_chat_history,
        args=(user_message, full_response)
    ).start()
    
    # 分析用户消息并记录记忆
    if "天气" in user_message:
        threading.Thread(
            target=record_memory,
            args=("用户兴趣", "用户对天气信息感兴趣")
        ).start()
    elif "排班" in user_message:
        threading.Thread(
            target=record_memory,
            args=("用户兴趣", "用户关注排班信息")
        ).start()
    elif "考勤" in user_message:
        threading.Thread(
            target=record_memory,
            args=("用户兴趣", "用户关注考勤记录")
        ).start()

# API路由：对话接口
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    
    return Response(
        stream_with_context(generate_stream_response(user_message)),
        content_type='text/plain'
    )

# API路由：历史记录接口
@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_message, ai_message, timestamp FROM chat_history ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        history = [
            {"user": row[0], "ai": row[1], "timestamp": row[2]}
            for row in rows
        ]
        
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：工具使用记录接口
@app.route('/api/tool-usage', methods=['GET'])
def get_tool_usage():
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        cursor.execute("SELECT tool_name, parameters, result, timestamp FROM tool_usage ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        tool_usages = [
            {
                "tool_name": row[0],
                "parameters": json.loads(row[1]),
                "result": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]
        
        return jsonify({"tool_usages": tool_usages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：记忆记录接口
@app.route('/api/memories', methods=['GET'])
def get_memories():
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        cursor.execute("SELECT type, content, created_at FROM memory ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        memories = [
            {"type": row[0], "content": row[1], "created_at": row[2]}
            for row in rows
        ]
        
        return jsonify({"memories": memories})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：推荐问题接口
@app.route('/api/suggested-questions', methods=['GET'])
def get_suggested_questions():
    context = request.args.get('context', '')
    
    # 默认推荐问题
    default_questions = [
        "今天北京的天气怎么样？",
        "查询最近的抖音热搜",
        "查询我本周的考勤记录",
        "查询我本周的排班信息",
        "查询我本月的休假记录",
        "我想请明天的事假"
    ]
    
    # 根据上下文生成相关推荐问题
    if context and llm:
        try:
            # 使用LLM生成相关问题
            prompt = f"""
            基于以下对话上下文，生成3个用户可能想问的后续问题：
            
            {context}
            
            请只返回问题列表，每行一个问题，不要有其他内容。
            """
            
            response = llm.invoke(prompt).content
            questions = [q.strip() for q in response.split('\n') if q.strip()]
            
            if questions:
                # 如果成功生成了问题，与默认问题合并
                return jsonify({"questions": questions + default_questions[:2]})
        except Exception as e:
            print(f"生成推荐问题出错: {str(e)}")
    
    # 如果没有上下文或生成失败，返回默认问题
    return jsonify({"questions": default_questions})

if __name__ == '__main__':
    # 检查环境变量
    missing_keys = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.environ.get("AMAP_API_KEY"):
        missing_keys.append("AMAP_API_KEY")
    if not os.environ.get("TIANAPI_KEY"):
        missing_keys.append("TIANAPI_KEY")
    
    if missing_keys:
        print(f"警告：以下环境变量未设置: {', '.join(missing_keys)}")
        print("请在.env文件中设置这些环境变量")
    
    app.run(host='0.0.0.0', port=5100, debug=True) 