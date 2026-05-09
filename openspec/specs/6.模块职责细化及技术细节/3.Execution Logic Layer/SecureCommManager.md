SecureCommManager / 安全通信管理模块
具体职责:

# SSL/TLS 证书管理
1. 确保证书文件存在
   - 输入:无(内部维护证书目录路径,默认为项目根目录/certs/)
   - 输出:证书绝对路径、私钥绝对路径
   - 触发场景:系统启动时(由 start.ps1 或 app.py 调用),确保 HTTPS 所需证书就绪
   - 行为:若证书文件已存在则直接返回路径;若不存在则自动生成自签名证书
   - 证书规格:RSA-2048 私钥,SHA-256 签名,SAN 扩展覆盖 localhost / 127.0.0.1 / ::1,有效期 10 年
   - 不负责的边界:不做 CA 签发证书的申请(生产环境应替换为 CA 签发证书)

2. 生成自签名 SSL 证书
   - 输入:无(证书路径由构造函数决定)
   - 输出:证书绝对路径、私钥绝对路径
   - 触发场景:ensure_certificates() 发现证书文件不存在时内部调用
   - 行为:使用 cryptography 库生成 RSA-2048 密钥对和 X.509 证书,写入 PEM 格式文件
   - 副作用:在文件系统上创建证书目录和证书文件

# SSL 配置提供
3. 获取 uvicorn SSL 启动参数
   - 输入:无
   - 输出:{"ssl_certfile": str, "ssl_keyfile": str}
   - 触发场景:uvicorn 启动时需配置 HTTPS(由 app.py __main__ 或 start.ps1 调用)
   - 行为:内部调用 ensure_certificates() 确保证书就绪,返回 uvicorn 可直接解包的 SSL 关键字参数

# 安全响应头配置
4. 获取 HTTPS 安全响应头
   - 输入:无
   - 输出:安全头映射字典
     - Strict-Transport-Security: max-age=31536000; includeSubDomains (HSTS,强制浏览器 1 年内只走 HTTPS)
     - X-Content-Type-Options: nosniff (防止 MIME 类型嗅探)
     - X-Frame-Options: DENY (防止点击劫持)
   - 触发场景:WebUI 后端中间件为每个响应附加安全头(由 app.py 中 _SecurityHeadersMiddleware 调用)

# 接口契约
5. 通过 SecureCommManagerInterface 对外暴露上述能力,被 StateScheduler 和 WebUI 调用

不需要的:[建立/维护 C-S 底层通信链路(由 uvicorn + HTTPS/TLS 保障),对任何对象做应用层加解密(原 RSA 方案已移除),向外部模块分发或暴露密钥,记录加解密操作日志]

依赖模块:无(cryptography 为运行时依赖,已在 requirements.txt 中声明)
调用接口:无
应实现接口:SecureCommManagerInterface
被依赖模块:StateScheduler, WebUI(通过 app.py)
技术细节:
- 原RSA-2048 + OAEP应用层加密方案已移除,传输层安全由 HTTPS/TLS 保障
- 账号密码传输:通过 HTTPS 明文传输,服务端由 bcrypt 哈希存储
- 私有配置文件传输:通过 HTTPS 明文传输,服务端明文存储
- 自签名证书仅供本地开发使用,生产环境应替换为 CA 签发证书(如 Let's Encrypt)
- 证书目录 certs/ 已列入 .gitignore,证书文件不纳入版本控制
- SessionMiddleware 已配置 https_only=True 和 same_site="lax",确保 Cookie 仅通过 HTTPS 传输
