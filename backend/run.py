from app import app

if __name__ == "__main__":
    print("\n=== AI智能助手后端服务 ===")
    print("正在启动服务，端口: 5100")
    app.run(host='0.0.0.0', port=5100, debug=True) 