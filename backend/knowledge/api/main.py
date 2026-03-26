import logging

# 配置日志系统：
# level=logging.INFO 表示显示 INFO、WARNING、ERROR 等级别的日志
logging.basicConfig(level=logging.INFO)

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

import uvicorn
from fastapi import FastAPI


def create_fast_api() -> FastAPI:
    """
    创建并返回 FastAPI 应用实例
    """

    # 1. 创建 FastAPI 实例
    # title 会显示在 Swagger 文档页面中
    app = FastAPI(title="Knowledge API")

    # 2. 注册项目中的路由
    # 这样 router 里定义的所有接口都会挂载到 app 上
    app.include_router(router=router)

    # 3. 返回创建好的 FastAPI 应用对象
    return app


if __name__ == "__main__":
    # 程序直接运行时，会从这里开始执行
    print("1. 准备启动 Web 服务器")

    try:
        # 启动 Uvicorn 服务器
        # app=create_fast_api()：创建 FastAPI 应用
        # host="127.0.0.1"：表示只允许本机访问
        # port=8001：服务运行端口
        uvicorn.run(app=create_fast_api(), host="127.0.0.1", port=8001)

        # 注意：
        # uvicorn.run() 是阻塞运行的，只有服务停止后才会继续执行下面这行
        logger.info("2. 启动 Web 服务器成功...")

    except KeyboardInterrupt as e:
        # 当你手动按下 Ctrl+C 停止服务时，会进入这里
        logger.error(f"2. 启动 Web 服务器失败: {str(e)}")
