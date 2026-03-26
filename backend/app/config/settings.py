"""
应用配置管理模块。

这份文件的职责不是“保存固定常量”，而是把项目运行依赖的外部配置统一收口。
这样做有几个直接好处：
1. 配置来源集中，业务代码不需要到处自己读环境变量。
2. 配置有类型约束，像端口这种字段会自动转换成 int，减少字符串类型带来的隐性 bug。
3. 缺失配置、非法配置可以在应用启动阶段尽早暴露，而不是等到运行某个接口时才报错。
4. 每个字段都能通过 Field 的 description 留下语义说明，后续维护成本更低。
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing_extensions import Self

APP_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """
    应用配置类。

    继承 BaseSettings 的原因：
    1. 字段名会自动映射到同名环境变量，比如 SF_API_KEY <- 环境变量 SF_API_KEY。
    2. 读取到的值会按字段类型做校验和转换，比如 MYSQL_PORT 会被校验为 int。
    3. 支持把默认值、.env 文件、系统环境变量统一放到一个对象里管理。

    配置项会自动从以下来源读取（优先级从高到低）：
    1. 环境变量
    2. .env 文件
    3. 默认值
    """

    # ==================== AI 服务配置 ====================

    # 这里用 Optional[str] + default=None，而不是直接给空字符串，
    # 是为了明确区分“没有配置”与“配置了一个值但内容为空”这两种状态。
    # 对接外部服务时，这种区分通常是有意义的。
    #
    # 硅基流动 API：只有同时提供 Key 和 Base URL，代码才认为这个服务是可用的。
    SF_API_KEY: Optional[str] = Field(default=None, description="硅基流动 API Key")
    SF_BASE_URL: Optional[str] = Field(default=None, description="硅基流动 Base URL")

    # 阿里百炼 API：同样要求 Key 和 URL 成对出现。
    AL_BAILIAN_API_KEY: Optional[str] = Field(
        default=None, description="阿里百炼 API Key"
    )
    AL_BAILIAN_BASE_URL: Optional[str] = Field(
        default=None, description="阿里百炼 Base URL"
    )

    # ==================== 模型配置 ====================

    # 主模型给了默认值，表示项目在“最常见场景”下可以直接启动，
    # 同时又保留通过环境变量覆盖的能力。
    MAIN_MODEL_NAME: Optional[str] = Field(
        default="Qwen/Qwen3-32B", description="主模型名称"
    )

    # 子模型允许为空字符串，说明它不是启动必需项，而是“有就用、没有就跳过”的辅助配置。
    SUB_MODEL_NAME: Optional[str] = Field(default="", description="qwen3-max")

    # ==================== 数据库配置 ====================

    # 数据库配置普遍给默认值，是因为本地开发通常有一套约定俗成的默认环境。
    # 这样新同学或本地调试时不需要先配一大堆环境变量，也能快速跑起来。
    MYSQL_HOST: Optional[str] = Field(default="localhost", description="MySQL主机地址")
    MYSQL_PORT: int = Field(default=3306, description="MySQL端口")
    MYSQL_USER: Optional[str] = Field(default="root", description="MySQL用户名")
    MYSQL_PASSWORD: Optional[str] = Field(default="", description="MySQL密码")
    MYSQL_DATABASE: Optional[str] = Field(default="its_db", description="MySQL数据库名")
    MYSQL_CHARSET: str = Field(default="utf8mb4", description="MySQL字符集")
    MYSQL_CONNECT_TIMEOUT: int = Field(default=10, description="MySQL连接超时（秒）")
    MYSQL_MAX_CONNECTIONS: int = Field(default=5, description="MySQL最大连接数")

    # ==================== 外部服务配置 ====================

    # 知识库服务地址。这里不提供默认值，意味着它更像部署环境相关配置，
    # 不能假设每台机器都有统一地址。
    KNOWLEDGE_BASE_URL: Optional[str] = Field(default=None, description="知识库服务URL")

    # DashScope 相关配置。
    # Base URL 单独放出来，是为了让项目可以兼容不同网关、代理或内部中转地址。
    DASHSCOPE_BASE_URL: Optional[str] = Field(
        default=None, description="通义千问 DashScope Base URL"
    )
    DASHSCOPE_API_KEY: Optional[str] = Field(
        default="sk-26d57c968c364e7bb14f1fc350d4bff0",
        description="通义千问 DashScope API Key",
    )

    # 百度地图服务密钥，只有在确实需要地图能力时才配置。
    BAIDUMAP_AK: Optional[str] = Field(
        default=None, description="百度地图 AK (Access Key)"
    )

    # ==================== Pydantic Settings 配置 ====================

    model_config = SettingsConfigDict(
        # 不把 .env 路径写成硬编码字符串，而是基于当前文件路径动态计算，
        # 这样项目换机器、换工作目录时更稳，不依赖“从哪里启动 Python”。
        #
        # __file__ -> 当前 settings.py
        # parent   -> config 目录
        # parent.parent -> app 目录
        # 最终定位到 backend/app/.env
        env_file=str(APP_ENV_FILE),
        # 显式声明编码，避免 Windows / Linux 环境默认编码不同导致读取异常。
        env_file_encoding="utf-8",
        # 要求环境变量名大小写严格匹配字段名，减少“看起来写了其实没生效”的问题。
        case_sensitive=True,
        # 环境里可能还有别的无关变量，这里选择忽略而不是报错，
        # 让 Settings 只关心自己定义过的字段。
        extra="ignore",
        # 连默认值也一起校验，避免“默认值本身就写错了”却长期没人发现。
        validate_default=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        默认顺序是环境变量优先于 .env。
        这个项目里 app 和 knowledge 都有同名配置项，如果沿用默认顺序，
        一个包预先注入到进程环境中的值就可能覆盖另一个包自己的 .env。

        这里把 dotenv_settings 提前，改成“当前包下的 .env 优先，其次才是系统环境变量”，
        这样每个后端包都会稳定读取自己目录里的配置。
        """
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    # 这个校验器会在整个 Settings 对象构建完成后执行。
    # 选择 mode="after" 是因为这里需要同时查看多个字段的最终结果，
    # 如果在字段级别分别校验，就不容易表达“至少满足一组配置”这种规则。
    @model_validator(mode="after")
    def check_ai_service_configuration(self) -> Self:
        """
        校验“至少有一套 AI 服务可用”。

        这类规则属于“跨字段约束”：
        单看某一个字段都无法判断配置是否合法，必须把 API Key 和 Base URL 成对检查。
        如果启动时一个 AI 服务都没配好，应用后续大概率无法正常工作，
        所以选择在这里直接抛错，尽早失败。
        """
        # 注意：这里 self 已经是完成解析和类型转换后的 Settings 实例，
        # 所以读取到的是“最终配置值”，不是原始字符串。
        has_service = any(
            [
                # and 的写法很常见：只有 Key 和 URL 都为真值时，这一项才算可用。
                self.SF_API_KEY and self.SF_BASE_URL,
                self.AL_BAILIAN_API_KEY and self.AL_BAILIAN_BASE_URL,
            ]
        )

        if not has_service:
            raise ValueError("必须配置至少一个 AI 服务 (硅基流动 或 阿里百炼)")

        # model_validator(mode="after") 约定返回 self，
        # 表示当前对象通过校验，继续作为最终配置对象使用。
        return self


# 在模块导入时就创建一个全局配置实例，目的是让其他代码直接：
# from app.config.settings import settings
# 然后统一从 settings.xxx 取值。
#
# 这种写法的好处是：
# 1. 配置只解析一次，避免每个模块重复读取 .env。
# 2. 如果配置不合法，导入阶段就会失败，问题暴露更早。
settings = Settings()
        
